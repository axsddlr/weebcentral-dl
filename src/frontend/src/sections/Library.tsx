import { useState, useEffect } from 'react';
import type { View, LibraryManga, LibraryChapter } from '@/types';
import * as api from '@/services/api';
import { getCoverUrl } from '@/services/api';

interface LibraryProps {
  onViewChange: (view: View) => void;
  onOpenReader?: (manga: LibraryManga, chapter: LibraryChapter) => void;
}

export function Library({ onViewChange, onOpenReader }: LibraryProps) {
  const [series, setSeries] = useState<api.LibrarySeries[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState('');

  useEffect(() => {
    api.getLibrary()
      .then(setSeries)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const handleRescan = () => {
    setLoading(true);
    api.refreshLibrary()
      .then(setSeries)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  const filtered = series.filter((s) =>
    !filter || s.title.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <>
      <div className="b-head">
        <div>
          <div className="b-eyebrow">COLLECTION</div>
          <div className="b-title">Library</div>
          <div className="b-deck">
            {loading ? 'Scanning…' : error ? error : `${series.length} series in your collection.`}
          </div>
        </div>
        <div className="b-headact">
          <div className="b-byline">FILED <b>{series.length}</b> SERIES</div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="b-btn" onClick={handleRescan}>
              <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><path d="M21 12a9 9 0 1 1-3-6.7L21 8M21 3v5h-5"/></svg>
              Rescan
            </button>
          </div>
        </div>
      </div>

      <div className="b-toolbar">
        <div className="b-search" style={{ maxWidth: 320 }}>
          <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
          <input
            placeholder="Search the stacks…"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
        </div>
      </div>

      {loading && (
        <div style={{ color: 'var(--dim)', fontFamily: '"JetBrains Mono",monospace', fontSize: 12, padding: '40px 0', textAlign: 'center' }}>
          SCANNING LIBRARY…
        </div>
      )}

      {!loading && !error && filtered.length === 0 && (
        <div style={{ color: 'var(--dim)', fontFamily: '"JetBrains Mono",monospace', fontSize: 12, padding: '40px 0', textAlign: 'center' }}>
          {filter ? 'NO RESULTS' : 'LIBRARY EMPTY — DOWNLOAD SOME MANGA FIRST'}
        </div>
      )}

      {!loading && (
        <div className="b-lib-grid">
          {filtered.map((s) => {
            const cover = getCoverUrl(s.path);
            return (
              <div className="b-lib-card" key={s.id} onClick={async () => {
                if (!onOpenReader) { onViewChange('reader'); return; }
                const chapters = await api.getLibraryChapters(s.path).catch(() => []);
                if (chapters.length > 0) {
                  const manga: LibraryManga = { ...s, downloadedChapters: chapters.length, readChapters: 0 };
                  const chapter: LibraryChapter = { ...chapters[0], read: false, lastReadPage: 0, images: [] };
                  onOpenReader(manga, chapter);
                } else {
                  onViewChange('reader');
                }
              }}>
                <div style={{
                  width: '100%',
                  aspectRatio: '2/3',
                  borderRadius: 2,
                  overflow: 'hidden',
                  background: '#1c1814',
                  border: '1px solid var(--line)',
                  position: 'relative',
                }}>
                  <img
                    src={cover}
                    alt={s.title}
                    style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
                    onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                  />
                </div>
                <div>
                  <div className="b-lib-title">{s.title}</div>
                  <div className="b-lib-meta">
                    <span><span className="num">{s.totalChapters}</span> CH</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </>
  );
}
