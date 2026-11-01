"""Thin wrapper around `retraction_bench.reproduce.main` -- kept at this path so
`scripts/` stays the discoverable, repository-convention location for one-off/top-level
reproduction and figure-generation entry points, while the actual logic lives in the installable
package (`src/retraction_bench/reproduce.py`) so `retraction-bench evaluate` (cli.py) and
`make reproduce` can import and run it too, not just a direct script invocation.

Run with: `uv run python scripts/reproduce_paper_numbers.py`
(equivalent to `uv run retraction-bench evaluate` or `make reproduce`).
"""

from retraction_bench.reproduce import main

if __name__ == "__main__":
    main()
