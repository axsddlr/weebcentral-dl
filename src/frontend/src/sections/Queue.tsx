import { useState, useEffect } from 'react';
import * as api from '@/services/api';

export function Queue() {
  const [queue, setQueue] = useState<api.QueueState | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchQueue = () => {
    api.getQueue()
      .then(setQueue)
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchQueue();
    const interval = setInterval(fetchQueue, 3000);
    return () => clearInterval(interval);
  }, []);

  const active = queue?.tasks.filter((q) => q.status === 'downloading') ?? [];
  const pending = queue?.tasks.filter((q) => q.status === 'pending') ?? [];
  const failed = queue?.tasks.filter((q) => q.status === 'failed') ?? [];

  return (
    <>
      <div className="b-head">
        <div>
          <div className="b-eyebrow">TRANSMISSION IN PROGRESS</div>
          <div className="b-title">Queue</div>
          <div className="b-deck">
            {active.length > 0
              ? `${active.length} chapter${active.length > 1 ? 's' : ''} downloading. ${pending.length} queued.`
              : pending.length > 0 ? `${pending.length} chapters queued.` : 'Queue is idle.'}
          </div>
        </div>
        <div className="b-headact">
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="b-btn" onClick={() => { api.clearCompleted().then(fetchQueue); }}>
              <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/></svg>
              Clear done
            </button>
            {queue?.isRunning ? (
              <button className="b-btn b-btn-primary" onClick={() => { api.pauseQueue().then(fetchQueue); }}>
                <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
                Pause all
              </button>
            ) : (
              <button className="b-btn b-btn-primary" onClick={() => { api.resumeQueue().then(fetchQueue); }}>
                <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="currentColor"><path d="M7 4v16l13-8z"/></svg>
                Resume
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="b-figures">
        <div className="b-figure"><div className="b-fig-label"><span>TOTAL</span></div><div className="b-fig-num">{queue?.totalTasks ?? '—'}</div></div>
        <div className="b-figure"><div className="b-fig-label"><span>DOWNLOADING</span></div><div className="b-fig-num" style={{ color: 'var(--crimson)' }}>{active.length}</div></div>
        <div className="b-figure"><div className="b-fig-label"><span>PENDING</span></div><div className="b-fig-num">{pending.length}</div></div>
        <div className="b-figure"><div className="b-fig-label"><span>FAILED</span></div><div className="b-fig-num" style={{ color: failed.length > 0 ? 'var(--crimson)' : 'inherit' }}>{queue?.failedTasks ?? 0}</div></div>
      </div>

      {loading && (
        <div style={{ color: 'var(--dim)', fontFamily: '"JetBrains Mono",monospace', fontSize: 11, padding: '20px 0' }}>LOADING…</div>
      )}

      {!loading && active.length > 0 && (
        <div className="b-section">
          <div className="b-sec-head">
            <span className="b-sec-num">01 /</span>
            <span className="b-sec-title">Currently downloading</span>
            <span className="b-sec-line" />
            <span className="b-sec-meta">{active.length} ACTIVE</span>
          </div>
          {active.map((q) => (
            <div className="b-queue-item active" key={q.id}>
              <div className="b-queue-body" style={{ gridColumn: '1 / -1' }}>
                <div className="b-queue-row">
                  <div>
                    <div className="b-queue-name">{q.mangaTitle}<span className="ct">CH.{q.chapterNumber}</span></div>
                    <div className="b-queue-stats">
                      <span>PAGE <b>{q.downloadedPages}/{q.totalPages}</b></span>
                    </div>
                  </div>
                  <div className="b-queue-pct">{Math.round(q.progress * 100)}<span style={{ fontSize: '.55em', color: 'var(--dim)', letterSpacing: '0.05em' }}>%</span></div>
                </div>
                <div className="b-progress" style={{ height: 3 }}><div className="b-progress-fill" style={{ width: `${q.progress * 100}%` }} /></div>
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && pending.length > 0 && (
        <div className="b-section">
          <div className="b-sec-head">
            <span className="b-sec-num">02 /</span>
            <span className="b-sec-title">In the wings</span>
            <span className="b-sec-line" />
            <span className="b-sec-meta">{pending.length} PENDING</span>
          </div>
          <div style={{ borderTop: '1px solid var(--line)' }}>
            {pending.map((q, i) => (
              <div className="b-new-item" key={q.id} style={{ padding: '12px 0', borderBottom: '1px solid var(--line)' }}>
                <div>
                  <div className="b-new-title"><span className="b-new-num">{String(i + 1).padStart(2, '0')}</span>{q.mangaTitle} · CH.{q.chapterNumber}</div>
                  <div className="b-new-sub">{q.totalPages} PAGES · POSITION #{i + 1}</div>
                </div>
                <div className="b-new-badge" style={{ background: 'rgba(245,240,225,.04)', color: 'var(--dim)', borderColor: 'var(--line)' }}>#{i + 1}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {!loading && failed.length > 0 && (
        <div className="b-section">
          <div className="b-sec-head">
            <span className="b-sec-num">03 /</span>
            <span className="b-sec-title">Failed</span>
            <span className="b-sec-line" />
            <span className="b-sec-meta" style={{ color: 'var(--crimson)' }}>{failed.length} ERRORS</span>
          </div>
          <div style={{ borderTop: '1px solid var(--line)' }}>
            {failed.map((q, i) => (
              <div className="b-new-item" key={q.id} style={{ padding: '12px 0', borderBottom: '1px solid var(--line)' }}>
                <div>
                  <div className="b-new-title"><span className="b-new-num" style={{ color: 'var(--crimson)' }}>{String(i + 1).padStart(2, '0')}</span>{q.mangaTitle} · CH.{q.chapterNumber}</div>
                  <div className="b-new-sub" style={{ color: 'var(--crimson)' }}>{q.error ?? 'UNKNOWN ERROR'}</div>
                </div>
                <button className="b-btn" onClick={() => api.retryTask(q.id).then(fetchQueue)}>Retry</button>
              </div>
            ))}
          </div>
        </div>
      )}

      {!loading && (queue?.tasks ?? []).length === 0 && (
        <div style={{ color: 'var(--dim)', fontFamily: '"JetBrains Mono",monospace', fontSize: 11, padding: '40px 0', textAlign: 'center' }}>
          QUEUE EMPTY
        </div>
      )}
    </>
  );
}
