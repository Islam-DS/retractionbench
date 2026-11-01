"""Disk-backed response cache with resume (ADR-129).

Free-tier and local inference routes are the entire model set now (ADR-129, zero-cost
constraint) -- every one of them can cut off unpredictably (a rate limit, a dropped
connection, a laptop going to sleep mid-run), unlike ADR-045's original assumption of a
reliable paid API. This module exists so a run that stops at call 900 resumes at 901: every
response is written to disk the moment it arrives, keyed on the same five fields
ADR-045/ADR-129 specify, and a fresh run loads the existing cache and skips any key already
present before making a single call. Resuming and starting fresh are the same code path.
"""

from collections.abc import Callable
from pathlib import Path

from retraction_bench.schemas import Condition, ModelResponse

CacheKey = tuple[str, str, str, int, str]  # (item_id, condition, model_identifier, seed, prompt_template_id)


def cache_key(
    item_id: str, condition: Condition | str, model_identifier: str, seed: int, prompt_template_id: str
) -> CacheKey:
    return (item_id, str(condition), model_identifier, seed, prompt_template_id)


class ResponseCache:
    """Append-only JSONL cache. One line per ModelResponse, written and flushed immediately
    on `put` -- never buffered and written in bulk at the end, since the whole point is that
    the file on disk reflects every call made so far, even if the process dies on the next one.
    """

    def __init__(self, cache_path: Path) -> None:
        self.cache_path = cache_path
        self._index: dict[CacheKey, ModelResponse] = {}
        self._load()

    def _load(self) -> None:
        if not self.cache_path.exists():
            return
        with self.cache_path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                response = ModelResponse.model_validate_json(line)
                key = cache_key(
                    response.item_id,
                    response.condition,
                    response.model_identifier,
                    response.seed,
                    response.prompt_template_id,
                )
                self._index[key] = response

    def has(self, key: CacheKey) -> bool:
        return key in self._index

    def get(self, key: CacheKey) -> ModelResponse | None:
        return self._index.get(key)

    def put(self, response: ModelResponse) -> None:
        key = cache_key(
            response.item_id,
            response.condition,
            response.model_identifier,
            response.seed,
            response.prompt_template_id,
        )
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with self.cache_path.open("a", encoding="utf-8") as f:
            f.write(response.model_dump_json() + "\n")
            f.flush()
        self._index[key] = response

    def __len__(self) -> int:
        return len(self._index)

    def all_responses(self) -> list[ModelResponse]:
        return list(self._index.values())


def run_with_cache(
    item_ids: list[str],
    conditions: list[Condition],
    model_identifiers: list[str],
    seeds: list[int],
    prompt_template_id: str,
    call_fn: Callable[[str, Condition, str, int, str], ModelResponse],
    cache: ResponseCache,
) -> list[ModelResponse]:
    """Iterate the full (item, condition, model, seed) cross product, skip anything already
    cached, call `call_fn` for the rest, and write each result to `cache` immediately.

    `call_fn(item_id, condition, model_identifier, seed, prompt_template_id) -> ModelResponse`
    is injected rather than hardcoded to a specific provider -- tests exercise this with a fake
    that never makes a network call, matching this project's standing pattern
    (corpus/embed_index.py's injectable embed_fn). The real call_fn (litellm-backed, per
    provider) is wired in by the pipeline's CLI entry point, not by this module -- this module
    only owns the cache/resume contract, not any model's calling convention.

    Order matters for resumability under a rate limit: items are visited in a fixed, stable
    order (the order of the input lists) so a run that stops partway through always resumes at
    the same next call, not a different one depending on dict ordering or a set's iteration
    order.
    """
    results: list[ModelResponse] = []
    for item_id in item_ids:
        for condition in conditions:
            for model_identifier in model_identifiers:
                for seed in seeds:
                    key = cache_key(item_id, condition, model_identifier, seed, prompt_template_id)
                    cached = cache.get(key)
                    if cached is not None:
                        results.append(cached)
                        continue
                    response = call_fn(item_id, condition, model_identifier, seed, prompt_template_id)
                    cache.put(response)
                    results.append(response)
    return results


def missing_keys(
    item_ids: list[str],
    conditions: list[Condition],
    model_identifiers: list[str],
    seeds: list[int],
    prompt_template_id: str,
    cache: ResponseCache,
) -> list[CacheKey]:
    """What run_with_cache would still need to call, without actually calling anything --
    for reporting remaining call budget before a run (e.g. "912 of 1,344 calls remain") without
    triggering any of them.
    """
    missing = []
    for item_id in item_ids:
        for condition in conditions:
            for model_identifier in model_identifiers:
                for seed in seeds:
                    key = cache_key(item_id, condition, model_identifier, seed, prompt_template_id)
                    if not cache.has(key):
                        missing.append(key)
    return missing
