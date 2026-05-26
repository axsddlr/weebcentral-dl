import { useState } from 'react';
import type { View } from '@/types';
import { SERIES, READER_PAGES } from '@/lib/mockData';

interface ReaderProps {
  onViewChange: (view: View) => void;
}

export function Reader({ onViewChange }: ReaderProps) {
  const s = SERIES[0];
  const [page, setPage] = useState(2);

  return (
    <div className="b-reader">
      <div className="b-reader-top">
        <button className="b-reader-back" onClick={() => onViewChange('library')}>
          <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><path d="M19 12H5m0 0 6-6m-6 6 6 6"/></svg>
          Back to library
        </button>
        <div>
          <div className="b-reader-title">{s.title} · Ch. 313</div>
          <div className="b-reader-sub">VOL.17 // CONFESSION ARC // P.{String(page + 1).padStart(2, '0')}/30</div>
        </div>
        <div className="b-reader-tools">
          <div className="b-tool is-active" title="Vertical">⇕</div>
          <div className="b-tool" title="Page">⇔</div>
          <div className="b-tool" title="Zoom">⌕</div>
          <div className="b-tool" title="Settings">⚙</div>
        </div>
      </div>

      <div className="b-reader-stage">
        <div className="b-reader-rail">
          {READER_PAGES.map((p, i) => (
            <div
              key={i}
              className={'b-reader-thumb' + (i === page ? ' is-active' : '')}
              style={{ background: `linear-gradient(160deg, ${p.c[0]}, ${p.c[1]})` }}
              onClick={() => setPage(i)}
            />
          ))}
        </div>
        <div className="b-reader-pages" style={{ transform: 'translateY(-280px)' }}>
          {READER_PAGES.map((p, i) => (
            <div key={i} className="b-reader-page" style={{
              height: 600,
              background: `linear-gradient(160deg, ${p.c[0]}, ${p.c[1]})`,
            }}>
              <div className="b-reader-page-num">P.{String(p.n).padStart(2, '0')}/30</div>
              <div className="b-reader-page-cap">// {p.caption}</div>
              <div style={{ position: 'absolute', inset: '44px 32px', display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gridTemplateRows: '1.4fr 1fr 1.2fr', gap: 6 }}>
                <div style={{ gridColumn: '1 / -1', background: 'rgba(0,0,0,.4)', border: '1px solid rgba(255,255,255,.1)' }} />
                <div style={{ background: 'rgba(0,0,0,.25)', border: '1px solid rgba(255,255,255,.1)' }} />
                <div style={{ gridColumn: '2 / 4', background: 'rgba(0,0,0,.5)', border: '1px solid rgba(255,255,255,.1)' }} />
                <div style={{ gridColumn: '1 / -1', background: 'rgba(0,0,0,.35)', border: '1px solid rgba(255,255,255,.1)' }} />
              </div>
              <div style={{ position: 'absolute', inset: 0, backgroundImage: 'repeating-linear-gradient(45deg, rgba(255,255,255,.025) 0 1px, transparent 1px 2px)', pointerEvents: 'none' }} />
            </div>
          ))}
        </div>
      </div>

      <div className="b-reader-bottom">
        <span><span className="num">P.13</span> &nbsp;OF 30</span>
        <div className="b-reader-progress"><div className="b-reader-progress-fill" style={{ width: '43%' }} /></div>
        <span style={{ color: 'var(--cream)', fontWeight: 600 }}>NEXT: CH.314 →</span>
      </div>
    </div>
  );
}
