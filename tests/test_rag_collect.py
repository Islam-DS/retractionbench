import json
from datetime import date
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("faiss")

import retraction_bench.rag.collect as collect_module
from retraction_bench.corpus.embed_index import build_index
from retraction_bench.rag.backends import BackendFatalError, BackendRetryableError
from retraction_bench.rag.cache import ResponseCache
from retraction_bench.rag.collect import (
    ProgressTracker,
    _corpus_text_lookup,
    build_call_fn,
    notice_eligible_item_ids,
    precompute_retrieval,
    write_manifest,
)
from retraction_bench.schemas import (
    BenchmarkItem,
    Claim,
    ClaimPolarity,
    ClaimType,
    Condition,
    EvidenceDirection,
    EvidenceTierMatch,
    ItemType,
    ModelResponse,
    NoticeSpecificity,
    Provenance,
    SourceEvidenceLevel,
    SupersededSource,
    SupersessionType,
)

DIM = 8


def _fake_embed_fn(texts: list[str]) -> np.ndarray:
    vectors = np.zeros((len(texts), DIM), dtype="float32")
    for i, text in enumerate(texts):
        for j, ch in enumerate(text[:DIM]):
            vectors[i, j % DIM] += ord(ch)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms


def _source(registry_id: str, notice_text: str | None, notice_text_verified: bool) -> SupersededSource:
    return SupersededSource(
        source_registry_id=registry_id,
        external_ids={"pmid": f"{registry_id}-pmid"},
        title=f"Title for {registry_id}",
        venue="Journal",
        original_date=date(2017, 6, 1),
        evidence_level=SourceEvidenceLevel.SYNTHESIS,
        notice_specificity=NoticeSpecificity.CATEGORICAL if notice_text_verified else NoticeSpecificity.UNVERIFIABLE,
        notice_text_verified=notice_text_verified,
        notice_text=notice_text,
        supersession_type=SupersessionType.RETRACTION,
        supersession_date=date(2018, 1, 1),
        verification_method="pubmed_retraction_tag",
        verification_confirmed=True,
        summary=f"Abstract for {registry_id}.",
    )


def _item(item_id: str, registry_id: str) -> BenchmarkItem:
    return BenchmarkItem(
        item_id=item_id,
        question=f"Question about {registry_id}?",
        domain="TestDomain",
        claim_type=ClaimType.CLINICAL_INTERVENTION,
        item_type=ItemType.SUPERSEDED_WITH_CURRENT_ANSWER,
        claim_polarity=ClaimPolarity.POSITIVE,
        replacement_exists=False,
        evidence_direction=EvidenceDirection.CONCORDANT,
        evidence_tier_match=EvidenceTierMatch.SAME_TIER,
        trap_claim=Claim(text="trap"),
        gold_claim=Claim(text="gold"),
        supporting_sources=[registry_id],
        post_supersession_evidence=[],
        provenance=Provenance.DRAFT,
    )


# --- notice_eligible_item_ids ---


def test_eligible_when_verified_with_text() -> None:
    sources = {"rw-1": _source("rw-1", "real text", True)}
    items = [_item("RB-01", "rw-1")]
    assert notice_eligible_item_ids(items, sources) == {"RB-01"}


def test_eligible_when_verified_bare() -> None:
    sources = {"rw-1": _source("rw-1", None, True)}
    items = [_item("RB-01", "rw-1")]
    assert notice_eligible_item_ids(items, sources) == {"RB-01"}


def test_eligible_when_unverified_but_has_text() -> None:
    """ADR-136: the case that was wrongly excluded once already."""
    sources = {"rw-1": _source("rw-1", "secondhand text", False)}
    items = [_item("RB-01", "rw-1")]
    assert notice_eligible_item_ids(items, sources) == {"RB-01"}


def test_ineligible_when_no_text_and_unverified() -> None:
    sources = {"rw-1": _source("rw-1", None, False)}
    items = [_item("RB-01", "rw-1")]
    assert notice_eligible_item_ids(items, sources) == set()


# --- _corpus_text_lookup ---


def test_corpus_text_lookup_finds_requested_pmids_only(tmp_path: Path) -> None:
    corpus_path = tmp_path / "corpus.jsonl"
    rows = [
        {"pmid": "1", "title": "T1", "abstract": "A1"},
        {"pmid": "2", "title": "T2", "abstract": "A2"},
        {"pmid": "3", "title": "T3", "abstract": "A3"},
    ]
    corpus_path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    result = _corpus_text_lookup({"1", "3"}, corpus_path)
    assert result == {"1": ("T1", "A1"), "3": ("T3", "A3")}


def test_corpus_text_lookup_raises_if_pmid_missing(tmp_path: Path) -> None:
    corpus_path = tmp_path / "corpus.jsonl"
    corpus_path.write_text(json.dumps({"pmid": "1", "title": "T1", "abstract": "A1"}) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="not found"):
        _corpus_text_lookup({"1", "999"}, corpus_path)


# --- precompute_retrieval (real FAISS, fake embed_fn) ---


def _build_test_corpus_and_index(tmp_path: Path) -> tuple[Path, Path]:
    corpus_path = tmp_path / "corpus.jsonl"
    rows = [
        {
            "pmid": "src-1",
            "title": "The Trap Source",
            "abstract": "trap content",
            "domain": "D",
            "corpus_role": "benchmark_source",
            "linked_source_registry_id": "rw-1",
        },
        {
            "pmid": "rw-1-notice",
            "title": "Notice: The Trap Source",
            "abstract": "retracted",
            "domain": "D",
            "corpus_role": "supersession_notice",
            "linked_source_registry_id": "rw-1",
        },
        {"pmid": "bg-1", "title": "Background 1", "abstract": "bg1", "domain": "D", "corpus_role": "background"},
        {"pmid": "bg-2", "title": "Background 2", "abstract": "bg2", "domain": "D", "corpus_role": "background"},
    ]
    corpus_path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    index_dir = tmp_path / "index"
    build_index(corpus_path, index_dir, embed_fn=_fake_embed_fn, batch_size=2)
    return corpus_path, index_dir


def test_precompute_retrieval_builds_notice_doc_for_eligible_item(tmp_path: Path) -> None:
    corpus_path, index_dir = _build_test_corpus_and_index(tmp_path)
    sources = {"rw-1": _source("rw-1", "real notice text", True)}
    items = [_item("RB-01", "rw-1")]

    result = precompute_retrieval(items, sources, index_dir, corpus_path, embed_fn=_fake_embed_fn)

    assert "RB-01" in result
    r = result["RB-01"]
    assert r.notice_doc is not None
    assert r.notice_doc.doc_id == "rw-1-notice"
    assert len(r.ranked_docs) == 4  # every corpus doc, pool_k=10 > 4 available


def test_precompute_retrieval_notice_doc_none_for_ineligible_item(tmp_path: Path) -> None:
    corpus_path, index_dir = _build_test_corpus_and_index(tmp_path)
    sources = {"rw-1": _source("rw-1", None, False)}  # no notice document exists in this corpus
    items = [_item("RB-01", "rw-1")]

    result = precompute_retrieval(items, sources, index_dir, corpus_path, embed_fn=_fake_embed_fn)
    assert result["RB-01"].notice_doc is None


# --- ProgressTracker ---


def test_progress_tracker_counts_and_computes_rate() -> None:
    tracker = ProgressTracker(total=3)
    tracker.tick("call 1")
    assert tracker.done == 1
    tracker.tick("call 2")
    tracker.tick("call 3")
    assert tracker.done == 3


# --- build_call_fn dispatch and post_notice ordering dependency ---


def _model_response(
    item_id: str, condition: Condition, seed: int, model_identifier: str, answer_text: str
) -> ModelResponse:
    from datetime import datetime

    return ModelResponse(
        response_id=f"{item_id}_{condition.value}_{seed}",
        item_id=item_id,
        model_identifier=model_identifier,
        seed=seed,
        condition=condition,
        raw_answer_text=answer_text,
        prompt_template_id="v1",
        temperature=0.0,
        max_tokens=512,
        call_timestamp=datetime(2026, 8, 20, 12, 0, 0),
    )


def test_post_notice_raises_clearly_if_no_retrieval_not_cached_yet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from retraction_bench.rag.prompts import RenderedDocument

    retrieval_by_item = {
        "RB-01": type(
            "R",
            (),
            {"question": "Q?", "ranked_docs": [], "notice_doc": RenderedDocument("rw-1-notice", "Notice", "text")},
        )()
    }
    cache = ResponseCache(tmp_path / "cache.jsonl")
    progress = ProgressTracker(total=1)
    call_fn = build_call_fn(retrieval_by_item, cache, progress)

    with pytest.raises(RuntimeError, match="no_retrieval must run to completion"):
        call_fn("RB-01", Condition.POST_NOTICE, "fake-model", 1, "v1")


def test_post_notice_succeeds_once_no_retrieval_is_cached(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from retraction_bench.rag.prompts import RenderedDocument

    retrieval_by_item = {
        "RB-01": type(
            "R",
            (),
            {"question": "Q?", "ranked_docs": [], "notice_doc": RenderedDocument("rw-1-notice", "Notice", "text")},
        )()
    }
    cache = ResponseCache(tmp_path / "cache.jsonl")
    cache.put(
        _model_response(
            "RB-01", Condition.NO_RETRIEVAL, 1, "fake-model", "ANSWER: Yes.\nCITED_DOCUMENT_IDS: NONE\nCONFIDENCE: high"
        )
    )

    def fake_backend(model_identifier: str):
        return lambda prompt, model, seed: (
            "ANSWER: Reconsidered.\nCITED_DOCUMENT_IDS: rw-1-notice\nCONFIDENCE: low",
            {},
        )

    monkeypatch.setattr("retraction_bench.rag.collect.resolve_backend", fake_backend)
    progress = ProgressTracker(total=1)
    call_fn = build_call_fn(retrieval_by_item, cache, progress)

    response = call_fn("RB-01", Condition.POST_NOTICE, "fake-model", 1, "v1")
    assert response.condition == Condition.POST_NOTICE
    assert response.retrieved_document_ids == ["rw-1-notice"]
    assert progress.done == 1


# --- write_manifest ---


def test_write_manifest_records_configuration_and_corpus_hash(tmp_path: Path) -> None:
    index_dir = tmp_path / "index"
    index_dir.mkdir()
    manifest_file = index_dir / "corpus_manifest.jsonl"
    manifest_file.write_text('{"pmid": "1"}\n{"pmid": "2"}\n', encoding="utf-8")
    manifest_dir = tmp_path / "manifests"

    out_path = write_manifest(
        manifest_dir,
        models=("model-a", "model-b"),
        seeds=(1, 2, 3),
        conditions=(Condition.NO_RETRIEVAL, Condition.RETRIEVAL_NAIVE),
        item_counts={"no_retrieval": 28, "retrieval_naive": 24},
        index_dir=index_dir,
        root=tmp_path,
    )
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert data["models"] == ["model-a", "model-b"]
    assert data["seeds"] == [1, 2, 3]
    assert data["item_counts_per_condition"] == {"no_retrieval": 28, "retrieval_naive": 24}
    assert data["corpus_manifest_row_count"] == 2
    assert len(data["corpus_manifest_sha256"]) == 64  # a real sha256 hex digest


# --- run_collection: a stalled model must not block the others (the author's explicit instruction) ---


def test_run_collection_skips_stalled_model_and_completes_the_rest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    corpus_path, index_dir = _build_test_corpus_and_index(tmp_path)
    sources = [_source("rw-1", "real notice text", True)]
    items = [_item("RB-01", "rw-1")]

    monkeypatch.setattr(collect_module, "load_items", lambda: items)
    monkeypatch.setattr(collect_module, "load_sources", lambda: sources)
    monkeypatch.setattr(collect_module, "CORPUS_PATH", corpus_path)
    monkeypatch.setattr(collect_module, "INDEX_DIR", index_dir)
    monkeypatch.setattr(collect_module, "CACHE_PATH", tmp_path / "cache.jsonl")
    monkeypatch.setattr(collect_module, "MANIFEST_DIR", tmp_path / "manifests")

    def fake_resolve_backend(model_identifier: str):
        if model_identifier == "broken-model":

            def always_fails(prompt, model, seed):
                raise BackendRetryableError("HTTP 429: daily quota exceeded, retry in 14h32m")

            return always_fails
        return lambda prompt, model, seed: ("ANSWER: Fine.\nCITED_DOCUMENT_IDS: NONE\nCONFIDENCE: high", {})

    monkeypatch.setattr(collect_module, "resolve_backend", fake_resolve_backend)
    monkeypatch.setattr(collect_module, "_default_embed_fn", lambda: _fake_embed_fn)

    result = collect_module.run_collection(models=("broken-model", "working-model"), seeds=(1,))

    assert result.stalled_models == ["broken-model"]
    # the working model still produced its full set of responses despite the other model's stall
    cache = ResponseCache(collect_module.CACHE_PATH)
    working_responses = [r for r in cache.all_responses() if r.model_identifier == "working-model"]
    broken_responses = [r for r in cache.all_responses() if r.model_identifier == "broken-model"]
    assert len(working_responses) == 4  # no_retrieval + naive + with_notice + post_notice, 1 item, 1 seed
    assert len(broken_responses) == 0


def test_run_collection_does_not_swallow_a_fatal_backend_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A BackendFatalError (auth failure, unrecognized model) must propagate uncaught -- unlike
    a quota/network stall, retrying it later would reproduce the identical failure, so a
    supervising process needs to see this as a real crash, not a skip-and-continue.
    """
    corpus_path, index_dir = _build_test_corpus_and_index(tmp_path)
    sources = [_source("rw-1", "real notice text", True)]
    items = [_item("RB-01", "rw-1")]

    monkeypatch.setattr(collect_module, "load_items", lambda: items)
    monkeypatch.setattr(collect_module, "load_sources", lambda: sources)
    monkeypatch.setattr(collect_module, "CORPUS_PATH", corpus_path)
    monkeypatch.setattr(collect_module, "INDEX_DIR", index_dir)
    monkeypatch.setattr(collect_module, "CACHE_PATH", tmp_path / "cache.jsonl")
    monkeypatch.setattr(collect_module, "MANIFEST_DIR", tmp_path / "manifests")

    def fake_resolve_backend(model_identifier: str):
        def always_fails(prompt, model, seed):
            raise BackendFatalError("Groq authentication failed, HTTP 401: invalid api key")

        return always_fails

    monkeypatch.setattr(collect_module, "resolve_backend", fake_resolve_backend)
    monkeypatch.setattr(collect_module, "_default_embed_fn", lambda: _fake_embed_fn)

    with pytest.raises(BackendFatalError, match="authentication failed"):
        collect_module.run_collection(models=("broken-model",), seeds=(1,))
