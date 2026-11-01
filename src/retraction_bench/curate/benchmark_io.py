"""Validated JSONL persistence for the benchmark deliverable (the project protocol).

BenchmarkItem and SupersededSource are the actual dataset -- irreplaceable,
human-verified output, not a regenerable pipeline artifact. Every write and
read round-trips through the Pydantic schema, so a malformed record fails
loudly at write time (the project protocol) rather than being discovered
later during evaluation.
"""

import json
from pathlib import Path

from retraction_bench.schemas import BenchmarkItem, DeferredCandidate, RejectedCandidate, SupersededSource

DEFAULT_ITEMS_PATH = Path("data/benchmark/items.jsonl")
DEFAULT_SOURCES_PATH = Path("data/benchmark/sources.jsonl")
DEFAULT_REJECTED_PATH = Path("data/benchmark/rejected_candidates.jsonl")
DEFAULT_DEFERRED_PATH = Path("data/benchmark/deferred_candidates.jsonl")


def append_source(source: SupersededSource, path: Path = DEFAULT_SOURCES_PATH) -> None:
    _append(source, path)


def append_item(item: BenchmarkItem, path: Path = DEFAULT_ITEMS_PATH) -> None:
    _append(item, path)


def append_rejected(candidate: RejectedCandidate, path: Path = DEFAULT_REJECTED_PATH) -> None:
    _append(candidate, path)


def append_deferred(candidate: DeferredCandidate, path: Path = DEFAULT_DEFERRED_PATH) -> None:
    _append(candidate, path)


def _append(record: BenchmarkItem | SupersededSource | RejectedCandidate | DeferredCandidate, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record.model_dump(mode="json")) + "\n")


def load_sources(path: Path = DEFAULT_SOURCES_PATH) -> list[SupersededSource]:
    return _load(path, SupersededSource)


def load_items(path: Path = DEFAULT_ITEMS_PATH) -> list[BenchmarkItem]:
    return _load(path, BenchmarkItem)


def load_rejected(path: Path = DEFAULT_REJECTED_PATH) -> list[RejectedCandidate]:
    return _load(path, RejectedCandidate)


def load_deferred(path: Path = DEFAULT_DEFERRED_PATH) -> list[DeferredCandidate]:
    return _load(path, DeferredCandidate)


def _load(path: Path, model: type) -> list:
    if not path.exists():
        return []
    records = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(model.model_validate_json(line))
    return records
