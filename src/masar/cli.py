"""Agent-First CLI for Masar Takhrīj Engine.

Optimized for token thrifty agent interactions (--compact), structured machine
projections (--format json --receipts), and reversible workspace execution.
"""

import json
from pathlib import Path
import sqlite3
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table

from masar.core.corpus_db import RiwayatCorpusAdapter
from masar.core.manual_entry import ManualEntryPipeline, ManualEntryRequest
from masar.core.models import TakhrijQuery
from masar.discovery.hybrid_engine import HybridTakhrijEngine
from masar.verification.accretive_store import AccretiveStore
from masar.verification.session_store import SessionJournal
from masar.verification.split_editor import SplitEditor

app = typer.Typer(
    name="masar",
    help="Masar: Agent-ergonomic Hadith Takhrīj and variant discovery engine.",
    no_args_is_help=True,
)
session_app = typer.Typer(help="Manage session journal and rollback actions.")
app.add_typer(session_app, name="session")
console = Console()


@app.command("search")
def search_hadiths(
    seed: str = typer.Option(..., "--seed", "-s", help="Arabic text seed snippet."),
    db: str = typer.Option("corpus.db", "--db", help="Path to hadiths SQLite database."),
    scope: str = typer.Option("all", "--scope", help="Corpus scope: all, sunni, shia."),
    compact: bool = typer.Option(False, "--compact", "-c", help="Emit high-density token-thrifty output."),
    format: str = typer.Option("text", "--format", "-f", help="Output format: text, json."),
    receipts: bool = typer.Option(False, "--receipts", "-r", help="Include explainability receipts."),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum candidates to return."),
):
    """Search for hadith variants across multi-signal discovery engine."""
    conn = sqlite3.connect(db)
    engine = HybridTakhrijEngine(conn)
    engine.ensure_index()

    q = TakhrijQuery(seed_text=seed, scope=scope)
    candidates = engine.discover(q, limit=limit)

    if format == "json":
        data = [
            c.model_dump(mode="json", exclude=None if receipts else {"receipt"})
            for c in candidates
        ]
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
        return

    if compact:
        # High-density token-thrifty ASCII projection (< 300 tokens)
        lines = [f"ID | COLL | SEC | SCORE | MATN_SNIPPET"]
        for c in candidates:
            score = c.receipt.ensemble_score if c.receipt else 0.0
            is_trap = "[TRAP]" if (c.receipt and c.receipt.is_topical_false_positive) else ""
            lines.append(f"{c.id} | {c.collection} | {c.sect[:3]} | {score:.2f}{is_trap} | {c.matn[:40]}")
        typer.echo("\n".join(lines))
        return

    # Rich formatted table
    table = Table(title="Masar Takhrīj Discovery Candidates")
    table.add_column("ID", style="cyan")
    table.add_column("Collection", style="green")
    table.add_column("Sect", style="magenta")
    table.add_column("Score", style="yellow")
    table.add_column("Matn Snippet", style="white")

    for c in candidates:
        score_str = f"{c.receipt.ensemble_score:.2f}" if c.receipt else "N/A"
        if c.receipt and c.receipt.is_topical_false_positive:
            score_str += " [red](QUARANTINED)[/red]"
        table.add_row(c.id, c.collection, c.sect, score_str, c.matn[:60])

    console.print(table)


@app.command("inspect")
def inspect_hadith(
    id: str = typer.Option(..., "--id", help="Hadith ID to inspect."),
    db: str = typer.Option("corpus.db", "--db", help="Path to hadiths SQLite database."),
    receipt: bool = typer.Option(False, "--receipt", "-r", help="Include verification receipts."),
):
    """Inspect detailed text, isnad chain, and boundary split of a hadith."""
    adapter = RiwayatCorpusAdapter(db)
    record = adapter.get_record(id)
    if not record:
        typer.echo(f"Record with ID '{id}' not found.", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"ID: {record.id}")
    typer.echo(f"Collection: {record.collection} (Hadith #{record.hadith_number})")
    typer.echo(f"Sect: {record.sect}")
    typer.echo(f"Isnad: {record.isnad_raw or 'N/A'}")
    typer.echo(f"Matn: {record.matn}")
    typer.echo(f"Narrators: {', '.join(record.narrator_ids)}")


@app.command("split")
def adjust_split(
    id: str = typer.Option(..., "--id", help="Hadith ID to adjust."),
    start: int = typer.Option(..., "--start", help="Zero-based start index of matn."),
    end: int = typer.Option(..., "--end", help="Zero-based end index of matn."),
    db: str = typer.Option("corpus.db", "--db", help="Path to base corpus SQLite database."),
    curated_db: str = typer.Option("masar-curated.db", "--curated-db", help="Path to accretive store."),
):
    """Adjust isnad/matn split boundary and save to accretive curated overlay."""
    adapter = RiwayatCorpusAdapter(db)
    record = adapter.get_record(id)
    if not record or not record.full_text:
        typer.echo(f"Record '{id}' not found or lacks full_text.", err=True)
        raise typer.Exit(code=1)

    editor = SplitEditor()
    new_boundary = editor.adjust_split(record.full_text, start, end)

    store = AccretiveStore(curated_db)
    store.save_boundary_override(id, new_boundary, curator="agent_cli")

    typer.echo(f"Boundary saved for record {id}: matn_start={start}, matn_end={end}")
    typer.echo(f"Anchor token: '{new_boundary.post_isnad_token}'")


@app.command("add")
def add_manual(
    text: str = typer.Option(..., "--text", "-t", help="Raw Arabic hadith text."),
    collection: str = typer.Option(..., "--collection", "-c", help="Source manuscript or collection."),
    ref: str = typer.Option(..., "--ref", help="Source locator / folio reference."),
    family: str = typer.Option("fam_manual", "--family", help="Target family ID."),
    session_db: str = typer.Option("masar_session.db", "--session-db", help="Path to session journal."),
):
    """Add an external hadith text via manual entry pipeline and journal action."""
    pipeline = ManualEntryPipeline()
    req = ManualEntryRequest(
        raw_text=text,
        collection=collection,
        source_locator=ref,
        hadith_number="1",
        family_id=family,
    )
    rec = pipeline.create_record(req)

    journal = SessionJournal(session_db)
    journal.record(
        action="ADD",
        target_id=rec.hadith_id,
        payload=rec.model_dump(mode="json"),
    )

    typer.echo(f"Added record: {rec.hadith_id}")
    typer.echo(f"Matn snippet: {rec.matn_raw[:40] if rec.matn_raw else ''}")


@session_app.command("undo")
def session_undo(
    session_db: str = typer.Option("masar_session.db", "--session-db", help="Path to session journal."),
):
    """Undo the most recent agent operation in workspace."""
    journal = SessionJournal(session_db)
    undone = journal.undo()
    if not undone:
        typer.echo("No active operations to undo.")
        return
    typer.echo(f"Undone action: {undone.action} on target {undone.target_id}")


@session_app.command("history")
def session_history(
    session_db: str = typer.Option("masar_session.db", "--session-db", help="Path to session journal."),
):
    """View full execution history of workspace actions."""
    journal = SessionJournal(session_db)
    events = journal.get_history()
    for e in events:
        status = "[UNDONE]" if e.is_undone else "[ACTIVE]"
        typer.echo(f"{e.timestamp} | {status} {e.action} -> {e.target_id}")
