"""A direct, empirical check of this paper's central conceptual claim (Introduction, Related
Work): that a standard automated faithfulness/groundedness check would score a citation of a
retracted source as a success. Not part of the headline M1/M3/Correctness pipeline and not
subject to the project protocol's no-LLM-ground-truth rule the way those are -- this module
applies a well-established automated *metric* (NLI-based factual-consistency scoring, in the
lineage of Laban et al. 2022's SummaC) to the model's own output, exactly as a real faithfulness
pipeline would, and reports what that metric says. It is not used to establish or substitute for
any ground-truth label anywhere else in this project.

Method: for every parsed `retrieval_naive`/`retrieval_with_notice` response where the model
cited the trap source (M1's own `cites_superseded` condition), score NLI entailment between the
trap source's title+abstract (the premise -- exactly the text the model was actually shown, per
`rag/prompts.py`'s own rendering) and the model's parsed answer (the hypothesis), using
`roberta-large-mnli` (Liu et al. 2019's RoBERTa, fine-tuned on MNLI, Williams et al. 2018).

Known limitation, stated plainly rather than glossed over: this is whole-document-premise vs.
whole-answer-hypothesis NLI, not SummaC's sentence-segmented-and-aggregated approach -- Laban et
al. specifically found raw whole-document NLI underperforms for exactly this kind of task due to
a granularity mismatch between NLI training data (sentence-level) and real premises (paragraph-
or document-level). This is reported as a lighter-weight demonstration of the same underlying
question, not a claim to have reproduced SummaC's full method or its accuracy.
"""

import json
from collections import defaultdict
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from retraction_bench.curate.benchmark_io import load_items, load_sources
from retraction_bench.rag.cache import ResponseCache
from retraction_bench.rag.parse import parse_response
from retraction_bench.stats.bootstrap import bootstrap_proportion_ci

ROOT = Path(__file__).resolve().parents[3]
NLI_MODEL = "roberta-large-mnli"
BATCH_SIZE = 16
OUT_PATH = ROOT / "data/interim/eval/faithfulness_check_nli.json"


def collect_pairs() -> list[tuple[str, str, str, str, str]]:
    """Every (response_id, model, condition, premise, hypothesis) pair where a parsed response
    under retrieval_naive/retrieval_with_notice cited the item's trap source. Premise is the
    trap source's title+abstract exactly as rendered to the model; hypothesis is the model's
    own parsed answer text.
    """
    items = {i.item_id: i for i in load_items()}
    sources = {s.source_registry_id: s for s in load_sources()}

    corpus_text: dict[str, tuple[str, str]] = {}
    with open(ROOT / "data/interim/corpus/assembled_corpus.jsonl", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            corpus_text[row["pmid"]] = (row["title"], row["abstract"])

    cache = ResponseCache(ROOT / "data/interim/eval/model_responses.jsonl")

    pairs = []
    for r in cache.all_responses():
        if r.condition.value not in ("retrieval_naive", "retrieval_with_notice"):
            continue
        parsed = parse_response(r.raw_answer_text)
        if parsed.parse_status.value != "parsed":
            continue
        item = items[r.item_id]
        src = sources[item.supporting_sources[0]]
        trap_pmid = src.external_ids.get("pmid")
        if trap_pmid not in (parsed.cited_document_ids or []):
            continue
        title, abstract = corpus_text.get(trap_pmid, (None, None))
        if not abstract:
            continue
        pairs.append((r.response_id, r.model_identifier, r.condition.value, f"{title}\n{abstract}", parsed.answer))
    return pairs


def score_pairs(pairs: list[tuple[str, str, str, str, str]]) -> list[dict]:
    tok = AutoTokenizer.from_pretrained(NLI_MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(NLI_MODEL)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device).eval()
    id2label = model.config.id2label

    results = []
    with torch.no_grad():
        for i in range(0, len(pairs), BATCH_SIZE):
            batch = pairs[i : i + BATCH_SIZE]
            inputs = tok(
                [b[3] for b in batch],
                [b[4] for b in batch],
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=512,
            ).to(device)
            probs = torch.softmax(model(**inputs).logits, dim=-1).cpu()
            for (rid, mdl, cond, _, _), p in zip(batch, probs):
                results.append(
                    {
                        "response_id": rid,
                        "model": mdl,
                        "condition": cond,
                        "label": id2label[int(p.argmax())],
                        "p_contradiction": float(p[0]),
                        "p_neutral": float(p[1]),
                        "p_entailment": float(p[2]),
                    }
                )
    return results


def report(results: list[dict]) -> None:
    labels = [r["label"] for r in results]
    n = len(labels)
    print("\n=== Overall label distribution ===")
    for lbl in ("ENTAILMENT", "NEUTRAL", "CONTRADICTION"):
        res = bootstrap_proportion_ci([lab == lbl for lab in labels])
        print(f"  {lbl:15s} {labels.count(lbl)}/{n} = {res.point_estimate:.3f} CI=[{res.ci_low:.3f},{res.ci_high:.3f}]")

    not_contra = [r["label"] != "CONTRADICTION" for r in results]
    res = bootstrap_proportion_ci(not_contra)
    print(
        f"\nNOT CONTRADICTION (practical 'would pass a faithfulness check' proxy): "
        f"{sum(not_contra)}/{n} = {res.point_estimate:.3f} CI=[{res.ci_low:.3f},{res.ci_high:.3f}]"
    )

    for label, key in (("condition", "condition"), ("model", "model")):
        print(f"\n=== By {label} ===")
        grouped = defaultdict(list)
        for r in results:
            grouped[r[key]].append(r["label"] != "CONTRADICTION")
        for k, vals in grouped.items():
            res = bootstrap_proportion_ci(vals)
            print(f"  {k:35s} not-contradiction rate = {res.point_estimate:.3f} CI=[{res.ci_low:.3f},{res.ci_high:.3f}] n={len(vals)}")


def main() -> None:
    pairs = collect_pairs()
    print(f"n pairs (parsed, cites trap source, retrieval_naive/with_notice): {len(pairs)}")
    results = score_pairs(pairs)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
    report(results)


if __name__ == "__main__":
    main()
