import pytest

from retraction_bench.stats.strata import StratumReliability, check_stratum_size


def test_reliable_at_min_headline_n() -> None:
    assert check_stratum_size(10).reliability == StratumReliability.RELIABLE


def test_reliable_above_min_headline_n() -> None:
    assert check_stratum_size(28).reliability == StratumReliability.RELIABLE


def test_thin_between_itemize_and_headline() -> None:
    assert check_stratum_size(7).reliability == StratumReliability.THIN


def test_too_thin_below_itemize_n() -> None:
    assert check_stratum_size(4).reliability == StratumReliability.TOO_THIN_TO_RATE


def test_zero_is_too_thin() -> None:
    assert check_stratum_size(0).reliability == StratumReliability.TOO_THIN_TO_RATE


def test_negative_n_rejected() -> None:
    with pytest.raises(ValueError, match="negative"):
        check_stratum_size(-1)


def test_boundary_at_itemize_n() -> None:
    assert check_stratum_size(5).reliability == StratumReliability.THIN
