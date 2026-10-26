import React, { useState } from 'react';

interface QueryBarProps {
  onSearch: (seed: string, scope: 'all' | 'sunni' | 'shia') => void;
  isLoading: boolean;
}

export const QueryBar: React.FC<QueryBarProps> = ({ onSearch, isLoading }) => {
  const [seed, setSeed] = useState('إنما الأعمال بالنيات وإنما لكل امرئ ما نوى');
  const [scope, setScope] = useState<'all' | 'sunni' | 'shia'>('all');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (seed.trim()) {
      onSearch(seed.trim(), scope);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '1.5rem', background: '#1e293b', padding: '1rem', borderRadius: '8px' }}>
      <input
        type="text"
        value={seed}
        onChange={(e) => setSeed(e.target.value)}
        placeholder="أدخل نص الحديث أو جزءاً منه..."
        style={{ flex: 1, padding: '0.75rem 1rem', fontSize: '1.1rem', borderRadius: '6px', border: '1px solid #334155', background: '#0f172a', color: '#f8fafc' }}
      />
      <select
        value={scope}
        onChange={(e) => setScope(e.target.value as any)}
        style={{ padding: '0.75rem', borderRadius: '6px', border: '1px solid #334155', background: '#0f172a', color: '#f8fafc' }}
      >
        <option value="all">جميع المجموعات (مشترك بين المذاهب)</option>
        <option value="sunni">أهل السنة فقط</option>
        <option value="shia">الشيعة الإمامية فقط</option>
      </select>
      <button
        type="submit"
        disabled={isLoading}
        style={{ padding: '0.75rem 1.5rem', background: '#0284c7', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}
      >
        {isLoading ? 'جاري البحث...' : 'تخريج الشواهد'}
      </button>
    </form>
  );
};
