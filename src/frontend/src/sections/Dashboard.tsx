import { Cover } from '@/components/Cover';
import { SERIES, ACTIVITY_14D, NEW_AVAILABLE, seriesById } from '@/lib/mockData';

export function Dashboard() {
  const resume = [SERIES[0], SERIES[2], SERIES[5], SERIES[7], SERIES[10]];
  const newCh = NEW_AVAILABLE.slice(0, 5);
  const peak = Math.max(...ACTIVITY_14D);
  const storageItems = [SERIES[5], SERIES[10], SERIES[7], SERIES[2], SERIES[6], SERIES[3]];
  const maxGB = 5.1;

  return (
    <>
      <div className="b-head">
        <div>
          <div className="b-eyebrow">№ 047 · DASHBOARD · 25.MAY.2026</div>
          <div className="b-title">State of the <span className="accent">Library</span>.</div>
          <div className="b-deck">A morning briefing — what's new across your tracked series, what's downloading right now, and what awaits your attention.</div>
        </div>
        <div className="b-headact">
          <div className="b-byline">EDITED BY <b>SYSTEM</b> · 14:32 UTC</div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="b-btn">
              <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><path d="M21 12a9 9 0 1 1-3-6.7L21 8M21 3v5h-5"/></svg>
              Sync
            </button>
            <button className="b-btn b-btn-primary">
              <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="currentColor"><path d="M7 4v16l13-8z"/></svg>
              Check Now
            </button>
          </div>
        </div>
      </div>

      <div className="b-figures">
        <div className="b-figure">
          <div className="b-fig-label"><span>TOTAL SERIES</span><span style={{ color: '#10B981' }}>+3 ▲</span></div>
          <div className="b-fig-num">59</div>
          <div className="b-fig-foot"><span>IN LIBRARY</span><span className="b-fig-delta">+3 / 30d</span></div>
        </div>
        <div className="b-figure">
          <div className="b-fig-label"><span>CHAPTERS</span><span style={{ color: '#10B981' }}>+128 ▲</span></div>
          <div className="b-fig-num">10,774</div>
          <div className="b-fig-foot"><span>INDEXED</span><span className="b-fig-delta">+128 today</span></div>
        </div>
        <div className="b-figure">
          <div className="b-fig-label"><span>STORAGE</span><span>SSD</span></div>
          <div className="b-fig-num">80.2<span className="unit">GB</span></div>
          <div className="b-fig-foot"><span>OF 500 GB</span><span className="b-fig-delta">16%</span></div>
        </div>
        <div className="b-figure">
          <div className="b-fig-label"><span>QUEUE</span><span style={{ color: 'var(--crimson)' }}>● ACTIVE</span></div>
          <div className="b-fig-num">02<span className="unit">/05</span></div>
          <div className="b-fig-foot"><span>2 ACTIVE · 3 PENDING</span><span className="b-fig-delta warn">2.4 MB/s</span></div>
        </div>
      </div>

      <div className="b-section">
        <div className="b-sec-head">
          <span className="b-sec-num">01 /</span>
          <span className="b-sec-title">Continue Reading</span>
          <span className="b-sec-line" />
          <span className="b-sec-meta">{resume.length} OPEN VOLUMES</span>
        </div>
        <div className="b-resume">
          {resume.map((s) => (
            <div className="b-resume-item" key={s.id}>
              <Cover series={s} height={190} />
              <div>
                <div className="b-resume-title">{s.title}</div>
                <div className="b-resume-author">BY {s.author.toUpperCase()}</div>
                <div className="b-resume-meta"><span>CH.{s.read}/{s.ch}</span><span>{s.lastRead.toUpperCase()}</span></div>
                <div className="b-progress" style={{ marginTop: 6 }}><div className="b-progress-fill" style={{ width: `${s.progress * 100}%` }} /></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="b-editorial">
        <div className="b-col">
          <div className="b-col-head">
            <div className="b-col-title">New Chapters Filed</div>
            <span className="b-col-meta">02 /</span>
          </div>
          {newCh.map((n, i) => {
            const s = seriesById[n.series];
            return (
              <div className="b-new-item" key={n.series}>
                <div style={{ minWidth: 0 }}>
                  <div className="b-new-title"><span className="b-new-num">{String(i + 1).padStart(2, '0')}</span>{s.title}</div>
                  <div className="b-new-sub">CH.{n.latest} · {n.since.toUpperCase()}</div>
                </div>
                <div className="b-new-badge">+{n.count}<span className="sm">UNREAD</span></div>
              </div>
            );
          })}
        </div>

        <div className="b-col">
          <div className="b-col-head">
            <div className="b-col-title">Activity · 14 days</div>
            <span className="b-col-meta">03 / PEAK {peak}</span>
          </div>
          <div className="b-spark">
            {ACTIVITY_14D.map((v, i) => (
              <div key={i} className={'b-spark-bar' + (v === peak ? ' peak' : '')} style={{ height: `${(v / peak) * 100}%` }} />
            ))}
          </div>
          <div className="b-spark-axis"><span>14D AGO</span><span>7D</span><span>TODAY</span></div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 12, marginTop: 8, paddingTop: 12, borderTop: '1px dashed var(--line)' }}>
            <div>
              <div style={{ font: '600 9.5px/1 "JetBrains Mono",monospace', color: 'var(--dim)', letterSpacing: '0.15em' }}>STREAK</div>
              <div style={{ font: '800 22px/1 "Bricolage Grotesque",sans-serif', color: 'var(--cream)', marginTop: 4, letterSpacing: '-0.03em' }}>14<span style={{ fontSize: '.5em', color: 'var(--crimson)', marginLeft: 3 }}>d</span></div>
            </div>
            <div>
              <div style={{ font: '600 9.5px/1 "JetBrains Mono",monospace', color: 'var(--dim)', letterSpacing: '0.15em' }}>AVG / DAY</div>
              <div style={{ font: '800 22px/1 "Bricolage Grotesque",sans-serif', color: 'var(--cream)', marginTop: 4, letterSpacing: '-0.03em' }}>32.4</div>
            </div>
            <div>
              <div style={{ font: '600 9.5px/1 "JetBrains Mono",monospace', color: 'var(--dim)', letterSpacing: '0.15em' }}>UNREAD</div>
              <div style={{ font: '800 22px/1 "Bricolage Grotesque",sans-serif', color: 'var(--crimson)', marginTop: 4, letterSpacing: '-0.03em' }}>1,847</div>
            </div>
          </div>
        </div>

        <div className="b-col">
          <div className="b-col-head">
            <div className="b-col-title">Storage by Series</div>
            <span className="b-col-meta">04 / 80.2 GB</span>
          </div>
          {storageItems.map((s) => {
            const gb = parseFloat(s.size);
            return (
              <div className="b-storage-row" key={s.id}>
                <div style={{ minWidth: 0 }}>
                  <div className="name">{s.title}</div>
                  <div className="bar" style={{ width: `${(gb / maxGB) * 100}%` }} />
                </div>
                <div className="val">{s.size}</div>
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
}
