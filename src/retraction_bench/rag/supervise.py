"""Unsupervised long-running retry wrapper around `collect.run_collection` (ADR pending).

Built for exactly one situation: Groq's daily token quota resets on an unknown, multi-hour
cycle, and the author wants to start one command, walk away for hours, and come back to either
a complete collection or a clear log of what went wrong. `run_collection` already resumes from
cache and already distinguishes a retryable stall (`BackendRetryableError`, caught internally,
reported via `CollectionResult.stalled_models`) from a fatal one (`BackendFatalError`, left to
propagate) -- this module adds the outer loop: back off and retry on a stall, exit immediately
and loudly on anything fatal, and log every step with a timestamp so a human returning after
several hours can read what happened without re-deriving it from process behavior.
"""

import sys
import time
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from retraction_bench.curate.benchmark_io import load_items, load_sources
from retraction_bench.rag.backends import BackendFatalError
from retraction_bench.rag.cache import ResponseCache, missing_keys
from retraction_bench.rag.collect import (
    CACHE_PATH,
    CONDITIONS_ORDER,
    CollectionResult,
    notice_eligible_item_ids,
    run_collection,
)

# 15 min, 30 min, 1 hour -- then holds at 1 hour. Deliberately does not reset after a partial
# success: the run observed in practice (a "cleared" quota re-stalling after 9 calls) means a
# short window opening briefly is not evidence the next window will be any longer.
BACKOFF_STEPS_SECONDS = (15 * 60, 30 * 60, 60 * 60)


def default_log_path() -> Path:
    return Path(__file__).resolve().parents[3] / "data/interim/eval/groq_supervisor.log"


def make_logger(log_path: Path) -> Callable[[str], None]:
    log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(message: str) -> None:
        line = f"[{datetime.now().isoformat(timespec='seconds')}] {message}"
        print(line, flush=True)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    return log


def count_remaining(model: str, seeds: tuple[int, ...] = (1, 2, 3), prompt_template_id: str = "v1") -> int:
    """The exact remaining-call count for one model, computed the same way `collect.py` itself
    would -- never assumed. Recomputed on every loop iteration since a partially-successful
    attempt (some calls landed before a stall) changes it.
    """
    items = load_items()
    sources = {s.source_registry_id: s for s in load_sources()}
    eligible_ids = notice_eligible_item_ids(items, sources)
    all_ids = [i.item_id for i in items]
    eligible_only = [i.item_id for i in items if i.item_id in eligible_ids]
    item_ids_per_condition = {
        CONDITIONS_ORDER[0]: all_ids,
        CONDITIONS_ORDER[1]: eligible_only,
        CONDITIONS_ORDER[2]: eligible_only,
        CONDITIONS_ORDER[3]: eligible_only,
    }
    cache = ResponseCache(CACHE_PATH)
    return sum(
        len(missing_keys(item_ids_per_condition[c], [c], [model], list(seeds), prompt_template_id, cache))
        for c in CONDITIONS_ORDER
    )


@dataclass
class SuperviseOutcome:
    status: str  # "complete" | "fatal" | "max_attempts"
    attempts: int
    remaining: int


def supervise(
    model: str,
    log: Callable[[str], None],
    run_collection_fn: Callable[..., CollectionResult] = run_collection,
    count_remaining_fn: Callable[[str], int] = count_remaining,
    sleep_fn: Callable[[float], None] = time.sleep,
    backoff_steps: tuple[int, ...] = BACKOFF_STEPS_SECONDS,
    max_attempts: int | None = None,
) -> SuperviseOutcome:
    """The retry loop itself, with every dependency injected so it's testable without real
    time.sleep, a real Groq call, or the real corpus/cache on disk.
    """
    initial_remaining = count_remaining_fn(model)
    log(f"Supervisor started for {model}. Remaining calls: {initial_remaining}")
    if initial_remaining == 0:
        log("COMPLETE: nothing to collect -- 0 calls remaining at start.")
        return SuperviseOutcome(status="complete", attempts=0, remaining=0)

    attempt = 0
    backoff_idx = 0
    while max_attempts is None or attempt < max_attempts:
        attempt += 1
        remaining = count_remaining_fn(model)
        log(f"Attempt {attempt}: {remaining} calls remaining. Starting collection run...")

        try:
            result = run_collection_fn(models=(model,))
        except BackendFatalError as e:
            log(f"FATAL: {e}")
            log(
                "Stopping -- this will not succeed on retry (auth failure, bad model name, or a "
                "malformed request). Fix the underlying problem and re-run manually."
            )
            return SuperviseOutcome(status="fatal", attempts=attempt, remaining=count_remaining_fn(model))
        except Exception as e:  # noqa: BLE001 -- an unrecognized failure must stop the run, not retry forever against an unknown bug
            log(f"FATAL (unexpected {type(e).__name__}): {e}")
            log(traceback.format_exc())
            return SuperviseOutcome(status="fatal", attempts=attempt, remaining=count_remaining_fn(model))

        new_remaining = count_remaining_fn(model)
        if not result.stalled_models:
            if new_remaining == 0:
                log(f"COMPLETE: all calls collected. Total responses in cache: {result.total_responses}.")
                return SuperviseOutcome(status="complete", attempts=attempt, remaining=0)
            log(
                f"WARNING: run finished with no stall reported, but {new_remaining} calls still "
                "remain. Investigate manually -- stopping rather than looping on an unexplained state."
            )
            return SuperviseOutcome(status="fatal", attempts=attempt, remaining=new_remaining)

        delay = backoff_steps[min(backoff_idx, len(backoff_steps) - 1)]
        backoff_idx += 1
        log(
            f"STALLED (quota or transient). {new_remaining} calls still remaining. "
            f"Waiting {delay // 60} minutes before the next attempt..."
        )
        sleep_fn(delay)

    log(f"Reached max_attempts={max_attempts} without completing. {count_remaining_fn(model)} calls remain.")
    return SuperviseOutcome(status="max_attempts", attempts=attempt, remaining=count_remaining_fn(model))


def main() -> None:
    from retraction_bench.rag.backends import GROQ_MODEL

    log = make_logger(default_log_path())
    outcome = supervise(GROQ_MODEL, log)
    sys.exit(0 if outcome.status == "complete" else 1)


if __name__ == "__main__":
    main()
