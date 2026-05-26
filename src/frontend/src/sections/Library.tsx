import type { View } from '@/types';
import { Cover } from '@/components/Cover';
import { SERIES } from '@/lib/mockData';

interface LibraryProps {
  onViewChange: (view: View) => void;
}

export function Library({ onViewChange }: LibraryProps) {
  return (
    <>
      <div className="b-head">
        <div>
          <div className="b-eyebrow">№ 047 · COLLECTION</div>
          <div className="b-title">Library</div>
          <div className="b-deck">Fifty-nine series. Ten thousand seven hundred and seventy-four chapters. Eighty-point-two gigabytes of paneled fiction, sorted by what you opened last.</div>
        </div>
        <div className="b-headact">
          <div className="b-byline">FILED <b>{SERIES.length}</b> SERIES</div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="b-btn">
              <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><path d="M21 12a9 9 0 1 1-3-6.7L21 8M21 3v5h-5"/></svg>
              Rescan
            </button>
            <button className="b-btn b-btn-primary">
              <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>
              Grid
            </button>
          </div>
        </div>
      </div>

      <div className="b-toolbar">
        <div className="b-pill is-active">All <span className="ct">59</span></div>
        <div className="b-pill">Reading <span className="ct">38</span></div>
        <div className="b-pill">Caught up <span className="ct">12</span></div>
        <div className="b-pill">Complete <span className="ct">9</span></div>
        <div className="b-search" style={{ maxWidth: 280, marginLeft: 'auto' }}>
          <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
          <input placeholder="Search the stacks…" />
        </div>
      </div>

      <div className="b-lib-grid">
        {SERIES.slice(0, 12).map((s) => (
          <div className="b-lib-card" key={s.id} onClick={() => onViewChange('reader')}>
            <Cover series={s} height={220} />
            <div className="b-progress"><div className="b-progress-fill" style={{ width: `${s.progress * 100}%` }} /></div>
            <div>
              <div className="b-lib-title">{s.title}</div>
              <div className="b-resume-author" style={{ marginTop: 2 }}>BY {s.author.toUpperCase()}</div>
              <div className="b-lib-meta"><span><span className="num">{s.read}</span>/{s.ch} CH</span><span>{s.lastRead}</span></div>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
