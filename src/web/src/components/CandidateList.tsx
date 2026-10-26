import React from 'react';
import { CandidateRecord } from '../api/client';

interface CandidateListProps {
  candidates: CandidateRecord[];
  selectedIds: Set<string>;
  onToggleSelect: (id: string) => void;
  onInspect: (cand: CandidateRecord) => void;
}

export const CandidateList: React.FC<CandidateListProps> = ({
  candidates,
  selectedIds,
  onToggleSelect,
  onInspect,
}) => {
  if (candidates.length === 0) {
    return <div style={{ color: '#94a3b8', textAlign: 'center', padding: '2rem' }}>لا توجد نتائج حتى الآن. أدخل حديثاً للبحث.</div>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      {candidates.map((cand) => {
        const isQuarantined = cand.receipt?.is_topical_false_positive;
        const isSelected = selectedIds.has(cand.id);

        return (
          <div
            key={cand.id}
            style={{
              padding: '1rem',
              borderRadius: '8px',
              background: isQuarantined ? '#3b1c1c' : '#1e293b',
              border: `1px solid ${isSelected ? '#38bdf8' : isQuarantined ? '#7f1d1d' : '#334155'}`,
              display: 'flex',
              gap: '1rem',
              alignItems: 'flex-start',
            }}
          >
            <input
              type="checkbox"
              checked={isSelected}
              onChange={() => onToggleSelect(cand.id)}
              disabled={isQuarantined}
              style={{ marginTop: '0.35rem', cursor: 'pointer' }}
            />
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span style={{ fontWeight: 'bold', color: '#38bdf8' }}>
                  {cand.collection} (حديث #{cand.hadith_number})
                </span>
                <span style={{ fontSize: '0.85rem', color: cand.sect === 'sunni' ? '#a78bfa' : '#34d399' }}>
                  [{cand.sect === 'sunni' ? 'سنة' : 'شيعة'}]
                </span>
                {cand.receipt && (
                  <span style={{ fontSize: '0.85rem', color: isQuarantined ? '#f87171' : '#facc15' }}>
                    {isQuarantined ? '⚠️ معزول (تشابه موضوعي كاذب)' : `المطابقة: ${(cand.receipt.ensemble_score * 100).toFixed(0)}%`}
                  </span>
                )}
              </div>
              <p style={{ margin: '0 0 0.5rem 0', lineHeight: 1.6, color: '#f1f5f9' }}>{cand.matn}</p>
              {cand.receipt?.quarantine_reason && (
                <div style={{ fontSize: '0.85rem', color: '#fca5a5', marginTop: '0.25rem' }}>
                  سبب العزل: {cand.receipt.quarantine_reason}
                </div>
              )}
              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
                <button
                  onClick={() => onInspect(cand)}
                  style={{ fontSize: '0.8rem', padding: '0.25rem 0.5rem', background: '#334155', color: '#e2e8f0', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                >
                  فحص وتعديل الفصل (Split)
                </button>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
