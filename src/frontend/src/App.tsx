import { useState } from 'react';
import { Sidebar } from '@/components/Sidebar';
import { Dashboard } from '@/sections/Dashboard';
import { Search } from '@/sections/Search';
import { Queue } from '@/sections/Queue';
import { Library } from '@/sections/Library';
import { Reader } from '@/sections/Reader';
import { Settings } from '@/sections/Settings';
import { Logs } from '@/sections/Logs';
import { Tracked } from '@/sections/Tracked';
import type { View } from '@/types';

type Route = View;

function getNow() {
  const d = new Date();
  return d.toLocaleDateString('en-US', { weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' }).toUpperCase();
}

function App() {
  const [route, setRoute] = useState<Route>('dashboard');
  const isReader = route === 'reader';

  const screen: Record<Route, JSX.Element> = {
    dashboard: <Dashboard />,
    search:    <Search />,
    tracked:   <Tracked />,
    queue:     <Queue />,
    library:   <Library onViewChange={setRoute} />,
    reader:    <Reader onViewChange={setRoute} />,
    settings:  <Settings />,
    logs:      <Logs />,
  };

  return (
    <div className="b-root">
      <Sidebar currentView={route} onViewChange={setRoute} />
      <div className="b-stage">
        {!isReader && (
          <div className="b-mast-bar">
            <div className="b-issue">
              <span>VOL <b>II</b></span>
              <span className="pipe">·</span>
              <span>№ <b>047</b></span>
              <span className="pipe">·</span>
              <span><b>{getNow()}</b></span>
              <span className="pipe">·</span>
              <span className="quote">"All the manga that's fit to read."</span>
            </div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <div className="b-search" style={{ width: 200, padding: '6px 12px', fontSize: 11 }}>
                <svg viewBox="0 0 24 24" style={{ width: 12, height: 12 }} fill="none" stroke="currentColor" strokeWidth={1.6}><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
                <input placeholder="Quick search…" />
              </div>
              <div style={{ width: 30, height: 30, borderRadius: 99, background: 'linear-gradient(135deg, var(--crimson), var(--crimson-2))', color: 'var(--cream)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: 11, boxShadow: '0 0 0 2px var(--ink), 0 0 12px rgba(220,38,38,.4)' }}>A</div>
            </div>
          </div>
        )}
        <main className="b-content" style={isReader ? { padding: 0, position: 'relative' } : {}}>
          {screen[route]}
        </main>
      </div>
    </div>
  );
}

export default App;
