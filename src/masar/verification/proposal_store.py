"""AI Proposal Staging Buffer and Drift Guard (FM-08, ADR D015)."""

from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any, Optional
import uuid
from pydantic import BaseModel

from masar.core.models import SplitBoundary
from masar.verification.accretive_store import AccretiveStore


class ProposalStatus(str, Enum):
    """Lifecycle states for AI-generated curation proposals."""

    PENDING = "PENDING"
    PREFLIGHT_PASSED = "PREFLIGHT_PASSED"
    COMMITTED = "COMMITTED"
    REJECTED = "REJECTED"


class ProposalEvaluation(BaseModel):
    """Result of deterministic preflight validation on an AI proposal."""

    proposal_id: str
    status: ProposalStatus
    sha256_receipt: Optional[str] = None
    rejection_reason: Optional[str] = None


class ProposalStore:
    """Staging buffer isolating AI proposals from curated ground truth until verified."""

    def __init__(self, db_path: str | Path, curated_store: AccretiveStore):
        self.db_path = str(db_path)
        self.curated_store = curated_store
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS proposals (
                    proposal_id TEXT PRIMARY KEY,
                    hadith_id TEXT NOT NULL,
                    proposal_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    rationale TEXT,
                    status TEXT NOT NULL,
                    sha256_receipt TEXT,
                    rejection_reason TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def stage_split_proposal(
        self,
        hadith_id: str,
        matn_start: int,
        matn_end: int,
        pre_matn_token: Optional[str] = None,
        post_isnad_token: Optional[str] = None,
        anchor_window: Optional[str] = None,
        agent_id: str = "ai_agent",
        rationale: Optional[str] = None,
    ) -> str:
        """Stage a proposed boundary split into the staging buffer with status PENDING."""
        proposal_id = f"prop_{uuid.uuid4().hex[:10]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        payload = {
            "matn_start": matn_start,
            "matn_end": matn_end,
            "pre_matn_token": pre_matn_token,
            "post_isnad_token": post_isnad_token,
            "anchor_window": anchor_window,
        }

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO proposals (
                    proposal_id, hadith_id, proposal_type, payload,
                    agent_id, rationale, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    proposal_id,
                    hadith_id,
                    "SPLIT_BOUNDARY",
                    json.dumps(payload, ensure_ascii=False),
                    agent_id,
                    rationale,
                    ProposalStatus.PENDING.value,
                    now_iso,
                ),
            )
            conn.commit()

        return proposal_id

    def evaluate_proposal(self, proposal_id: str) -> ProposalEvaluation:
        """Run deterministic preflight validation on staged proposal and emit SHA-256 receipt."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM proposals WHERE proposal_id = ?", (proposal_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Proposal '{proposal_id}' not found.")

            payload = json.loads(row["payload"])
            matn_start = payload.get("matn_start", 0)
            matn_end = payload.get("matn_end", 0)

            # Invariant check: matn_start < matn_end and matn_start >= 0
            if matn_start < 0 or matn_end <= matn_start:
                reason = f"Invalid boundary span: matn_start ({matn_start}) must be < matn_end ({matn_end})"
                cursor.execute(
                    "UPDATE proposals SET status = ?, rejection_reason = ? WHERE proposal_id = ?",
                    (ProposalStatus.REJECTED.value, reason, proposal_id),
                )
                conn.commit()
                return ProposalEvaluation(
                    proposal_id=proposal_id,
                    status=ProposalStatus.REJECTED,
                    rejection_reason=reason,
                )

            # Generate SHA-256 operation receipt
            raw_signature = f"{proposal_id}:{row['hadith_id']}:{row['payload']}:{row['agent_id']}"
            sha256_receipt = hashlib.sha256(raw_signature.encode("utf-8")).hexdigest()

            cursor.execute(
                "UPDATE proposals SET status = ?, sha256_receipt = ? WHERE proposal_id = ?",
                (ProposalStatus.PREFLIGHT_PASSED.value, sha256_receipt, proposal_id),
            )
            conn.commit()

            return ProposalEvaluation(
                proposal_id=proposal_id,
                status=ProposalStatus.PREFLIGHT_PASSED,
                sha256_receipt=sha256_receipt,
            )

    def commit_proposal(self, proposal_id: str) -> bool:
        """Promote an approved proposal from staging buffer into persistent curated overlay."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM proposals WHERE proposal_id = ?", (proposal_id,))
            row = cursor.fetchone()
            if not row or row["status"] != ProposalStatus.PREFLIGHT_PASSED.value:
                return False

            payload = json.loads(row["payload"])
            boundary = SplitBoundary(
                matn_start=payload["matn_start"],
                matn_end=payload["matn_end"],
                pre_matn_token=payload.get("pre_matn_token"),
                post_isnad_token=payload.get("post_isnad_token"),
                anchor_window=payload.get("anchor_window"),
            )

            # Save to accretive curated overlay
            self.curated_store.save_boundary_override(
                hadith_id=row["hadith_id"],
                boundary=boundary,
                curator=f"ai_proposal:{row['agent_id']}",
            )

            cursor.execute(
                "UPDATE proposals SET status = ? WHERE proposal_id = ?",
                (ProposalStatus.COMMITTED.value, proposal_id),
            )
            conn.commit()
            return True
