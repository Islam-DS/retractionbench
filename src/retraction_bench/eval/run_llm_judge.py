"""Entry point for the M3 and correctness LLM-judge secondary analyses (eval/llm_judge.py).

Backend is selected by two env vars, defaulting to the zero-cost local path so a bare `python -m
retraction_bench.eval.run_llm_judge m3` never silently reaches for a paid API:

    JUDGE_BACKEND=ollama|anthropic   (default: ollama)
    JUDGE_MODEL=<model identifier>   (default: mistral:7b-instruct for ollama, claude-opus-5 for anthropic)

    python -m retraction_bench.eval.run_llm_judge m3
    python -m retraction_bench.eval.run_llm_judge correctness

Every run appends one line to `<output>.meta.jsonl` recording backend, model, timestamp, and the
item count attempted -- so which backend/model produced a given results file is never left to be
inferred from memory later.
"""

import json
import os
import sys
import time
from pathlib import Path

from retraction_bench.eval.llm_judge import (
    CORRECTNESS_LABELS,
    M3_LABELS,
    anthropic_call_fn,
    build_correctness_prompt,
    build_m3_prompt,
    ollama_call_fn,
    run_judge,
)

ROOT = Path(__file__).resolve().parents[3]
EVAL_DIR = ROOT / "data/interim/eval"

TASKS = {
    "m3": {
        "input": EVAL_DIR / "m3_judge_input.json",
        "output": EVAL_DIR / "m3_llm_judge_results.jsonl",
        "prompt_fn": build_m3_prompt,
        "labels": M3_LABELS,
    },
    "correctness": {
        "input": EVAL_DIR / "correctness_judge_input.json",
        "output": EVAL_DIR / "correctness_llm_judge_results.jsonl",
        "prompt_fn": build_correctness_prompt,
        "labels": CORRECTNESS_LABELS,
    },
}

DEFAULT_MODEL = {"ollama": "mistral:7b-instruct", "anthropic": "claude-opus-5"}


def build_call_fn(backend: str, model: str):
    if backend == "ollama":
        return ollama_call_fn(model=model)
    if backend == "anthropic":
        return anthropic_call_fn(model=model)
    raise ValueError(f"Unknown JUDGE_BACKEND: {backend!r} (expected 'ollama' or 'anthropic')")


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in TASKS:
        print(f"Usage: python -m retraction_bench.eval.run_llm_judge <{'|'.join(TASKS)}>")
        raise SystemExit(1)

    backend = os.environ.get("JUDGE_BACKEND", "ollama")
    model = os.environ.get("JUDGE_MODEL", DEFAULT_MODEL.get(backend, ""))
    if not model:
        raise SystemExit(f"No default model for JUDGE_BACKEND={backend!r}; set JUDGE_MODEL explicitly.")

    task = TASKS[sys.argv[1]]
    with task["input"].open(encoding="utf-8") as f:
        records = json.load(f)

    started = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    t0 = time.time()
    done = run_judge(
        records,
        task["output"],
        task["prompt_fn"],
        task["labels"],
        build_call_fn(backend, model),
        extra_fields=("item_id", "model", "seed"),
        delay_seconds=0.0 if backend == "ollama" else 0.3,
    )
    elapsed = time.time() - t0

    meta_path = task["output"].with_suffix(task["output"].suffix + ".meta.jsonl")
    with meta_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "task": sys.argv[1],
            "judge_backend": backend,
            "judge_model": model,
            "started": started,
            "elapsed_seconds": round(elapsed, 1),
            "n_input": len(records),
            "n_done_this_run": done,
        }) + "\n")

    print(f"Done. {done}/{len(records)} judged with backend={backend} model={model} in {elapsed:.1f}s. "
          f"Results: {task['output']} | Meta: {meta_path}")


if __name__ == "__main__":
    main()
