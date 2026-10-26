/**
 * Client API for interacting with Masar backend.
 */

export interface ExplainabilityReceipt {
  candidate_id: string;
  ensemble_score: number;
  signal_scores: {
    bm25_lexical: number;
    pericope_jaccard: number;
    semantic_cosine: number;
    isnad_overlap: number;
  };
  is_topical_false_positive: boolean;
  quarantine_reason?: string | null;
  pericope_spans?: [number, number][];
}

export interface CandidateRecord {
  id: string;
  collection: string;
  book_number?: number | null;
  hadith_number: string;
  sect: 'sunni' | 'shia';
  full_text?: string | null;
  matn: string;
  isnad_raw?: string | null;
  narrator_ids: string[];
  receipt?: ExplainabilityReceipt | null;
}

const API_BASE = '/api';

export async function searchHadiths(
  seed: string,
  scope: 'all' | 'sunni' | 'shia' = 'all',
  limit: number = 20
): Promise<CandidateRecord[]> {
  const resp = await fetch(`${API_BASE}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      seed_text: seed,
      scope: scope,
      semantic_top_k: limit,
      min_pericope_threshold: 0.35,
    }),
  });
  if (!resp.ok) {
    throw new Error(`Search failed: ${resp.statusText}`);
  }
  return resp.json();
}

export async function getHadith(hadithId: string): Promise<CandidateRecord> {
  const resp = await fetch(`${API_BASE}/hadith/${hadithId}`);
  if (!resp.ok) {
    throw new Error(`Failed to fetch hadith: ${resp.statusText}`);
  }
  return resp.json();
}

export async function adjustSplit(
  hadithId: string,
  matnStart: number,
  matnEnd: number
): Promise<{ status: string; boundary: any }> {
  const resp = await fetch(`${API_BASE}/split`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      hadith_id: hadithId,
      matn_start: matnStart,
      matn_end: matnEnd,
    }),
  });
  if (!resp.ok) {
    throw new Error(`Failed to save split: ${resp.statusText}`);
  }
  return resp.json();
}

export async function exportBatch(
  recordIds: string[],
  familyId: string
): Promise<any> {
  const resp = await fetch(`${API_BASE}/export`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      record_ids: recordIds,
      family_id: familyId,
    }),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || `Export failed: ${resp.statusText}`);
  }
  return resp.json();
}
