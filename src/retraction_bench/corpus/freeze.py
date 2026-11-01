"""Corpus freeze-manifest bookkeeping: the content hash and record counts that make the
corpus a versioned, reproducible artifact (ADR-046, ADR-048).

The original 2026-08-09 freeze hash was computed by a one-off script that was never
committed to `src/` -- this module fills that gap so later corpus updates (benchmark
documents inserted individually, per ADR-048's freeze policy) can be re-hashed
reproducibly rather than by an unrepeatable manual step. See ADR-054 for the first use.

`write_manifest` (added ADR-152) exists because the top-level manifest fell out of sync
with two later structural corpus rebuilds (a duplicate-row removal and a
notice-creation-gate fix) that were never run back through this file -- a real
reproducibility gap disclosed in the paper's Appendix A and fixed there by a one-off
script. This function makes that fix repeatable instead of another unrepeatable manual
step, matching this module's own stated purpose above.
"""

import hashlib
import json
from collections import Counter
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path


def content_sha256(rows: Iterable[dict]) -> str:
    """SHA-256 over the sorted (pmid, abstract) pairs. Order-independent over the input
    iterable, so appending rows in a different order than they were originally read still
    reproduces the same hash for the same underlying document set.
    """
    pairs = sorted((r["pmid"], r.get("abstract", "")) for r in rows)
    digest = hashlib.sha256()
    for pmid, abstract in pairs:
        digest.update(pmid.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(abstract.encode("utf-8"))
        digest.update(b"\x00")
    return digest.hexdigest()


def write_manifest(corpus_rows: list[dict], manifest_path: Path, reason: str) -> dict:
    """Recompute record_count/content_sha256/domain and role counts/pub-year distribution
    against `corpus_rows` (the live, in-memory corpus -- callers read `assembled_corpus.jsonl`
    themselves rather than this function taking a path, so it stays testable without disk I/O)
    and rewrite `manifest_path` in place, appending one `update_history` entry rather than
    discarding the prior ones. Raises if `manifest_path` does not already exist -- this
    function updates an existing freeze, it does not perform the original freeze.
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"{manifest_path} does not exist -- this function updates an existing manifest")
    old = json.loads(manifest_path.read_text(encoding="utf-8"))

    record_count = len(corpus_rows)
    new_hash = content_sha256(corpus_rows)
    domain_counts = Counter(r["domain"] for r in corpus_rows)
    role_counts = Counter(r["corpus_role"] for r in corpus_rows)
    pub_year_distribution = dict(sorted(Counter(r["pub_year"] for r in corpus_rows if r.get("pub_year")).items()))

    manifest = {
        "freeze_date": old["freeze_date"],
        "freeze_datetime_utc": old["freeze_datetime_utc"],
        "record_count": record_count,
        "content_sha256": new_hash,
        "domain_counts": dict(domain_counts),
        "corpus_role_counts": dict(role_counts),
        "pub_year_min": min(pub_year_distribution) if pub_year_distribution else None,
        "pub_year_max": max(pub_year_distribution) if pub_year_distribution else None,
        "pub_year_distribution": pub_year_distribution,
        "update_history": [
            *old["update_history"],
            {
                "update_date": datetime.now(UTC).date().isoformat(),
                "update_datetime_utc": datetime.now(UTC).isoformat(),
                "reason": reason,
                "records_added": record_count - old["record_count"],
                "previous_record_count": old["record_count"],
                "previous_content_sha256": old["content_sha256"],
                "new_record_count": record_count,
                "new_content_sha256": new_hash,
            },
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
