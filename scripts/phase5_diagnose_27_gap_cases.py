"""Phase 5, Part A (prereg/phase5_record_level_audit.md): diagnose the 27 RW-vs-PubMed gap rows
(24 distinct PMIDs -- 3 appear twice in the gap set as duplicate candidate-pool rows, not
duplicate retractions) against Crossref and OpenAlex, cross-referencing RW's own fields.

Full enumeration of an already-identified, deterministic set -- not a sample.
"""

import json
import time
from pathlib import Path

import duckdb
import httpx
from dotenv import load_dotenv
import os

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data/interim/retraction_watch.duckdb"
OUT_JSON = ROOT / "results/phase5_27_gap_case_diagnosis.json"
OUT_MD = ROOT / "results/phase5_27_gap_case_diagnosis.md"

GAP_ROWS = [
    ("12945", "28617973"), ("21551", "26955437"), ("24857", "32946583"), ("43260", "27294218"),
    ("70441", "37940041"), ("71762", "39566682"), ("16851", "28395637"), ("18348", "19959915"),
    ("18495", "29438490"), ("20361", "30267080"), ("21323", "31563928"), ("25061", "30688986"),
    ("30918", "16856030"), ("70654", "39906865"), ("16669", "28226403"), ("23160", "31415103"),
    ("31158", "27552401"), ("31159", "27140910"), ("31160", "25069726"), ("31161", "22696330"),
    ("31162", "14583953"), ("70609", "6522427"), ("8140", "26658572"), ("8610", "27098397"),
]
DISTINCT_PMIDS = sorted({pmid for _, pmid in GAP_ROWS})

# RW's CSV export uses literal placeholder strings for a missing DOI in some rows (caught on
# PMID 31563928, "unavailable") rather than leaving the field empty -- treated as absent, not
# passed to Crossref/OpenAlex as if it were a real DOI (which previously produced two spurious
# 404s misread as "not corroborated elsewhere").
_DOI_PLACEHOLDERS = {"unavailable", "n/a", "na", "none", "unknown", ""}


def _real_doi(raw: str | None) -> str | None:
    if raw is None or raw.strip().lower() in _DOI_PLACEHOLDERS:
        return None
    return raw


def rw_fields_for(record_ids: list[str]) -> dict[str, dict]:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    ids_sql = ",".join(f"'{r}'" for r in record_ids)
    df = con.execute(
        f"select record_id, journal, publisher, retraction_date, retraction_nature, reason, original_paper_doi "
        f"from raw_retraction_watch where record_id in ({ids_sql})"
    ).fetchdf()
    return {row["record_id"]: row.to_dict() for _, row in df.iterrows()}


def openalex_check(doi: str, email: str) -> dict:
    try:
        r = httpx.get(f"https://api.openalex.org/works/doi:{doi}", params={"mailto": email}, timeout=20.0)
        if r.status_code != 200:
            return {"status": r.status_code, "is_retracted": None}
        d = r.json()
        return {"status": 200, "is_retracted": d.get("is_retracted"), "title": d.get("title")}
    except httpx.HTTPError as e:
        return {"status": "error", "error": str(e)}


def crossref_check(doi: str, email: str) -> dict:
    try:
        r = httpx.get(f"https://api.crossref.org/works/{doi}", params={"mailto": email}, timeout=20.0)
        if r.status_code != 200:
            return {"status": r.status_code, "relation": None, "update_to": None}
        msg = r.json().get("message", {})
        return {"status": 200, "relation": msg.get("relation") or {}, "update_to": msg.get("update-to")}
    except httpx.HTTPError as e:
        return {"status": "error", "error": str(e)}


def pubmed_check(pmid: str, email: str, api_key: str | None) -> dict:
    params = {"db": "pubmed", "id": pmid, "retmode": "json", "tool": "retraction-bench", "email": email}
    if api_key:
        params["api_key"] = api_key
    r = httpx.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi", params=params, timeout=20.0)
    if r.status_code != 200:
        return {"status": r.status_code, "pubtype": None}
    rec = r.json().get("result", {}).get(pmid)
    if rec is None or "error" in rec:
        return {"status": "no_record", "pubtype": None}
    return {"status": 200, "pubtype": rec.get("pubtype", [])}


def main() -> None:
    email = os.environ.get("NCBI_EMAIL", "test@example.com")
    api_key = os.environ.get("NCBI_API_KEY")

    record_ids = sorted({rid for rid, _ in GAP_ROWS})
    rw_data = rw_fields_for(record_ids)

    results = []
    for pmid in DISTINCT_PMIDS:
        record_ids_for_pmid = [rid for rid, p in GAP_ROWS if p == pmid]
        rw_rows = [rw_data[rid] for rid in record_ids_for_pmid if rid in rw_data]
        doi = next((_real_doi(r.get("original_paper_doi")) for r in rw_rows if _real_doi(r.get("original_paper_doi"))), None)

        pm = pubmed_check(pmid, email, api_key)
        time.sleep(0.11 if api_key else 0.34)
        oa = openalex_check(doi, email) if doi else {"status": "no_doi"}
        time.sleep(0.1)
        cr = crossref_check(doi, email) if doi else {"status": "no_doi"}
        time.sleep(0.1)

        still_untagged_pubmed = pm.get("status") == 200 and "Retracted Publication" not in (pm.get("pubtype") or [])
        confirmed_by_openalex = oa.get("is_retracted") is True
        confirmed_by_crossref = bool(cr.get("relation")) or bool(cr.get("update_to"))

        if still_untagged_pubmed and (confirmed_by_openalex or confirmed_by_crossref):
            classification = "true_pubmed_gap_corroborated"
        elif still_untagged_pubmed and not confirmed_by_openalex and not confirmed_by_crossref:
            classification = "true_pubmed_gap_uncorroborated_elsewhere"
        elif not still_untagged_pubmed:
            classification = "no_longer_a_gap_pubmed_now_tagged"
        else:
            classification = "unresolved"

        row = {
            "pmid": pmid,
            "record_ids": record_ids_for_pmid,
            "duplicate_candidate_rows": len(record_ids_for_pmid) > 1,
            "doi": doi,
            "rw_journal": rw_rows[0].get("journal") if rw_rows else None,
            "rw_publisher": rw_rows[0].get("publisher") if rw_rows else None,
            "rw_retraction_date": rw_rows[0].get("retraction_date") if rw_rows else None,
            "rw_retraction_nature": rw_rows[0].get("retraction_nature") if rw_rows else None,
            "rw_reason": rw_rows[0].get("reason") if rw_rows else None,
            "pubmed_check": pm,
            "openalex_check": oa,
            "crossref_check": cr,
            "classification": classification,
        }
        results.append(row)
        print(f"{pmid}: {classification} (pubmed={pm.get('status')}, openalex_retracted={oa.get('is_retracted')}, "
              f"crossref_relation={bool(cr.get('relation'))})")

    OUT_JSON.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\nwrote {OUT_JSON}")

    from collections import Counter
    class_counts = Counter(r["classification"] for r in results)

    lines = [
        "# Phase 5 Part A: diagnosis of the 27 RW-vs-PubMed gap rows (24 distinct PMIDs)",
        "",
        "Prereg: `prereg/phase5_record_level_audit.md`. Full enumeration of an already-identified",
        "set, not a sample.",
        "",
        f"**27 gap rows map to {len(DISTINCT_PMIDS)} distinct PMIDs** -- 3 PMIDs "
        f"(37940041, 19959915, 30267080) each appear twice as duplicate candidate-pool rows, not "
        f"duplicate retractions. Diagnosing the {len(DISTINCT_PMIDS)} distinct cases below.",
        "",
        "## Classification summary",
        "",
        "| Classification | n |",
        "|---|---|",
    ]
    for k, v in class_counts.items():
        lines.append(f"| {k} | {v} |")

    lines += [
        "",
        "## Full per-case detail",
        "",
        "| PMID | RW journal | RW publisher | RW date | RW nature | PubMed tag now | OpenAlex retracted | Crossref relation present | Classification |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        pm_tagged = "Retracted Publication" in (r["pubmed_check"].get("pubtype") or [])
        lines.append(
            f"| {r['pmid']} | {r['rw_journal']} | {r['rw_publisher']} | {r['rw_retraction_date']} | "
            f"{r['rw_retraction_nature']} | {pm_tagged} | {r['openalex_check'].get('is_retracted')} | "
            f"{bool(r['crossref_check'].get('relation'))} | {r['classification']} |"
        )

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
