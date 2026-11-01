from pathlib import Path

import pytest

from retraction_bench.check_disk import DiskCheckEntry, _dir_size_bytes, _points_to_d, check_all, format_report


def test_points_to_d_true_for_d_drive_path() -> None:
    assert _points_to_d(r"D:\RAG_AWS_Project\.caches\ollama\models") is True


def test_points_to_d_false_for_c_drive_path() -> None:
    assert _points_to_d(r"C:\Users\User\.ollama") is False


def test_points_to_d_false_for_unset_value() -> None:
    assert _points_to_d(None) is False


def test_points_to_d_case_insensitive_drive_letter() -> None:
    assert _points_to_d(r"d:\some\path") is True


def test_dir_size_bytes_returns_none_for_nonexistent_path(tmp_path: Path) -> None:
    assert _dir_size_bytes(tmp_path / "does-not-exist") is None


def test_dir_size_bytes_sums_files_recursively(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_bytes(b"x" * 100)
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.txt").write_bytes(b"y" * 50)

    assert _dir_size_bytes(tmp_path) == 150


def test_dir_size_bytes_zero_for_empty_directory(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    assert _dir_size_bytes(empty) == 0


def test_check_all_flags_d_pointing_var_as_ok(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    d_path = tmp_path / "D_ollama_models"
    d_path.mkdir()
    (d_path / "blob").write_bytes(b"x" * 1000)
    # Simulate a D:-style path even on a test machine without a real D: drive, by checking the
    # drive-letter logic directly rather than requiring tmp_path to literally be on D:.
    monkeypatch.setenv("OLLAMA_MODELS", "D:\\fake\\ollama\\models")
    entries = check_all()
    ollama_entry = next(e for e in entries if e.env_var == "OLLAMA_MODELS")
    assert ollama_entry.points_to_d is True


def test_check_all_flags_c_pointing_var_as_not_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HF_HOME", "C:\\Users\\someone\\.cache\\huggingface")
    entries = check_all()
    hf_entry = next(e for e in entries if e.env_var == "HF_HOME")
    assert hf_entry.points_to_d is False


def test_check_all_unset_var_reports_no_current_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TORCH_HOME", raising=False)
    entries = check_all()
    torch_entry = next(e for e in entries if e.env_var == "TORCH_HOME")
    assert torch_entry.current_value is None
    assert torch_entry.points_to_d is False
    assert torch_entry.d_target_size_bytes is None


def test_format_report_includes_every_checked_variable() -> None:
    entries = check_all()
    report = format_report(entries)
    for env_var in ("OLLAMA_MODELS", "HF_HOME", "UV_CACHE_DIR", "PIP_CACHE_DIR", "TORCH_HOME", "TMPDIR"):
        assert env_var in report


def test_format_report_warns_for_misconfigured_entry() -> None:
    entry = DiskCheckEntry(
        env_var="OLLAMA_MODELS",
        current_value=r"C:\Users\someone\.ollama\models",
        points_to_d=False,
        d_target_size_bytes=1000,
        c_default_path=r"C:\Users\someone\.ollama\models",
        c_default_size_bytes=1000,
    )
    report = format_report([entry])
    assert "WARNING" in report
