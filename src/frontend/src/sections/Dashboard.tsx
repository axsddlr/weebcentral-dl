import { useState, useEffect } from 'react';
import * as api from '@/services/api';

export function Dashboard() {
  const [stats, setStats] = useState<api.DashboardStats | null>(null);
  const [recent, setRecent] = useState<api.RecentChapter[]>([]);
  const [queue, setQueue] = useState<api.QueueState | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.getStats().catch(() => null),
      api.getRecentChapters(5).catch(() => []),
      api.getQueue().catch(() => null),
    ]).then(([s, r, q]) => {
      setStats(s);
      setRecent(r as api.RecentChapter[]);
      setQueue(q);
      setLoading(false);
    });
  }, []);

  const handleCheckNow = () => {
    api.checkTracked().catch(() => {});
  };

  return (
    <>
      <div className="b-head">
        <div>
          <div className="b-eyebrow">DASHBOARD</div>
          <div className="b-title">State of the <span className="accent">Library</span>.</div>
          <div className="b-deck">A morning briefing — what's new across your tracked series, what's downloading right now, and what awaits your attention.</div>
        </div>
        <div className="b-headact">
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="b-btn" onClick={() => window.location.reload()}>
              <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><path d="M21 12a9 9 0 1 1-3-6.7L21 8M21 3v5h-5"/></svg>
              Refresh
            </button>
            <button className="b-btn b-btn-primary" onClick={handleCheckNow}>
              <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="currentColor"><path d="M7 4v16l13-8z"/></svg>
              Check Now
            </button>
          </div>
        </div>
      </div>

      <div className="b-figures">
        <div className="b-figure">
          <div className="b-fig-label"><span>TOTAL SERIES</span></div>
          <div className="b-fig-num">{loading ? '—' : (stats?.totalSeries ?? '—')}</div>
          <div className="b-fig-foot"><span>IN LIBRARY</span></div>
        </div>
        <div className="b-figure">
          <div className="b-fig-label"><span>CHAPTERS</span></div>
          <div className="b-fig-num">{loading ? '—' : (stats?.totalChapters?.toLocaleString() ?? '—')}</div>
          <div className="b-fig-foot"><span>INDEXED</span></div>
        </div>
        <div className="b-figure">
          <div className="b-fig-label"><span>STORAGE</span><span>SSD</span></div>
          <div className="b-fig-num" style={{ fontSize: 28 }}>{loading ? '—' : (stats?.storageUsed ?? '—')}</div>
          <div className="b-fig-foot"><span>USED</span></div>
        </div>
        <div className="b-figure">
          <div className="b-fig-label">
            <span>QUEUE</span>
            <span style={{ color: queue?.isRunning ? 'var(--crimson)' : 'var(--dim)' }}>
              {queue?.isRunning ? '● ACTIVE' : '○ IDLE'}
            </span>
          </div>
          <div className="b-fig-num">
            {loading ? '—' : (queue?.tasks.filter(t => t.status === 'downloading').length ?? 0)}
            <span className="unit">/{queue?.totalTasks ?? 0}</span>
          </div>
          <div className="b-fig-foot">
            <span>{queue?.completedTasks ?? 0} DONE · {queue?.failedTasks ?? 0} FAILED</span>
          </div>
        </div>
      </div>

      <div className="b-section">
        <div className="b-sec-head">
          <span className="b-sec-num">01 /</span>
          <span className="b-sec-title">Recently Downloaded</span>
          <span className="b-sec-line" />
          <span className="b-sec-meta">{recent.length} CHAPTERS</span>
        </div>
        {loading && (
          <div style={{ color: 'var(--dim)', fontFamily: '"JetBrains Mono",monospace', fontSize: 11 }}>LOADING…</div>
        )}
        {!loading && recent.length === 0 && (
          <div style={{ color: 'var(--dim)', fontFamily: '"JetBrains Mono",monospace', fontSize: 11 }}>NO RECENT DOWNLOADS</div>
        )}
        {!loading && recent.map((ch, i) => (
          <div className="b-new-item" key={ch.id}>
            <div style={{ minWidth: 0 }}>
              <div className="b-new-title">
                <span className="b-new-num">{String(i + 1).padStart(2, '0')}</span>
                {ch.series_title}
              </div>
              <div className="b-new-sub">CH.{ch.number} · {ch.totalPages} PAGES</div>
            </div>
            <div className="b-new-badge" style={{ fontSize: 12 }}>
              #{ch.number}<span className="sm">CH</span>
            </div>
          </div>
        ))}
      </div>

      {queue && queue.tasks.filter(t => t.status === 'downloading' || t.status === 'pending').length > 0 && (
        <div className="b-section">
          <div className="b-sec-head">
            <span className="b-sec-num">02 /</span>
            <span className="b-sec-title">Active Downloads</span>
            <span className="b-sec-line" />
            <span className="b-sec-meta">{queue.tasks.filter(t => t.status === 'downloading').length} ACTIVE</span>
          </div>
          {queue.tasks.filter(t => t.status === 'downloading' || t.status === 'pending').slice(0, 5).map((task) => (
            <div className="b-new-item" key={task.id}>
              <div style={{ minWidth: 0, flex: 1 }}>
                <div className="b-new-title">{task.mangaTitle} · CH.{task.chapterNumber}</div>
                <div className="b-progress" style={{ marginTop: 6 }}>
                  <div className="b-progress-fill" style={{ width: `${task.progress * 100}%` }} />
                </div>
                <div className="b-new-sub" style={{ marginTop: 4 }}>
                  {task.downloadedPages}/{task.totalPages} PAGES · {task.status.toUpperCase()}
                </div>
              </div>
              <div className="b-new-badge">
                {Math.round(task.progress * 100)}<span className="sm">%</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
