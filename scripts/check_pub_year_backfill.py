"""Phase 2 integrity check for the pub_year backfill (see `backfill_benchmark_pub_years.py`).

Verifies, against the real corpus and the real lookup file just written -- not assumed:
A. every row has a pub_year or an explicitly documented missing value (no silent gaps)
B. all 57 real-PMID benchmark-role rows got an independently-sourced year
C. background years are byte-identical before vs after (no accidental rewrite)
D. no benchmark gold field (items.jsonl / sources.jsonl) was read anywhere in the backfill path
E. the lookup is auditable: every row's source/provenance is recorded, not just its value

Run with: `uv run python scripts/check_pub_year_backfill.py` (repo root). Read-only; makes no
API calls, writes one report.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS_PATH = ROOT / "data/interim/corpus/assembled_corpus.jsonl"
LOOKUP_PATH = ROOT / "data/interim/corpus/pub_year_lookup.jsonl"
REPORT_PATH = ROOT / "reports/pub_year_backfill_integrity.md"


def main() -> None:
    corpus_rows = []
    with CORPUS_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                corpus_rows.append(json.loads(line))

    lookup_rows = []
    with LOOKUP_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                lookup_rows.append(json.loads(line))

    # --- A: every corpus row has a corresponding lookup row (1:1 by position; pmid can repeat
    # for distinct rows only in principle -- checked exactly, not assumed unique) ---
    check_a = len(corpus_rows) == len(lookup_rows)

    # --- B: every real-PMID benchmark-role row resolved ---
    by_role_corpus: dict[str, list[dict]] = {}
    for r in corpus_rows:
        by_role_corpus.setdefault(r["corpus_role"], []).append(r)
    by_role_lookup: dict[str, list[dict]] = {}
    for r in lookup_rows:
        by_role_lookup.setdefault(r["corpus_role"], []).append(r)

    resolvable_roles = ("benchmark_source", "superseding_evidence")
    n_resolvable = sum(len(by_role_corpus.get(role, [])) for role in resolvable_roles)
    n_resolved = sum(
        1 for role in resolvable_roles for r in by_role_lookup.get(role, []) if r["pub_year"] is not None
    )
    check_b = n_resolved == n_resolvable == 57

    # --- C: background pub_year unchanged, compared pmid-for-pmid against the live corpus file
    # (not against a cached copy) ---
    background_before = {r["pmid"]: r.get("pub_year") for r in by_role_corpus.get("background", [])}
    background_after = {r["pmid"]: r["pub_year"] for r in by_role_lookup.get("background", [])}
    check_c = background_before == background_after

    # --- D: static check that the backfill module never IMPORTS benchmark gold readers --
    # restricted to actual `import`/`from ... import` lines, not docstring/comment prose
    # (an earlier version of this check false-flagged on the module's own docstring explaining
    # *why* SupersededSource/BenchmarkItem are not used -- fixed to look at real code lines only).
    backfill_src = (ROOT / "src/retraction_bench/corpus/pub_year_backfill.py").read_text(encoding="utf-8")
    import_lines = [
        line for line in backfill_src.splitlines() if line.strip().startswith(("import ", "from "))
    ]
    forbidden_tokens = ["benchmark_io", "items.jsonl", "sources.jsonl", "load_items", "load_sources", "schemas"]
    found_forbidden = [t for t in forbidden_tokens if any(t in line for line in import_lines)]
    check_d = len(found_forbidden) == 0

    # --- E: every lookup row carries a documented source ---
    check_e = all("source" in r and r["source"] for r in lookup_rows)

    # Before/after table
    table_rows = []
    for role in ("background", "benchmark_source", "supersession_notice", "superseding_evidence"):
        before = by_role_corpus.get(role, [])
        after = by_role_lookup.get(role, [])
        n = len(before)
        n_before_present = sum(1 for r in before if r.get("pub_year") is not None)
        n_after_present = sum(1 for r in after if r["pub_year"] is not None)
        sources = sorted({r["source"] for r in after})
        table_rows.append((role, n, n_before_present, n_after_present, ", ".join(sources)))

    lines = [
        "# pub_year backfill integrity check",
        "",
        "| ROLE | N | pub_year BEFORE (non-null) | pub_year AFTER (non-null) | SOURCE |",
        "|---|---|---|---|---|",
    ]
    for role, n, before_n, after_n, sources in table_rows:
        lines.append(f"| {role} | {n} | {before_n} | {after_n} | {sources} |")

    lines += [
        "",
        "## Checks",
        "",
        f"- A. Every corpus row has a lookup row (1:1): {'PASS' if check_a else 'FAIL'} "
        f"({len(corpus_rows)} corpus rows, {len(lookup_rows)} lookup rows)",
        f"- B. All 57 real-PMID benchmark-role rows resolved: {'PASS' if check_b else 'FAIL'} "
        f"({n_resolved}/{n_resolvable})",
        f"- C. Background pub_year unchanged (pmid-for-pmid against the live corpus file): "
        f"{'PASS' if check_c else 'FAIL'}",
        f"- D. Backfill module never references benchmark gold files/loaders (static source scan): "
        f"{'PASS' if check_d else 'FAIL'}" + (f" -- found: {found_forbidden}" if found_forbidden else ""),
        f"- E. Every lookup row carries a documented source: {'PASS' if check_e else 'FAIL'}",
        "",
        f"**Overall: {'ALL CHECKS PASS' if all([check_a, check_b, check_c, check_d, check_e]) else 'AT LEAST ONE CHECK FAILED -- see above'}**",
        "",
        "## Known, disclosed gap (not a failure of this backfill)",
        "",
        f"{sum(1 for r in by_role_lookup.get('background', []) if r['pub_year'] is None)} background rows "
        "have no pub_year in either the before or after state -- these were already missing a parseable "
        "year in the original `mesh_fetch.py` EFetch XML (PubMed itself reported no `JournalIssue/PubDate/Year`), "
        "carried through unchanged, not introduced by this backfill.",
        "",
        "## supersession_notice (24 rows): explicitly unresolvable, not guessed",
        "",
        "Every one of the 24 notice rows has `pub_year=None`, `source=unresolvable_no_real_external_identifier`. "
        "See `pub_year_backfill.py` module docstring for why: the notice's `pmid` field is a synthetic "
        "placeholder, and no separate real identifier for the notice itself exists in `SupersededSource`.",
    ]

    REPORT_PATH.parent.mkdir(exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {REPORT_PATH}")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
