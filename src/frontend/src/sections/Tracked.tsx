import { useState, useEffect } from 'react';
import * as api from '@/services/api';

export function Tracked() {
  const [items, setItems] = useState<api.TrackedManga[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [checking, setChecking] = useState(false);

  const fetchTracked = (q = '') => {
    api.getTracked(q ? `?q=${encodeURIComponent(q)}` : '')
      .then(({ series, total: t }) => { setItems(series); setTotal(t); })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchTracked(); }, []);

  const handleCheck = () => {
    setChecking(true);
    api.checkTracked().finally(() => { setChecking(false); fetchTracked(filter); });
  };

  const handleRemove = (seriesId: string) => {
    api.removeTracked(seriesId).then(() => fetchTracked(filter));
  };

  const handleImport = () => {
    api.importTracked().then(() => fetchTracked(filter));
  };

  return (
    <>
      <div className="b-head">
        <div>
          <div className="b-eyebrow">WATCHLIST · {total} SERIES</div>
          <div className="b-title">Tracked</div>
          <div className="b-deck">Series watched for new chapters by the Docker tracker.</div>
        </div>
        <div className="b-headact">
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="b-btn" onClick={handleImport}>
              <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><path d="M12 16V3m0 13 5-5m-5 5-5-5M4 21h16"/></svg>
              Import
            </button>
            <button className="b-btn b-btn-primary" onClick={handleCheck} disabled={checking}>
              <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="currentColor"><path d="M7 4v16l13-8z"/></svg>
              {checking ? 'Checking…' : 'Check Now'}
            </button>
          </div>
        </div>
      </div>

      <div className="b-toolbar">
        <div className="b-search" style={{ maxWidth: 280, marginLeft: 'auto' }}>
          <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
          <input
            placeholder="Filter tracked manga…"
            value={filter}
            onChange={(e) => { setFilter(e.target.value); fetchTracked(e.target.value); }}
          />
        </div>
      </div>

      <div className="b-tracked">
        {loading && (
          <div style={{ color: 'var(--dim)', fontFamily: '"JetBrains Mono",monospace', fontSize: 11, padding: '20px 0' }}>LOADING…</div>
        )}
        {!loading && items.length === 0 && (
          <div style={{ color: 'var(--dim)', fontFamily: '"JetBrains Mono",monospace', fontSize: 11, padding: '40px 0', textAlign: 'center' }}>
            {filter ? 'NO RESULTS' : 'NO TRACKED SERIES — USE SEARCH TO ADD SOME'}
          </div>
        )}
        {items.map((s, i) => (
          <div className="b-tracked-row" key={s.series_id}>
            <div style={{
              width: 64,
              height: 84,
              borderRadius: 2,
              overflow: 'hidden',
              background: '#1c1814',
              border: '1px solid var(--line)',
              flexShrink: 0,
            }}>
              {s.cover_url && (
                <img src={s.cover_url} alt={s.title} style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
              )}
            </div>
            <div className="b-tracked-info">
              <div className="b-tracked-name">
                <span className="ct">{String(i + 1).padStart(2, '0')}.</span>{s.title}
              </div>
              {s.authors && s.authors.length > 0 && (
                <div className="b-tracked-byline">BY {s.authors[0].toUpperCase()}</div>
              )}
              <div className="b-tracked-tags">
                <span className="b-tag">{s.series_status?.toUpperCase() ?? s.status?.toUpperCase() ?? 'ONGOING'}</span>
                {s.adult && <span className="b-tag warn">18+</span>}
                {(s.tags ?? []).slice(0, 3).map((t) => <span key={t} className="b-tag">{t}</span>)}
              </div>
            </div>
            <div className={'b-tracked-status' + (s.status === 'reading' ? '' : '')}>
              {s.status?.toUpperCase() ?? 'READING'}
            </div>
            <div style={{ display: 'flex', gap: 6 }}>
              <button className="b-btn" onClick={() => handleRemove(s.series_id)}>
                <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/></svg>
              </button>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
