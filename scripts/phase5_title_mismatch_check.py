"""Phase 5, author-requested validation (2026-10-05, item 4): fetch the real PubMed title for
every PMID in the curated pool (Part A, 296 distinct papers) and the Part B v2 sample (300
records), and flag any whose PubMed title does not reasonably match Retraction Watch's own
`title` field for that same record.

This exists because the 2026-10-05 dossier re-check (`results/phase5_part_b_downstream_dossiers.md`)
found exactly this kind of mismatch by accident, for one case (RW record_id 250, PMID "1834920"):
RW's title described the Scott Reuben celecoxib fraud case, but PubMed's real record at that PMID
was an unrelated 1991 E. coli protein-translocation paper -- RW's PMID field was simply wrong (a
one-digit truncation of the real PMID). This script makes that check systematic across both
populations rather than relying on noticing a mismatch by chance.

Caches every raw ESummary response (batched, up to 100 PMIDs per request) with its query
timestamp, retried with backoff, resumable across runs.
"""

from __future__ import annotations

import difflib
import json
import os
import re
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
CACHE_PATH = ROOT / "data" / "interim" / "phase5_title_mismatch_esummary_cache.json"
OUT_JSON = ROOT / "results" / "phase5_title_mismatch_check.json"
OUT_MD = ROOT / "results" / "phase5_title_mismatch_check.md"

_PAREN_SUFFIX = re.compile(r"\s*\((pub\s*\d+|review|protocol)\)\s*$", re.IGNORECASE)
_PUNCT = re.compile(r"[^a-z0-9\s]")


def normalize_title(title: str) -> str:
    """Lowercase, drop a trailing '(Pub N)'/'(Review)'/'(Protocol)' tag, strip punctuation."""
    t = _PAREN_SUFFIX.sub("", title or "")
    t = t.lower()
    t = _PUNCT.sub(" ", t)
    return " ".join(t.split())


def title_similarity(a: str, b: str) -> float:
    """difflib SequenceMatcher ratio on normalized titles, in [0.0, 1.0]."""
    na, nb = normalize_title(a), normalize_title(b)
    if not na or not nb:
        return 0.0
    return difflib.SequenceMatcher(None, na, nb).ratio()


def _git_hash() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "unknown"


def load_cache() -> dict[str, dict]:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text())
    return {}


def save_cache(cache: dict[str, dict]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2))


def fetch_titles(pmids: list[str], client: httpx.Client, cache: dict[str, dict]) -> dict[str, str]:
    """Batched ESummary lookup (<=100 PMIDs/request per NCBI guidance), cached, retried."""
    email = os.environ.get("NCBI_EMAIL")
    titles: dict[str, str] = {}
    to_fetch = [p for p in pmids if p not in cache]
    for i in range(0, len(to_fetch), 100):
        batch = to_fetch[i : i + 100]
        for attempt in range(5):
            try:
                resp = client.get(
                    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                    params={"db": "pubmed", "id": ",".join(batch), "retmode": "json", "email": email},
                    timeout=30,
                )
                data = resp.json()
                result = data.get("result", {})
                now = datetime.now(UTC).isoformat()
                for pmid in batch:
                    rec = result.get(pmid, {})
                    title = rec.get("title", "") if "error" not in rec else ""
                    cache[pmid] = {"title": title, "queried_at_utc": now}
                break
            except Exception:
                if attempt == 4:
                    for pmid in batch:
                        cache.setdefault(pmid, {"title": "", "queried_at_utc": None, "error": True})
                time.sleep(2**attempt)
        time.sleep(0.4)
        save_cache(cache)
    for p in pmids:
        titles[p] = cache.get(p, {}).get("title", "")
    return titles


def load_part_a() -> pd.DataFrame:
    df = pd.read_csv(ROOT / "data" / "interim" / "tier1_candidates_final3_verified.csv")
    df = df.dropna(subset=["pmid"]).copy()
    df["pmid"] = df["pmid"].astype(str).str.strip()
    df = df[df["pmid"] != "0"]
    df = df.drop_duplicates(subset="record_id", keep="first")
    df = df.drop_duplicates(subset="pmid", keep="first")
    return df[["record_id", "pmid", "title"]].rename(columns={"title": "rw_title"})


def load_part_b() -> pd.DataFrame:
    sample = json.loads(
        (ROOT / "data" / "interim" / "phase5_scaled_sample_v2_retraction_only.json").read_text()
    )["sample"]
    import duckdb

    con = duckdb.connect(str(ROOT / "data" / "interim" / "retraction_watch.duckdb"), read_only=True)
    pmids = [str(r["original_paper_pubmed_id"]) for r in sample]
    rows = con.execute(
        "SELECT original_paper_pubmed_id, title FROM raw_retraction_watch "
        f"WHERE original_paper_pubmed_id IN ({','.join('?' * len(pmids))})",
        pmids,
    ).fetchall()
    df = pd.DataFrame(rows, columns=["pmid", "rw_title"])
    df["pmid"] = df["pmid"].astype(str)
    df = df.drop_duplicates(subset="pmid", keep="first")
    return df


def main(threshold: float = 0.4) -> None:
    part_a = load_part_a()
    part_b = load_part_b()

    client = httpx.Client()
    cache = load_cache()

    a_titles = fetch_titles(part_a["pmid"].tolist(), client, cache)
    b_titles = fetch_titles(part_b["pmid"].tolist(), client, cache)

    def flag(df: pd.DataFrame, titles: dict[str, str], pool_name: str) -> list[dict]:
        flagged = []
        for _, row in df.iterrows():
            pmid = row["pmid"]
            pubmed_title = titles.get(pmid, "")
            sim = title_similarity(row["rw_title"], pubmed_title)
            if sim < threshold:
                flagged.append(
                    {
                        "pool": pool_name,
                        "pmid": pmid,
                        "rw_title": row["rw_title"],
                        "pubmed_title": pubmed_title,
                        "similarity": round(sim, 3),
                        "pubmed_lookup_empty": pubmed_title == "",
                    }
                )
        return flagged

    flagged_a = flag(part_a, a_titles, "Part A (curated pool)")
    flagged_b = flag(part_b, b_titles, "Part B v2 (broad sample)")
    flagged = flagged_a + flagged_b

    out = {
        "git_hash": _git_hash(),
        "threshold": threshold,
        "n_checked_part_a": len(part_a),
        "n_checked_part_b": len(part_b),
        "n_flagged_part_a": len(flagged_a),
        "n_flagged_part_b": len(flagged_b),
        "flagged": flagged,
    }
    OUT_JSON.write_text(json.dumps(out, indent=2))

    lines = [
        "# Phase 5: PubMed-title-vs-RW-title mismatch check",
        "",
        "Author-requested validation (2026-10-05, item 4), following the accidental discovery of",
        "one wrong/truncated PMID (RW record_id 250) during the Part B downstream dossier re-check.",
        f"Git hash: `{out['git_hash']}`.",
        "",
        f"Checked {out['n_checked_part_a']} distinct PMIDs in the curated pool (Part A) and "
        f"{out['n_checked_part_b']} in the Part B v2 broad sample. Similarity: difflib "
        f"`SequenceMatcher` ratio on normalized titles (lowercased, punctuation stripped, "
        f"trailing `(Pub N)`/`(Review)`/`(Protocol)` tags removed); threshold {threshold} chosen "
        "to catch genuine mismatches while tolerating RW's own paraphrasing/abbreviation of "
        "titles (observed to vary even for confirmed-correct pairs).",
        "",
        f"**Part A flagged: {out['n_flagged_part_a']}/{out['n_checked_part_a']}. "
        f"Part B flagged: {out['n_flagged_part_b']}/{out['n_checked_part_b']}.**",
        "",
        "| Pool | PMID | RW title | PubMed title | Similarity |",
        "|---|---|---|---|---|",
    ]
    for f in flagged:
        lines.append(
            f"| {f['pool']} | {f['pmid']} | {f['rw_title'][:80]} | "
            f"{(f['pubmed_title'] or '(empty/no record)')[:80]} | {f['similarity']} |"
        )
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"Part A flagged: {out['n_flagged_part_a']}/{out['n_checked_part_a']}")
    print(f"Part B flagged: {out['n_flagged_part_b']}/{out['n_checked_part_b']}")
    for f in flagged:
        print(f)


if __name__ == "__main__":
    main()
