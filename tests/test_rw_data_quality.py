import pandas as pd

from retraction_bench.ingest.rw_data_quality import (
    check_date_placeholder,
    check_doi_field,
    check_duplicate_pmids,
    check_pmid_field,
    check_retraction_nature,
    validate_rw_dataframe,
)


def test_pmid_placeholder_detected():
    s = pd.Series(["12345", "0", "0", "67890", None, ""])
    r = check_pmid_field(s, "x")
    assert not r.passed
    assert r.n_flagged == 2
    assert r.n_checked == 4  # None/"" excluded from the denominator, not counted as flagged


def test_pmid_non_numeric_detected():
    s = pd.Series(["12345", "abc123", "0"])
    r = check_pmid_field(s, "x")
    assert r.n_flagged == 2  # the placeholder "0" AND the non-numeric "abc123"


def test_pmid_clean_passes():
    s = pd.Series(["12345", "67890", None])
    r = check_pmid_field(s, "x")
    assert r.passed
    assert r.n_flagged == 0


def test_doi_placeholder_detected_case_insensitive():
    s = pd.Series(["10.1000/real", "unavailable", "Unavailable", None])
    r = check_doi_field(s, "x")
    assert not r.passed
    assert r.n_flagged == 2


def test_doi_malformed_detected():
    s = pd.Series(["10.1000/real", "not-a-doi-at-all"])
    r = check_doi_field(s, "x")
    assert r.n_flagged == 1


def test_date_placeholder_detected():
    s = pd.Series(["1/1/1970 0:00", "3/4/2020 0:00", "1/1/1970 0:00"])
    r = check_date_placeholder(s, "x")
    assert r.n_flagged == 2


def test_retraction_nature_flags_unknown_value():
    s = pd.Series(["Retraction", "Correction", "Something Else Entirely"])
    r = check_retraction_nature(s)
    assert not r.passed
    assert r.n_flagged == 1


def test_retraction_nature_all_known_passes():
    s = pd.Series(["Retraction", "Correction", "Expression of concern", "Reinstatement"])
    r = check_retraction_nature(s)
    assert r.passed


def test_duplicate_pmids_detected_excluding_placeholder():
    df = pd.DataFrame({"original_paper_pubmed_id": ["111", "111", "222", "0", "0", "333"]})
    r = check_duplicate_pmids(df)
    assert not r.passed
    assert r.n_flagged == 2  # the two "111" rows; the two "0" rows are excluded as placeholders


def test_validate_rw_dataframe_runs_all_checks():
    df = pd.DataFrame(
        {
            "original_paper_pubmed_id": ["111", "0"],
            "retraction_pubmed_id": ["222", "333"],
            "original_paper_doi": ["10.1000/a", "unavailable"],
            "retraction_date": ["3/4/2020 0:00", "1/1/1970 0:00"],
            "retraction_nature": ["Retraction", "Correction"],
        }
    )
    reports = validate_rw_dataframe(df)
    assert len(reports) == 6
    names = {r.check_name for r in reports}
    assert "pmid_placeholder:original_paper_pubmed_id" in names
    assert "retraction_nature_distribution" in names


def test_validate_rw_dataframe_require_retraction_nature_only():
    df = pd.DataFrame(
        {
            "original_paper_pubmed_id": ["111", "222"],
            "retraction_pubmed_id": ["333", "444"],
            "original_paper_doi": ["10.1000/a", "10.1000/b"],
            "retraction_date": ["3/4/2020 0:00", "3/4/2020 0:00"],
            "retraction_nature": ["Retraction", "Correction"],
        }
    )
    reports = validate_rw_dataframe(df, require_retraction_nature_only=True)
    extra = [r for r in reports if r.check_name == "retraction_nature_only_required"]
    assert len(extra) == 1
    assert not extra[0].passed


def test_real_rw_table_current_known_issues():
    """Documents the real, current state of the live RW table against this validator --
    confirms the already-known placeholder issues are still there and still caught (not a
    regression check that they've been silently cleaned up without this code noticing),
    and confirms the already-known distinct count of non-Retraction-nature rows.
    """
    import duckdb
    from pathlib import Path

    db_path = Path(__file__).resolve().parent.parent / "data/interim/retraction_watch.duckdb"
    if not db_path.exists():
        import pytest

        pytest.skip("live RW database not present in this environment")

    con = duckdb.connect(str(db_path), read_only=True)
    df = con.execute(
        "SELECT original_paper_pubmed_id, retraction_pubmed_id, original_paper_doi, "
        "retraction_date, retraction_nature FROM raw_retraction_watch"
    ).fetchdf()

    reports = validate_rw_dataframe(df)
    by_name = {r.check_name: r for r in reports}

    assert by_name["pmid_placeholder:original_paper_pubmed_id"].n_flagged > 0, (
        "expected the known '0' placeholder to still be present -- if this now passes, the "
        "underlying data changed and every script relying on this exclusion should be re-checked"
    )
    assert by_name["doi_placeholder:original_paper_doi"].n_flagged >= 2
    # The known-value-set check passes (every real value is one of the 4 expected natures) --
    # that is a different question from whether the data is PURE Retraction, which it is not.
    # Any audit that needs Retraction-only data must say so explicitly via
    # `require_retraction_nature_only=True`, confirmed by this assertion that non-Retraction
    # natures are genuinely present in the live table (the exact contamination this round of
    # Phase 5 caught in Part B's original, unfiltered sampling frame).
    assert by_name["retraction_nature_distribution"].passed
    nature_values = set(df["retraction_nature"].dropna().unique())
    assert nature_values != {"Retraction"}, "expected non-Retraction natures to be present"
    assert "Correction" in nature_values and "Expression of concern" in nature_values
