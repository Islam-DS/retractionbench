"""`retraction-bench check-disk` -- reports whether every bulk-data cache environment variable
points at D: (not C:), and the size of both the D: target and the C: default location for each.

Exists because the same mistake -- a tool's cache silently writing to C: because an env var was
never set, or was set one directory level off from what the tool actually expects -- has now
happened three times on this machine (uv/pip/HF's original redirect, and OLLAMA_MODELS pointing
at its own parent directory instead of the `models` subdirectory Ollama actually reads).
the project protocol now requires running this before any command that downloads or caches bulk data.
"""

import os
from dataclasses import dataclass
from pathlib import Path

HOME = Path.home()
LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", HOME / "AppData" / "Local"))

# (env var name, this tool's actual default location if the var is unset -- verified against
# each tool's own documented behavior, not guessed; OLLAMA_MODELS's default is the `models`
# subdirectory of ~/.ollama specifically, the same distinction that caused the original bug)
_CHECKS: list[tuple[str, Path]] = [
    ("OLLAMA_MODELS", HOME / ".ollama" / "models"),
    ("HF_HOME", HOME / ".cache" / "huggingface"),
    ("UV_CACHE_DIR", LOCALAPPDATA / "uv" / "cache"),
    ("PIP_CACHE_DIR", LOCALAPPDATA / "pip" / "Cache"),
    ("TORCH_HOME", HOME / ".cache" / "torch"),
    ("TMPDIR", LOCALAPPDATA / "Temp"),
]


@dataclass
class DiskCheckEntry:
    env_var: str
    current_value: str | None
    points_to_d: bool
    d_target_size_bytes: int | None  # None if current_value is unset or doesn't exist on disk
    c_default_path: str
    c_default_size_bytes: int | None  # None if the C: default path doesn't exist


def _dir_size_bytes(path: Path) -> int | None:
    if not path.exists():
        return None
    total = 0
    for entry in path.rglob("*"):
        if entry.is_file():
            try:
                total += entry.stat().st_size
            except OSError:
                continue  # a file vanished or is locked mid-walk -- skip it, don't crash the check
    return total


def _points_to_d(value: str | None) -> bool:
    if not value:
        return False
    return Path(value).drive.upper() == "D:"


def check_all() -> list[DiskCheckEntry]:
    entries = []
    for env_var, c_default in _CHECKS:
        current_value = os.environ.get(env_var)
        d_size = _dir_size_bytes(Path(current_value)) if current_value else None
        entries.append(
            DiskCheckEntry(
                env_var=env_var,
                current_value=current_value,
                points_to_d=_points_to_d(current_value),
                d_target_size_bytes=d_size,
                c_default_path=str(c_default),
                c_default_size_bytes=_dir_size_bytes(c_default),
            )
        )
    return entries


def format_report(entries: list[DiskCheckEntry]) -> str:
    lines = []
    for e in entries:
        status = "OK (points at D:)" if e.points_to_d else "WARNING: NOT pointing at D:"
        lines.append(f"{e.env_var}: {status}")
        lines.append(f"  current value: {e.current_value or '(unset)'}")
        if e.current_value:
            if e.d_target_size_bytes is not None:
                size_str = f"{e.d_target_size_bytes / 1e9:.2f} GB"
            else:
                size_str = "(path does not exist yet)"
            lines.append(f"  current target size: {size_str}")
        if e.c_default_size_bytes is not None:
            c_size_str = f"{e.c_default_size_bytes / 1e9:.2f} GB"
        else:
            c_size_str = "0 GB (does not exist)"
        lines.append(f"  C: default ({e.c_default_path}): {c_size_str}")
        lines.append("")
    return "\n".join(lines)
