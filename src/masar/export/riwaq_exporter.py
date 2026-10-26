"""Riwaq batch exporter assembling verified HadithRecord bundles (schema_version: 1)."""

from datetime import datetime, timezone
from typing import Optional

from masar.core.corpus_adapter import CorpusAdapter
from masar.core.models import (
    CandidateRecord,
    HadithRecord,
    ImportBatch,
    IsnadVariant,
    SourceRef,
)
from masar.export.preflight_gates import PreflightReport, PreflightValidator
from masar.verification.accretive_store import AccretiveStore


class PreflightGateError(Exception):
    """Raised when an export batch fails any of the 4 deterministic preflight gates."""

    def __init__(self, message: str, report: Optional[PreflightReport] = None):
        super().__init__(message)
        self.report = report


class RiwaqExporter:
    """Serializes verified candidate sets into Riwaq schema_version: 1 ImportBatch bundles."""

    def __init__(
        self,
        corpus_adapter: CorpusAdapter,
        curated_store: Optional[AccretiveStore] = None,
        validator: Optional[PreflightValidator] = None,
    ):
        self.corpus_adapter = corpus_adapter
        self.curated_store = curated_store
        self.validator = validator or PreflightValidator()

    def _convert_candidate(self, cand: CandidateRecord, family_id: str) -> HadithRecord:
        """Convert a CandidateRecord into a strict Riwaq HadithRecord."""
        now_iso = datetime.now(timezone.utc).isoformat()
        chain = cand.narrator_ids if cand.narrator_ids else ["transmitter_unknown"]

        source_ref = SourceRef(
            collection=cand.collection,
            source_type="print",
            source_locator=f"Hadith #{cand.hadith_number}",
            ingested_at=now_iso,
        )

        variant = IsnadVariant(
            variant_id=f"var_{cand.id}",
            isnad_chain=chain,
            isnad_raw=cand.isnad_raw,
            matn_raw=cand.matn,
            status="primary",
        )

        return HadithRecord(
            hadith_id=f"rec_{cand.id}",
            family_id=family_id,
            title=f"{cand.collection} - #{cand.hadith_number}",
            source_ref=source_ref,
            variants=[variant],
            matn_raw=cand.matn,
        )

    def build_batch(
        self,
        record_ids: list[str],
        family_id: str,
        import_id: Optional[str] = None,
    ) -> ImportBatch:
        """Assemble candidates, resolve curated overlays, and execute preflight gates."""
        now_iso = datetime.now(timezone.utc).isoformat()
        records: list[HadithRecord] = []

        for rid in record_ids:
            if self.curated_store:
                cand = self.curated_store.resolve_record(rid, self.corpus_adapter)
            else:
                cand = self.corpus_adapter.get_record(rid)

            if not cand:
                raise ValueError(f"Record with ID '{rid}' not found.")

            records.append(self._convert_candidate(cand, family_id))

        batch = ImportBatch(
            schema_version=1,
            imported_at=now_iso,
            import_id=import_id,
            records=records,
        )

        # Enforce 4 deterministic preflight gates
        report = self.validator.validate_batch(batch)
        if not report.all_passed:
            err_msg = f"Preflight validation failed for export batch: {'; '.join(report.errors)}"
            raise PreflightGateError(err_msg, report)

        return batch
