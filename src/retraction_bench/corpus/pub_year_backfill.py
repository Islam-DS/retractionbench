"""Real, independently-sourced publication years for the corpus's benchmark-role rows.

`corpus/assemble.py`'s `collect_benchmark_documents` writes `benchmark_source` /
`supersession_notice` / `superseding_evidence` rows with only
`{pmid, title, abstract, domain, corpus_role, linked_source_registry_id}` -- unlike
background rows (from `corpus/mesh_fetch.py`), these never got a `pub_year` at all. Confirmed
directly against the live corpus (`data/interim/corpus/assembled_corpus.jsonl`), not assumed
from the schema: 325,086/325,167 rows (background) have `pub_year`; the 81 benchmark-role rows
have none.

This module closes that gap for the 57 rows that have a real PMID (`benchmark_source`,
`superseding_evidence`) by querying NCBI ESummary directly -- the same endpoint and
credential/rate-limit pattern `ingest/pubmed.py` already uses for retraction-tag verification,
here read for its `pubdate` field instead of `pubtype`. Response shape confirmed live before
writing the parser (not assumed): `result.<pmid>.pubdate` is a string like `"2017 Jun"`.

The 24 `supersession_notice` rows are NOT resolvable this way: their `pmid` field is a synthetic
internal placeholder (`f"{source_registry_id}-notice"`, e.g. `"rw-17019-notice"`), not a real
PubMed ID, and `schemas.py`'s `SupersededSource` records no separate real identifier (PMID or
DOI) for the notice itself as a distinct publication event -- there is nothing in the existing
real-identifier-resolution pathway to query. Explicitly left as `pub_year=None`, documented, not
guessed and not backfilled from `SupersededSource.supersession_date` or any other benchmark
annotation field (that would source corpus metadata from gold/annotation data, which this
intervention's leakage discipline forbids regardless of whether the numeric value would coincide).
"""

import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
BATCH_SIZE = 150
NO_KEY_DELAY_SECONDS = 1.0 / 3
WITH_KEY_DELAY_SECONDS = 1.0 / 10
_YEAR_RE = re.compile(r"\d{4}")

BACKGROUND_SOURCE = "corpus_background_pubmed_fetch"  # already real, from mesh_fetch.py; not refetched
FRESH_LOOKUP_SOURCE = "fresh_pubmed_esummary_lookup"
UNRESOLVABLE_SOURCE = "unresolvable_no_real_external_identifier"


@dataclass
class PubYearRecord:
    pmid: str
    corpus_role: str
    pub_year: int | None
    source: str
    note: str = ""


def _get_credentials() -> tuple[str, str | None]:
    email = os.environ.get("NCBI_EMAIL")
    if not email:
        raise RuntimeError("NCBI_EMAIL is not set -- required before any PubMed call is made.")
    return email, os.environ.get("NCBI_API_KEY") or None


def _parse_year(pubdate: str) -> int | None:
    """NCBI's `pubdate` string is loosely formatted ("2017 Jun", "2017 Jun-Jul", "2017",
    sometimes "2017 Jun 12") -- a leading or embedded 4-digit token is the year in every
    observed case (confirmed against the live API response for a real PMID before writing
    this). Returns None rather than guessing if no 4-digit token is present at all.
    """
    match = _YEAR_RE.search(pubdate or "")
    return int(match.group()) if match else None


def fetch_pub_years_from_pubmed(pmids: list[str], client: httpx.Client | None = None) -> dict[str, int | None]:
    """Batched ESummary lookup. Returns pmid -> year, or pmid -> None if the record was
    unresolvable or carried no parseable pubdate -- never a guessed value.
    """
    email, api_key = _get_credentials()
    delay = WITH_KEY_DELAY_SECONDS if api_key else NO_KEY_DELAY_SECONDS

    results: dict[str, int | None] = {}
    owns_client = client is None
    client = client or httpx.Client(timeout=30.0)
    try:
        for i in range(0, len(pmids), BATCH_SIZE):
            batch = pmids[i : i + BATCH_SIZE]
            params = {
                "db": "pubmed",
                "id": ",".join(batch),
                "retmode": "json",
                "tool": "retraction-bench",
                "email": email,
            }
            if api_key:
                params["api_key"] = api_key
            response = client.get(ESUMMARY_URL, params=params)
            response.raise_for_status()
            result_block = response.json().get("result", {})
            for pmid in batch:
                record = result_block.get(pmid)
                if record is None or "error" in record:
                    results[pmid] = None
                else:
                    results[pmid] = _parse_year(record.get("pubdate", ""))
            if i + BATCH_SIZE < len(pmids):
                time.sleep(delay)
    finally:
        if owns_client:
            client.close()
    return results


def _read_corpus_rows(corpus_path: Path) -> list[dict]:
    rows = []
    with corpus_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def build_pub_year_lookup(corpus_path: Path, client: httpx.Client | None = None) -> list[PubYearRecord]:
    """One record per corpus row. Background rows keep their existing, already-real `pub_year`
    unchanged (no refetch -- it's already a genuine PubMed-sourced value, re-fetching it would
    add API load for no informational gain). `benchmark_source`/`superseding_evidence` rows are
    resolved fresh from NCBI, keyed by their own real `pmid` field -- never from any
    `BenchmarkItem`/`SupersededSource`/`Evidence` annotation field. `supersession_notice` rows
    are recorded as explicitly unresolvable (see module docstring).
    """
    rows = _read_corpus_rows(corpus_path)

    real_pmid_rows = [r for r in rows if r["corpus_role"] in ("benchmark_source", "superseding_evidence")]
    real_pmids = sorted({r["pmid"] for r in real_pmid_rows})
    fresh_years = fetch_pub_years_from_pubmed(real_pmids, client=client) if real_pmids else {}

    out: list[PubYearRecord] = []
    for r in rows:
        role = r["corpus_role"]
        if role == "background":
            out.append(
                PubYearRecord(
                    pmid=r["pmid"], corpus_role=role, pub_year=r.get("pub_year"), source=BACKGROUND_SOURCE
                )
            )
        elif role in ("benchmark_source", "superseding_evidence"):
            year = fresh_years.get(r["pmid"])
            out.append(
                PubYearRecord(
                    pmid=r["pmid"],
                    corpus_role=role,
                    pub_year=year,
                    source=FRESH_LOOKUP_SOURCE,
                    note="" if year is not None else "ESummary returned no parseable pubdate for this real PMID",
                )
            )
        elif role == "supersession_notice":
            out.append(
                PubYearRecord(
                    pmid=r["pmid"],
                    corpus_role=role,
                    pub_year=None,
                    source=UNRESOLVABLE_SOURCE,
                    note=(
                        "pmid is a synthetic internal placeholder, not a real PubMed ID; no separate "
                        "real identifier for the notice itself exists in SupersededSource -- nothing in "
                        "the real-identifier-resolution pathway to query. Not guessed, not backfilled "
                        "from supersession_date or any other annotation field."
                    ),
                )
            )
        else:
            raise ValueError(f"unrecognized corpus_role {role!r} for pmid {r['pmid']!r}")
    return out


def write_lookup(records: list[PubYearRecord], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(
                json.dumps(
                    {
                        "pmid": rec.pmid,
                        "corpus_role": rec.corpus_role,
                        "pub_year": rec.pub_year,
                        "source": rec.source,
                        "note": rec.note,
                    }
                )
                + "\n"
            )


def load_lookup(lookup_path: Path) -> dict[str, int | None]:
    """pmid -> pub_year (or None), for the reranker's adapter to join against. Provenance
    fields are for audit, not passed to the reranker itself.
    """
    out: dict[str, int | None] = {}
    with lookup_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                row = json.loads(line)
                out[row["pmid"]] = row["pub_year"]
    return out
