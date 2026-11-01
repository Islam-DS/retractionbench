"""Phase 1 Stage 1A exploration report.

Reads the raw Retraction Watch DuckDB table, derives typed/split fields in
memory (the raw table itself is never mutated), and writes
results/phase1_exploration.md. No filtering or domain-selection decisions
are made here -- this is what Stage 1B's decisions get made from.

Every distribution is broken down by RetractionNature (Retraction,
Correction, Expression of Concern, Reinstatement, ...), with the
Retraction column marked "(paper-1 scope)". See docs/DECISIONS.md ADR-014
for why notice type is a first-class dimension here rather than a filter.
"""

import itertools
from collections import Counter
from datetime import date
from pathlib import Path

import duckdb
import pandas as pd

from retraction_bench.curate.claim_type_screen import (
    DEFAULT_CLAIM_SCREEN_PATH,
    ClaimType,
    classify_claim_type,
    load_claim_type_screen,
)
from retraction_bench.curate.reason_screen import DEFAULT_SCREEN_PATH, Tier, classify_tier, load_reason_screen
from retraction_bench.ingest.data_notes import append_entry
from retraction_bench.ingest.parsing import is_missing_value, is_resolvable_doi, parse_rw_date, split_multivalue
from retraction_bench.ingest.retraction_watch import DATA_NOTES_PATH, DB_PATH, RAW_TABLE_NAME

REPORT_PATH = Path("results/phase1_exploration.md")

NOTICE_TYPE_ORDER = ["Retraction", "Correction", "Expression of Concern", "Reinstatement"]
PAPER1_SCOPE_NOTICE = "Retraction"
IMPLAUSIBLE_GAP_DAYS = 365 * 40  # disclosed heuristic, not a hard exclusion -- see report text.
CLINICAL_CANDIDATE_SUBJECT_PREFIX = "(HSC)"
CLINICAL_CANDIDATE_EXTRA_SUBJECTS = ["(BLS) Toxicology"]  # requested alongside the (HSC) family


# --------------------------------------------------------------------------
# Derivation
# --------------------------------------------------------------------------


def load_enriched_frame(
    db_path: Path = DB_PATH,
    screen_path: Path = DEFAULT_SCREEN_PATH,
    claim_screen_path: Path = DEFAULT_CLAIM_SCREEN_PATH,
) -> pd.DataFrame:
    """Load the raw table and add derived columns needed for the report, without mutating the raw table."""
    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        df = conn.execute(f"SELECT * FROM {RAW_TABLE_NAME}").df()
    finally:
        conn.close()

    # DuckDB VARCHAR NULLs surface as float NaN through pandas; normalize to
    # None so the parsing.py helpers (which only know about str | None) see
    # a consistent "missing" signal instead of crashing on a stray float.
    df = df.astype(object).where(df.notna(), None)

    # The source CSV contains fully blank rows (every field null) -- a
    # structural export artifact, not real records. Kept in this frame for
    # full fidelity, but every report section and data-quality count below
    # excludes them explicitly, since a phantom row isn't a retraction of
    # anything and would silently distort every percentage otherwise.
    df["is_blank_row"] = df["record_id"].isna()

    df["retraction_nature"] = df["retraction_nature"].fillna("(blank)")

    for col in ("retraction_date", "original_paper_date"):
        raw = df[col]
        missing = raw.apply(is_missing_value)
        parsed = raw.apply(parse_rw_date)
        df[f"{col}_missing"] = missing
        df[f"{col}_parsed"] = pd.to_datetime(parsed)
        df[f"{col}_malformed"] = (~missing) & parsed.isna()

    for col in ("retraction_doi", "original_paper_doi"):
        raw = df[col]
        missing = raw.apply(is_missing_value)
        resolvable = raw.apply(is_resolvable_doi)
        df[f"{col}_resolvable"] = resolvable
        df[f"{col}_malformed"] = (~missing) & (~resolvable)

    df["original_paper_pubmed_id_resolvable"] = ~df["original_paper_pubmed_id"].apply(is_missing_value)

    df["subject_list"] = df["subject"].apply(split_multivalue)
    df["reason_list"] = df["reason"].apply(split_multivalue)
    df["reason_count"] = df["reason_list"].apply(len)

    reason_screen = load_reason_screen(screen_path)
    df["candidate_tier"] = df["reason_list"].apply(lambda rs: classify_tier(rs, reason_screen))
    unmapped = {reason for rs in df["reason_list"] for reason in rs} - set(reason_screen)
    df.attrs["unmapped_reasons"] = sorted(unmapped)

    # Claim-type screen: heuristic, unvalidated as of ADR-021 until the
    # author's 100 hand labels come back. Provisional -- see report text.
    claim_screen = load_claim_type_screen(claim_screen_path)
    df["article_type_list"] = df["article_type"].apply(split_multivalue)
    df["claim_type"] = df.apply(
        lambda row: classify_claim_type(row["title"] or "", row["article_type_list"], claim_screen), axis=1
    )
    df["is_clinical_claim"] = df["claim_type"].isin([ClaimType.CLINICAL_INTERVENTION, ClaimType.CLINICAL_OBSERVATIONAL])

    df["gap_valid"] = df["retraction_date_parsed"].notna() & df["original_paper_date_parsed"].notna()
    df["gap_days"] = (df["retraction_date_parsed"] - df["original_paper_date_parsed"]).dt.days
    df["gap_negative"] = df["gap_valid"] & (df["gap_days"] < 0)
    df["gap_implausible"] = df["gap_valid"] & (df["gap_days"] >= 0) & (df["gap_days"] > IMPLAUSIBLE_GAP_DAYS)

    return df


def _notice_types_present(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    observed = df["retraction_nature"].value_counts().index.tolist()
    extra = sorted(nt for nt in observed if nt not in NOTICE_TYPE_ORDER)
    return NOTICE_TYPE_ORDER + extra, extra


# --------------------------------------------------------------------------
# Markdown helpers
# --------------------------------------------------------------------------


def _markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(v) for v in row) + " |")
    return "\n".join(lines)


def _notice_headers(notice_types: list[str]) -> list[str]:
    return [f"{nt} (paper-1 scope)" if nt == PAPER1_SCOPE_NOTICE else nt for nt in notice_types]


def _count_pivot(
    values: pd.Series, notice: pd.Series, notice_types: list[str], top_n: int | None = None
) -> pd.DataFrame:
    """Crosstab a (possibly exploded) categorical series against notice type, sorted by the Retraction column."""
    ct = pd.crosstab(values, notice)
    for nt in notice_types:
        if nt not in ct.columns:
            ct[nt] = 0
    ct = ct[notice_types]
    ct["Total"] = ct.sum(axis=1)
    sort_col = PAPER1_SCOPE_NOTICE if PAPER1_SCOPE_NOTICE in ct.columns else "Total"
    ct = ct.sort_values(sort_col, ascending=False)
    if top_n:
        ct = ct.head(top_n)
    return ct


def _pivot_to_markdown(ct: pd.DataFrame, index_label: str) -> str:
    headers = [index_label] + _notice_headers(list(ct.columns[:-1])) + ["Total"]
    rows = [[str(idx), *[int(v) for v in row]] for idx, row in ct.iterrows()]
    return _markdown_table(headers, rows)


# --------------------------------------------------------------------------
# Report sections
# --------------------------------------------------------------------------


def _section_overview(df: pd.DataFrame, notice_types: list[str]) -> str:
    total = len(df)
    counts = df["retraction_nature"].value_counts().reindex(notice_types, fill_value=0)
    rows = [
        [f"{nt} (paper-1 scope)" if nt == PAPER1_SCOPE_NOTICE else nt, int(c), f"{c / total * 100:.1f}%"]
        for nt, c in counts.items()
    ]
    rows.append(["**Total**", total, "100.0%"])
    table = _markdown_table(["Notice type", "Count", "% of all records"], rows)
    return f"## 1. Overview by notice type\n\nTotal raw records (all notice types): **{total}**.\n\n{table}\n"


def _section_doi_resolvability(df: pd.DataFrame, notice_types: list[str]) -> str:
    rows = []
    for nt in notice_types:
        sub = df[df["retraction_nature"] == nt]
        total = len(sub)
        resolvable = int(sub["original_paper_doi_resolvable"].sum())
        pct = f"{resolvable / total * 100:.1f}%" if total else "n/a"
        label = f"{nt} (paper-1 scope)" if nt == PAPER1_SCOPE_NOTICE else nt
        rows.append([label, total, resolvable, pct])
    table = _markdown_table(["Notice type", "Total records", "Resolvable OriginalPaperDOI", "%"], rows)
    return (
        "## 2. Records with a resolvable DOI\n\n"
        '"Resolvable DOI" here means `OriginalPaperDOI` -- the superseded paper\'s own identifier, '
        "not the retraction notice's DOI (which is reported separately under data quality).\n\n"
        f"{table}\n"
    )


def _section_year_distribution(df: pd.DataFrame, notice_types: list[str]) -> str:
    retraction_df = df[df["retraction_nature"] == PAPER1_SCOPE_NOTICE]
    years = retraction_df["retraction_date_parsed"].dt.year.dropna().astype(int)
    year_counts = years.value_counts().sort_index()
    year_rows = [[int(y), int(c)] for y, c in year_counts.items()]
    year_table = _markdown_table(["Retraction year", "Count (paper-1 scope: Retraction only)"], year_rows)

    summary_rows = []
    for nt in notice_types:
        sub = df[df["retraction_nature"] == nt]
        sub_years = sub["retraction_date_parsed"].dt.year.dropna().astype(int)
        label = f"{nt} (paper-1 scope)" if nt == PAPER1_SCOPE_NOTICE else nt
        summary_rows.append([label, len(sub), int((sub_years >= 2016).sum()), int((sub_years >= 2021).sum())])
    summary_table = _markdown_table(
        ["Notice type", "Total", "Post-2015 (year >= 2016)", "Post-2020 (year >= 2021)"], summary_rows
    )

    return (
        "## 3. Distribution by year\n\n"
        "Summary by notice type:\n\n"
        f"{summary_table}\n\n"
        "Full year-by-year breakdown, Retraction only (paper-1 scope):\n\n"
        f"{year_table}\n"
    )


def _section_subject_distribution(df: pd.DataFrame, notice_types: list[str]) -> pd.DataFrame:
    exploded = (
        df[["retraction_nature", "subject_list"]]
        .explode("subject_list")
        .dropna(subset=["subject_list"])
        .reset_index(drop=True)
    )
    ct = _count_pivot(exploded["subject_list"], exploded["retraction_nature"], notice_types, top_n=25)
    text = (
        "## 4. Subject category distribution\n\n"
        "Counted per-label: a record listing multiple subjects is counted once for each. "
        "Top 25 by Retraction count (paper-1 scope).\n\n"
        f"{_pivot_to_markdown(ct, 'Subject')}\n"
    )
    return text, ct


def _section_reason_distribution(df: pd.DataFrame, notice_types: list[str]) -> tuple[str, pd.DataFrame]:
    exploded = (
        df[["retraction_nature", "reason_list"]]
        .explode("reason_list")
        .dropna(subset=["reason_list"])
        .reset_index(drop=True)
    )
    ct = _count_pivot(exploded["reason_list"], exploded["retraction_nature"], notice_types, top_n=20)
    text = (
        "## 5. Retraction reason distribution\n\n"
        "Counted per-label, same convention as subjects. Top 20 by Retraction count (paper-1 scope).\n\n"
        f"{_pivot_to_markdown(ct, 'Reason')}\n"
    )
    return text, ct


def _section_multi_reason(df: pd.DataFrame, notice_types: list[str]) -> str:
    rows = []
    for nt in notice_types:
        sub = df[df["retraction_nature"] == nt]
        total = len(sub)
        multi = int((sub["reason_count"] > 1).sum())
        pct = f"{multi / total * 100:.1f}%" if total else "n/a"
        label = f"{nt} (paper-1 scope)" if nt == PAPER1_SCOPE_NOTICE else nt
        rows.append([label, total, multi, pct])
    table = _markdown_table(["Notice type", "Total records", "Records with >1 reason", "%"], rows)
    return f"## 6. Records with more than one reason\n\n{table}\n"


def _section_top_subjects_post2015_doi(df: pd.DataFrame, subject_ct: pd.DataFrame) -> str:
    top15_subjects = subject_ct.index[:15].tolist()
    retraction_df = df[df["retraction_nature"] == PAPER1_SCOPE_NOTICE].copy()
    retraction_df = retraction_df[retraction_df["retraction_date_parsed"].dt.year >= 2016]
    exploded = retraction_df[["subject_list", "original_paper_doi_resolvable"]].explode("subject_list")
    exploded = exploded[exploded["subject_list"].isin(top15_subjects)]

    rows = []
    for subj in top15_subjects:
        sub = exploded[exploded["subject_list"] == subj]
        total = len(sub)
        with_doi = int(sub["original_paper_doi_resolvable"].sum())
        pct = f"{with_doi / total * 100:.1f}%" if total else "n/a"
        rows.append([subj, total, with_doi, pct])
    table = _markdown_table(
        ["Subject (top 15 overall, from section 4)", "Post-2015 retractions", "...with resolvable DOI", "%"], rows
    )
    return (
        "## 7. Top 15 subject categories: post-2015 retractions with a DOI\n\n"
        "Retraction-only, year >= 2016. Subject ranking taken from section 4's overall top 15.\n\n"
        f"{table}\n"
    )


def _section_reason_cooccurrence(df: pd.DataFrame) -> str:
    retraction_df = df[df["retraction_nature"] == PAPER1_SCOPE_NOTICE]
    reason_counts = retraction_df["reason_list"].explode().value_counts()
    top20 = set(reason_counts.head(20).index)

    pair_counter: Counter[tuple[str, str]] = Counter()
    for reasons in retraction_df["reason_list"]:
        present = sorted({r for r in reasons if r in top20})
        for a, b in itertools.combinations(present, 2):
            pair_counter[(a, b)] += 1

    rows = [[a, b, count] for (a, b), count in pair_counter.most_common(25)]
    table = _markdown_table(["Reason A", "Reason B", "Co-occurrence count"], rows)
    return (
        "## 8. Reason co-occurrence (top 25 pairs)\n\n"
        "Retraction only (paper-1 scope) -- this is candidate stratification-variable analysis for domain "
        "selection, which is a paper-1-scoped decision. Restricted to pairs where both reasons are in the "
        "top 20 most frequent reasons (section 5), to keep the pair space bounded.\n\n"
        f"{table}\n"
    )


def _section_time_to_supersession(df: pd.DataFrame, notice_types: list[str], subject_ct: pd.DataFrame) -> str:
    rows = []
    for nt in notice_types:
        sub = df[df["retraction_nature"] == nt]
        valid = sub[sub["gap_valid"] & ~sub["gap_negative"]]
        label = f"{nt} (paper-1 scope)" if nt == PAPER1_SCOPE_NOTICE else nt
        if len(valid) == 0:
            rows.append([label, 0, "n/a", "n/a", "n/a", "n/a", int(sub["gap_negative"].sum())])
            continue
        rows.append(
            [
                label,
                len(valid),
                f"{valid['gap_days'].mean():.0f}",
                f"{valid['gap_days'].median():.0f}",
                int(valid["gap_days"].min()),
                int(valid["gap_days"].max()),
                int(sub["gap_negative"].sum()),
            ]
        )
    overall_table = _markdown_table(
        ["Notice type", "N (valid, non-negative gap)", "Mean days", "Median days", "Min", "Max", "Negative gaps"],
        rows,
    )

    retraction_df = df[df["retraction_nature"] == PAPER1_SCOPE_NOTICE]
    top15_subjects = subject_ct.index[:15].tolist()
    exploded = retraction_df[retraction_df["gap_valid"] & ~retraction_df["gap_negative"]][
        ["subject_list", "gap_days"]
    ].explode("subject_list")
    exploded = exploded[exploded["subject_list"].isin(top15_subjects)]
    by_subject_rows = []
    for subj in top15_subjects:
        vals = exploded.loc[exploded["subject_list"] == subj, "gap_days"]
        if len(vals) == 0:
            by_subject_rows.append([subj, 0, "n/a", "n/a"])
        else:
            by_subject_rows.append([subj, len(vals), f"{vals.mean():.0f}", f"{vals.median():.0f}"])
    by_subject_table = _markdown_table(
        ["Subject (top 15, from section 4)", "N", "Mean days", "Median days"], by_subject_rows
    )

    implausible = int(df["gap_implausible"].sum())

    return (
        "## 9. Time-to-supersession (gap between OriginalPaperDate and notice date)\n\n"
        "By notice type (negative gaps excluded from the stats and counted separately -- see section 10 for "
        "why they're a data quality issue, not a real value):\n\n"
        f"{overall_table}\n\n"
        f"Gaps longer than {IMPLAUSIBLE_GAP_DAYS // 365} years are flagged as implausible but *not* excluded "
        f"from the stats above (unusual isn't the same as impossible): **{implausible}** records.\n\n"
        "By subject, Retraction only (paper-1 scope), top 15 subjects from section 4:\n\n"
        f"{by_subject_table}\n"
    )


def _section_subject_reason_crosstab(df: pd.DataFrame, subject_ct: pd.DataFrame, reason_ct: pd.DataFrame) -> str:
    top10_subjects = subject_ct.index[:10].tolist()
    top10_reasons = reason_ct.index[:10].tolist()
    retraction_df = df[df["retraction_nature"] == PAPER1_SCOPE_NOTICE]
    exploded = (
        retraction_df[["subject_list", "reason_list"]]
        .explode("subject_list")
        .explode("reason_list")
        .reset_index(drop=True)
    )
    exploded = exploded[exploded["subject_list"].isin(top10_subjects) & exploded["reason_list"].isin(top10_reasons)]
    ct = pd.crosstab(exploded["subject_list"], exploded["reason_list"]).reindex(
        index=top10_subjects, columns=top10_reasons, fill_value=0
    )
    headers = ["Subject \\ Reason"] + [r[:24] for r in top10_reasons]
    rows = [[subj, *[int(ct.loc[subj, r]) for r in top10_reasons]] for subj in top10_subjects]
    table = _markdown_table(headers, rows)

    return (
        "## 10. Subject x reason cross-tabulation (top 10 subjects x top 10 reasons)\n\n"
        "Retraction only (paper-1 scope). A record with multiple subjects and/or reasons contributes to every "
        "(subject, reason) cell it's tagged with -- cells are not mutually exclusive counts.\n\n"
        f"{table}\n"
    )


def _section_pmid_by_subject(df: pd.DataFrame, subject_ct: pd.DataFrame) -> str:
    top15_subjects = subject_ct.index[:15].tolist()
    retraction_df = df[df["retraction_nature"] == PAPER1_SCOPE_NOTICE]
    exploded = retraction_df[["subject_list", "original_paper_pubmed_id_resolvable"]].explode("subject_list")
    exploded = exploded[exploded["subject_list"].isin(top15_subjects)]

    rows = []
    for subj in top15_subjects:
        sub = exploded[exploded["subject_list"] == subj]
        total = len(sub)
        with_pmid = int(sub["original_paper_pubmed_id_resolvable"].sum())
        pct = f"{with_pmid / total * 100:.1f}%" if total else "n/a"
        rows.append([subj, total, with_pmid, pct])
    table = _markdown_table(
        ["Subject (top 15, from section 4)", "Retractions", "...with resolvable OriginalPaperPubMedID", "%"], rows
    )
    return (
        "## 11. PubMed ID availability by subject\n\n"
        "Retraction only -- this is scoped to the the project protocol verification rule, which only applies "
        "to retractions. A subject rich in retraction counts but poor in PMIDs is a weak domain candidate "
        "regardless of raw volume, since the PubMed tag can't be checked without a PMID.\n\n"
        f"{table}\n"
    )


def _section_clinical_domain_candidates(df: pd.DataFrame) -> str:
    """(HSC)-prefixed subjects plus (BLS) Toxicology: tiered candidate pools for domain selection.

    Scope matches the funnel used throughout domain selection: Retraction only,
    post-2015, PubMed-ID-resolvable. Tiers are defined in
    src/retraction_bench/curate/reason_screen.py -- see docs/DECISIONS.md
    ADR-016/017 for why this replaced a single pass/fail cutoff.
    """
    retraction_df = df[df["retraction_nature"] == PAPER1_SCOPE_NOTICE]
    exploded = (
        retraction_df[
            [
                "subject_list",
                "retraction_date_parsed",
                "original_paper_pubmed_id_resolvable",
                "original_paper_doi_resolvable",
                "candidate_tier",
                "gap_valid",
                "gap_negative",
                "gap_days",
            ]
        ]
        .explode("subject_list")
        .reset_index(drop=True)
    )
    is_target = exploded["subject_list"].astype(str).str.startswith(CLINICAL_CANDIDATE_SUBJECT_PREFIX) | exploded[
        "subject_list"
    ].isin(CLINICAL_CANDIDATE_EXTRA_SUBJECTS)
    target_subjects = sorted(exploded.loc[is_target, "subject_list"].dropna().unique())

    rows = []
    for subj in target_subjects:
        all_time = exploded[exploded["subject_list"] == subj]
        post2015 = all_time[all_time["retraction_date_parsed"].dt.year >= 2016]
        pmid_ok = post2015[post2015["original_paper_pubmed_id_resolvable"]]
        doi_pct = f"{post2015['original_paper_doi_resolvable'].mean() * 100:.1f}%" if len(post2015) else "n/a"
        pmid_pct = f"{post2015['original_paper_pubmed_id_resolvable'].mean() * 100:.1f}%" if len(post2015) else "n/a"

        t1 = pmid_ok[pmid_ok["candidate_tier"] == Tier.TIER_1_CLEAN]
        t2 = pmid_ok[pmid_ok["candidate_tier"] == Tier.TIER_2_DUPLICATION]
        t3 = pmid_ok[pmid_ok["candidate_tier"] == Tier.TIER_3_OTHER_AMBIGUOUS]

        def median_gap(pool: pd.DataFrame) -> str:
            valid = pool[pool["gap_valid"] & ~pool["gap_negative"]]
            return f"{valid['gap_days'].median():.0f}" if len(valid) else "n/a"

        rows.append(
            [
                subj,
                len(all_time),
                len(post2015),
                doi_pct,
                pmid_pct,
                len(t1),
                len(t2),
                len(t3),
                median_gap(t1),
            ]
        )

    rows.sort(key=lambda r: -r[5])
    table = _markdown_table(
        [
            "Subject",
            "Total retractions",
            "Post-2015",
            "Resolvable DOI %",
            "Resolvable PMID %",
            "tier_1_clean",
            "tier_2_duplication",
            "tier_3_other_ambiguous",
            "tier_1 median days",
        ],
        rows,
    )

    unmapped = df.attrs.get("unmapped_reasons", [])
    unmapped_note = (
        f"\n**{len(unmapped)} reason tag(s) encountered with no entry in reason_screen.yaml:** {unmapped}. "
        "Treated conservatively as tier_3-forcing (see classify_tier). Update the screen if these recur.\n"
        if unmapped
        else ""
    )

    return (
        "## 12. Clinical domain candidates: (HSC) subjects + (BLS) Toxicology, tiered\n\n"
        "Retraction only, post-2015, PubMed-ID-resolvable -- the same population used throughout domain "
        "selection. DOI %/PMID % are computed over the post-2015 subset, matching section 7's convention. "
        "tier_1_clean / tier_2_duplication / tier_3_other_ambiguous are defined in "
        "`src/retraction_bench/curate/reason_screen.py`; see docs/DECISIONS.md ADR-016 through ADR-018 for "
        "the methodology and the domain-selection reasoning built on these numbers.\n\n"
        f"{table}\n"
        f"{unmapped_note}"
    )


def _section_claim_type_funnel(df: pd.DataFrame) -> str:
    """Tier-1 pools re-ranked by claim type: clinical_intervention/clinical_observational vs. preclinical/unclear.

    PROVISIONAL: claim_type comes from an unvalidated heuristic screen (see
    docs/DECISIONS.md ADR-021). Numbers here will move once the screen is
    scored against the author's 100 hand labels.
    """
    retraction_df = df[df["retraction_nature"] == PAPER1_SCOPE_NOTICE]
    exploded = (
        retraction_df[
            [
                "subject_list",
                "retraction_date_parsed",
                "original_paper_pubmed_id_resolvable",
                "candidate_tier",
                "is_clinical_claim",
                "gap_valid",
                "gap_negative",
                "gap_days",
            ]
        ]
        .explode("subject_list")
        .reset_index(drop=True)
    )
    is_target = exploded["subject_list"].astype(str).str.startswith(CLINICAL_CANDIDATE_SUBJECT_PREFIX)
    target_subjects = sorted(exploded.loc[is_target, "subject_list"].dropna().unique())

    def median_gap(pool: pd.DataFrame) -> str:
        valid = pool[pool["gap_valid"] & ~pool["gap_negative"]]
        return f"{valid['gap_days'].median():.0f}" if len(valid) else "n/a"

    rows = []
    for subj in target_subjects:
        all_time = exploded[exploded["subject_list"] == subj]
        post2015 = all_time[all_time["retraction_date_parsed"].dt.year >= 2016]
        pmid_ok = post2015[post2015["original_paper_pubmed_id_resolvable"]]
        t1 = pmid_ok[pmid_ok["candidate_tier"] == Tier.TIER_1_CLEAN]
        t1_clinical = t1[t1["is_clinical_claim"]]

        rows.append(
            [
                subj,
                len(t1),
                len(t1_clinical),
                median_gap(all_time),  # broad, unfiltered -- matches the author's original anchor definition
                median_gap(t1_clinical),
            ]
        )

    rows.sort(key=lambda r: -r[2])
    table = _markdown_table(
        [
            "Subject",
            "tier_1 (unfiltered)",
            "tier_1 AND clinical claim type",
            "broad median days (unfiltered)",
            "tier_1+clinical median days",
        ],
        rows,
    )

    return (
        "## 13. Claim-type-filtered ranking (PROVISIONAL -- screen not yet validated)\n\n"
        "**The claim_type column comes from a heuristic keyword screen "
        "(`config/vocabularies/claim_type_screen.yaml`) that has not yet been scored against hand labels.** "
        "Treat this table as provisional until docs/DECISIONS.md ADR-021 records a measured agreement rate. "
        "`tier_1 AND clinical claim type` = tier_1_clean records whose title/ArticleType were classified "
        "`clinical_intervention` or `clinical_observational` (not `preclinical` or `unclear`). The "
        "`tier_1+clinical median days` figure is computed over that same narrow, doubly-filtered subset, and "
        "is partly an artifact of which reason tags and which title keywords happen to survive both screens -- "
        "not a clean estimate of the subject's true evidence-turnover speed. The broad median (unfiltered, "
        "all retractions in the subject) is the more stable number and the one comparable across subjects; "
        "report both in the paper, never the narrow one alone.\n\n"
        f"{table}\n"
    )


def _section_data_quality(df: pd.DataFrame, notice_types: list[str], extra_notice_types: list[str]) -> str:
    lines = ["## 14. Data quality problems\n"]

    if extra_notice_types:
        lines.append(f"- **Unexpected RetractionNature values** (not in the documented set): {extra_notice_types}")

    rows = []
    for nt in notice_types:
        sub = df[df["retraction_nature"] == nt]
        rows.append(
            [
                f"{nt} (paper-1 scope)" if nt == PAPER1_SCOPE_NOTICE else nt,
                int(sub["retraction_date_missing"].sum()),
                int(sub["retraction_date_malformed"].sum()),
                int(sub["original_paper_date_missing"].sum()),
                int(sub["original_paper_date_malformed"].sum()),
            ]
        )
    date_table = _markdown_table(
        [
            "Notice type",
            "RetractionDate missing",
            "RetractionDate malformed",
            "OriginalPaperDate missing",
            "OriginalPaperDate malformed",
        ],
        rows,
    )
    lines.append("\n### Dates\n")
    lines.append(date_table)

    doi_rows = []
    for nt in notice_types:
        sub = df[df["retraction_nature"] == nt]
        doi_rows.append(
            [
                f"{nt} (paper-1 scope)" if nt == PAPER1_SCOPE_NOTICE else nt,
                int(sub["retraction_doi_malformed"].sum()),
                int(sub["original_paper_doi_malformed"].sum()),
            ]
        )
    doi_table = _markdown_table(
        ["Notice type", "RetractionDOI malformed (present, bad syntax)", "OriginalPaperDOI malformed"], doi_rows
    )
    lines.append("\n### Malformed DOIs (present but not valid DOI syntax)\n")
    lines.append(doi_table)

    dup_mask = df["record_id"].duplicated(keep=False)
    dup_groups = df.loc[dup_mask, "record_id"].nunique()
    lines.append("\n### Duplicate records\n")
    lines.append(
        f"- Record IDs appearing more than once: **{dup_groups}** distinct IDs, **{int(dup_mask.sum())}** rows total."
    )

    doi_dup_groups = df.loc[df["original_paper_doi_resolvable"], "original_paper_doi"]
    doi_dup_count = doi_dup_groups[doi_dup_groups.duplicated(keep=False)].nunique()
    lines.append(
        f"- Distinct OriginalPaperDOI values appearing on more than one record: **{doi_dup_count}** "
        "(this can legitimately mean multiple notices for the same paper, e.g. a Correction followed later "
        "by a Retraction -- not necessarily an error; reported separately from true Record ID duplicates)."
    )

    exploded_subj = df[["subject_list"]].explode("subject_list").dropna(subset=["subject_list"])
    exploded_subj["normalized"] = (
        exploded_subj["subject_list"].str.strip().str.casefold().str.replace(r"\s+", " ", regex=True)
    )
    variant_groups = exploded_subj.groupby("normalized")["subject_list"].agg(lambda s: sorted(set(s)))
    inconsistent = variant_groups[variant_groups.apply(len) > 1]
    lines.append("\n### Inconsistent subject category labels (case/whitespace variants of the same label)\n")
    if len(inconsistent) == 0:
        lines.append("- None found.")
    else:
        lines.append(f"- **{len(inconsistent)}** normalized subject labels have more than one raw variant. Examples:")
        for normalized, variants in inconsistent.head(10).items():
            lines.append(f"  - `{normalized}`: {variants}")

    trailing_nonempty = int((df["trailing_unnamed"].notna() & (df["trailing_unnamed"] != "")).sum())
    lines.append("\n### Trailing unnamed column (from the source header's trailing comma)\n")
    lines.append(f"- Non-empty values: **{trailing_nonempty}** (expected: 0).")

    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------


def build_report(df: pd.DataFrame) -> str:
    blank_count = int(df["is_blank_row"].sum())
    df = df[~df["is_blank_row"]].copy()

    notice_types, extra_notice_types = _notice_types_present(df)

    subject_text, subject_ct = _section_subject_distribution(df, notice_types)
    reason_text, reason_ct = _section_reason_distribution(df, notice_types)

    sections = [
        f"# Phase 1 Exploration Report\n\nGenerated: {date.today().isoformat()}. "
        "Source: raw Retraction Watch table (see docs/DATA_NOTES.md for exact source URL and access date). "
        f"**{blank_count} completely blank rows** (every field null -- a source CSV export artifact, not real "
        "records) were found and are excluded from every count and table below; the raw DuckDB table itself is "
        "untouched and still contains them. See docs/DATA_NOTES.md for the full exclusion accounting. "
        "No filtering or domain-selection decisions are made in this report -- see docs/DECISIONS.md ADR-013 "
        "for why the benchmark's domain count is small (3-4) and chosen only after this report is read.\n",
        _section_overview(df, notice_types),
        _section_doi_resolvability(df, notice_types),
        _section_year_distribution(df, notice_types),
        subject_text,
        reason_text,
        _section_multi_reason(df, notice_types),
        _section_top_subjects_post2015_doi(df, subject_ct),
        _section_reason_cooccurrence(df),
        _section_time_to_supersession(df, notice_types, subject_ct),
        _section_subject_reason_crosstab(df, subject_ct, reason_ct),
        _section_pmid_by_subject(df, subject_ct),
        _section_clinical_domain_candidates(df),
        _section_claim_type_funnel(df),
        _section_data_quality(df, notice_types, extra_notice_types),
    ]
    return "\n".join(sections)


def append_data_quality_notes(df: pd.DataFrame, notes_path: Path = DATA_NOTES_PATH) -> None:
    """Record every exclusion-relevant count from the exploration pass, per the project protocol's reviewer scrutiny rule."""
    blank_count = int(df["is_blank_row"].sum())
    df = df[~df["is_blank_row"]].copy()

    dup_mask = df["record_id"].duplicated(keep=False)

    lines = [
        f"Completely blank source rows (every field null -- a CSV export artifact): {blank_count} records "
        f"out of {blank_count + len(df)} total rows. Excluded from every count below and from the exploration "
        "report; the raw DuckDB table is unmodified and still contains them.",
        f"RetractionDate unparseable (present but malformed, strict M/D/YYYY H:MM): "
        f"{int(df['retraction_date_malformed'].sum())} records.",
        f"OriginalPaperDate unparseable: {int(df['original_paper_date_malformed'].sum())} records.",
        f"RetractionDate missing (blank): {int(df['retraction_date_missing'].sum())} records.",
        f"OriginalPaperDate missing (blank): {int(df['original_paper_date_missing'].sum())} records.",
        f"OriginalPaperDOI present but not valid DOI syntax: {int(df['original_paper_doi_malformed'].sum())} records.",
        f"RetractionDOI present but not valid DOI syntax: {int(df['retraction_doi_malformed'].sum())} records.",
        f"Duplicate Record IDs (among non-blank rows only): {int(dup_mask.sum())} rows across "
        f"{df.loc[dup_mask, 'record_id'].nunique()} distinct IDs -- not deduplicated at this stage; "
        "Stage 1B decides how to handle these.",
        f"Negative RetractionDate-OriginalPaperDate gaps (retraction predates the paper it retracts -- always a "
        f"data error, excluded from section 9's distribution): {int(df['gap_negative'].sum())} records.",
        f"Implausibly long gaps (> {IMPLAUSIBLE_GAP_DAYS // 365} years, flagged but included in section 9's "
        f"distribution): {int(df['gap_implausible'].sum())} records.",
    ]
    trailing_nonempty = int((df["trailing_unnamed"].notna() & (df["trailing_unnamed"] != "")).sum())
    if trailing_nonempty:
        lines.append(
            f"Trailing unnamed column (from the source header's trailing comma) is non-empty in "
            f"{trailing_nonempty} records -- unexpected, needs investigation."
        )
    append_entry(notes_path, "Phase 1 exploration: data quality findings", lines)


def run_explore(db_path: Path = DB_PATH, report_path: Path = REPORT_PATH, notes_path: Path = DATA_NOTES_PATH) -> Path:
    df = load_enriched_frame(db_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(build_report(df), encoding="utf-8")
    append_data_quality_notes(df, notes_path)
    return report_path
