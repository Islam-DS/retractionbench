"""Command-line entry points for RetractionBench.

`ingest retraction-watch`, `explore`, and `curate export-candidates` are
real (Phase 1). Every other command is still a stub: it prints what it will
do once the corresponding module (corpus/, rag/, eval/, stats/) is
implemented. No research logic lives in this file -- it only orchestrates
calls into the modules under src/retraction_bench/.
"""

from pathlib import Path

import typer
from dotenv import load_dotenv

from retraction_bench import check_disk as check_disk_module
from retraction_bench.curate import candidates as candidates_module
from retraction_bench.curate import validate_claim_type_screen as validate_claim_type_screen_module
from retraction_bench.ingest import explore as explore_module
from retraction_bench.ingest import pubmed as pubmed_module
from retraction_bench.ingest import retraction_watch as retraction_watch_module

load_dotenv()  # picks up .env for NCBI_EMAIL/NCBI_API_KEY etc. -- no-op if .env doesn't exist

app = typer.Typer(help="RetractionBench CLI.")

ingest_app = typer.Typer(help="Data acquisition commands.")
app.add_typer(ingest_app, name="ingest")


@ingest_app.command("retraction-watch")
def ingest_retraction_watch(
    force: bool = typer.Option(False, "--force", help="Re-download even if today's cached copy already exists."),
) -> None:
    """Download the Retraction Watch database and load it into DuckDB, raw shape preserved."""
    report = retraction_watch_module.ingest(force=force)
    typer.echo(f"Loaded {report.row_count} raw records into {retraction_watch_module.DB_PATH}")
    if report.trailing_column_nonempty_count:
        typer.echo(
            f"WARNING: trailing unnamed column has {report.trailing_column_nonempty_count} non-empty values "
            "(expected 0) -- see docs/DATA_NOTES.md."
        )


@ingest_app.command("verify-pubmed")
def ingest_verify_pubmed(
    candidates: Path = typer.Option(  # noqa: B008
        ..., "--candidates", help="Candidate CSV with a 'pmid' column, e.g. from curate export-candidates."
    ),
    output: Path = typer.Option(  # noqa: B008
        Path("data/interim/pubmed_verified_candidates.csv"), "--output", help="Output CSV path."
    ),
) -> None:
    """Check PubMed's own record for each candidate's PMID for the Retracted Publication tag.

    the project protocol's non-negotiable verification rule: Retraction
    Watch membership alone is not sufficient, the PubMed tag must also be
    confirmed. Never inferred.
    """
    out = pubmed_module.verify_candidates_csv(candidates, output_path=output)
    confirmed = int(out["pubmed_retracted_tag_confirmed"].sum())
    total = len(out)
    typer.echo(f"Wrote {output}")
    typer.echo(f"PubMed-confirmed: {confirmed}/{total} ({confirmed / total * 100:.1f}%)")
    unconfirmed = out[~out["pubmed_retracted_tag_confirmed"]]
    if len(unconfirmed):
        typer.echo(f"NOT confirmed (no Retracted Publication tag, or lookup failed): {len(unconfirmed)}")


@app.command()
def explore() -> None:
    """Generate the Phase 1 exploration report from the raw Retraction Watch table."""
    report_path = explore_module.run_explore()
    typer.echo(f"Wrote {report_path}")
    typer.echo("Data-quality findings appended to docs/DATA_NOTES.md.")


curate_app = typer.Typer(help="Candidate selection and annotation support commands.")
app.add_typer(curate_app, name="curate")


@curate_app.command("export-candidates")
def curate_export_candidates(
    subject: list[str] = typer.Option(  # noqa: B008 -- this is Typer's documented pattern
        ..., "--subject", help="Subject label(s) to include, e.g. '(HSC) Medicine - Oncology'. Repeatable."
    ),
    output: Path = typer.Option(  # noqa: B008
        candidates_module.DEFAULT_OUTPUT_PATH, "--output", help="Output CSV path."
    ),
) -> None:
    """Export tier_1_clean candidates (Retraction, post-2015, PMID-resolvable) for hand review."""
    out = candidates_module.export_tier1_candidates(subject, output_path=output)
    typer.echo(f"Wrote {len(out)} candidates across {out['domain'].nunique()} subject(s) to {output}")
    for subj, count in out["domain"].value_counts().items():
        typer.echo(f"  {subj}: {count}")


@curate_app.command("score-claim-type-screen")
def curate_score_claim_type_screen() -> None:
    """Validate the claim-type screen against the author's 100 hand labels (ADR-021)."""
    validate_claim_type_screen_module.run_validation()
    typer.echo(f"Wrote {validate_claim_type_screen_module.DEFAULT_REPORT_PATH}")
    typer.echo(f"Wrote {validate_claim_type_screen_module.DEFAULT_DISAGREEMENTS_PATH}")


@app.command("check-disk")
def check_disk() -> None:
    """Report whether OLLAMA_MODELS/HF_HOME/UV_CACHE_DIR/PIP_CACHE_DIR/TORCH_HOME/TMPDIR point
    at D:, and the size of both the D: target and the C: default for each (the project protocol:
    run this before any command that downloads or caches bulk data).
    """
    entries = check_disk_module.check_all()
    typer.echo(check_disk_module.format_report(entries))
    misconfigured = [e for e in entries if not e.points_to_d]
    if misconfigured:
        names = ", ".join(e.env_var for e in misconfigured)
        typer.echo(f"WARNING: {len(misconfigured)} variable(s) not pointing at D: -- {names}")
        raise typer.Exit(code=1)


@app.command()
def index() -> None:
    """Build the embedding + FAISS index over the corpus."""
    typer.echo("[stub] index: will embed the corpus and build the FAISS retrieval index.")


@app.command()
def run(
    dry_run_items: str = typer.Option(
        None,
        "--dry-run-items",
        help="Comma-separated item_ids to restrict collection to (e.g. RB-0001,RB-0002). "
        "Omit for the full 28-item run.",
    ),
    models: str = typer.Option(
        None,
        "--models",
        help="Comma-separated model identifiers to restrict collection to. Omit for all three "
        "(collect_module.MODELS).",
    ),
) -> None:
    """Run the RAG pipeline across items, conditions, and seeds, producing ModelResponse records.

    Resumable: already-cached (item, condition, model, seed) results are skipped, not re-called
    (rag/cache.py). Writes a run manifest before any call fires (models, seeds, conditions,
    per-condition item counts, corpus hash, git commit) so every result file stays traceable to
    the exact configuration that produced it.
    """
    from retraction_bench.rag import collect as collect_module

    item_ids = dry_run_items.split(",") if dry_run_items else None
    model_tuple = tuple(models.split(",")) if models else collect_module.MODELS
    collect_module.run_collection(models=model_tuple, dry_run_items=item_ids)


@app.command()
def evaluate() -> None:
    """Score the cached model run (M1, M3, Correctness) directly from
    `data/interim/eval/model_responses.jsonl` and the hand-label CSVs, writing
    `results/reproduced_paper_numbers.{json,md}` (ADR-153).

    Not routed through a fully-populated `EvaluationResult` per response: that schema's
    `correctness` field is required, but only 100 of 900 responses were ever hand-scored for
    correctness, so a real `EvaluationResult` cannot be honestly constructed for the other 800
    without fabricating a label. `scripts/reproduce_paper_numbers.py` scores M1 directly from
    each cached response via `eval/citation.py`, and M3/Correctness directly from their own
    (smaller, hand-labeled) samples -- exactly matching what this project's evaluation phase
    actually does, and exactly what `tests/test_reproduce_paper_numbers.py` checks against the
    numbers published in the paper.
    """
    from retraction_bench.reproduce import main as reproduce_main

    reproduce_main()


@app.command()
def report() -> None:
    """Print the human-readable summary `evaluate` most recently wrote
    (`results/reproduced_paper_numbers.md`) -- run `evaluate` first if it doesn't exist yet."""
    path = Path("results/reproduced_paper_numbers.md")
    if not path.exists():
        typer.echo(f"{path} does not exist yet -- run `retraction-bench evaluate` first.")
        raise typer.Exit(code=1)
    typer.echo(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    app()
