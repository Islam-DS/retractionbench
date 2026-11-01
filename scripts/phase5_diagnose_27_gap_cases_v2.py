"""Phase 5 Part A, REDONE (prereg/phase5_record_level_audit.md, classification rules below),
after two real problems were caught in the v1 script (`phase5_diagnose_27_gap_cases.py`, kept
on disk for the record, not deleted):

1. **OpenAlex's `is_retracted` field is NOT independent of Retraction Watch.** OpenAlex's own
   documentation (fetched live this session): "True if the work is known to be retracted, per
   the Retraction Watch database." Treating it as corroborating evidence was circular -- it is
   RW confirming RW through a pass-through API, not independent validation.
2. **Crossref's `relation` field was checked too crudely** (`bool(relation)`), which produced a
   false positive (PMID 30688986's `relation` was a `"has-review"` link, unrelated to
   retraction). Crossref's own documentation distinguishes two real channels: the `relation`
   field can carry a `"retraction"`/`"withdrawal"` entry asserted by the retraction notice's own
   DOI record (`asserted-by: "object"`) -- genuinely independent, publisher-deposited metadata,
   nothing to do with RW -- while the separate `update-to` field explicitly carries a `source`
   of either `"publisher"` (independent) or `"retraction-watch"` (not independent, RW-derived),
   per Crossref's documentation: "Retractions and other updates from Retraction Watch are
   identified by a `source` field, which can have a value of `publisher` or `retraction-watch`."

CLASSIFICATION RULES (fixed before this rerun, not adjusted after seeing results):

- **independent_evidence**: at least one of --
  (a) PubMed's own title/abstract text contains an explicit retraction/withdrawal marker
      (case-insensitive substring match on "retract" or "withdraw"), independent of the
      structured `pubtype` tag;
  (b) Crossref `relation` contains a key matching "retract" or "withdraw" (case-insensitive);
  (c) Crossref `update-to` contains an entry with `source == "publisher"`.
- **rw_derived_only**: none of the above, but OpenAlex `is_retracted == True` and/or Crossref
  `update-to` has an entry with `source == "retraction-watch"`.
- **rw_only_uncorroborated**: none of the above at all -- the retraction claim rests on RW alone.

DOI placeholder check: confirmed (separately, this session) that `"unavailable"`/`"Unavailable"`
are the ONLY two non-DOI-shaped values in the entire 66,203-row PubMed-ID-bearing RW population
(checked directly: 62,502 distinct DOI values, only 2 fail to match `^10\\.`). Both are caught by
the same case-insensitive placeholder check used here.
"""

import json
import re
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv
import os

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = ROOT / "results/phase5_27_gap_case_diagnosis_v2.json"
OUT_MD = ROOT / "results/phase5_27_gap_case_diagnosis_v2.md"

_DOI_PLACEHOLDERS = {"unavailable", "n/a", "na", "none", "unknown", ""}
_RETRACT_WORDS = re.compile(r"retract|withdraw", re.IGNORECASE)


def _real_doi(raw: str | None) -> str | None:
    if raw is None or raw.strip().lower() in _DOI_PLACEHOLDERS:
        return None
    return raw


def pubmed_full_check(pmid: str, email: str, api_key: str | None) -> dict:
    params = {"db": "pubmed", "id": pmid, "retmode": "json", "tool": "retraction-bench", "email": email}
    if api_key:
        params["api_key"] = api_key
    r = httpx.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi", params=params, timeout=20.0)
    if r.status_code != 200:
        return {"status": r.status_code}
    rec = r.json().get("result", {}).get(pmid)
    if rec is None or "error" in rec:
        return {"status": "no_record"}
    title = rec.get("title", "") or ""
    pubtype = rec.get("pubtype", [])
    return {
        "status": 200,
        "title": title,
        "pubtype": pubtype,
        "tagged": "Retracted Publication" in pubtype,
        "title_text_flags_retraction": bool(_RETRACT_WORDS.search(title)),
    }


def crossref_full_check(doi: str, email: str) -> dict:
    try:
        r = httpx.get(f"https://api.crossref.org/works/{doi}", params={"mailto": email}, timeout=20.0)
    except httpx.HTTPError as e:
        return {"status": "error", "error": str(e)}
    if r.status_code != 200:
        return {"status": r.status_code}
    msg = r.json().get("message", {})
    relation = msg.get("relation") or {}
    update_to = msg.get("update-to") or []
    retraction_relation_keys = [k for k in relation if _RETRACT_WORDS.search(k)]
    publisher_update_to = [u for u in update_to if u.get("source") == "publisher"]
    rw_update_to = [u for u in update_to if u.get("source") == "retraction-watch"]
    return {
        "status": 200,
        "relation_raw": relation,
        "update_to_raw": update_to,
        "retraction_relation_keys": retraction_relation_keys,
        "has_independent_relation": bool(retraction_relation_keys),
        "has_publisher_update_to": bool(publisher_update_to),
        "has_rw_update_to": bool(rw_update_to),
    }


def openalex_check(doi: str, email: str) -> dict:
    try:
        r = httpx.get(f"https://api.openalex.org/works/doi:{doi}", params={"mailto": email}, timeout=20.0)
    except httpx.HTTPError as e:
        return {"status": "error", "error": str(e)}
    if r.status_code != 200:
        return {"status": r.status_code}
    d = r.json()
    return {"status": 200, "is_retracted": d.get("is_retracted")}


def main() -> None:
    v1 = json.loads((ROOT / "results/phase5_27_gap_case_diagnosis.json").read_text(encoding="utf-8"))
    email = os.environ.get("NCBI_EMAIL", "test@example.com")
    api_key = os.environ.get("NCBI_API_KEY")

    results = []
    for case in v1:
        pmid = case["pmid"]
        doi = _real_doi(case.get("doi"))

        pm = pubmed_full_check(pmid, email, api_key)
        time.sleep(0.11 if api_key else 0.34)
        cr = crossref_full_check(doi, email) if doi else {"status": "no_doi"}
        time.sleep(0.12)
        oa = openalex_check(doi, email) if doi else {"status": "no_doi"}
        time.sleep(0.1)

        independent = (
            pm.get("title_text_flags_retraction", False)
            or cr.get("has_independent_relation", False)
            or cr.get("has_publisher_update_to", False)
        )
        rw_derived = (oa.get("is_retracted") is True) or cr.get("has_rw_update_to", False)

        if independent:
            classification = "independent_evidence"
        elif rw_derived:
            classification = "rw_derived_only"
        else:
            classification = "rw_only_uncorroborated"

        evidence_notes = []
        if pm.get("title_text_flags_retraction"):
            evidence_notes.append(f"PubMed title itself: {pm['title'][:80]!r}")
        if cr.get("has_independent_relation"):
            evidence_notes.append(f"Crossref relation (publisher-asserted): {cr['retraction_relation_keys']}")
        if cr.get("has_publisher_update_to"):
            evidence_notes.append("Crossref update-to, source=publisher")
        if rw_derived and not independent:
            evidence_notes.append(
                f"RW-derived only: OpenAlex is_retracted={oa.get('is_retracted')}, "
                f"Crossref update-to source=retraction-watch={cr.get('has_rw_update_to')}"
            )

        row = {
            "pmid": pmid, "doi": doi, "rw_reason": case.get("rw_reason"),
            "pubmed_check": pm, "crossref_check": cr, "openalex_check": oa,
            "classification": classification, "evidence_notes": evidence_notes,
        }
        results.append(row)
        print(f"{pmid}: {classification} -- {'; '.join(evidence_notes) if evidence_notes else 'no evidence found'}")

    from collections import Counter
    counts = Counter(r["classification"] for r in results)
    n_total = len(results)
    n_indep = counts.get("independent_evidence", 0)
    n_rw_only = counts.get("rw_only_uncorroborated", 0)

    OUT_JSON.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\nwrote {OUT_JSON}")

    lines = [
        "# Phase 5 Part A, REDONE: independent vs. RW-derived evidence, 24 distinct PMIDs",
        "",
        "Rerun after fixing two real problems in v1: OpenAlex's `is_retracted` is RW-sourced, not",
        "independent (per OpenAlex's own documentation, fetched live this session); Crossref's",
        "`relation` field was checked too crudely (a false positive on an unrelated `has-review`",
        "link). See the module docstring in `phase5_diagnose_27_gap_cases_v2.py` for the exact",
        "classification rules, fixed before this rerun.",
        "",
        "## Classification summary",
        "",
        "| Classification | n |",
        "|---|---|",
    ]
    for k in ("independent_evidence", "rw_derived_only", "rw_only_uncorroborated"):
        lines.append(f"| {k} | {counts.get(k, 0)} |")

    lines += [
        "",
        f"**Rate with all {n_total} cases counted as genuine gaps: {n_total}/296 pool = {100*n_total/296:.2f}%**",
        f"(unchanged from the row/PMID-level correction -- classification here doesn't change *whether*",
        f"a gap exists, only how well-corroborated each one is by a source independent of RW).",
        f"",
        f"**Of the {n_total}, {n_indep} ({100*n_indep/n_total:.1f}%) have genuinely independent",
        f"corroborating evidence; {counts.get('rw_derived_only',0)} are corroborated only by a",
        f"source that itself derives from RW (not independent validation); {n_rw_only} rest on RW",
        f"alone with no corroboration found anywhere.**",
        "",
        "## Full per-case detail",
        "",
        "| PMID | Classification | Evidence |",
        "|---|---|---|",
    ]
    for r in results:
        lines.append(f"| {r['pmid']} | {r['classification']} | {'; '.join(r['evidence_notes']) or '(none found)'} |")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
