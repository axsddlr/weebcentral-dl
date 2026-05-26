import { useState, useEffect } from 'react';
import type { View } from '@/types';
import type { LibraryManga, LibraryChapter } from '@/types';
import * as api from '@/services/api';

interface ReaderProps {
  manga?: LibraryManga | null;
  chapter?: LibraryChapter | null;
  onViewChange: (view: View) => void;
}

export function Reader({ manga, chapter, onViewChange }: ReaderProps) {
  const [pages, setPages] = useState<string[]>([]);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!manga || !chapter) return;
    setLoading(true);
    setPage(0);
    api.getPages(manga.path, chapter.filename)
      .then(({ pages: p }) => setPages(p))
      .catch(() => setPages([]))
      .finally(() => setLoading(false));
  }, [manga?.path, chapter?.filename]);

  const title = manga?.title ?? 'No series selected';
  const chNum = chapter?.number ?? '—';
  const totalPages = pages.length || chapter?.totalPages || 0;

  return (
    <div className="b-reader">
      <div className="b-reader-top">
        <button className="b-reader-back" onClick={() => onViewChange('library')}>
          <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><path d="M19 12H5m0 0 6-6m-6 6 6 6"/></svg>
          Back to library
        </button>
        <div>
          <div className="b-reader-title">{title} · Ch. {chNum}</div>
          <div className="b-reader-sub">P.{String(page + 1).padStart(2, '0')}/{totalPages || '—'}</div>
        </div>
        <div className="b-reader-tools">
          <div className="b-tool is-active" title="Vertical">⇕</div>
          <div className="b-tool" title="Zoom">⌕</div>
        </div>
      </div>

      <div className="b-reader-stage">
        {pages.length > 0 && (
          <div className="b-reader-rail">
            {pages.slice(0, 12).map((_, i) => (
              <div
                key={i}
                className={'b-reader-thumb' + (i === page ? ' is-active' : '')}
                style={{ background: '#1c1814' }}
                onClick={() => setPage(i)}
              />
            ))}
          </div>
        )}

        {loading && (
          <div style={{ color: 'var(--dim)', fontFamily: '"JetBrains Mono",monospace', fontSize: 12, margin: 'auto' }}>
            LOADING…
          </div>
        )}

        {!loading && !manga && (
          <div style={{ color: 'var(--dim)', fontFamily: '"JetBrains Mono",monospace', fontSize: 12, margin: 'auto', textAlign: 'center' }}>
            OPEN A CHAPTER FROM THE LIBRARY
          </div>
        )}

        {!loading && manga && pages.length === 0 && (
          <div style={{ color: 'var(--dim)', fontFamily: '"JetBrains Mono",monospace', fontSize: 12, margin: 'auto' }}>
            NO PAGES FOUND
          </div>
        )}

        {!loading && pages.length > 0 && (
          <div className="b-reader-pages">
            {pages.map((_url, i) => (
              <div key={i} className="b-reader-page" style={{ height: 'auto' }}>
                <div className="b-reader-page-num">P.{String(i + 1).padStart(2, '0')}/{totalPages}</div>
                <img
                  src={api.getPageUrl(manga!.path, chapter!.filename, i)}
                  alt={`Page ${i + 1}`}
                  style={{ width: '100%', display: 'block' }}
                  loading="lazy"
                  onLoad={() => { if (i === page) {} }}
                />
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="b-reader-bottom">
        <span><span className="num">P.{page + 1}</span> &nbsp;OF {totalPages || '—'}</span>
        <div className="b-reader-progress">
          <div className="b-reader-progress-fill" style={{ width: totalPages ? `${((page + 1) / totalPages) * 100}%` : '0%' }} />
        </div>
        <span style={{ color: 'var(--cream)', fontWeight: 600 }}>
          {pages.length > 0 ? `${totalPages - page - 1} PAGES LEFT` : '—'}
        </span>
      </div>
    </div>
  );
}
