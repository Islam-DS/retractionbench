"""Phase 5 Part B, THIRD run (prereg/phase5_record_level_audit.md + both 2026-10-04 addenda):
scaled PubMed-tag-vs-RW check against the prespecified, now Retraction-nature-only, PMID-deduped
300-record stratified sample (`data/interim/phase5_scaled_sample_v2_retraction_only.json`), using
the same independent-vs-RW-derived classification rules as Part A's redo, PLUS a check for
`"Retraction of Publication"` (the distinct PubMed pubtype that applies to a retraction NOTICE's
own PMID, not the original paper's) to catch a possible original/notice PMID mix-up in RW's own
`original_paper_pubmed_id` field, per the author's explicit request this round.

Caches every raw API response verbatim with its query timestamp
(`data/interim/phase5_part_b_raw_responses.jsonl`) so this run is auditable and re-derivable
without re-querying the live APIs. Records the exact git commit this script ran under.
"""

import json
import re
import subprocess
import time
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

import httpx
from dotenv import load_dotenv
import os

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_PATH = ROOT / "data/interim/phase5_scaled_sample_v2_retraction_only.json"
RAW_CACHE_PATH = ROOT / "data/interim/phase5_part_b_raw_responses_v2.jsonl"
OUT_JSON = ROOT / "results/phase5_part_b_scaled_check_v2.json"
OUT_MD = ROOT / "results/phase5_part_b_scaled_check_v2.md"

_DOI_PLACEHOLDERS = {"unavailable", "n/a", "na", "none", "unknown", ""}
_RETRACT_WORDS = re.compile(r"retract|withdraw", re.IGNORECASE)


def _real_doi(raw) -> str | None:
    # The sample JSON was serialized from a pandas DataFrame; a missing DOI round-trips as a
    # literal float NaN (Python's json module emits/parses the non-standard `NaN` token), not a
    # string -- caught when this crashed on `.strip()` against a float. Treat any non-string
    # (NaN included) the same as an empty/placeholder DOI, not an error.
    if not isinstance(raw, str) or raw.strip().lower() in _DOI_PLACEHOLDERS:
        return None
    return raw


def _git_hash() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def _cache_raw(cache_f, source: str, key: str, response_json) -> None:
    cache_f.write(
        json.dumps(
            {"source": source, "key": key, "queried_at_utc": datetime.now(UTC).isoformat(), "response": response_json}
        )
        + "\n"
    )


def _get_with_retries(url: str, params: dict, attempts: int = 3) -> httpx.Response | None:
    """A transient read-timeout or connection error is retried, not left to crash the whole
    batch -- caught the hard way when one PubMed timeout killed a run 95/300 records in, with
    no retry around that call even though Crossref/OpenAlex already had one. Same backoff
    shape as `ingest/pubmed.py`'s own MAX_RETRIES pattern elsewhere in this project.
    """
    for attempt in range(attempts):
        try:
            return httpx.get(url, params=params, timeout=20.0)
        except httpx.HTTPError:
            if attempt == attempts - 1:
                return None
            time.sleep(2**attempt)
    return None


def _parse_pubmed(data: dict, pmid: str) -> dict:
    rec = data.get("result", {}).get(pmid)
    if rec is None or "error" in rec:
        return {"status": "no_record"}
    title = rec.get("title", "") or ""
    pubtype = rec.get("pubtype", [])
    return {
        "status": 200, "title": title, "pubtype": pubtype,
        "tagged": "Retracted Publication" in pubtype,
        # "Retraction of Publication" is PubMed's distinct pubtype for a retraction NOTICE's own
        # PMID (not the original article). If RW's `original_paper_pubmed_id` actually points to
        # a notice PMID rather than the original paper's, this would be true instead of
        # "Retracted Publication" -- a possible notice/original mix-up, checked per the author's
        # explicit request this round, not assumed absent.
        "is_itself_a_retraction_notice": "Retraction of Publication" in pubtype,
        "title_text_flags_retraction": bool(_RETRACT_WORDS.search(title)),
    }


def _parse_crossref(data: dict) -> dict:
    msg = data.get("message", {})
    relation = msg.get("relation") or {}
    update_to = msg.get("update-to") or []
    return {
        "status": 200,
        "has_independent_relation": any(_RETRACT_WORDS.search(k) for k in relation),
        "has_publisher_update_to": any(u.get("source") == "publisher" for u in update_to),
        "has_rw_update_to": any(u.get("source") == "retraction-watch" for u in update_to),
    }


def pubmed_check(pmid: str, email: str, api_key: str | None, cache_f, resume_cache: dict) -> dict:
    cached = resume_cache.get(("pubmed", pmid))
    if cached is not None:
        return _parse_pubmed(cached, pmid)
    params = {"db": "pubmed", "id": pmid, "retmode": "json", "tool": "retraction-bench", "email": email}
    if api_key:
        params["api_key"] = api_key
    r = _get_with_retries("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi", params)
    if r is None:
        return {"status": "error_after_retries"}
    if r.status_code != 200:
        return {"status": r.status_code}
    data = r.json()
    _cache_raw(cache_f, "pubmed", pmid, data)
    return _parse_pubmed(data, pmid)


def crossref_check(doi: str, email: str, cache_f, resume_cache: dict) -> dict:
    cached = resume_cache.get(("crossref", doi))
    if cached is not None:
        return _parse_crossref(cached)
    r = _get_with_retries(f"https://api.crossref.org/works/{doi}", {"mailto": email})
    if r is None:
        return {"status": "error_after_retries"}
    if r.status_code != 200:
        return {"status": r.status_code}
    data = r.json()
    _cache_raw(cache_f, "crossref", doi, data)
    return _parse_crossref(data)


def _parse_openalex(data: dict) -> dict:
    return {"status": 200, "is_retracted": data.get("is_retracted")}


def openalex_check(doi: str, email: str, cache_f, resume_cache: dict) -> dict:
    cached = resume_cache.get(("openalex", doi))
    if cached is not None:
        return _parse_openalex(cached)
    r = _get_with_retries(f"https://api.openalex.org/works/doi:{doi}", {"mailto": email})
    if r is None:
        return {"status": "error_after_retries"}
    if r.status_code != 200:
        return {"status": r.status_code}
    data = r.json()
    _cache_raw(cache_f, "openalex", doi, data)
    return _parse_openalex(data)


def _load_resume_cache() -> dict:
    """Resumability: a prior run that crashed partway (caught live -- a transient PubMed
    timeout killed a run 95/300 records in) should not re-spend API calls for records it
    already fetched. Keyed by (source, key); last write wins if a key appears more than once.
    """
    cache: dict = {}
    if not RAW_CACHE_PATH.exists():
        return cache
    with RAW_CACHE_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            cache[(row["source"], row["key"])] = row["response"]
    return cache


def main() -> None:
    sample_doc = json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))
    sample = sample_doc["sample"]
    allocation = sample_doc["allocation"]
    email = os.environ.get("NCBI_EMAIL", "test@example.com")
    api_key = os.environ.get("NCBI_API_KEY")
    git_hash = _git_hash()

    n_sampled = len(sample)
    n_no_pmid = sum(1 for r in sample if not r.get("original_paper_pubmed_id"))
    eligible = [r for r in sample if r.get("original_paper_pubmed_id")]

    resume_cache = _load_resume_cache()
    print(f"Resuming with {len(resume_cache)} already-cached responses from a prior run.")

    results = []
    with RAW_CACHE_PATH.open("a", encoding="utf-8") as cache_f:
        for i, row in enumerate(eligible):
            pmid = row["original_paper_pubmed_id"].strip()
            doi = _real_doi(row.get("original_paper_doi"))
            year = row.get("year")

            pm_was_cached = ("pubmed", pmid) in resume_cache
            pm = pubmed_check(pmid, email, api_key, cache_f, resume_cache)
            if not pm_was_cached:
                time.sleep(0.11 if api_key else 0.34)

            cr_was_cached = doi is not None and ("crossref", doi) in resume_cache
            cr = crossref_check(doi, email, cache_f, resume_cache) if doi else {"status": "no_doi"}
            if doi and not cr_was_cached:
                time.sleep(0.12)

            oa_was_cached = doi is not None and ("openalex", doi) in resume_cache
            oa = openalex_check(doi, email, cache_f, resume_cache) if doi else {"status": "no_doi"}
            if doi and not oa_was_cached:
                time.sleep(0.1)

            if pm.get("status") != 200:
                classification_gap = "unresolved_pubmed_lookup_failed"
                is_gap = None
            elif pm.get("is_itself_a_retraction_notice"):
                # RW's original_paper_pubmed_id resolves to a record PubMed itself classifies as
                # a retraction NOTICE ("Retraction of Publication"), not the original paper --
                # a likely notice/original mix-up in RW's own data, not a genuine PubMed tagging
                # gap on the original paper (which this ID isn't). Flagged separately, not
                # silently folded into either the gap or non-gap count.
                classification_gap = "notice_original_mixup_suspected"
                is_gap = None
            else:
                is_gap = not pm.get("tagged", False)
                if not is_gap:
                    classification_gap = "pubmed_tagged_no_gap"
                else:
                    independent = (
                        pm.get("title_text_flags_retraction", False)
                        or cr.get("has_independent_relation", False)
                        or cr.get("has_publisher_update_to", False)
                    )
                    rw_derived = (oa.get("is_retracted") is True) or cr.get("has_rw_update_to", False)
                    if independent:
                        classification_gap = "gap_independent_evidence"
                    elif rw_derived:
                        classification_gap = "gap_rw_derived_only"
                    else:
                        classification_gap = "gap_rw_only_uncorroborated"

            results.append(
                {"pmid": pmid, "doi": doi, "year": year, "publisher": row.get("publisher"),
                 "is_gap": is_gap, "classification": classification_gap,
                 "queried_at_utc": datetime.now(UTC).isoformat()}
            )
            if (i + 1) % 25 == 0:
                print(f"...{i+1}/{len(eligible)} processed")

    OUT_JSON.write_text(
        json.dumps({"git_hash": git_hash, "n_sampled": n_sampled, "n_no_pmid_excluded": n_no_pmid,
                    "n_checked": len(eligible), "results": results}, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"wrote {OUT_JSON}")
    print(f"wrote raw response cache: {RAW_CACHE_PATH}")

    # --- Wilson CI by year (primary) ---
    from statsmodels.stats.proportion import proportion_confint

    n_mixup = sum(1 for r in results if r["classification"] == "notice_original_mixup_suspected")
    n_lookup_failed = sum(1 for r in results if r["classification"] == "unresolved_pubmed_lookup_failed")
    resolved = [r for r in results if r["is_gap"] is not None]
    by_year = defaultdict(list)
    for r in resolved:
        by_year[r["year"]].append(r["is_gap"])

    overall_gap = sum(r["is_gap"] for r in resolved)
    overall_n = len(resolved)
    lo, hi = proportion_confint(overall_gap, overall_n, method="wilson") if overall_n else (float("nan"), float("nan"))

    max_alloc_dev = max(abs(a["exact_fraction"] - a["realized_fraction"]) for a in allocation.values()) if allocation else None

    lines = [
        "# Phase 5 Part B, v2: scaled PubMed-tag-vs-RW check, Retraction-nature-only, PMID-deduped",
        "",
        f"Prereg: `prereg/phase5_record_level_audit.md` + both 2026-10-04 addenda. Git hash this",
        f"ran under: `{git_hash}`.",
        "",
        "## Sampling-frame counts",
        "",
        f"- Population with a real PubMed ID, before nature filter: 33,359",
        f"- Excluded as non-Retraction-nature (Correction/Expression of concern/Reinstatement): 3,837",
        f"- Excluded as PMID-level duplicates (deduped, lowest record_id kept): 22",
        f"- **Final population (Retraction-nature, real PMID, distinct, dated): 29,500**",
        f"- Sample drawn (stratified by year, seed 42, proportional allocation, "
        f"max exact-vs-realized fraction deviation: {max_alloc_dev:.5f} -- negligible, naive pooled "
        f"rate below is not meaningfully biased by rounding): {n_sampled}",
        f"- Excluded at query time (no PubMed ID after all): {n_no_pmid}",
        f"- Checked: {len(eligible)}",
        f"- Unresolved (PubMed lookup failed after retries): {n_lookup_failed}",
        f"- **Flagged as suspected notice/original PMID mix-up** (PubMed itself classifies this ID",
        f"  as a retraction notice, `\"Retraction of Publication\"`, not the original paper) -- ",
        f"  excluded from the gap-rate denominator, not counted as a gap or a non-gap: {n_mixup}",
        f"- Resolved and classified (gap rate denominator): {overall_n}",
        "",
        f"## Overall miss rate: {overall_gap}/{overall_n} = {100*overall_gap/overall_n:.2f}%, "
        f"Wilson 95% CI [{lo*100:.2f}%, {hi*100:.2f}%]" if overall_n else "## No resolved records",
        "",
        "## By retraction year (Wilson 95% CI -- primary)",
        "",
        "| Year | n | Gap n | Gap rate | Wilson 95% CI |",
        "|---|---|---|---|---|",
    ]
    for year in sorted(by_year):
        vals = by_year[year]
        n = len(vals)
        g = sum(vals)
        ylo, yhi = proportion_confint(g, n, method="wilson") if n else (float("nan"), float("nan"))
        lines.append(f"| {year} | {n} | {g} | {100*g/n:.1f}% | [{ylo*100:.1f}%, {yhi*100:.1f}%] |")

    lines += ["", "## By publisher (descriptive only -- no CI, most publishers have very few sampled records)", "",
              "| Publisher | n | Gap n | Gap rate |", "|---|---|---|---|"]
    by_pub = defaultdict(list)
    for r in resolved:
        by_pub[r["publisher"] or "(unknown)"].append(r["is_gap"])
    for pub, vals in sorted(by_pub.items(), key=lambda kv: -len(kv[1]))[:30]:
        n = len(vals)
        g = sum(vals)
        lines.append(f"| {pub} | {n} | {g} | {100*g/n:.1f}% |")

    class_counts = Counter(r["classification"] for r in results)
    lines += ["", "## Independent-vs-RW-derived breakdown (gap cases only)", "",
              "| Classification | n |", "|---|---|"]
    for k in ("gap_independent_evidence", "gap_rw_derived_only", "gap_rw_only_uncorroborated"):
        lines.append(f"| {k} | {class_counts.get(k, 0)} |")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
