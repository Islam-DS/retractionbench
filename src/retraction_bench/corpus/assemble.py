"""Corpus assembly: exactly-once benchmark documents inside the background pool
(docs/CORPUS_PLAN.md section 4).

Benchmark documents (retracted sources, their notices, and superseding evidence) are
collected first, then the background pool (corpus/mesh_fetch.py's per-domain output) is
deduplicated against them before the two are combined -- guaranteeing every benchmark
document appears exactly once regardless of whether the general MeSH+date sample happened
to also catch it.

**Every row written is also deduplicated globally by pmid, across domains and against
whatever was already written** (see ADR-133): background rows can legitimately duplicate
across two domains' MeSH queries (~165 cases), and `mesh_fetch.py` had a resumability bug
that duplicated rows *within* a single domain's own output far more often (~75,000 rows,
confirmed byte-identical to their first occurrence). Both causes are defended against here,
at the one place all rows converge before being written and indexed, rather than only fixed
at their respective sources -- so a future duplication cause of either shape still can't
reach the index.
"""

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx

from retraction_bench.schemas import BenchmarkItem, SupersededSource

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"


def _get_credentials() -> tuple[str, str | None]:
    email = os.environ.get("NCBI_EMAIL")
    if not email:
        raise RuntimeError("NCBI_EMAIL is not set -- required before any PubMed call is made.")
    return email, os.environ.get("NCBI_API_KEY") or None


def resolve_doi_to_pmid(doi: str, client: httpx.Client) -> str | None:
    """ESearch by DOI field. Returns the PMID if exactly one match is found, else None."""
    email, api_key = _get_credentials()
    params = {
        "db": "pubmed",
        "term": f"{doi}[AID]",
        "retmode": "json",
        "tool": "retraction-bench",
        "email": email,
    }
    if api_key:
        params["api_key"] = api_key
    response = client.get(ESEARCH_URL, params=params)
    response.raise_for_status()
    ids = response.json()["esearchresult"].get("idlist", [])
    return ids[0] if len(ids) == 1 else None


@dataclass
class BenchmarkDocument:
    pmid: str
    corpus_role: str  # "benchmark_source" | "supersession_notice" | "superseding_evidence"
    domain: str
    title: str
    text: str  # abstract, or notice text for supersession_notice
    linked_source_registry_id: str


@dataclass
class AssemblyStats:
    background_written: int = 0
    background_deduped: int = 0
    benchmark_source: int = 0
    supersession_notice: int = 0
    superseding_evidence: int = 0
    superseding_evidence_unresolved: int = 0
    per_domain_background: dict[str, int] = field(default_factory=dict)


def _item_domain_for_source(source_registry_id: str, items: list[BenchmarkItem]) -> str | None:
    for item in items:
        if source_registry_id in item.supporting_sources:
            return item.domain
    return None


def collect_benchmark_documents(
    sources: list[SupersededSource],
    items: list[BenchmarkItem],
    client: httpx.Client | None = None,
) -> tuple[list[BenchmarkDocument], int]:
    """Returns (documents, unresolved_evidence_count). One entry per source abstract, one
    per notice with text, one per resolvable evidence identifier. Evidence identifiers that
    don't resolve to a single PMID are skipped and counted, not silently dropped without a
    trace.
    """
    owns_client = client is None
    client = client or httpx.Client(timeout=30.0)
    _, api_key = _get_credentials()
    delay = 1.0 / 10 if api_key else 1.0 / 3

    documents: list[BenchmarkDocument] = []
    unresolved = 0
    try:
        for source in sources:
            pmid = source.external_ids.get("pmid")
            domain = _item_domain_for_source(source.source_registry_id, items) or "unknown"
            if pmid:
                documents.append(
                    BenchmarkDocument(
                        pmid=pmid,
                        corpus_role="benchmark_source",
                        domain=domain,
                        title=source.title,
                        text=source.summary,
                        linked_source_registry_id=source.source_registry_id,
                    )
                )
            if source.notice_text or source.notice_text_verified:
                # Whether a document exists is a retrievability question (is there text a
                # retriever could find), not a claims-we-can-stand-behind question (ADR-136,
                # correcting ADR-133's own first fix). notice_text_verified alone under-counts:
                # 2 sources (rw-7837/RB-0003, rw-1471/RB-0004) have real notice text that was
                # never independently confirmed against a primary source (ADR-042 forbids using
                # it for a *specificity judgment* in the gold claim) but the text itself exists
                # and is exactly as retrievable as any other document -- excluding it here would
                # conflate "we cannot certify this quote" with "there is nothing to retrieve."
                # notice_text_verified=True with notice_text=None is the separate, real "bare"
                # state (confirmed empty, not missing) and still belongs in the corpus, hence the
                # `or`. Only notice_text=None AND notice_text_verified=False -- genuinely nothing
                # recoverable, RB-0005/RB-0026/RB-0027/RB-0028 -- excludes a source entirely.
                documents.append(
                    BenchmarkDocument(
                        pmid=f"{source.source_registry_id}-notice",
                        corpus_role="supersession_notice",
                        domain=domain,
                        title=f"Notice: {source.title}",
                        text=source.notice_text or "",
                        linked_source_registry_id=source.source_registry_id,
                    )
                )

        for item in items:
            for evidence in item.post_supersession_evidence:
                identifier = evidence.identifier
                pmid = identifier if identifier.isdigit() else resolve_doi_to_pmid(identifier, client)
                if not identifier.isdigit():
                    time.sleep(delay)
                if pmid is None:
                    unresolved += 1
                    continue
                documents.append(
                    BenchmarkDocument(
                        pmid=pmid,
                        corpus_role="superseding_evidence",
                        domain=item.domain,
                        title=evidence.note[:120],
                        text=evidence.note,
                        linked_source_registry_id=identifier,
                    )
                )
    finally:
        if owns_client:
            client.close()
    return documents, unresolved


def assemble_corpus(
    background_paths: dict[str, Path],
    sources: list[SupersededSource],
    items: list[BenchmarkItem],
    output_path: Path,
    client: httpx.Client | None = None,
) -> AssemblyStats:
    """Dedup background against benchmark PMIDs, insert benchmark docs exactly once, write
    the combined corpus as JSONL with corpus_role/domain tags.
    """
    benchmark_docs, unresolved = collect_benchmark_documents(sources, items, client=client)
    benchmark_pmids = {doc.pmid for doc in benchmark_docs if doc.corpus_role != "supersession_notice"}

    stats = AssemblyStats(superseding_evidence_unresolved=unresolved)
    written_pmids: set[str] = set()  # global, across domains -- see module docstring / ADR-133
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as out:
        for domain, path in background_paths.items():
            written = 0
            if not path.exists():
                stats.per_domain_background[domain] = 0
                continue
            with path.open(encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    row = json.loads(line)
                    if row["pmid"] in benchmark_pmids:
                        stats.background_deduped += 1
                        continue
                    if row["pmid"] in written_pmids:
                        stats.background_deduped += 1
                        continue
                    written_pmids.add(row["pmid"])
                    row["corpus_role"] = "background"
                    out.write(json.dumps(row) + "\n")
                    written += 1
            stats.per_domain_background[domain] = written
            stats.background_written += written

        for doc in benchmark_docs:
            if doc.pmid in written_pmids:
                continue
            written_pmids.add(doc.pmid)
            out.write(
                json.dumps(
                    {
                        "pmid": doc.pmid,
                        "title": doc.title,
                        "abstract": doc.text,
                        "domain": doc.domain,
                        "corpus_role": doc.corpus_role,
                        "linked_source_registry_id": doc.linked_source_registry_id,
                    }
                )
                + "\n"
            )
            if doc.corpus_role == "benchmark_source":
                stats.benchmark_source += 1
            elif doc.corpus_role == "supersession_notice":
                stats.supersession_notice += 1
            elif doc.corpus_role == "superseding_evidence":
                stats.superseding_evidence += 1

    return stats
