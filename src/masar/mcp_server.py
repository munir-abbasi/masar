"""Native Model Context Protocol (MCP) stdio server for Masar (ADR D014)."""

import json
from pathlib import Path
import sqlite3
import sys
from typing import Any, Optional

from masar.agent_control import AgentControlPlane
from masar.core.corpus_db import RiwayatCorpusAdapter
from masar.core.manual_entry import ManualEntryPipeline, ManualEntryRequest
from masar.core.models import TakhrijQuery
from masar.discovery.hybrid_engine import HybridTakhrijEngine
from masar.verification.accretive_store import AccretiveStore
from masar.verification.split_editor import SplitEditor

MCP_TOOLS = [
    {
        "name": "masar_search",
        "description": "Search for hadith variants using 4-signal takhrīj engine with explainability receipts.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "seed": {"type": "string", "description": "Seed matn or hadith phrase to search for."},
                "scope": {"type": "string", "enum": ["all", "sunni", "shia"], "default": "all"},
                "limit": {"type": "integer", "default": 10},
            },
            "required": ["seed"],
        },
    },
    {
        "name": "masar_inspect",
        "description": "Retrieve full text, isnad chain, and boundary split of a hadith record.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "hadith_id": {"type": "string", "description": "Unique record identifier."},
            },
            "required": ["hadith_id"],
        },
    },
    {
        "name": "masar_adjust_split",
        "description": "Adjust isnad/matn split boundary and persist to accretive curated overlay.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "hadith_id": {"type": "string"},
                "start": {"type": "integer", "description": "Zero-based start index of matn."},
                "end": {"type": "integer", "description": "Zero-based end index of matn."},
            },
            "required": ["hadith_id", "start", "end"],
        },
    },
    {
        "name": "masar_add_manual",
        "description": "Ingest an ad-hoc unsegmented hadith report into workspace with heuristic split.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "collection": {"type": "string"},
                "ref": {"type": "string"},
                "family_id": {"type": "string", "default": "fam_manual"},
            },
            "required": ["text", "collection", "ref"],
        },
    },
    {
        "name": "masar_diagnose",
        "description": "Inspect cross-layer system health and database statistics.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


class MasarMcpServer:
    """Model Context Protocol server exposing Masar capabilities over JSON-RPC 2.0 stdio."""

    def __init__(
        self,
        db_path: str | Path = "corpus.db",
        curated_db: str | Path = "masar-curated.db",
        session_db: str | Path = "masar_session.db",
    ):
        self.db_path = str(db_path)
        self.curated_db = str(curated_db)
        self.session_db = str(session_db)
        self.control = AgentControlPlane(db_path, curated_db, session_db)

    def list_tools(self) -> list[dict[str, Any]]:
        """Return list of supported MCP tools and their schemas."""
        return MCP_TOOLS

    def _exec_search(self, args: dict[str, Any]) -> str:
        conn = sqlite3.connect(self.db_path)
        engine = HybridTakhrijEngine(conn)
        engine.ensure_index()
        q = TakhrijQuery(seed_text=args["seed"], scope=args.get("scope", "all"))
        limit = args.get("limit", 10)
        candidates = engine.discover(q, limit=limit)
        return json.dumps([c.model_dump(mode="json") for c in candidates], ensure_ascii=False)

    def _exec_inspect(self, args: dict[str, Any]) -> str:
        adapter = RiwayatCorpusAdapter(self.db_path)
        record = adapter.get_record(args["hadith_id"])
        if not record:
            raise ValueError(f"Hadith '{args['hadith_id']}' not found.")
        return json.dumps(record.model_dump(mode="json"), ensure_ascii=False)

    def _exec_adjust_split(self, args: dict[str, Any]) -> str:
        adapter = RiwayatCorpusAdapter(self.db_path)
        record = adapter.get_record(args["hadith_id"])
        if not record or not record.full_text:
            raise ValueError(f"Hadith '{args['hadith_id']}' not found or lacks full text.")
        editor = SplitEditor()
        boundary = editor.adjust_split(record.full_text, args["start"], args["end"])
        store = AccretiveStore(self.curated_db)
        store.save_boundary_override(args["hadith_id"], boundary, curator="mcp_agent")
        return json.dumps({"status": "SUCCESS", "boundary": boundary.model_dump()}, ensure_ascii=False)

    def _exec_add_manual(self, args: dict[str, Any]) -> str:
        pipeline = ManualEntryPipeline()
        req = ManualEntryRequest(
            raw_text=args["text"],
            collection=args["collection"],
            source_locator=args["ref"],
            hadith_number="1",
            family_id=args.get("family_id", "fam_manual"),
        )
        record = pipeline.create_record(req)
        return json.dumps(record.model_dump(mode="json"), ensure_ascii=False)

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Dispatch tool invocation and format MCP response."""
        try:
            if name == "masar_search":
                res_text = self._exec_search(arguments)
            elif name == "masar_inspect":
                res_text = self._exec_inspect(arguments)
            elif name == "masar_adjust_split":
                res_text = self._exec_adjust_split(arguments)
            elif name == "masar_add_manual":
                res_text = self._exec_add_manual(arguments)
            elif name == "masar_diagnose":
                res_text = json.dumps(self.control.diagnose(), ensure_ascii=False)
            else:
                return {"isError": True, "content": [{"type": "text", "text": f"Unknown tool: {name}"}]}

            return {"content": [{"type": "text", "text": res_text}], "isError": False}
        except Exception as e:
            return {"isError": True, "content": [{"type": "text", "text": str(e)}]}

    def run_stdio_server(self):
        """Run stdio JSON-RPC 2.0 loop."""
        for line in sys.stdin:
            if not line.strip():
                continue
            try:
                req = json.loads(line)
                req_id = req.get("id")
                method = req.get("method")
                params = req.get("params", {})

                if method == "initialize":
                    result = {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "masar", "version": "0.1.0"},
                    }
                elif method == "tools/list":
                    result = {"tools": self.list_tools()}
                elif method == "tools/call":
                    result = self.call_tool(params.get("name", ""), params.get("arguments", {}))
                else:
                    result = {"error": f"Method {method} not supported"}

                response = {"jsonrpc": "2.0", "id": req_id, "result": result}
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
            except Exception as e:
                err_resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": str(e)}}
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()
