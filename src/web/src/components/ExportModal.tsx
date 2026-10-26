import React, { useState } from 'react';
import { exportBatch } from '../api/client';

interface ExportModalProps {
  selectedIds: string[];
  onClose: () => void;
}

export const ExportModal: React.FC<ExportModalProps> = ({ selectedIds, onClose }) => {
  const [familyId, setFamilyId] = useState('fam_niyyah_bundle_01');
  const [isExporting, setIsExporting] = useState(false);
  const [exportedJson, setExportedJson] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleExport = async () => {
    setIsExporting(true);
    setErrorMsg(null);
    try {
      const batch = await exportBatch(selectedIds, familyId);
      setExportedJson(JSON.stringify(batch, null, 2));
    } catch (e: any) {
      setErrorMsg(e.message);
    } finally {
      setIsExporting(false);
    }
  };

  const handleCopy = () => {
    if (exportedJson) {
      navigator.clipboard.writeText(exportedJson);
      alert('تم نسخ حمولة Riwaq إلى الحافظة!');
    }
  };

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 100 }}>
      <div style={{ background: '#1e293b', padding: '1.5rem', borderRadius: '8px', width: '90%', maxWidth: '700px', maxHeight: '90vh', overflowY: 'auto' }}>
        <h2 style={{ marginTop: 0, color: '#38bdf8' }}>تصدير الحزمة إلى محرك رواق (Riwaq)</h2>
        <p style={{ color: '#94a3b8' }}>
          سيتم التحقق من مطابقة الحزمة لـ 4 بوابات حتمية (المخطط، اتساق العائلة، سلامة الحدود، وتكامل الإسناد).
        </p>

        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', color: '#cbd5e1' }}>معرف العائلة (Family Identifier):</label>
          <input
            type="text"
            value={familyId}
            onChange={(e) => setFamilyId(e.target.value)}
            style={{ width: '100%', padding: '0.6rem', borderRadius: '6px', border: '1px solid #475569', background: '#0f172a', color: '#f8fafc' }}
          />
        </div>

        {errorMsg && (
          <div style={{ background: '#7f1d1d', padding: '0.75rem', borderRadius: '6px', color: '#fecaca', marginBottom: '1rem' }}>
            فشلت بوابات التحقق: {errorMsg}
          </div>
        )}

        {exportedJson ? (
          <div>
            <h4 style={{ color: '#34d399', margin: '0 0 0.5rem 0' }}>✅ تم التحقق والتصدير بنجاح (schema_version: 1)</h4>
            <textarea
              readOnly
              value={exportedJson}
              style={{ width: '100%', height: '250px', background: '#0f172a', color: '#38bdf8', padding: '0.75rem', borderRadius: '6px', fontFamily: 'monospace', fontSize: '0.85rem' }}
            />
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1rem' }}>
              <button
                onClick={handleCopy}
                style={{ padding: '0.5rem 1rem', background: '#0284c7', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
              >
                نسخ JSON
              </button>
              <button
                onClick={onClose}
                style={{ padding: '0.5rem 1rem', background: '#475569', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
              >
                إغلاق
              </button>
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1.5rem' }}>
            <button
              onClick={onClose}
              style={{ padding: '0.5rem 1rem', background: '#475569', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
            >
              إلغاء
            </button>
            <button
              onClick={handleExport}
              disabled={isExporting}
              style={{ padding: '0.5rem 1rem', background: '#059669', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}
            >
              {isExporting ? 'جاري التحقق والتصدير...' : `تصدير ${selectedIds.length} شواهد`}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
