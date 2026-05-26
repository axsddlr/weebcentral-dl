import { useState, useEffect } from 'react';
import * as api from '@/services/api';

export function Settings() {
  const [config, setConfig] = useState<api.AppConfig | null>(null);
  const [tab, setTab] = useState('general');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.getConfig().then(setConfig).catch(() => {});
  }, []);

  const update = (key: keyof api.AppConfig, value: api.AppConfig[keyof api.AppConfig]) => {
    if (!config) return;
    setConfig({ ...config, [key]: value });
  };

  const handleSave = () => {
    if (!config) return;
    setSaving(true);
    api.updateConfig(config)
      .then(setConfig)
      .then(() => { setSaved(true); setTimeout(() => setSaved(false), 2000); })
      .catch(() => {})
      .finally(() => setSaving(false));
  };

  const handleReset = () => {
    api.resetConfig().then(setConfig).catch(() => {});
  };

  return (
    <>
      <div className="b-head">
        <div>
          <div className="b-eyebrow">CONFIGURATION · v2.1</div>
          <div className="b-title">Settings</div>
          <div className="b-deck">Tune behaviour. Most defaults are sensible; adjust paths and the auto-check interval for your setup.</div>
        </div>
        <div className="b-headact">
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="b-btn" onClick={handleReset}>
              <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><path d="M21 12a9 9 0 1 1-3-6.7L21 8M21 3v5h-5"/></svg>
              Reset
            </button>
            <button className="b-btn b-btn-primary" onClick={handleSave} disabled={saving || !config}>
              <svg viewBox="0 0 24 24" style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth={1.6}><path d="m5 12 5 5L20 7"/></svg>
              {saved ? 'Saved!' : saving ? 'Saving…' : 'Save changes'}
            </button>
          </div>
        </div>
      </div>

      {!config && (
        <div style={{ color: 'var(--dim)', fontFamily: '"JetBrains Mono",monospace', fontSize: 11, padding: '20px 0' }}>LOADING…</div>
      )}

      {config && (
        <div className="b-settings">
          <div className="b-settings-tabs">
            {['general', 'download', 'tracker', 'advanced'].map((t) => (
              <div key={t} className={'b-settings-tab' + (tab === t ? ' is-active' : '')} onClick={() => setTab(t)}>
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </div>
            ))}
          </div>

          <div>
            {tab === 'general' && <>
              <div className="b-setting">
                <div>
                  <div className="b-set-title">Output directory</div>
                  <div className="b-set-sub">Where downloaded CBZ/ZIP archives land.</div>
                </div>
                <input className="b-input" value={config.outputDir} onChange={(e) => update('outputDir', e.target.value)} />
              </div>
              <div className="b-setting">
                <div>
                  <div className="b-set-title">Library paths</div>
                  <div className="b-set-sub">Additional folders the Library reader will scan. One per line.</div>
                </div>
                <input className="b-input" value={config.libraryPaths.join(', ')} onChange={(e) => update('libraryPaths', e.target.value.split(',').map(s => s.trim()).filter(Boolean))} />
              </div>
            </>}

            {tab === 'download' && <>
              <div className="b-setting">
                <div>
                  <div className="b-set-title">Parallel workers</div>
                  <div className="b-set-sub">How many pages download in parallel per chapter.</div>
                </div>
                <input className="b-input" type="number" value={config.parallelWorkers} onChange={(e) => update('parallelWorkers', parseInt(e.target.value))} />
              </div>
              <div className="b-setting">
                <div>
                  <div className="b-set-title">Max retries</div>
                  <div className="b-set-sub">How many times to retry a failed page download.</div>
                </div>
                <input className="b-input" type="number" value={config.maxRetries} onChange={(e) => update('maxRetries', parseInt(e.target.value))} />
              </div>
              <div className="b-setting">
                <div>
                  <div className="b-set-title">Pack as CBZ</div>
                  <div className="b-set-sub">Bundle pages into a single CBZ archive per chapter.</div>
                </div>
                <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 10 }}>
                  <span style={{ font: '600 10.5px/1 "JetBrains Mono",monospace', color: 'var(--dim)', letterSpacing: '0.1em' }}>{!config.zip ? 'CBZ' : 'ZIP'}</span>
                  <div className={'b-toggle' + (!config.zip ? ' on' : '')} onClick={() => update('zip', !config.zip)} />
                </div>
              </div>
              <div className="b-setting">
                <div>
                  <div className="b-set-title">Skip existing chapters</div>
                  <div className="b-set-sub">Avoid re-downloading anything already on disk.</div>
                </div>
                <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 10 }}>
                  <span style={{ font: '600 10.5px/1 "JetBrains Mono",monospace', color: 'var(--dim)', letterSpacing: '0.1em' }}>{config.latest ? 'LATEST ONLY' : 'ALL'}</span>
                  <div className={'b-toggle' + (config.latest ? ' on' : '')} onClick={() => update('latest', !config.latest)} />
                </div>
              </div>
            </>}

            {tab === 'tracker' && <>
              <div className="b-setting">
                <div>
                  <div className="b-set-title">Auto-check interval</div>
                  <div className="b-set-sub">Minutes between automatic checks. 0 to disable.</div>
                </div>
                <input className="b-input" type="number" value={config.checkInterval} onChange={(e) => update('checkInterval', parseInt(e.target.value))} />
              </div>
            </>}

            {tab === 'advanced' && <>
              <div className="b-setting">
                <div>
                  <div className="b-set-title">Rate limit chapters</div>
                  <div className="b-set-sub">Chapters between rate limit pauses.</div>
                </div>
                <input className="b-input" type="number" value={config.rlc} onChange={(e) => update('rlc', parseInt(e.target.value))} />
              </div>
              <div className="b-setting">
                <div>
                  <div className="b-set-title">Max sleep (seconds)</div>
                  <div className="b-set-sub">Maximum backoff time for rate limiting and retries.</div>
                </div>
                <input className="b-input" type="number" value={config.maxSleep} onChange={(e) => update('maxSleep', parseInt(e.target.value))} />
              </div>
              <div className="b-setting">
                <div>
                  <div className="b-set-title">Verbose logging</div>
                  <div className="b-set-sub">Enable debug-level output in logs.</div>
                </div>
                <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 10 }}>
                  <span style={{ font: '600 10.5px/1 "JetBrains Mono",monospace', color: 'var(--dim)', letterSpacing: '0.1em' }}>{config.verbose ? 'ENABLED' : 'DISABLED'}</span>
                  <div className={'b-toggle' + (config.verbose ? ' on' : '')} onClick={() => update('verbose', !config.verbose)} />
                </div>
              </div>
              <div className="b-setting">
                <div>
                  <div className="b-set-title">ComicInfo.xml</div>
                  <div className="b-set-sub">Embed ComicInfo.xml metadata in each CBZ archive.</div>
                </div>
                <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 10 }}>
                  <span style={{ font: '600 10.5px/1 "JetBrains Mono",monospace', color: 'var(--dim)', letterSpacing: '0.1em' }}>{config.comicinfo ? 'ENABLED' : 'DISABLED'}</span>
                  <div className={'b-toggle' + (config.comicinfo ? ' on' : '')} onClick={() => update('comicinfo', !config.comicinfo)} />
                </div>
              </div>
            </>}
          </div>
        </div>
      )}
    </>
  );
}
