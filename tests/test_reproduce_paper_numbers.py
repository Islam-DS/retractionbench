"""Integration/regression test: running retraction_bench.reproduce's computation against
the real, committed cached data must reproduce the exact numbers published in paper.md (ADR-153).

This is the test that makes the paper's reproducibility claim actually true -- before this
module existed, the paired test, Holm correction, and Correctness statistics had no committed
code path at all (AUDIT_REPORT.md section 3.2). The expected values below are transcribed
directly from the currently-published paper.md tables (sections 4.2, 4.3, 4.4), not invented; if
this test ever fails, either the code has a real bug or the paper's numbers need to change --
either way, the two must not be allowed to silently drift apart again.

Marked slow: loads the real 900-response cache and all 28 benchmark items/sources from disk,
unlike every other test in this suite, which uses small synthetic fixtures. Still fast in
practice (a few seconds), so not skipped by default -- if CI time ever becomes a concern, this is
the one test file to gate behind a `-m slow` marker.
"""

import pytest

from retraction_bench.curate.benchmark_io import load_items, load_sources
from retraction_bench.rag.cache import ResponseCache

pytestmark = pytest.mark.slow

ROOT_DATA = "data/interim/eval/model_responses.jsonl"


@pytest.fixture(scope="module")
def report():
    from pathlib import Path

    import retraction_bench.reproduce as rpn

    root = Path(rpn.__file__).resolve().parent.parent.parent
    items = load_items()
    sources = load_sources()
    items_by_id = {i.item_id: i for i in items}
    sources_by_id = {s.source_registry_id: s for s in sources}
    responses = list(ResponseCache(root / ROOT_DATA).all_responses())
    return {
        "m1": rpn.compute_m1_section(responses, items_by_id, sources_by_id),
        "m3": rpn.compute_m3_section(),
        "correctness": rpn.compute_correctness_section(),
        "n_responses": len(responses),
    }


def test_response_count_is_900(report) -> None:
    assert report["n_responses"] == 900


def test_m1_by_condition_matches_paper_section_4_2(report) -> None:
    by_cond = report["m1"]["by_condition"]
    assert by_cond["retrieval_naive"]["n"] == 213
    assert by_cond["retrieval_naive"]["rate"] == pytest.approx(0.920, abs=1e-3)
    assert by_cond["retrieval_naive"]["ci"]["ci_low"] == pytest.approx(0.833, abs=1e-3)
    assert by_cond["retrieval_naive"]["ci"]["ci_high"] == pytest.approx(0.991, abs=1e-3)

    assert by_cond["retrieval_with_notice"]["n"] == 209
    assert by_cond["retrieval_with_notice"]["rate"] == pytest.approx(0.794, abs=1e-3)
    assert by_cond["retrieval_with_notice"]["ci"]["ci_low"] == pytest.approx(0.675, abs=1e-3)
    assert by_cond["retrieval_with_notice"]["ci"]["ci_high"] == pytest.approx(0.899, abs=1e-3)


def test_m1_paired_test_matches_paper_section_4_2(report) -> None:
    paired = report["m1"]["paired_test_naive_vs_notice"]

    llama = paired["llama3.1:8b-instruct-q4_K_M"]
    assert llama["n_items"] == 21
    assert llama["mean_diff"] == pytest.approx(0.0, abs=1e-9)
    assert llama["raw_p"] == pytest.approx(1.0000, abs=1e-4)
    assert llama["holm_p"] == pytest.approx(1.0000, abs=1e-4)

    gptoss = paired["openai/gpt-oss-120b"]
    assert gptoss["mean_diff"] == pytest.approx(-0.097, abs=1e-3)
    assert gptoss["ci_low"] == pytest.approx(-0.236, abs=1e-3)
    assert gptoss["ci_high"] == pytest.approx(0.028, abs=1e-3)
    assert gptoss["raw_p"] == pytest.approx(0.1887, abs=5e-3)
    assert gptoss["holm_p"] == pytest.approx(0.3774, abs=1e-2)

    qwen = paired["qwen2.5:7b-instruct-q4_K_M"]
    assert qwen["mean_diff"] == pytest.approx(-0.306, abs=1e-3)
    assert qwen["ci_low"] == pytest.approx(-0.500, abs=1e-3)
    assert qwen["ci_high"] == pytest.approx(-0.111, abs=1e-3)
    assert qwen["raw_p"] == pytest.approx(0.0067, abs=5e-3)
    assert qwen["holm_p"] == pytest.approx(0.0201, abs=1e-2)


def test_m1_seed_agreement_matches_paper_section_4_2(report) -> None:
    agreement = report["m1"]["seed_agreement"]
    assert agreement["llama3.1:8b-instruct-q4_K_M"] == {"n_groups": 97, "n_3_of_3_agree": 97}
    assert agreement["qwen2.5:7b-instruct-q4_K_M"] == {"n_groups": 100, "n_3_of_3_agree": 99}
    assert agreement["openai/gpt-oss-120b"] == {"n_groups": 99, "n_3_of_3_agree": 94}


def test_m3_overall_matches_paper_section_4_4(report) -> None:
    overall = report["m3"]["overall"]
    assert overall["n"] == 150
    assert overall["counts"]["acknowledges"] == 84
    assert overall["counts"]["defends"] == 38
    assert overall["counts"]["silently_revises"] == 28


def test_correctness_overall_matches_paper_section_4_3(report) -> None:
    overall = report["correctness"]["overall"]
    assert overall["n"] == 100
    assert overall["counts"]["correct"] == 40
    assert overall["counts"]["incorrect"] == 47
    assert overall["counts"]["refused"] == 13
    assert overall["cis"]["correct"]["ci_low"] == pytest.approx(0.232, abs=1e-3)
    assert overall["cis"]["correct"]["ci_high"] == pytest.approx(0.560, abs=1e-3)
