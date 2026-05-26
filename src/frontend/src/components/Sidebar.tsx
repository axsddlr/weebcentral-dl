import type { View } from '@/types';

interface SidebarProps {
  currentView: View;
  onViewChange: (view: View) => void;
}

const NAV: Array<{ id: View; label: string; icon: string; badge?: string }> = [
  { id: 'dashboard', label: 'Dashboard',      icon: 'grid' },
  { id: 'search',    label: 'Search',         icon: 'search' },
  { id: 'tracked',   label: 'Tracked',        icon: 'bookmark', badge: '55' },
  { id: 'queue',     label: 'Download Queue', icon: 'download', badge: '2' },
  { id: 'library',   label: 'Library',        icon: 'library' },
  { id: 'reader',    label: 'Reader',         icon: 'book' },
  { id: 'settings',  label: 'Settings',       icon: 'settings' },
  { id: 'logs',      label: 'Logs',           icon: 'logs' },
];

function Icon({ name }: { name: string }) {
  const s = { width: 14, height: 14 } as const;
  const p = { viewBox: '0 0 24 24', style: s, fill: 'none', stroke: 'currentColor', strokeWidth: 1.6 } as const;
  switch (name) {
    case 'grid':     return <svg {...p}><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>;
    case 'search':   return <svg {...p}><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>;
    case 'bookmark': return <svg {...p}><path d="M6 3h12v18l-6-4-6 4z"/></svg>;
    case 'download': return <svg {...p}><path d="M12 3v13m0 0 5-5m-5 5-5-5M4 21h16"/></svg>;
    case 'library':  return <svg {...p}><path d="M4 4v16M9 4v16M14 5l5-1 2 16-5 1z"/></svg>;
    case 'book':     return <svg {...p}><path d="M4 5a2 2 0 0 1 2-2h12v18H6a2 2 0 0 1-2-2zM8 7h6M8 11h6"/></svg>;
    case 'settings': return <svg {...p}><circle cx="12" cy="12" r="3"/><path d="M19 12a7 7 0 0 0-.1-1.2l2-1.6-2-3.4-2.4.9a7 7 0 0 0-2-1.2L14 3h-4l-.5 2.5a7 7 0 0 0-2 1.2l-2.4-.9-2 3.4 2 1.6A7 7 0 0 0 5 12c0 .4 0 .8.1 1.2l-2 1.6 2 3.4 2.4-.9a7 7 0 0 0 2 1.2L10 21h4l.5-2.5a7 7 0 0 0 2-1.2l2.4.9 2-3.4-2-1.6c.1-.4.1-.8.1-1.2Z"/></svg>;
    case 'logs':     return <svg {...p}><path d="M5 4h14v16H5zM9 8h6M9 12h6M9 16h4"/></svg>;
    default:         return null;
  }
}

export function Sidebar({ currentView, onViewChange }: SidebarProps) {
  return (
    <aside className="b-side">
      <div className="b-brand">
        <div className="b-brand-mark">W</div>
        <div className="b-brand-text">
          <div className="b-brand-name">WeebCentral</div>
          <div className="b-brand-sub">DL // PRESS</div>
        </div>
      </div>

      <nav className="b-nav">
        <div className="b-nav-section">// NAVIGATION</div>
        {NAV.map((n, i) => (
          <div
            key={n.id}
            className={'b-nav-item' + (currentView === n.id ? ' is-active' : '')}
            onClick={() => onViewChange(n.id)}
          >
            <span className="b-nav-num">{String(i + 1).padStart(2, '0')}</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Icon name={n.icon} />
              {n.label}
            </span>
            {n.badge && <span className="b-nav-badge">{n.badge}</span>}
          </div>
        ))}
      </nav>

      <div className="b-side-foot">
        <div className="b-status">
          <div className="b-status-dot" />
          <div className="b-status-text">
            <div className="b-status-title">SYSTEM ONLINE</div>
            <div className="b-status-sub">2 active · 4.2 MB/s</div>
          </div>
        </div>
      </div>
    </aside>
  );
}
