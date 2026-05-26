import { useState } from 'react';
import * as api from '@/services/api';

const TAGS = ['Action','Romance','Isekai','Fantasy','Sports','Slice of Life','Horror','Comedy','Drama','Adult','Adventure','Mystery'];

export function Search() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<api.SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tracking, setTracking] = useState<Record<string, boolean>>({});
  const [tracked, setTracked] = useState<Record<string, boolean>>({});

  const handleSearch = () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    api.search(query.trim())
      .then(setResults)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  const handleTrack = (s: api.SearchResult) => {
    setTracking((t) => ({ ...t, [s.id]: true }));
    api.addTracked(s.id, s.title, s.coverUrl)
      .then(() => setTracked((t) => ({ ...t, [s.id]: true })))
      .catch(() => {})
      .finally(() => setTracking((t) => ({ ...t, [s.id]: false })));
  };

  return (
    <>
      <div className="b-head">
        <div>
          <div className="b-eyebrow">ACQUISITIONS</div>
          <div className="b-title">Search</div>
          <div className="b-deck">Discover new series across WeebCentral. Paste a URL, type a title, or browse by genre.</div>
        </div>
      </div>

      <div className="b-search-hero">
        <div className="b-search-input">
          <svg viewBox="0 0 24 24" style={{ width: 16, height: 16 }} fill="none" stroke="currentColor" strokeWidth={1.6}><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
          <input
            placeholder="Search by title, series ID, or paste a URL…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
        </div>
        <button className="b-btn b-btn-primary" onClick={handleSearch} disabled={loading}>
          <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
          {loading ? 'Searching…' : 'Search'}
        </button>
      </div>

      <div>
        <div className="b-eyebrow" style={{ marginBottom: 10 }}>TRENDING GENRES</div>
        <div className="b-trending">
          {TAGS.map((t) => (
            <div key={t} className="b-pill" onClick={() => { setQuery(t); }}>{t}</div>
          ))}
        </div>
      </div>

      {error && (
        <div style={{ color: 'var(--crimson)', fontFamily: '"JetBrains Mono",monospace', fontSize: 11 }}>
          ERROR: {error}
        </div>
      )}

      {results.length > 0 && (
        <div className="b-section">
          <div className="b-sec-head">
            <span className="b-sec-num">RESULTS /</span>
            <span className="b-sec-title">{query}</span>
            <span className="b-sec-line" />
            <span className="b-sec-meta">{results.length} FOUND</span>
          </div>
          <div className="b-lib-grid">
            {results.map((s) => (
              <div className="b-lib-card" key={s.id}>
                <div style={{
                  width: '100%',
                  aspectRatio: '0.7',
                  borderRadius: 2,
                  overflow: 'hidden',
                  background: '#1c1814',
                  border: '1px solid var(--line)',
                }}>
                  {s.coverUrl && (
                    <img src={s.coverUrl} alt={s.title} style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                  )}
                </div>
                <div>
                  <div className="b-lib-title">{s.title}</div>
                  {s.author && s.author.length > 0 && (
                    <div className="b-resume-author" style={{ marginTop: 2 }}>BY {s.author[0].toUpperCase()}</div>
                  )}
                  {s.tags && s.tags.length > 0 && (
                    <div className="b-lib-meta"><span>{s.tags[0]}</span></div>
                  )}
                </div>
                <button
                  className="b-btn"
                  style={{ justifyContent: 'center', opacity: tracked[s.id] ? 0.5 : 1 }}
                  onClick={() => !tracked[s.id] && handleTrack(s)}
                  disabled={tracking[s.id]}
                >
                  <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><path d="M12 5v14M5 12h14"/></svg>
                  {tracked[s.id] ? 'Tracked' : tracking[s.id] ? '…' : 'Track'}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {!loading && results.length === 0 && query && !error && (
        <div style={{ color: 'var(--dim)', fontFamily: '"JetBrains Mono",monospace', fontSize: 11, padding: '40px 0', textAlign: 'center' }}>
          NO RESULTS FOR "{query.toUpperCase()}"
        </div>
      )}
    </>
  );
}
