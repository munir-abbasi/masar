import React, { useState } from 'react';
import { CandidateRecord, adjustSplit } from '../api/client';

interface SplitEditorProps {
  candidate: CandidateRecord;
  onClose: () => void;
  onSaved: () => void;
}

export const SplitEditor: React.FC<SplitEditorProps> = ({ candidate, onClose, onSaved }) => {
  const fullText = candidate.full_text || `${candidate.isnad_raw || ''} ${candidate.matn}`.trim();
  const initialStart = fullText.indexOf(candidate.matn) !== -1 ? fullText.indexOf(candidate.matn) : 0;
  
  const [splitPos, setSplitPos] = useState<number>(initialStart);
  const [isSaving, setIsSaving] = useState(false);

  const isnadPart = fullText.slice(0, splitPos);
  const matnPart = fullText.slice(splitPos);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await adjustSplit(candidate.id, splitPos, fullText.length);
      alert('تم حفظ الفصل الجديد بنجاح في المستودع التراكمي (masar-curated.db)');
      onSaved();
      onClose();
    } catch (e: any) {
      alert(`خطأ أثناء الحفظ: ${e.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 100 }}>
      <div style={{ background: '#1e293b', padding: '1.5rem', borderRadius: '8px', width: '90%', maxWidth: '800px', maxHeight: '90vh', overflowY: 'auto' }}>
        <h2 style={{ marginTop: 0, color: '#38bdf8' }}>محرر فصل السند عن المتن (Split Editor)</h2>
        <div style={{ marginBottom: '1rem', color: '#94a3b8' }}>
          حرك المؤشر لتحديد نقطة بداية المتن وفصل صيغ الإسناد الزائدة:
        </div>

        <input
          type="range"
          min={0}
          max={fullText.length}
          value={splitPos}
          onChange={(e) => setSplitPos(Number(e.target.value))}
          style={{ width: '100%', marginBottom: '1rem' }}
        />

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
          <div style={{ background: '#0f172a', padding: '1rem', borderRadius: '6px', border: '1px solid #475569' }}>
            <h4 style={{ margin: '0 0 0.5rem 0', color: '#a78bfa' }}>السند المستخلص ({splitPos} حرف)</h4>
            <div style={{ fontSize: '0.95rem', lineHeight: 1.6, color: '#cbd5e1' }}>{isnadPart || '(فارغ)'}</div>
          </div>
          <div style={{ background: '#0f172a', padding: '1rem', borderRadius: '6px', border: '1px solid #475569' }}>
            <h4 style={{ margin: '0 0 0.5rem 0', color: '#34d399' }}>المتن المستخلص ({fullText.length - splitPos} حرف)</h4>
            <div style={{ fontSize: '0.95rem', lineHeight: 1.6, color: '#cbd5e1' }}>{matnPart || '(فارغ)'}</div>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
          <button
            onClick={onClose}
            style={{ padding: '0.5rem 1rem', background: '#475569', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
          >
            إلغاء
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            style={{ padding: '0.5rem 1rem', background: '#0284c7', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}
          >
            {isSaving ? 'جاري الحفظ...' : 'حفظ الفصل التراكمي'}
          </button>
        </div>
      </div>
    </div>
  );
};
