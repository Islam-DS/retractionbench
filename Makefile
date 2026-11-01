.PHONY: setup test lint format reproduce

setup:
	uv sync

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

reproduce:
	@echo "Regenerating every M1/M3/Correctness number in the paper from cached data"
	@echo "(data/interim/eval/model_responses.jsonl, data/human/*.csv) -- no live API call (ADR-153)."
	uv run retraction-bench evaluate
	@echo "Wrote results/reproduced_paper_numbers.{json,md}. See tests/test_reproduce_paper_numbers.py"
	@echo "for the check that these match the numbers currently published in paper.md."
