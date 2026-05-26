import { Cover } from '@/components/Cover';
import { QUEUE_SAMPLE, seriesById } from '@/lib/mockData';

export function Queue() {
  const active = QUEUE_SAMPLE.filter((q) => q.status === 'downloading');
  const pending = QUEUE_SAMPLE.filter((q) => q.status === 'pending');

  return (
    <>
      <div className="b-head">
        <div>
          <div className="b-eyebrow">№ 047 · TRANSMISSION IN PROGRESS</div>
          <div className="b-title">Queue</div>
          <div className="b-deck">Two chapters are downloading. Three more are queued behind them. Average throughput: 2.4 megabytes per second.</div>
        </div>
        <div className="b-headact">
          <div className="b-byline">UPTIME <b>14h 22m</b></div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="b-btn">
              <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/></svg>
              Clear done
            </button>
            <button className="b-btn b-btn-primary">
              <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
              Pause all
            </button>
          </div>
        </div>
      </div>

      <div className="b-figures">
        <div className="b-figure"><div className="b-fig-label"><span>TOTAL</span></div><div className="b-fig-num">{QUEUE_SAMPLE.length}</div></div>
        <div className="b-figure"><div className="b-fig-label"><span>DOWNLOADING</span></div><div className="b-fig-num" style={{ color: 'var(--crimson)' }}>{active.length}</div></div>
        <div className="b-figure"><div className="b-fig-label"><span>PENDING</span></div><div className="b-fig-num">{pending.length}</div></div>
        <div className="b-figure"><div className="b-fig-label"><span>SPEED</span></div><div className="b-fig-num">4.2<span className="unit">MB/s</span></div></div>
      </div>

      <div className="b-section">
        <div className="b-sec-head">
          <span className="b-sec-num">01 /</span>
          <span className="b-sec-title">Currently downloading</span>
          <span className="b-sec-line" />
          <span className="b-sec-meta">{active.length} ACTIVE</span>
        </div>
        {active.map((q) => {
          const s = seriesById[q.series];
          return (
            <div className="b-queue-item active" key={q.id}>
              <Cover series={s} height={86} showTitle={false} showBadge={false} />
              <div className="b-queue-body">
                <div className="b-queue-row">
                  <div>
                    <div className="b-queue-name">{s.title}<span className="ct">CH.{q.ch}</span></div>
                    <div className="b-queue-stats">
                      <span>PAGE <b>{q.page}/{q.pages}</b></span>
                      <span>{q.speed}</span>
                      <span>ETA <b>{q.eta}</b></span>
                    </div>
                  </div>
                  <div className="b-queue-pct">{Math.round(q.progress * 100)}<span style={{ fontSize: '.55em', color: 'var(--dim)', letterSpacing: '0.05em' }}>%</span></div>
                </div>
                <div className="b-progress" style={{ height: 3 }}><div className="b-progress-fill" style={{ width: `${q.progress * 100}%` }} /></div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="b-section">
        <div className="b-sec-head">
          <span className="b-sec-num">02 /</span>
          <span className="b-sec-title">In the wings</span>
          <span className="b-sec-line" />
          <span className="b-sec-meta">{pending.length} PENDING</span>
        </div>
        <div style={{ borderTop: '1px solid var(--line)' }}>
          {pending.map((q, i) => {
            const s = seriesById[q.series];
            return (
              <div className="b-new-item" key={q.id} style={{ padding: '12px 0', borderBottom: '1px solid var(--line)' }}>
                <div>
                  <div className="b-new-title"><span className="b-new-num">{String(i + 1).padStart(2, '0')}</span>{s.title} · CH.{q.ch}</div>
                  <div className="b-new-sub">{q.pages} PAGES · POSITION #{i + 1}</div>
                </div>
                <div className="b-new-badge" style={{ background: 'rgba(245,240,225,.04)', color: 'var(--dim)', borderColor: 'var(--line)' }}>#{i + 1}</div>
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
}
