"""PubMed E-utilities verification (the project protocol, second half of the rule).

A paper counts as retracted only if it appears in Retraction Watch AND
PubMed's own record for it carries the "Retracted Publication" publication
type tag. Retraction Watch membership is already satisfied by candidate
selection; this module checks the PubMed half. Never infer retraction
status from anything else -- this is the one place that actually asks
PubMed, via NCBI's ESummary endpoint, and records what it said.

Response shape confirmed against the live API before writing this (not
assumed): `result.<pmid>.pubtype` is a list of strings, e.g.
["Journal Article", "Retracted Publication"]. An unresolvable PMID comes
back as `result.<pmid>.error` instead of a pubtype list.
"""

import os
import time
from dataclasses import dataclass
from pathlib import Path

import httpx
import pandas as pd

ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
RETRACTED_PUBTYPE = "Retracted Publication"

# NCBI allows up to ~200 IDs per ESummary request; stay comfortably under that.
BATCH_SIZE = 150
# Politeness rate limits per NCBI's usage policy: 3 req/sec without a key, 10/sec with one.
NO_KEY_DELAY_SECONDS = 1.0 / 3
WITH_KEY_DELAY_SECONDS = 1.0 / 10

DEFAULT_CACHE_PATH = Path("data/interim/pubmed_verification_cache.csv")


@dataclass
class PubMedVerification:
    pmid: str
    pubtypes: list[str] | None  # None means the lookup itself failed -- not "no tag found"
    is_retracted_tagged: bool
    error: str | None = None


def _get_credentials() -> tuple[str, str | None]:
    email = os.environ.get("NCBI_EMAIL")
    if not email:
        raise RuntimeError(
            "NCBI_EMAIL is not set. Copy .env.example to .env and fill it in -- required by "
            "NCBI's usage policy to identify this tool, and required before any PubMed call is made."
        )
    return email, os.environ.get("NCBI_API_KEY") or None


def verify_pmids(pmids: list[str], client: httpx.Client | None = None) -> dict[str, PubMedVerification]:
    """Query PubMed ESummary in batches. Returns pmid -> PubMedVerification for every input pmid."""
    email, api_key = _get_credentials()
    delay = WITH_KEY_DELAY_SECONDS if api_key else NO_KEY_DELAY_SECONDS

    results: dict[str, PubMedVerification] = {}
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
            data = response.json()
            result_block = data.get("result", {})

            for pmid in batch:
                record = result_block.get(pmid)
                if record is None or "error" in record:
                    results[pmid] = PubMedVerification(
                        pmid=pmid,
                        pubtypes=None,
                        is_retracted_tagged=False,
                        error=(record or {}).get("error", "missing from ESummary response"),
                    )
                else:
                    pubtypes = record.get("pubtype", [])
                    results[pmid] = PubMedVerification(
                        pmid=pmid,
                        pubtypes=pubtypes,
                        is_retracted_tagged=RETRACTED_PUBTYPE in pubtypes,
                    )

            if i + BATCH_SIZE < len(pmids):
                time.sleep(delay)
    finally:
        if owns_client:
            client.close()
    return results


def load_cache(cache_path: Path) -> dict[str, PubMedVerification]:
    if not cache_path.exists():
        return {}
    df = pd.read_csv(cache_path, dtype=str, keep_default_na=False)
    cache = {}
    for _, row in df.iterrows():
        pubtypes = row["pubtypes"].split(";") if row["pubtypes"] else None
        cache[row["pmid"]] = PubMedVerification(
            pmid=row["pmid"],
            pubtypes=pubtypes,
            is_retracted_tagged=row["is_retracted_tagged"] == "True",
            error=row["error"] or None,
        )
    return cache


def save_cache(cache_path: Path, cache: dict[str, PubMedVerification]) -> None:
    rows = [
        {
            "pmid": v.pmid,
            "pubtypes": ";".join(v.pubtypes) if v.pubtypes else "",
            "is_retracted_tagged": v.is_retracted_tagged,
            "error": v.error or "",
        }
        for v in cache.values()
    ]
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=["pmid", "pubtypes", "is_retracted_tagged", "error"]).to_csv(cache_path, index=False)


def verify_pmids_cached(
    pmids: list[str],
    cache_path: Path = DEFAULT_CACHE_PATH,
    client: httpx.Client | None = None,
) -> dict[str, PubMedVerification]:
    """Same as verify_pmids, but skips PMIDs already on disk from a prior run."""
    cache = load_cache(cache_path)
    missing = [p for p in dict.fromkeys(pmids) if p not in cache]
    if missing:
        new_results = verify_pmids(missing, client=client)
        cache.update(new_results)
        save_cache(cache_path, cache)
    return {p: cache[p] for p in pmids}


def verify_candidates_csv(
    candidates_path: Path,
    output_path: Path,
    pmid_col: str = "pmid",
    cache_path: Path = DEFAULT_CACHE_PATH,
    client: httpx.Client | None = None,
) -> pd.DataFrame:
    """Read a candidate export (e.g. from curate.candidates), verify every PMID's
    the project protocol tag, and write the same table with verification columns added.
    """
    candidates = pd.read_csv(candidates_path, dtype={pmid_col: str})
    pmids = candidates[pmid_col].tolist()
    verifications = verify_pmids_cached(pmids, cache_path=cache_path, client=client)

    candidates = candidates.copy()
    candidates["pubmed_retracted_tag_confirmed"] = [verifications[p].is_retracted_tagged for p in pmids]
    candidates["pubmed_lookup_error"] = [verifications[p].error or "" for p in pmids]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    candidates.to_csv(output_path, index=False)
    return candidates
