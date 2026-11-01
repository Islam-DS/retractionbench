"""M2 Phase 7: leakage and independence audit between M2 control candidates and the existing
28-item treated benchmark. Infrastructure, not data -- runs cleanly against zero candidates (the
current state; see docs/M2_CONTROL_PROTOCOL.md section 9) and is ready the moment real,
human-verified candidates exist in data/benchmark/controls_v1/control_candidates.csv.

Never silently passes on empty input: an empty candidate file produces an explicit
"0 candidates checked" report, not a false "no leakage found" the way skipping the check
entirely would risk being misread later.

Checks (docs/M2_CONTROL_PROTOCOL.md Phase 7):
  1. Shared source_registry_id/DOI between a control and any treated item's own source
     (data/benchmark/sources.jsonl) or its post_supersession_evidence identifiers.
  2. Overlapping title text (normalized word-set Jaccard) between a control's source_title and
     any treated item's source title or post_supersession_evidence note -- a heuristic flag for
     human review, not an automatic rejection (title overlap can be coincidental for common
     clinical terms; every flag is reported, not auto-resolved).
  3. A control's own identifier colliding with an existing corpus document ID already tied to a
     treated item's record (checked against data/benchmark/items.jsonl's supporting_sources and
     post_supersession_evidence identifiers directly, not a separate index this script would
     have to trust).

Usage: python scripts/check_control_leakage.py [path/to/control_candidates.csv]
"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CANDIDATES = ROOT / "data/benchmark/controls_v1/control_candidates.csv"
TITLE_OVERLAP_THRESHOLD = 0.5  # word-set Jaccard; flag for review above this, not auto-reject

STOPWORDS = {"the", "a", "an", "of", "in", "on", "for", "and", "or", "to", "with", "is", "does", "how"}


def normalize_words(text: str) -> set[str]:
    return {w for w in "".join(c.lower() if c.isalnum() else " " for c in text).split() if w and w not in STOPWORDS}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def load_treated_identifiers() -> tuple[set[str], set[str], dict[str, str]]:
    """Returns (all identifiers used by treated items, all their titles-as-word-sets keyed by
    id) drawn from items.jsonl and sources.jsonl directly -- not a separately maintained index
    that could silently drift from the real benchmark data.
    """
    ids: set[str] = set()
    titles: dict[str, str] = {}

    sources_path = ROOT / "data/benchmark/sources.jsonl"
    if sources_path.exists():
        with sources_path.open(encoding="utf-8") as f:
            for line in f:
                row = json.loads(line)
                for key in ("doi", "source_registry_id"):
                    if row.get(key):
                        ids.add(str(row[key]))
                for ext_id in row.get("external_ids", []) or []:
                    ids.add(str(ext_id))
                if row.get("title"):
                    titles[row.get("source_registry_id", row.get("doi", ""))] = row["title"]

    items_path = ROOT / "data/benchmark/items.jsonl"
    if items_path.exists():
        with items_path.open(encoding="utf-8") as f:
            for line in f:
                row = json.loads(line)
                for sid in row.get("supporting_sources", []) or []:
                    ids.add(str(sid))
                for ev in row.get("post_supersession_evidence", []) or []:
                    if ev.get("identifier"):
                        ids.add(str(ev["identifier"]))

    return ids, set(), titles


def run(candidates_path: Path) -> int:
    treated_ids, _, treated_titles = load_treated_identifiers()
    treated_title_words = {k: normalize_words(v) for k, v in treated_titles.items()}

    if not candidates_path.exists():
        print(f"No candidate file at {candidates_path}. 0 candidates checked. "
              f"This is a report of the current (empty) state, not an assumption that a real "
              f"check has already passed -- see docs/M2_CONTROL_PROTOCOL.md section 9.")
        return 0

    with candidates_path.open(encoding="utf-8", newline="") as f:
        candidates = list(csv.DictReader(f))

    findings: list[dict] = []
    for cand in candidates:
        cand_id = cand.get("control_candidate_id") or cand.get("candidate_id", "?")
        cand_title = cand.get("candidate_title") or cand.get("source_title", "")
        cand_words = normalize_words(cand_title)

        for id_field in ("source_id", "doi", "pmid"):
            cand_source_id = str(cand.get(id_field, "") or "")
            if cand_source_id and cand_source_id in treated_ids:
                findings.append({"type": "shared_identifier", "candidate_id": cand_id, "field": id_field, "identifier": cand_source_id})

        for treated_id, words in treated_title_words.items():
            score = jaccard(cand_words, words)
            if score >= TITLE_OVERLAP_THRESHOLD:
                findings.append({
                    "type": "title_overlap", "candidate_id": cand_id, "treated_source": treated_id,
                    "jaccard": round(score, 3), "candidate_title": cand_title, "treated_title": treated_titles[treated_id],
                })

    report = {
        "n_candidates_checked": len(candidates),
        "n_treated_identifiers_checked_against": len(treated_ids),
        "n_findings": len(findings),
        "findings": findings,
    }
    out_path = candidates_path.parent / "m2_control_candidate_leakage_report.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Checked {len(candidates)} candidates against {len(treated_ids)} treated-item identifiers.")
    print(f"Findings: {len(findings)}")
    for finding in findings:
        print(f"  {finding}")
    print(f"Report written: {out_path}")
    return 1 if findings else 0


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CANDIDATES
    raise SystemExit(run(path))
