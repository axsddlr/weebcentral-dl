import { useState } from 'react';

const TOGGLE_FIELDS: Array<[string, string, string]> = [
  ['skipExisting', 'Skip existing chapters', 'Avoid re-downloading anything already on disk.'],
  ['cbz',          'Pack as CBZ',            'Bundle pages into a single CBZ archive per chapter.'],
  ['autoCheck',    'Auto-check tracked series', 'Run the tracker on a schedule, using the interval above.'],
  ['notifs',       'Desktop notifications',  'Receive a notification when new chapters are detected.'],
];

export function Settings() {
  const [tab, setTab] = useState('general');
  const [toggles, setToggles] = useState<Record<string, boolean>>({ skipExisting: true, autoCheck: false, cbz: true, parallel: true, notifs: false });

  const flip = (k: string) => setToggles((t) => ({ ...t, [k]: !t[k] }));

  return (
    <>
      <div className="b-head">
        <div>
          <div className="b-eyebrow">№ 047 · CONFIGURATION · v2.1</div>
          <div className="b-title">Settings</div>
          <div className="b-deck">Tune behaviour. Most defaults are sensible; adjust paths and the auto-check interval for your setup.</div>
        </div>
        <div className="b-headact">
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="b-btn">
              <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><path d="M21 12a9 9 0 1 1-3-6.7L21 8M21 3v5h-5"/></svg>
              Reset
            </button>
            <button className="b-btn b-btn-primary">
              <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><path d="m5 12 5 5L20 7"/></svg>
              Save changes
            </button>
          </div>
        </div>
      </div>

      <div className="b-settings">
        <div className="b-settings-tabs">
          {['general', 'download', 'tracker', 'advanced'].map((t) => (
            <div key={t} className={'b-settings-tab' + (tab === t ? ' is-active' : '')} onClick={() => setTab(t)}>
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </div>
          ))}
        </div>

        <div>
          <div className="b-setting">
            <div>
              <div className="b-set-title">Output directory</div>
              <div className="b-set-sub">Where downloaded CBZ/ZIP archives land. Docker users mount this folder into the container.</div>
            </div>
            <input className="b-input" defaultValue="./manga_downloads" />
          </div>
          <div className="b-setting">
            <div>
              <div className="b-set-title">Library paths</div>
              <div className="b-set-sub">Additional folders the Library reader will scan. Use container paths when running in Docker.</div>
            </div>
            <input className="b-input" defaultValue="D:/manga/collection" />
          </div>
          <div className="b-setting">
            <div>
              <div className="b-set-title">Auto-check interval</div>
              <div className="b-set-sub">How frequently the tracker scans WeebCentral for new chapters. Set to 0 to disable.</div>
            </div>
            <input className="b-input" defaultValue="1h 30m" />
          </div>
          <div className="b-setting">
            <div>
              <div className="b-set-title">Concurrent downloads</div>
              <div className="b-set-sub">How many chapters download in parallel. Higher values use more bandwidth.</div>
            </div>
            <input className="b-input" defaultValue="3" />
          </div>
          {TOGGLE_FIELDS.map(([k, label, sub]) => (
            <div className="b-setting" key={k}>
              <div>
                <div className="b-set-title">{label}</div>
                <div className="b-set-sub">{sub}</div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 10 }}>
                <span style={{ font: '600 10.5px/1 "JetBrains Mono",monospace', color: 'var(--dim)', letterSpacing: '0.1em' }}>{toggles[k] ? 'ENABLED' : 'DISABLED'}</span>
                <div className={'b-toggle' + (toggles[k] ? ' on' : '')} onClick={() => flip(k)} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
