import React, { useState } from 'react';
import { CandidateRecord, searchHadiths } from './api/client';
import { QueryBar } from './components/QueryBar';
import { CandidateList } from './components/CandidateList';
import { SplitEditor } from './components/SplitEditor';
import { ExportModal } from './components/ExportModal';

export const App: React.FC = () => {
  const [candidates, setCandidates] = useState<CandidateRecord[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [inspectingCand, setInspectingCand] = useState<CandidateRecord | null>(null);
  const [showExportModal, setShowExportModal] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [lastQuery, setLastQuery] = useState<{ seed: string; scope: 'all' | 'sunni' | 'shia' } | null>(null);

  const handleSearch = async (seed: string, scope: 'all' | 'sunni' | 'shia') => {
    setIsLoading(true);
    setLastQuery({ seed, scope });
    try {
      const results = await searchHadiths(seed, scope);
      setCandidates(results);
      // Auto-select verified non-quarantined results
      const valid = new Set(
        results.filter((c) => !c.receipt?.is_topical_false_positive).map((c) => c.id)
      );
      setSelectedIds(valid);
    } catch (e: any) {
      alert(`خطأ في البحث: ${e.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleSelect = (id: string) => {
    const updated = new Set(selectedIds);
    if (updated.has(id)) {
      updated.delete(id);
    } else {
      updated.add(id);
    }
    setSelectedIds(updated);
  };

  const handleRefresh = () => {
    if (lastQuery) {
      handleSearch(lastQuery.seed, lastQuery.scope);
    }
  };

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '2rem 1rem' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '2rem', color: '#38bdf8' }}>مسار (Masar)</h1>
          <p style={{ margin: '0.25rem 0 0 0', color: '#94a3b8' }}>
            منصة تخريج الشواهد وحزم الأحاديث لمحراب رواق (Riwaq Upstream Feeder)
          </p>
        </div>
        {selectedIds.size > 0 && (
          <button
            onClick={() => setShowExportModal(true)}
            style={{ padding: '0.75rem 1.5rem', background: '#059669', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}
          >
            تصدير إلى رواق ({selectedIds.size})
          </button>
        )}
      </header>

      <main>
        <QueryBar onSearch={handleSearch} isLoading={isLoading} />
        <CandidateList
          candidates={candidates}
          selectedIds={selectedIds}
          onToggleSelect={toggleSelect}
          onInspect={(c) => setInspectingCand(c)}
        />
      </main>

      {inspectingCand && (
        <SplitEditor
          candidate={inspectingCand}
          onClose={() => setInspectingCand(null)}
          onSaved={handleRefresh}
        />
      )}

      {showExportModal && (
        <ExportModal
          selectedIds={Array.from(selectedIds)}
          onClose={() => setShowExportModal(false)}
        />
      )}
    </div>
  );
};
export default App;
