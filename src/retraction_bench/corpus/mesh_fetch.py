"""Domain-bounded PubMed abstract fetching via MeSH terms (docs/CORPUS_PLAN.md, ADR-046).

Uses NCBI's history server (ESearch usehistory=y -> WebEnv/query_key) for batched EFetch.
**NCBI caps retstart at 9999 per query_key, even with the history server** -- confirmed
live (not assumed) when a naive single-query fetch of the Pharmacology domain (55,047
records) failed at retstart=9999 with a 400 error. Domains this corpus needs are well
above that cap (Rehabilitation alone is ~258,000), so each domain's query is recursively
split by publication-date range until every chunk's count is <= 9999, and each chunk gets
its own ESearch history session. This is a real constraint discovered by running the code
against the live API, not a design choice made in advance.

Response fields parsed from EFetch XML: PMID, title, abstract (concatenated across
structured AbstractText sections, since some abstracts are multi-part e.g.
Background/Methods/Results/Conclusion), journal title, and publication year (for the
date-distribution report in ADR-046/CORPUS_PLAN.md section 3).
"""

import json
import os
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import httpx

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# Pinned exact MeSH terms, ADR-046 -- not hand-tuned keywords. The date range and
# hasabstract filter are applied separately per chunk (see DATE_START/DATE_END below),
# not baked into this string, since chunking needs to vary the date bound per sub-query.
DOMAIN_MESH_TERMS: dict[str, str] = {
    "(HSC) Medicine - Pharmacology": '"Pharmacology"[MeSH Terms]',
    "(HSC) Medicine - Obstetrics/Gynecology": '("Obstetrics"[MeSH Terms] OR "Gynecology"[MeSH Terms])',
    "(HSC) Medicine - Rehabilitation/Therapy": '"Rehabilitation"[MeSH Terms]',
}
DATE_START = date(2000, 1, 1)
DATE_END = date(2026, 12, 31)

# Kept for reference/backwards compatibility with anything that wants the un-chunked query.
DOMAIN_QUERIES: dict[str, str] = {
    domain: f"{terms} AND {DATE_START.strftime('%Y/%m/%d')}:{DATE_END.strftime('%Y/%m/%d')}[dp] AND hasabstract[text]"
    for domain, terms in DOMAIN_MESH_TERMS.items()
}

MAX_RECORDS_PER_CHUNK = 9999  # NCBI's hard retstart cap, confirmed live
EFETCH_BATCH_SIZE = 300
NO_KEY_DELAY_SECONDS = 1.0 / 3
WITH_KEY_DELAY_SECONDS = 1.0 / 10
MAX_RETRIES = 4


@dataclass
class PubMedRecord:
    pmid: str
    title: str
    abstract: str
    journal: str
    pub_year: int | None


def _get_credentials() -> tuple[str, str | None]:
    email = os.environ.get("NCBI_EMAIL")
    if not email:
        raise RuntimeError("NCBI_EMAIL is not set -- required before any PubMed call is made.")
    return email, os.environ.get("NCBI_API_KEY") or None


def _dated_query(mesh_terms: str, start: date, end: date) -> str:
    return f"{mesh_terms} AND {start.strftime('%Y/%m/%d')}:{end.strftime('%Y/%m/%d')}[dp] AND hasabstract[text]"


def esearch_count(query: str, client: httpx.Client) -> int:
    """Count-only ESearch, no history session created -- cheap, used for chunk discovery."""
    email, api_key = _get_credentials()
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": "0",
        "tool": "retraction-bench",
        "email": email,
    }
    if api_key:
        params["api_key"] = api_key
    response = client.get(ESEARCH_URL, params=params)
    response.raise_for_status()
    return int(response.json()["esearchresult"]["count"])


def find_date_chunks(
    mesh_terms: str,
    client: httpx.Client,
    start: date = DATE_START,
    end: date = DATE_END,
    max_count: int = MAX_RECORDS_PER_CHUNK,
) -> list[tuple[date, date, int]]:
    """Recursively bisect [start, end] by publication date until every chunk's ESearch
    count is <= max_count. Returns (chunk_start, chunk_end, chunk_count) triples covering
    the full range with no gaps or overlaps. Rate-limited per NCBI's politeness policy --
    bisection over a domain the size of this corpus makes many count-only calls in quick
    succession, and a 429 was hit live before this delay was added.
    """
    _, api_key = _get_credentials()
    delay = WITH_KEY_DELAY_SECONDS if api_key else NO_KEY_DELAY_SECONDS

    query = _dated_query(mesh_terms, start, end)
    count = esearch_count(query, client)
    time.sleep(delay)
    if count <= max_count or start >= end:
        return [(start, end, count)]
    mid = start + (end - start) // 2
    left = find_date_chunks(mesh_terms, client, start, mid, max_count)
    right = find_date_chunks(mesh_terms, client, mid + timedelta(days=1), end, max_count)
    return left + right


def esearch_with_history(query: str, client: httpx.Client) -> tuple[str, str, int]:
    """Returns (webenv, query_key, total_count) for a query, using NCBI's history server."""
    email, api_key = _get_credentials()
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "usehistory": "y",
        "retmax": "0",
        "tool": "retraction-bench",
        "email": email,
    }
    if api_key:
        params["api_key"] = api_key
    response = client.get(ESEARCH_URL, params=params)
    response.raise_for_status()
    result = response.json()["esearchresult"]
    return result["webenv"], result["querykey"], int(result["count"])


def _parse_efetch_xml(xml_text: str) -> list[PubMedRecord]:
    root = ET.fromstring(xml_text)
    records = []
    for article in root.findall(".//PubmedArticle"):
        pmid_el = article.find(".//PMID")
        if pmid_el is None or not pmid_el.text:
            continue
        title_el = article.find(".//ArticleTitle")
        title = "".join(title_el.itertext()) if title_el is not None else ""
        abstract_parts = [
            "".join(el.itertext()) for el in article.findall(".//Abstract/AbstractText") if el is not None
        ]
        abstract = " ".join(part.strip() for part in abstract_parts if part.strip())
        journal_el = article.find(".//Journal/Title")
        journal = journal_el.text if journal_el is not None and journal_el.text else ""
        year_el = article.find(".//JournalIssue/PubDate/Year")
        pub_year = int(year_el.text) if year_el is not None and year_el.text and year_el.text.isdigit() else None
        records.append(
            PubMedRecord(pmid=pmid_el.text, title=title, abstract=abstract, journal=journal, pub_year=pub_year)
        )
    return records


def efetch_batch(webenv: str, query_key: str, retstart: int, retmax: int, client: httpx.Client) -> list[PubMedRecord]:
    email, api_key = _get_credentials()
    params = {
        "db": "pubmed",
        "query_key": query_key,
        "WebEnv": webenv,
        "retstart": str(retstart),
        "retmax": str(retmax),
        "rettype": "abstract",
        "retmode": "xml",
        "tool": "retraction-bench",
        "email": email,
    }
    if api_key:
        params["api_key"] = api_key

    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            response = client.get(EFETCH_URL, params=params, timeout=60.0)
            response.raise_for_status()
            return _parse_efetch_xml(response.text)
        except (httpx.HTTPError, ET.ParseError) as e:
            last_error = e
            time.sleep(2**attempt)
    raise RuntimeError(f"efetch failed after {MAX_RETRIES} retries at retstart={retstart}") from last_error


def _progress_path(output_path: Path) -> Path:
    return output_path.with_suffix(".progress.json")


def _load_chunk_progress(output_path: Path) -> dict[str, int]:
    """Maps chunk_key -> retstart already written for that chunk (0 if never started).

    Was a set of *completed* chunk keys (ADR-133): a chunk was only ever marked done after
    its whole `while retstart < confirmed_count` loop finished, but batches were written and
    flushed to `output_path` one at a time inside that loop. A process interrupted after some
    batches but before the chunk finished left the chunk absent from that set, so the next
    run re-fetched the entire chunk from retstart=0 and re-appended every record the partial
    attempt had already written -- confirmed as the cause of ~75,000 duplicate rows in the
    real corpus (Rehabilitation, the domain needing the most chunks, had the most duplicates;
    every duplicate was byte-identical to its first occurrence). Tracking retstart per chunk,
    persisted after every batch instead of only at chunk end, makes an interrupted chunk
    resume from where it left off instead of from the start.
    """
    progress_path = _progress_path(output_path)
    if not progress_path.exists():
        return {}
    raw = json.loads(progress_path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return {}  # stale pre-ADR-133 format (a completed-chunk-keys list) -- not resumable from
    return raw


def _save_chunk_retstart(output_path: Path, chunk_key: str, retstart: int) -> None:
    progress_path = _progress_path(output_path)
    progress = _load_chunk_progress(output_path)
    progress[chunk_key] = retstart
    progress_path.write_text(json.dumps(progress), encoding="utf-8")


def fetch_domain_corpus(
    domain: str,
    output_path: Path,
    client: httpx.Client | None = None,
    batch_size: int = EFETCH_BATCH_SIZE,
) -> int:
    """Fetch every record for a domain's pinned MeSH terms across the full date range,
    chunked to stay under NCBI's 9999-record retstart cap per query. Appends JSONL to
    output_path. Resumable across chunks (a sidecar .progress.json tracks which date
    chunks are already fully written) -- a chunk already marked complete is never re-fetched,
    even across separate process runs.
    """
    mesh_terms = DOMAIN_MESH_TERMS[domain]
    owns_client = client is None
    client = client or httpx.Client(timeout=60.0)
    _, api_key = _get_credentials()
    delay = WITH_KEY_DELAY_SECONDS if api_key else NO_KEY_DELAY_SECONDS

    try:
        chunks = find_date_chunks(mesh_terms, client)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        progress = _load_chunk_progress(output_path)
        total_written = 0

        with output_path.open("a", encoding="utf-8") as f:
            for start, end, chunk_count in chunks:
                chunk_key = f"{start.isoformat()}:{end.isoformat()}"
                resume_at = progress.get(chunk_key, 0)
                if chunk_count == 0 or resume_at >= chunk_count:
                    continue
                query = _dated_query(mesh_terms, start, end)
                webenv, query_key, confirmed_count = esearch_with_history(query, client)
                retstart = resume_at
                while retstart < confirmed_count:
                    batch = efetch_batch(webenv, query_key, retstart, batch_size, client)
                    if not batch:
                        break
                    for record in batch:
                        f.write(
                            json.dumps(
                                {
                                    "pmid": record.pmid,
                                    "title": record.title,
                                    "abstract": record.abstract,
                                    "journal": record.journal,
                                    "pub_year": record.pub_year,
                                    "domain": domain,
                                }
                            )
                            + "\n"
                        )
                    f.flush()
                    retstart += len(batch)
                    total_written += len(batch)
                    _save_chunk_retstart(output_path, chunk_key, retstart)
                    time.sleep(delay)
        return total_written
    finally:
        if owns_client:
            client.close()
