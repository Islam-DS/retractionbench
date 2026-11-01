import contextlib
from datetime import datetime
from pathlib import Path

from retraction_bench.rag.cache import ResponseCache, cache_key, missing_keys, run_with_cache
from retraction_bench.schemas import Condition, ModelResponse


def _response(
    item_id: str,
    condition: Condition,
    model_identifier: str,
    seed: int,
    prompt_template_id: str = "v1",
) -> ModelResponse:
    return ModelResponse(
        response_id=f"{item_id}-{condition}-{model_identifier}-{seed}",
        item_id=item_id,
        model_identifier=model_identifier,
        seed=seed,
        condition=condition,
        raw_answer_text="answer",
        prompt_template_id=prompt_template_id,
        temperature=0.0,
        max_tokens=256,
        call_timestamp=datetime(2026, 8, 20, 12, 0, 0),
    )


def test_cache_key_is_stable_tuple() -> None:
    key = cache_key("RB-0001", Condition.NO_RETRIEVAL, "model-a", 1, "v1")
    assert key == ("RB-0001", "no_retrieval", "model-a", 1, "v1")


def test_empty_cache_has_nothing(tmp_path: Path) -> None:
    cache = ResponseCache(tmp_path / "cache.jsonl")
    assert len(cache) == 0
    assert cache.get(cache_key("RB-0001", Condition.NO_RETRIEVAL, "m", 1, "v1")) is None


def test_put_then_get_roundtrip(tmp_path: Path) -> None:
    cache = ResponseCache(tmp_path / "cache.jsonl")
    response = _response("RB-0001", Condition.NO_RETRIEVAL, "model-a", 1)
    cache.put(response)

    key = cache_key("RB-0001", Condition.NO_RETRIEVAL, "model-a", 1, "v1")
    assert cache.has(key)
    assert cache.get(key).response_id == response.response_id


def test_put_writes_to_disk_immediately(tmp_path: Path) -> None:
    cache_path = tmp_path / "cache.jsonl"
    cache = ResponseCache(cache_path)
    cache.put(_response("RB-0001", Condition.NO_RETRIEVAL, "model-a", 1))

    assert cache_path.exists()
    lines = cache_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1


def test_reloading_cache_from_disk_recovers_prior_puts_simulating_resume(tmp_path: Path) -> None:
    cache_path = tmp_path / "cache.jsonl"
    first = ResponseCache(cache_path)
    first.put(_response("RB-0001", Condition.NO_RETRIEVAL, "model-a", 1))
    first.put(_response("RB-0002", Condition.NO_RETRIEVAL, "model-a", 1))
    # Simulate a crash: no explicit close/flush call needed since put() already flushed.
    # A fresh ResponseCache instance over the same path is what "resuming a run" looks like.
    second = ResponseCache(cache_path)
    assert len(second) == 2
    assert second.has(cache_key("RB-0001", Condition.NO_RETRIEVAL, "model-a", 1, "v1"))
    assert second.has(cache_key("RB-0002", Condition.NO_RETRIEVAL, "model-a", 1, "v1"))


def test_run_with_cache_skips_already_cached_and_calls_for_the_rest(tmp_path: Path) -> None:
    cache = ResponseCache(tmp_path / "cache.jsonl")
    cache.put(_response("RB-0001", Condition.NO_RETRIEVAL, "model-a", 1))

    calls_made: list[tuple] = []

    def fake_call(item_id, condition, model_identifier, seed, prompt_template_id):
        calls_made.append((item_id, condition, model_identifier, seed))
        return _response(item_id, condition, model_identifier, seed, prompt_template_id)

    results = run_with_cache(
        item_ids=["RB-0001", "RB-0002"],
        conditions=[Condition.NO_RETRIEVAL],
        model_identifiers=["model-a"],
        seeds=[1],
        prompt_template_id="v1",
        call_fn=fake_call,
        cache=cache,
    )

    assert len(results) == 2
    # Only RB-0002 should have triggered a real call -- RB-0001 was already cached.
    assert calls_made == [("RB-0002", Condition.NO_RETRIEVAL, "model-a", 1)]


def test_run_with_cache_writes_new_calls_to_cache_as_it_goes(tmp_path: Path) -> None:
    cache_path = tmp_path / "cache.jsonl"
    cache = ResponseCache(cache_path)

    def fake_call(item_id, condition, model_identifier, seed, prompt_template_id):
        return _response(item_id, condition, model_identifier, seed, prompt_template_id)

    run_with_cache(
        item_ids=["RB-0001"],
        conditions=[Condition.NO_RETRIEVAL],
        model_identifiers=["model-a"],
        seeds=[1, 2, 3],
        prompt_template_id="v1",
        call_fn=fake_call,
        cache=cache,
    )

    # A fresh instance over the same path proves the writes were flushed, not just in memory.
    reloaded = ResponseCache(cache_path)
    assert len(reloaded) == 3


def test_run_with_cache_simulated_interruption_resumes_at_the_right_call(tmp_path: Path) -> None:
    """A run that dies partway through resumes only the calls it hadn't made yet -- the
    scenario the author specifically asked to be designed for (call 900 dies, 901 resumes)."""
    cache_path = tmp_path / "cache.jsonl"
    item_ids = [f"RB-{i:04d}" for i in range(1, 6)]

    call_count = {"n": 0}

    def flaky_call(item_id, condition, model_identifier, seed, prompt_template_id):
        call_count["n"] += 1
        if call_count["n"] == 3:
            raise RuntimeError("simulated rate-limit cutoff")
        return _response(item_id, condition, model_identifier, seed, prompt_template_id)

    cache = ResponseCache(cache_path)
    # The "run" crashes partway through -- the successful calls made before that must still
    # be on disk, since put() flushes immediately rather than buffering until the end.
    with contextlib.suppress(RuntimeError):
        run_with_cache(
            item_ids=item_ids,
            conditions=[Condition.NO_RETRIEVAL],
            model_identifiers=["model-a"],
            seeds=[1],
            prompt_template_id="v1",
            call_fn=flaky_call,
            cache=cache,
        )

    assert len(ResponseCache(cache_path)) == 2

    # Resume: a fresh cache instance, a call_fn that always succeeds this time.
    resumed_cache = ResponseCache(cache_path)
    calls_on_resume: list[str] = []

    def reliable_call(item_id, condition, model_identifier, seed, prompt_template_id):
        calls_on_resume.append(item_id)
        return _response(item_id, condition, model_identifier, seed, prompt_template_id)

    results = run_with_cache(
        item_ids=item_ids,
        conditions=[Condition.NO_RETRIEVAL],
        model_identifiers=["model-a"],
        seeds=[1],
        prompt_template_id="v1",
        call_fn=reliable_call,
        cache=resumed_cache,
    )

    assert len(results) == 5  # all 5 items now accounted for
    assert len(calls_on_resume) == 3  # only the 3 that hadn't succeeded yet were re-requested


def test_missing_keys_reports_remaining_budget_without_calling_anything(tmp_path: Path) -> None:
    cache = ResponseCache(tmp_path / "cache.jsonl")
    cache.put(_response("RB-0001", Condition.NO_RETRIEVAL, "model-a", 1))

    remaining = missing_keys(
        item_ids=["RB-0001", "RB-0002"],
        conditions=[Condition.NO_RETRIEVAL],
        model_identifiers=["model-a"],
        seeds=[1],
        prompt_template_id="v1",
        cache=cache,
    )

    assert remaining == [("RB-0002", "no_retrieval", "model-a", 1, "v1")]


def test_missing_keys_empty_when_everything_cached(tmp_path: Path) -> None:
    cache = ResponseCache(tmp_path / "cache.jsonl")
    cache.put(_response("RB-0001", Condition.NO_RETRIEVAL, "model-a", 1))

    remaining = missing_keys(
        item_ids=["RB-0001"],
        conditions=[Condition.NO_RETRIEVAL],
        model_identifiers=["model-a"],
        seeds=[1],
        prompt_template_id="v1",
        cache=cache,
    )

    assert remaining == []
