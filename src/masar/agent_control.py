"""Agent Control Plane projections (manifest, snapshot, diagnose, impact) (ADR D014)."""

from pathlib import Path
import sqlite3
from typing import Any, Optional


class AgentControlPlane:
    """Provides high-density machine-readable system projections for AI agents."""

    def __init__(
        self,
        db_path: str | Path = "corpus.db",
        curated_db: str | Path = "masar-curated.db",
        session_db: str | Path = "masar_session.db",
    ):
        self.db_path = str(db_path)
        self.curated_db = str(curated_db)
        self.session_db = str(session_db)

    def get_manifest(self) -> dict[str, Any]:
        """Return machine manifest of tools, schemas, and capabilities."""
        return {
            "product": "Masar",
            "version": "0.1.0",
            "description": "High-precision Hadith Takhrīj variant discovery engine",
            "interop_target": "Riwaq (schema_version: 1)",
            "tools": [
                "masar_search",
                "masar_inspect",
                "masar_adjust_split",
                "masar_add_manual",
                "masar_diagnose",
            ],
            "data_stores": {
                "corpus_db": self.db_path,
                "curated_overlay": self.curated_db,
                "session_journal": self.session_db,
            },
        }

    def diagnose(self) -> dict[str, Any]:
        """Perform cross-layer health check and return diagnostics."""
        diag: dict[str, Any] = {
            "status": "HEALTHY",
            "corpus_db": self.db_path,
            "record_count": 0,
            "has_fts_index": False,
            "curated_overlay_exists": Path(self.curated_db).exists(),
            "session_journal_exists": Path(self.session_db).exists(),
        }

        if not Path(self.db_path).exists():
            diag["status"] = "UNINITIALIZED"
            diag["warning"] = f"Corpus database '{self.db_path}' does not exist."
            return diag

        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("SELECT count(*) FROM hadiths")
            diag["record_count"] = cur.fetchone()[0]

            cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='hadiths_fts'")
            diag["has_fts_index"] = cur.fetchone()[0] > 0
            conn.close()
        except Exception as e:
            diag["status"] = "DEGRADED"
            diag["error"] = str(e)

        return diag
