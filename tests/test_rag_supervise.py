from collections.abc import Callable
from pathlib import Path

import pytest

from retraction_bench.rag.backends import GROQ_MODEL, BackendFatalError
from retraction_bench.rag.collect import CollectionResult
from retraction_bench.rag.supervise import BACKOFF_STEPS_SECONDS, make_logger, supervise


def _logger(tmp_path: Path) -> tuple[list[str], Callable[[str], None]]:
    lines: list[str] = []
    log_path = tmp_path / "supervisor.log"
    real_log = make_logger(log_path)

    def capturing_log(msg: str) -> None:
        real_log(msg)
        lines.append(msg)

    return lines, capturing_log


def test_completes_immediately_when_nothing_remains(tmp_path: Path) -> None:
    lines, log = _logger(tmp_path)
    outcome = supervise(
        GROQ_MODEL,
        log,
        run_collection_fn=lambda **kw: pytest.fail("should never call run_collection when 0 remain"),
        count_remaining_fn=lambda model: 0,
        sleep_fn=lambda s: pytest.fail("should never sleep"),
    )
    assert outcome.status == "complete"
    assert outcome.attempts == 0
    assert any("COMPLETE" in line for line in lines)


def test_completes_after_one_successful_attempt(tmp_path: Path) -> None:
    lines, log = _logger(tmp_path)
    remaining_sequence = iter([130, 130, 0, 0])  # start, pre-attempt, post-attempt, final check

    def count_remaining_fn(model: str) -> int:
        return next(remaining_sequence, 0)

    def run_collection_fn(**kw):
        return CollectionResult(manifest_path=Path("m.json"), stalled_models=[], total_responses=900)

    outcome = supervise(
        GROQ_MODEL,
        log,
        run_collection_fn=run_collection_fn,
        count_remaining_fn=count_remaining_fn,
        sleep_fn=lambda s: pytest.fail("should never sleep"),
    )
    assert outcome.status == "complete"
    assert outcome.attempts == 1


def test_backs_off_progressively_on_repeated_stalls(tmp_path: Path) -> None:
    lines, log = _logger(tmp_path)
    sleeps: list[float] = []
    remaining = {"n": 130}

    def count_remaining_fn(model: str) -> int:
        return remaining["n"]

    def run_collection_fn(**kw):
        remaining["n"] -= 10  # each attempt makes a little progress, then stalls again
        return CollectionResult(manifest_path=Path("m.json"), stalled_models=[GROQ_MODEL], total_responses=770)

    outcome = supervise(
        GROQ_MODEL,
        log,
        run_collection_fn=run_collection_fn,
        count_remaining_fn=count_remaining_fn,
        sleep_fn=lambda s: sleeps.append(s),
        max_attempts=5,
    )
    assert outcome.status == "max_attempts"
    # 15min, 30min, 60min, then capped at 60min for every attempt after -- the author's exact spec
    assert sleeps == [15 * 60, 30 * 60, 60 * 60, 60 * 60, 60 * 60]


def test_stops_immediately_on_fatal_error_without_sleeping(tmp_path: Path) -> None:
    lines, log = _logger(tmp_path)

    def run_collection_fn(**kw):
        raise BackendFatalError("Groq authentication failed, HTTP 401: invalid api key")

    outcome = supervise(
        GROQ_MODEL,
        log,
        run_collection_fn=run_collection_fn,
        count_remaining_fn=lambda model: 130,
        sleep_fn=lambda s: pytest.fail("must not sleep after a fatal error"),
    )
    assert outcome.status == "fatal"
    assert outcome.attempts == 1
    assert any("FATAL" in line and "authentication failed" in line for line in lines)


def test_stops_on_unexpected_exception_rather_than_retrying_forever(tmp_path: Path) -> None:
    lines, log = _logger(tmp_path)

    def run_collection_fn(**kw):
        raise ValueError("corpus file missing")

    outcome = supervise(
        GROQ_MODEL,
        log,
        run_collection_fn=run_collection_fn,
        count_remaining_fn=lambda model: 130,
        sleep_fn=lambda s: pytest.fail("must not sleep after an unexpected exception"),
    )
    assert outcome.status == "fatal"
    assert any("FATAL" in line and "ValueError" in line for line in lines)


def test_log_lines_are_timestamped(tmp_path: Path) -> None:
    log_path = tmp_path / "supervisor.log"
    log = make_logger(log_path)
    log("hello")
    content = log_path.read_text(encoding="utf-8")
    assert content.startswith("[")
    assert "hello" in content


def test_backoff_steps_match_the_authors_spec() -> None:
    assert BACKOFF_STEPS_SECONDS == (15 * 60, 30 * 60, 60 * 60)
