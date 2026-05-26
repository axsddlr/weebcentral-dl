import { useState, useEffect } from 'react';
import * as api from '@/services/api';

type Level = 'all' | 'info' | 'debug' | 'warn' | 'error';

export function Logs() {
  const [logs, setLogs] = useState<api.LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [level, setLevel] = useState<Level>('all');
  const [search, setSearch] = useState('');

  useEffect(() => {
    api.getLogs()
      .then(setLogs)
      .catch(() => {})
      .finally(() => setLoading(false));
    const interval = setInterval(() => {
      api.getLogs().then(setLogs).catch(() => {});
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const counts = {
    info:  logs.filter(l => l.level === 'info').length,
    debug: logs.filter(l => l.level === 'debug').length,
    warn:  logs.filter(l => l.level === 'warn').length,
    error: logs.filter(l => l.level === 'error').length,
  };

  const filtered = logs.filter((l) => {
    if (level !== 'all' && l.level !== level) return false;
    if (search && !l.message.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <>
      <div className="b-head">
        <div>
          <div className="b-eyebrow">DISPATCHES · LIVE</div>
          <div className="b-title">Logs</div>
          <div className="b-deck">The activity stream. Filter by level, search within messages, export the whole thing if you're debugging.</div>
        </div>
        <div className="b-headact">
          <div className="b-byline"><b>{logs.length}</b> ENTRIES · {counts.error} ERRORS</div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="b-btn" onClick={() => {
              const blob = new Blob([logs.map(l => `${l.timestamp} [${l.level.toUpperCase()}] ${l.source ?? ''} ${l.message}`).join('\n')], { type: 'text/plain' });
              const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'weebcentral.log'; a.click();
            }}>
              <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><path d="M12 3v13m0 0 5-5m-5 5-5-5M4 21h16"/></svg>
              Export
            </button>
            <button className="b-btn b-btn-primary" onClick={() => { api.getLogs().then(setLogs).catch(() => {}); }}>
              <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><path d="M21 12a9 9 0 1 1-3-6.7L21 8M21 3v5h-5"/></svg>
              Refresh
            </button>
          </div>
        </div>
      </div>

      <div className="b-figures">
        <div className="b-figure"><div className="b-fig-label"><span>TOTAL</span></div><div className="b-fig-num">{logs.length}</div></div>
        <div className="b-figure"><div className="b-fig-label"><span>INFO</span></div><div className="b-fig-num" style={{ color: '#10B981' }}>{counts.info}</div></div>
        <div className="b-figure"><div className="b-fig-label"><span>DEBUG</span></div><div className="b-fig-num">{counts.debug}</div></div>
        <div className="b-figure"><div className="b-fig-label"><span>WARN</span></div><div className="b-fig-num" style={{ color: '#F59E0B' }}>{counts.warn}</div></div>
        <div className="b-figure"><div className="b-fig-label"><span>ERROR</span></div><div className="b-fig-num" style={{ color: 'var(--crimson)' }}>{counts.error}</div></div>
      </div>

      <div className="b-toolbar">
        {(['all','info','debug','warn','error'] as Level[]).map((l) => (
          <div key={l} className={'b-pill' + (level === l ? ' is-active' : '')} onClick={() => setLevel(l)}>
            {l.charAt(0).toUpperCase() + l.slice(1)}
          </div>
        ))}
        <div className="b-search" style={{ maxWidth: 280, marginLeft: 'auto' }}>
          <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
          <input placeholder="Search dispatches…" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
      </div>

      <div className="b-logs">
        <div className="b-log-row" style={{ background: 'rgba(245,240,225,.03)', color: 'var(--dim)' }}>
          <span>TIMESTAMP</span><span>LEVEL</span><span>SOURCE</span><span>MESSAGE</span>
        </div>
        {loading && (
          <div className="b-log-row"><span style={{ gridColumn: '1 / -1', color: 'var(--dim)' }}>LOADING…</span></div>
        )}
        {!loading && filtered.length === 0 && (
          <div className="b-log-row"><span style={{ gridColumn: '1 / -1', color: 'var(--dim)' }}>NO ENTRIES</span></div>
        )}
        {filtered.slice(-200).map((l) => (
          <div className="b-log-row" key={l.id}>
            <span className="b-log-time">{l.timestamp.split('T')[1]?.split('.')[0] ?? l.timestamp}</span>
            <span className={'b-log-lvl ' + l.level}>{l.level.toUpperCase()}</span>
            <span className="b-log-src">{l.source ?? '—'}</span>
            <span className="b-log-msg">{l.message}</span>
          </div>
        ))}
      </div>
    </>
  );
}
