import { LOG_LINES } from '@/lib/mockData';

export function Logs() {
  return (
    <>
      <div className="b-head">
        <div>
          <div className="b-eyebrow">№ 047 · DISPATCHES · LIVE</div>
          <div className="b-title">Logs</div>
          <div className="b-deck">The activity stream. Filter by level, search within messages, export the whole thing if you're debugging.</div>
        </div>
        <div className="b-headact">
          <div className="b-byline"><b>1,284</b> ENTRIES · 4 ERRORS</div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="b-btn">
              <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><path d="M12 3v13m0 0 5-5m-5 5-5-5M4 21h16"/></svg>
              Export
            </button>
            <button className="b-btn b-btn-primary">
              <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><path d="M21 12a9 9 0 1 1-3-6.7L21 8M21 3v5h-5"/></svg>
              Tail
            </button>
          </div>
        </div>
      </div>

      <div className="b-figures">
        <div className="b-figure"><div className="b-fig-label"><span>TOTAL</span></div><div className="b-fig-num">1,284</div></div>
        <div className="b-figure"><div className="b-fig-label"><span>INFO</span></div><div className="b-fig-num" style={{ color: '#10B981' }}>892</div></div>
        <div className="b-figure"><div className="b-fig-label"><span>DEBUG</span></div><div className="b-fig-num">340</div></div>
        <div className="b-figure"><div className="b-fig-label"><span>WARN</span></div><div className="b-fig-num" style={{ color: '#F59E0B' }}>48</div></div>
        <div className="b-figure"><div className="b-fig-label"><span>ERROR</span></div><div className="b-fig-num" style={{ color: 'var(--crimson)' }}>4</div></div>
      </div>

      <div className="b-toolbar">
        <div className="b-pill is-active">All</div>
        <div className="b-pill">Info</div>
        <div className="b-pill">Debug</div>
        <div className="b-pill">Warn</div>
        <div className="b-pill">Error</div>
        <div className="b-search" style={{ maxWidth: 280, marginLeft: 'auto' }}>
          <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
          <input placeholder="Search dispatches…" />
        </div>
      </div>

      <div className="b-logs">
        <div className="b-log-row" style={{ background: 'rgba(245,240,225,.03)', color: 'var(--dim)' }}>
          <span>TIMESTAMP</span><span>LEVEL</span><span>SOURCE</span><span>MESSAGE</span>
        </div>
        {LOG_LINES.map((l, i) => (
          <div className="b-log-row" key={i}>
            <span className="b-log-time">{l.t}</span>
            <span className={'b-log-lvl ' + l.lvl}>{l.lvl.toUpperCase()}</span>
            <span className="b-log-src">{l.src}</span>
            <span className="b-log-msg">{l.msg}</span>
          </div>
        ))}
      </div>
    </>
  );
}
