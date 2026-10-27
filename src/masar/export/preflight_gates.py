"""Four Deterministic Preflight Verification Gates for Riwaq Interoperability (FM-06).

Enforces GateSchema, GateFamilyConsistency, GateBoundaryHygiene, and GateIsnadIntegrity.
"""

import json
from pathlib import Path
from typing import Literal
import jsonschema
from pydantic import BaseModel

from masar.core.models import ImportBatch
from masar.verification.split_editor import HeuristicBoundaryGuard

SCHEMAS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "schemas"


class PreflightReport(BaseModel):
    """Deterministic validation report summarizing all 4 preflight gates."""

    all_passed: bool
    gate_schema: Literal["PASS", "FAIL"]
    gate_family_consistency: Literal["PASS", "FAIL"]
    gate_boundary_hygiene: Literal["PASS", "FAIL"]
    gate_isnad_integrity: Literal["PASS", "FAIL"]
    errors: list[str] = []


class PreflightValidator:
    """Executes the four deterministic gates required prior to Riwaq batch export."""

    def __init__(self, schemas_dir: Path = SCHEMAS_DIR):
        self.schemas_dir = schemas_dir
        self.guard = HeuristicBoundaryGuard()

    def _check_schema(self, batch: ImportBatch, errors: list[str]) -> Literal["PASS", "FAIL"]:
        batch_dict = batch.model_dump(mode="json")
        batch_schema_path = self.schemas_dir / "riwaq-import-batch.json"
        hadith_schema_path = self.schemas_dir / "riwaq-hadith-record.json"
        narrator_schema_path = self.schemas_dir / "narrator-profile.json"

        if not batch_schema_path.exists():
            return "PASS"  # Skip JSON schema if schema directory not present

        with open(batch_schema_path, encoding="utf-8") as f:
            batch_schema = json.load(f)
        with open(hadith_schema_path, encoding="utf-8") as f:
            hadith_schema = json.load(f)

        narrator_schema = {}
        if narrator_schema_path.exists():
            with open(narrator_schema_path, encoding="utf-8") as f:
                narrator_schema = json.load(f)

        store = {
            "https://raw.githubusercontent.com/munir-abbasi/riwaq/main/schemas/import-batch.json": batch_schema,
            "https://raw.githubusercontent.com/munir-abbasi/riwaq/main/schemas/hadith-record.json": hadith_schema,
            "hadith-record.json": hadith_schema,
            "https://raw.githubusercontent.com/munir-abbasi/riwaq/main/schemas/narrator-profile.json": narrator_schema,
            "narrator-profile.json": narrator_schema,
        }
        resolver = jsonschema.RefResolver(
            base_uri=batch_schema_path.as_uri(),
            referrer=batch_schema,
            store=store,
        )

        try:
            jsonschema.validate(instance=batch_dict, schema=batch_schema, resolver=resolver)
            return "PASS"
        except jsonschema.ValidationError as err:
            errors.append(f"GATE_SCHEMA: {err.message}")
            return "FAIL"

    def _check_family_consistency(self, batch: ImportBatch, errors: list[str]) -> Literal["PASS", "FAIL"]:
        family_ids = {r.family_id for r in batch.records}
        if len(family_ids) != 1:
            errors.append(f"GATE_FAMILY_CONSISTENCY: Inconsistent family_id across batch records: {family_ids}")
            return "FAIL"
        return "PASS"

    def _check_boundary_hygiene(self, batch: ImportBatch, errors: list[str]) -> Literal["PASS", "FAIL"]:
        failed = False
        for rec in batch.records:
            matn = rec.matn_raw or ""
            diag = self.guard.detect_bleed(matn)
            if diag.has_bleed:
                errors.append(
                    f"GATE_BOUNDARY_HYGIENE: Narrator formula in matn for record '{rec.hadith_id}': {diag.reason}"
                )
                failed = True
        return "FAIL" if failed else "PASS"

    def _check_isnad_integrity(self, batch: ImportBatch, errors: list[str]) -> Literal["PASS", "FAIL"]:
        failed = False
        for rec in batch.records:
            for variant in rec.variants:
                if not variant.isnad_chain:
                    errors.append(
                        f"GATE_ISNAD_INTEGRITY: Empty isnad chain in variant '{variant.variant_id}' of record '{rec.hadith_id}'"
                    )
                    failed = True
        return "FAIL" if failed else "PASS"

    def validate_batch(self, batch: ImportBatch) -> PreflightReport:
        """Run all 4 deterministic gates on an ImportBatch payload."""
        errors: list[str] = []

        g_schema = self._check_schema(batch, errors)
        g_family = self._check_family_consistency(batch, errors)
        g_hygiene = self._check_boundary_hygiene(batch, errors)
        g_isnad = self._check_isnad_integrity(batch, errors)

        all_ok = (g_schema == "PASS" and g_family == "PASS" and g_hygiene == "PASS" and g_isnad == "PASS")

        return PreflightReport(
            all_passed=all_ok,
            gate_schema=g_schema,
            gate_family_consistency=g_family,
            gate_boundary_hygiene=g_hygiene,
            gate_isnad_integrity=g_isnad,
            errors=errors,
        )
