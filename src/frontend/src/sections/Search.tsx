import { useState } from 'react';
import { Cover } from '@/components/Cover';
import { SERIES } from '@/lib/mockData';

const TAGS = ['Action','Romance','Isekai','Fantasy','Sports','Slice of Life','Horror','Comedy','Drama','Adult','Adventure','Mystery'];
const RESULTS = [SERIES[1], SERIES[4], SERIES[3], SERIES[13], SERIES[2], SERIES[11]];

export function Search() {
  const [activeTag, setActiveTag] = useState(2);
  const [query, setQuery] = useState('isekai romance');

  return (
    <>
      <div className="b-head">
        <div>
          <div className="b-eyebrow">№ 047 · ACQUISITIONS</div>
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
          />
        </div>
        <button className="b-btn b-btn-primary">
          <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
          Search
        </button>
      </div>

      <div>
        <div className="b-eyebrow" style={{ marginBottom: 10 }}>TRENDING GENRES</div>
        <div className="b-trending">
          {TAGS.map((t, i) => (
            <div key={t} className={'b-pill' + (i === activeTag ? ' is-active' : '')} onClick={() => setActiveTag(i)}>{t}</div>
          ))}
        </div>
      </div>

      <div className="b-section">
        <div className="b-sec-head">
          <span className="b-sec-num">05 /</span>
          <span className="b-sec-title">Results · {query}</span>
          <span className="b-sec-line" />
          <span className="b-sec-meta">SHOWING 6 OF 184</span>
        </div>
        <div className="b-lib-grid">
          {RESULTS.map((s) => (
            <div className="b-lib-card" key={s.id}>
              <Cover series={s} height={220} />
              <div>
                <div className="b-lib-title">{s.title}</div>
                <div className="b-resume-author" style={{ marginTop: 2 }}>BY {s.author.toUpperCase()}</div>
                <div className="b-lib-meta"><span><span className="num">{s.ch}</span> CHAPTERS</span><span>{s.tags[0]}</span></div>
              </div>
              <button className="b-btn" style={{ justifyContent: 'center' }}>
                <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><path d="M12 5v14M5 12h14"/></svg>
                Track
              </button>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
