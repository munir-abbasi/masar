"""Unit tests for Event-Sourced Session Journal and Undo/Redo."""

from pathlib import Path
import pytest
from masar.verification.session_store import SessionJournal, SessionEvent


def test_session_journal_record_and_history(tmp_path: Path):
    """Verify recording events in session journal."""
    db_file = tmp_path / "session_journal.db"
    journal = SessionJournal(db_file)

    journal.record(
        action="ADD",
        target_id="cand_1",
        payload={"family_id": "fam_001", "collection": "bukhari"},
    )
    journal.record(
        action="SPLIT",
        target_id="cand_1",
        payload={"matn_start": 149, "matn_end": 187},
    )

    history = journal.get_history()
    assert len(history) == 2
    assert history[0].action == "ADD"
    assert history[1].action == "SPLIT"


def test_session_journal_undo_redo(tmp_path: Path):
    """Verify single-step undo and redo of agent actions."""
    db_file = tmp_path / "session_journal.db"
    journal = SessionJournal(db_file)

    journal.record("ADD", "cand_1", {"family_id": "fam_001"})
    journal.record("ADD", "cand_2", {"family_id": "fam_001"})
    journal.record("PRUNE", "cand_2", {"reason": "topical_trap"})

    # Undo PRUNE
    undone = journal.undo()
    assert undone is not None
    assert undone.action == "PRUNE"
    assert undone.target_id == "cand_2"

    # Active events after undo
    active = journal.get_active_events()
    assert len(active) == 2
    assert active[-1].target_id == "cand_2"
    assert active[-1].action == "ADD"

    # Redo PRUNE
    redone = journal.redo()
    assert redone is not None
    assert redone.action == "PRUNE"

    active_after_redo = journal.get_active_events()
    assert len(active_after_redo) == 3
