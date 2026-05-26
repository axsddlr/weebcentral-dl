import { Cover } from '@/components/Cover';
import { SERIES, NEW_AVAILABLE } from '@/lib/mockData';

export function Tracked() {
  const items = SERIES.slice(0, 7);

  return (
    <>
      <div className="b-head">
        <div>
          <div className="b-eyebrow">№ 047 · WATCHLIST · 55 SERIES</div>
          <div className="b-title">Tracked</div>
          <div className="b-deck">Series watched for new chapters by the Docker tracker. Five have updates pending — queue them in a single click.</div>
        </div>
        <div className="b-headact">
          <div className="b-byline">LAST SCAN <b>6h 12m</b> AGO</div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="b-btn">
              <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><path d="M12 16V3m0 13 5-5m-5 5-5-5M4 21h16"/></svg>
              Import
            </button>
            <button className="b-btn b-btn-primary">
              <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="currentColor"><path d="M7 4v16l13-8z"/></svg>
              Check Now
            </button>
          </div>
        </div>
      </div>

      <div className="b-toolbar">
        <div className="b-pill is-active">All <span className="ct">55</span></div>
        <div className="b-pill">Reading <span className="ct">38</span></div>
        <div className="b-pill">New <span className="ct" style={{ color: 'var(--crimson)' }}>5</span></div>
        <div className="b-pill">Complete <span className="ct">9</span></div>
        <div className="b-search" style={{ maxWidth: 280, marginLeft: 'auto' }}>
          <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
          <input placeholder="Filter tracked manga…" />
        </div>
      </div>

      <div className="b-tracked">
        {items.map((s, i) => {
          const hasNew = NEW_AVAILABLE.find((n) => n.series === s.id);
          return (
            <div className="b-tracked-row" key={s.id}>
              <Cover series={s} height={84} showTitle={false} showBadge={false} />
              <div className="b-tracked-info">
                <div className="b-tracked-name"><span className="ct">{String(i + 1).padStart(2, '0')}.</span>{s.title}</div>
                <div className="b-tracked-byline">BY {s.author.toUpperCase()}</div>
                <div className="b-tracked-tags">
                  <span className="b-tag">{s.status === 'complete' ? 'COMPLETE' : 'ONGOING'}</span>
                  {s.tags.includes('Adult') && <span className="b-tag warn">18+</span>}
                  {s.tags.slice(0, 3).map((t) => <span key={t} className="b-tag">{t}</span>)}
                </div>
              </div>
              <div className={'b-tracked-status' + (hasNew ? ' warn' : '')}>
                {s.status === 'complete' ? 'COMPLETE'
                  : s.status === 'caught-up' ? 'CAUGHT UP'
                  : hasNew ? `+${hasNew.count} NEW`
                  : 'READING'}
              </div>
              <div className="b-tracked-num">{s.read}/{s.ch}<span className="lbl">CHAPTERS</span></div>
              <div style={{ display: 'flex', gap: 6 }}>
                <button className="b-btn">
                  <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><path d="M12 3v13m0 0 5-5m-5 5-5-5M4 21h16"/></svg>
                  Queue
                </button>
                <button className="b-btn">
                  <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/></svg>
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
}
