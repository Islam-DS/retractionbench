from pathlib import Path

from retraction_bench.eval.llm_judge import (
    CORRECTNESS_LABELS,
    M3_LABELS,
    build_correctness_prompt,
    build_m3_prompt,
    load_existing_judgments,
    parse_judge_response,
    run_judge,
)

# --- parse_judge_response ---


def test_parses_well_formed_m3_response() -> None:
    text = "LABEL: acknowledges\nREASONING: it named the retraction directly."
    label, reasoning = parse_judge_response(text, M3_LABELS)
    assert label == "acknowledges"
    assert reasoning == "it named the retraction directly."


def test_parse_is_case_insensitive_on_label_value() -> None:
    text = "LABEL: DEFENDS\nREASONING: unchanged claim."
    label, _ = parse_judge_response(text, M3_LABELS)
    assert label == "defends"


def test_parse_rejects_label_outside_the_valid_set() -> None:
    text = "LABEL: maybe\nREASONING: not sure."
    label, reasoning = parse_judge_response(text, M3_LABELS)
    assert label is None
    assert reasoning == text[:300]


def test_parse_rejects_missing_label_line() -> None:
    text = "The model acknowledges the error."
    label, _ = parse_judge_response(text, M3_LABELS)
    assert label is None


def test_correctness_labels_are_distinct_from_m3_labels() -> None:
    text = "LABEL: correct\nREASONING: matches the gold claim."
    assert parse_judge_response(text, CORRECTNESS_LABELS)[0] == "correct"
    assert parse_judge_response(text, M3_LABELS)[0] is None


# --- prompt builders ---


def test_build_m3_prompt_includes_all_four_fields() -> None:
    rec = {
        "question": "Does X help Y?",
        "turn1_answer": "ANSWER: Yes.",
        "notice_title": "Notice: Paper Z",
        "notice_text": "This article has been retracted.",
        "turn2_answer": "ANSWER: Unclear now.",
    }
    prompt = build_m3_prompt(rec)
    for value in rec.values():
        assert value in prompt


def test_build_correctness_prompt_includes_gold_claim_and_answer() -> None:
    rec = {"question": "Does X help Y?", "gold_claim": "X does not help Y.", "raw_answer_text": "ANSWER: X helps Y."}
    prompt = build_correctness_prompt(rec)
    assert rec["gold_claim"] in prompt
    assert rec["raw_answer_text"] in prompt


# --- run_judge: resumability and injected call_fn ---


def test_run_judge_calls_once_per_record_and_writes_results(tmp_path: Path) -> None:
    records = [
        {"response_id": "r1", "question": "Q1"},
        {"response_id": "r2", "question": "Q2"},
    ]
    calls = []

    def fake_call(prompt: str) -> str:
        calls.append(prompt)
        return "LABEL: defends\nREASONING: no change."

    out_path = tmp_path / "results.jsonl"
    done = run_judge(records, out_path, lambda r: r["question"], M3_LABELS, fake_call, delay_seconds=0)

    assert done == 2
    assert len(calls) == 2
    results = load_existing_judgments(out_path)
    assert set(results) == {"r1", "r2"}
    assert results["r1"]["judge_label"] == "defends"


def test_run_judge_skips_already_judged_records_on_resume(tmp_path: Path) -> None:
    records = [
        {"response_id": "r1", "question": "Q1"},
        {"response_id": "r2", "question": "Q2"},
    ]
    out_path = tmp_path / "results.jsonl"
    calls = []

    def fake_call(prompt: str) -> str:
        calls.append(prompt)
        return "LABEL: acknowledges\nREASONING: named the error."

    # First run judges only r1 (simulating an interrupted run)
    run_judge(records[:1], out_path, lambda r: r["question"], M3_LABELS, fake_call, delay_seconds=0)
    assert len(calls) == 1

    # Second run, given the full record list, must not re-call for r1
    done = run_judge(records, out_path, lambda r: r["question"], M3_LABELS, fake_call, delay_seconds=0)
    assert done == 2
    assert len(calls) == 2  # only one new call made (for r2)


def test_run_judge_preserves_extra_fields_in_output(tmp_path: Path) -> None:
    records = [{"response_id": "r1", "question": "Q1", "model": "test-model", "item_id": "RB-0001"}]
    out_path = tmp_path / "results.jsonl"
    run_judge(
        records,
        out_path,
        lambda r: r["question"],
        M3_LABELS,
        lambda p: "LABEL: unclear\nREASONING: ambiguous.",
        extra_fields=("model", "item_id"),
        delay_seconds=0,
    )
    results = load_existing_judgments(out_path)
    assert results["r1"]["model"] == "test-model"
    assert results["r1"]["item_id"] == "RB-0001"


def test_load_existing_judgments_returns_empty_dict_when_file_missing(tmp_path: Path) -> None:
    assert load_existing_judgments(tmp_path / "does_not_exist.jsonl") == {}
