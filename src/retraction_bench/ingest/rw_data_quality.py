"""Retraction Watch data-quality validation -- run BEFORE any audit script touches the RW
table, not discovered after the fact. Every check here encodes a real trap this project's own
Phase 5 audit hit the hard way (see `docs/ANALYSIS_LOG.md` 5.5-5.13 and this round's checks):

1. `original_paper_pubmed_id` / `retraction_pubmed_id` use the literal string `"0"` as a
   "no PubMed ID" placeholder, not a real PMID -- caught when a sample drawn without excluding
   it was 48% unresolvable PubMed lookups.
2. `original_paper_doi` uses the literal strings `"unavailable"`/`"Unavailable"` as placeholders
   -- caught when one of these was passed to Crossref/OpenAlex as if it were a real DOI.
3. `retraction_date` uses `"1/1/1970 0:00"` as a placeholder (the Unix epoch default).
4. The same real paper can appear under more than one `record_id` (independently captured by
   more than one domain-specific candidate search in this project's own benchmark-construction
   pipeline) -- row count and distinct-paper count are not the same thing.
5. `retraction_nature` is not always `"Retraction"` -- `"Correction"`, `"Expression of concern"`,
   and `"Reinstatement"` also appear, and checking a non-Retraction record for a missing
   `Retracted Publication` PubMed tag is the wrong check entirely (that tag was never expected
   on it in the first place).
"""

from dataclasses import dataclass, field

import pandas as pd

DOI_PLACEHOLDERS = {"unavailable", "n/a", "na", "none", "unknown", ""}
PMID_PLACEHOLDER = "0"
DATE_PLACEHOLDER = "1/1/1970 0:00"
KNOWN_RETRACTION_NATURES = {"Retraction", "Correction", "Expression of concern", "Reinstatement"}


@dataclass
class ValidationReport:
    check_name: str
    passed: bool
    n_checked: int
    n_flagged: int
    detail: str
    flagged_examples: list = field(default_factory=list)


def check_pmid_field(series: pd.Series, field_name: str) -> ValidationReport:
    non_null = series[series.notna() & (series.astype(str).str.strip() != "")]
    placeholder = non_null[non_null.astype(str).str.strip() == PMID_PLACEHOLDER]
    non_numeric = non_null[~non_null.astype(str).str.match(r"^[1-9][0-9]*$") & (non_null.astype(str).str.strip() != PMID_PLACEHOLDER)]
    n_flagged = len(placeholder) + len(non_numeric)
    return ValidationReport(
        check_name=f"pmid_placeholder:{field_name}",
        passed=n_flagged == 0,
        n_checked=len(non_null),
        n_flagged=n_flagged,
        detail=f"{len(placeholder)} rows hold the '0' placeholder; {len(non_numeric)} rows are non-numeric and not '0'",
        flagged_examples=list(non_numeric.head(5)),
    )


def check_doi_field(series: pd.Series, field_name: str) -> ValidationReport:
    non_null = series[series.notna()]
    flagged = non_null[non_null.astype(str).str.strip().str.lower().isin(DOI_PLACEHOLDERS)]
    malformed = non_null[
        ~non_null.astype(str).str.strip().str.lower().isin(DOI_PLACEHOLDERS)
        & (non_null.astype(str).str.strip() != "")
        & ~non_null.astype(str).str.match(r"^10\.")
    ]
    n_flagged = len(flagged) + len(malformed)
    return ValidationReport(
        check_name=f"doi_placeholder:{field_name}",
        passed=n_flagged == 0,
        n_checked=len(non_null),
        n_flagged=n_flagged,
        detail=f"{len(flagged)} known placeholder strings; {len(malformed)} values not shaped like a real DOI",
        flagged_examples=list(malformed.head(5)),
    )


def check_date_placeholder(series: pd.Series, field_name: str) -> ValidationReport:
    n_flagged = int((series == DATE_PLACEHOLDER).sum())
    return ValidationReport(
        check_name=f"date_placeholder:{field_name}",
        passed=n_flagged == 0,
        n_checked=len(series),
        n_flagged=n_flagged,
        detail=f"{n_flagged} rows hold the Unix-epoch placeholder date",
    )


def check_retraction_nature(series: pd.Series) -> ValidationReport:
    values = series.dropna()
    unknown = values[~values.isin(KNOWN_RETRACTION_NATURES)]
    counts = values.value_counts().to_dict()
    return ValidationReport(
        check_name="retraction_nature_distribution",
        passed=len(unknown) == 0,
        n_checked=len(values),
        n_flagged=len(unknown),
        detail=f"distribution: {counts}",
        flagged_examples=list(unknown.unique()[:5]),
    )


def check_duplicate_pmids(df: pd.DataFrame, pmid_field: str = "original_paper_pubmed_id") -> ValidationReport:
    real = df[df[pmid_field].notna() & (df[pmid_field].astype(str).str.strip() != "") & (df[pmid_field] != PMID_PLACEHOLDER)]
    counts = real[pmid_field].value_counts()
    dupes = counts[counts > 1]
    return ValidationReport(
        check_name=f"duplicate_pmids:{pmid_field}",
        passed=len(dupes) == 0,
        n_checked=len(real),
        n_flagged=int(dupes.sum()),
        detail=f"{len(dupes)} distinct PMIDs appear more than once ({int(dupes.sum())} rows total)",
        flagged_examples=list(dupes.head(5).items()),
    )


def validate_rw_dataframe(df: pd.DataFrame, require_retraction_nature_only: bool = False) -> list[ValidationReport]:
    """Run every check. Does not raise -- callers decide what to do with a failed report
    (e.g. filter before sampling, or abort). `require_retraction_nature_only` additionally fails
    the nature check if ANY non-"Retraction" row is present, for audits (like Phase 5 Part B)
    that are specifically about retractions, not corrections/EoC/reinstatements.
    """
    reports = [
        check_pmid_field(df["original_paper_pubmed_id"], "original_paper_pubmed_id"),
        check_pmid_field(df["retraction_pubmed_id"], "retraction_pubmed_id"),
        check_doi_field(df["original_paper_doi"], "original_paper_doi"),
        check_date_placeholder(df["retraction_date"], "retraction_date"),
        check_retraction_nature(df["retraction_nature"]),
        check_duplicate_pmids(df),
    ]
    if require_retraction_nature_only:
        nature_values = set(df["retraction_nature"].dropna().unique())
        if nature_values != {"Retraction"}:
            reports.append(
                ValidationReport(
                    check_name="retraction_nature_only_required",
                    passed=False,
                    n_checked=len(df),
                    n_flagged=int((df["retraction_nature"] != "Retraction").sum()),
                    detail=f"caller required Retraction-nature-only data but found: {nature_values}",
                )
            )
    return reports


def print_report(reports: list[ValidationReport]) -> bool:
    """Prints every report, returns True iff all passed."""
    all_passed = True
    for r in reports:
        status = "PASS" if r.passed else "FAIL"
        if not r.passed:
            all_passed = False
        print(f"[{status}] {r.check_name}: n_checked={r.n_checked}, n_flagged={r.n_flagged} -- {r.detail}")
        if r.flagged_examples:
            print(f"         examples: {r.flagged_examples}")
    return all_passed
