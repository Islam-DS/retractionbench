"""Collection orchestrator (ADR-137): iterates {item x condition x seed x model} through
retrieval, prompt rendering, and a model backend into `cache.py`'s resume-safe store.

Two standing risks this module is built against, both named by the author before any call
fired:

1. **Resumability.** ADR-133 found a corpus-fetch bug that silently duplicated ~19% of a
   corpus because progress was tracked too coarsely and re-appended on interruption. This
   module reuses `cache.py`'s already-tested per-(item, condition, model, seed) cache
   unchanged rather than inventing its own resumability logic -- the one thing this session
   just proved is expensive to get wrong is not the thing to redesign under time pressure.
2. **Traceability.** ADR-133/136 both corrected numbers computed against a corpus that had
   since changed, twice. `write_manifest` records the exact corpus/index state (hashed, not
   just named), the exact code commit, and the exact configuration for every collection run,
   so a future "why doesn't this number match" question has a file to check against instead
   of a memory to trust.

Item eligibility differs by condition (ADR-135/136): `no_retrieval` runs on all 28 items;
`retrieval_naive`, `retrieval_with_notice`, and `post_notice` run only on the 24 items with a
retrievable notice document (`source.notice_text or source.notice_text_verified`) -- the other
four have nothing for these three conditions to exclude, inject, or show.
"""

import hashlib
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from retraction_bench.corpus.embed_index import _default_embed_fn, load_index, search
from retraction_bench.curate.benchmark_io import load_items, load_sources
from retraction_bench.rag.backends import GROQ_MODEL, OLLAMA_MODELS, BackendRetryableError, resolve_backend
from retraction_bench.rag.cache import ResponseCache, missing_keys, run_with_cache
from retraction_bench.rag.parse import parse_response
from retraction_bench.rag.pipeline import (
    build_post_notice_turn2,
    select_retrieval_naive_documents,
    select_retrieval_with_notice_documents,
)
from retraction_bench.rag.prompts import (
    RenderedDocument,
    render_no_retrieval_prompt,
    render_retrieval_prompt,
)
from retraction_bench.schemas import BenchmarkItem, Condition, ModelResponse, SupersededSource

ROOT = Path(__file__).resolve().parents[3]
CORPUS_PATH = ROOT / "data/interim/corpus/assembled_corpus.jsonl"
INDEX_DIR = ROOT / "data/interim/corpus/index"
CACHE_PATH = ROOT / "data/interim/eval/model_responses.jsonl"
MANIFEST_DIR = ROOT / "data/interim/eval/manifests"

MODELS: tuple[str, ...] = (GROQ_MODEL, *OLLAMA_MODELS)
SEEDS: tuple[int, ...] = (1, 2, 3)
CONDITIONS_ORDER: tuple[Condition, ...] = (
    Condition.NO_RETRIEVAL,
    Condition.RETRIEVAL_NAIVE,
    Condition.RETRIEVAL_WITH_NOTICE,
    Condition.POST_NOTICE,
)
PROMPT_TEMPLATE_ID = "v1"
RETRIEVAL_POOL_K = 10  # depth fetched per item, enough to backfill after notice-exclusion
RETRIEVAL_K = 5  # documents actually shown to the model, matches prompts.RETRIEVAL_K


def notice_eligible_item_ids(items: list[BenchmarkItem], sources: dict[str, SupersededSource]) -> set[str]:
    """The 24-item set (ADR-136): a source is eligible when it has real notice text, a
    confirmed-bare notice, or both -- excluded only when neither exists (nothing to retrieve).
    """
    eligible_registry_ids = {rid for rid, s in sources.items() if s.notice_text or s.notice_text_verified}
    return {item.item_id for item in items if item.supporting_sources[0] in eligible_registry_ids}


@dataclass
class ItemRetrieval:
    question: str
    ranked_docs: list[RenderedDocument]  # top RETRIEVAL_POOL_K, naive similarity order
    notice_doc: RenderedDocument | None  # None for the 4 items with no retrievable notice at all


def _corpus_text_lookup(pmids: set[str], corpus_path: Path) -> dict[str, tuple[str, str]]:
    """One sequential pass over the corpus file, picking out only the requested pmids' (title,
    abstract) -- avoids holding all 325k rows' text in memory when only a few hundred are
    needed (the corpus_manifest.jsonl used for retrieval carries pmid/domain/role only, not
    title/text, by embed_index.py's design).
    """
    found: dict[str, tuple[str, str]] = {}
    remaining = set(pmids)
    with corpus_path.open(encoding="utf-8") as f:
        for line in f:
            if not remaining:
                break
            row = json.loads(line)
            if row["pmid"] in remaining:
                found[row["pmid"]] = (row.get("title", ""), row.get("abstract", ""))
                remaining.discard(row["pmid"])
    if remaining:
        raise ValueError(f"{len(remaining)} pmid(s) expected in the corpus were not found: {sorted(remaining)[:10]}")
    return found


def precompute_retrieval(
    items: list[BenchmarkItem],
    sources: dict[str, SupersededSource],
    index_dir: Path,
    corpus_path: Path,
    embed_fn=None,
) -> dict[str, ItemRetrieval]:
    """Runs retrieval once per item (not once per item x model x seed x condition -- retrieval
    is deterministic given the corpus and question, independent of all three) and resolves
    every retrieved pmid's actual title/abstract text in one pass over the corpus file.
    """
    embed_fn = embed_fn or _default_embed_fn()
    index, manifest = load_index(index_dir)
    eligible_ids = notice_eligible_item_ids(items, sources)

    per_item_hits: dict[str, list[dict]] = {}
    notice_pmid_by_item: dict[str, str | None] = {}
    needed_pmids: set[str] = set()

    for item in items:
        query_vector = embed_fn([item.question])
        hits = search(index, manifest, query_vector, k=RETRIEVAL_POOL_K)
        per_item_hits[item.item_id] = hits
        needed_pmids.update(h["pmid"] for h in hits)

        if item.item_id in eligible_ids:
            registry_id = item.supporting_sources[0]
            notice_pmid = f"{registry_id}-notice"
            notice_pmid_by_item[item.item_id] = notice_pmid
            needed_pmids.add(notice_pmid)
        else:
            notice_pmid_by_item[item.item_id] = None

    text_by_pmid = _corpus_text_lookup(needed_pmids, corpus_path)

    result: dict[str, ItemRetrieval] = {}
    for item in items:
        hits = per_item_hits[item.item_id]
        ranked_docs = [RenderedDocument(h["pmid"], *text_by_pmid[h["pmid"]]) for h in hits]
        notice_pmid = notice_pmid_by_item[item.item_id]
        notice_doc = RenderedDocument(notice_pmid, *text_by_pmid[notice_pmid]) if notice_pmid else None
        result[item.item_id] = ItemRetrieval(question=item.question, ranked_docs=ranked_docs, notice_doc=notice_doc)
    return result


def _model_slug(model_identifier: str) -> str:
    return model_identifier.replace("/", "-").replace(":", "-")


class ProgressTracker:
    """Logs calls completed/remaining/rate/ETA to stdout as the run proceeds -- an hours-long
    run with no visible output is indistinguishable from a hung one (the author's explicit
    concern), so this logs on every real call, not just periodically.
    """

    def __init__(self, total: int) -> None:
        self.total = total
        self.done = 0
        self.start = time.monotonic()

    def tick(self, label: str) -> None:
        self.done += 1
        elapsed = time.monotonic() - self.start
        rate = self.done / elapsed if elapsed > 0 else 0.0
        remaining = self.total - self.done
        eta_seconds = remaining / rate if rate > 0 else float("inf")
        eta = "unknown" if eta_seconds == float("inf") else f"{eta_seconds / 60:.1f}m"
        print(
            f"[{self.done}/{self.total}] {label}  rate={rate * 60:.1f}/min  elapsed={elapsed / 60:.1f}m  eta={eta}",
            flush=True,
        )


def build_call_fn(
    retrieval_by_item: dict[str, ItemRetrieval],
    cache: ResponseCache,
    progress: ProgressTracker,
):
    """Returns the closure `run_with_cache` calls on every cache miss. Reads `cache` for
    `post_notice`'s same-seed `no_retrieval` dependency -- correct only because
    `CONDITIONS_ORDER` runs `no_retrieval` to completion (all items, models, seeds) before any
    other condition starts, so that response is always already in `cache` by the time this
    branch needs it (see `run_collection`'s per-condition `run_with_cache` calls).
    """

    def call_fn(
        item_id: str, condition: Condition, model_identifier: str, seed: int, prompt_template_id: str
    ) -> ModelResponse:
        # Resolved after the prompt is built, not before: an unresolvable model_identifier
        # should not mask a more specific prompt-construction failure (e.g. post_notice's
        # missing-turn1 check) with a less informative "unrecognized model" error instead.
        retrieval = retrieval_by_item[item_id]
        response_id = f"{item_id}_{condition.value}_{seed}_{_model_slug(model_identifier)}"
        retrieved_ids: list[str] = []

        if condition == Condition.NO_RETRIEVAL:
            prompt = render_no_retrieval_prompt(retrieval.question)
        elif condition == Condition.RETRIEVAL_NAIVE:
            docs = select_retrieval_naive_documents(retrieval.ranked_docs, retrieval.notice_doc, k=RETRIEVAL_K)
            retrieved_ids = [d.doc_id for d in docs]
            prompt = render_retrieval_prompt(docs, retrieval.question)
        elif condition == Condition.RETRIEVAL_WITH_NOTICE:
            docs = select_retrieval_with_notice_documents(retrieval.ranked_docs, retrieval.notice_doc, k=RETRIEVAL_K)
            retrieved_ids = [d.doc_id for d in docs]
            prompt = render_retrieval_prompt(docs, retrieval.question)
        elif condition == Condition.POST_NOTICE:
            from retraction_bench.rag.cache import cache_key

            turn1_key = cache_key(item_id, Condition.NO_RETRIEVAL, model_identifier, seed, prompt_template_id)
            turn1_response = cache.get(turn1_key)
            if turn1_response is None:
                raise RuntimeError(
                    f"post_notice for {item_id}/{model_identifier}/seed={seed} needs a cached "
                    "no_retrieval response for the same seed, and none was found -- "
                    "no_retrieval must run to completion before post_notice starts."
                )
            assert retrieval.notice_doc is not None, f"{item_id} is not notice-eligible; should not reach post_notice"
            retrieved_ids = [retrieval.notice_doc.doc_id]
            prompt = build_post_notice_turn2(turn1_response, seed, retrieval.notice_doc, retrieval.question)
        else:
            raise ValueError(f"Unhandled condition: {condition!r}")

        backend = resolve_backend(model_identifier)
        raw_text, usage = backend(prompt, model_identifier, seed)
        parsed = parse_response(raw_text)

        response = ModelResponse(
            response_id=response_id,
            item_id=item_id,
            model_identifier=model_identifier,
            seed=seed,
            condition=condition,
            retrieved_document_ids=retrieved_ids,
            raw_answer_text=raw_text,
            prompt_template_id=prompt_template_id,
            temperature=0.0,
            max_tokens=512,
            call_timestamp=datetime.now(),
            raw_call_metadata=usage,
            verbalised_confidence=parsed.confidence,
        )
        progress.tick(f"{item_id} {condition.value} seed={seed} {model_identifier}")
        return response

    return call_fn


def _git_commit_and_dirty(root: Path) -> tuple[str | None, bool]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--short"], cwd=root, capture_output=True, text=True, check=True
        ).stdout
        return commit, bool(status.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None, True  # can't confirm clean -- treat as dirty rather than assume


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest(
    manifest_dir: Path,
    models: tuple[str, ...],
    seeds: tuple[int, ...],
    conditions: tuple[Condition, ...],
    item_counts: dict[str, int],
    index_dir: Path,
    root: Path,
) -> Path:
    """Every result file traceable to the exact configuration that produced it (the author's
    explicit instruction, having been bitten twice by this exact gap) -- models, seeds,
    conditions, per-condition item counts, a hash of the corpus manifest actually searched
    (not just its path -- the path stayed the same across all three corpus rebuilds today), and
    the code commit, written once at the start of a run, not reconstructed after the fact.
    """
    manifest_path_file = index_dir / "corpus_manifest.jsonl"
    commit, dirty = _git_commit_and_dirty(root)
    manifest = {
        "run_started_at": datetime.now().isoformat(),
        "models": list(models),
        "seeds": list(seeds),
        "conditions": [c.value for c in conditions],
        "item_counts_per_condition": item_counts,
        "prompt_template_id": PROMPT_TEMPLATE_ID,
        "corpus_manifest_path": str(manifest_path_file),
        "corpus_manifest_sha256": _sha256_file(manifest_path_file),
        "corpus_manifest_row_count": sum(1 for _ in manifest_path_file.open(encoding="utf-8")),
        "git_commit": commit,
        "git_working_tree_dirty": dirty,
        "python_version": sys.version,
    }
    manifest_dir.mkdir(parents=True, exist_ok=True)
    out_path = manifest_dir / f"run_{datetime.now().strftime('%Y%m%dT%H%M%S')}.json"
    out_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if dirty:
        print(
            f"WARNING: git working tree is dirty -- {out_path.name}'s git_commit "
            "does not fully describe the code that produced these results.",
            flush=True,
        )
    return out_path


@dataclass
class CollectionResult:
    manifest_path: Path
    stalled_models: list[str]
    total_responses: int


def run_collection(
    models: tuple[str, ...] = MODELS,
    seeds: tuple[int, ...] = SEEDS,
    dry_run_items: list[str] | None = None,
) -> CollectionResult:
    """Full orchestration entry point. `dry_run_items`, if given, restricts collection to
    those item_ids (still across all eligible conditions/models/seeds) -- the project protocol's
    cost-discipline rule and this project's own staged rollout (docs/STATUS.md) both call for a
    small real run before the full one, not a hand-estimated one.
    """
    items = load_items()
    sources_list = load_sources()
    sources = {s.source_registry_id: s for s in sources_list}
    eligible_ids = notice_eligible_item_ids(items, sources)

    if dry_run_items is not None:
        items = [i for i in items if i.item_id in dry_run_items]

    retrieval_by_item = precompute_retrieval(items, sources, INDEX_DIR, CORPUS_PATH)

    all_item_ids = [i.item_id for i in items]
    eligible_item_ids = [i.item_id for i in items if i.item_id in eligible_ids]
    item_ids_per_condition = {
        Condition.NO_RETRIEVAL: all_item_ids,
        Condition.RETRIEVAL_NAIVE: eligible_item_ids,
        Condition.RETRIEVAL_WITH_NOTICE: eligible_item_ids,
        Condition.POST_NOTICE: eligible_item_ids,
    }

    cache = ResponseCache(CACHE_PATH)

    total_missing = 0
    for condition in CONDITIONS_ORDER:
        total_missing += len(
            missing_keys(
                item_ids_per_condition[condition], [condition], list(models), list(seeds), PROMPT_TEMPLATE_ID, cache
            )
        )

    manifest_path = write_manifest(
        MANIFEST_DIR,
        models,
        seeds,
        CONDITIONS_ORDER,
        {c.value: len(item_ids_per_condition[c]) for c in CONDITIONS_ORDER},
        INDEX_DIR,
        ROOT,
    )
    print(f"Manifest written: {manifest_path}")
    print(f"Total calls pending: {total_missing} (already cached: {len(cache)})")

    progress = ProgressTracker(total_missing)
    call_fn = build_call_fn(retrieval_by_item, cache, progress)

    # Model-outer, condition-inner (not condition-outer as an earlier draft had it): a model
    # that stalls (a persistent quota, not a transient blip -- backends.py already retries
    # transient ones) must not block the other models' progress. Looping condition-outer with
    # all models passed to one run_with_cache call would mean a Groq failure on item 3 aborts
    # that whole call, including the Ollama models' still-answerable work for items 4-28 in the
    # same condition. Per-model isolation is the only way "partial results across all items beat
    # complete results for one model" (the author's explicit instruction) is actually true.
    # post_notice's same-seed no_retrieval ordering guarantee still holds per model, since
    # CONDITIONS_ORDER still runs no_retrieval to completion for a model before that same
    # model's other conditions start.
    stalled_models: list[str] = []
    for model in models:
        try:
            for condition in CONDITIONS_ORDER:
                run_with_cache(
                    item_ids_per_condition[condition],
                    [condition],
                    [model],
                    list(seeds),
                    PROMPT_TEMPLATE_ID,
                    call_fn,
                    cache,
                )
        except BackendRetryableError as e:
            # A BackendFatalError (auth failure, unrecognized model, malformed request) is
            # deliberately NOT caught here -- it propagates uncaught, since retrying it later
            # would reproduce the identical failure. Only a retryable stall (quota, 5xx, network)
            # is worth skipping past and coming back to.
            stalled_models.append(model)
            print(
                f"\nSTALLED on {model}: {e}\n"
                f"Skipping remaining calls for this model -- other models continue. "
                f"Re-run the same command later to pick up where {model} left off "
                f"(already-cached responses for it are not re-called).\n",
                flush=True,
            )
            continue

    print(f"Collection complete. {len(cache)} total responses in {CACHE_PATH}")
    if stalled_models:
        print(f"Stalled models (incomplete, resumable): {stalled_models}")
    return CollectionResult(manifest_path=manifest_path, stalled_models=stalled_models, total_responses=len(cache))


if __name__ == "__main__":
    run_collection()
