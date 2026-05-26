import type { Series } from '@/lib/mockData';

interface CoverProps {
  series: Series;
  height?: number;
  showBadge?: boolean;
  showTitle?: boolean;
}

export function Cover({ series, height = 320, showBadge = true, showTitle = true }: CoverProps) {
  const [c1, c2, c3] = series.c;
  const width = height * 0.7;

  return (
    <div style={{
      position: 'relative',
      width,
      height,
      borderRadius: 2,
      overflow: 'hidden',
      background: `linear-gradient(155deg, ${c1} 0%, ${c2} 55%, ${c3} 100%)`,
      boxShadow: '0 4px 24px rgba(0,0,0,.5), inset 0 0 0 1px rgba(255,255,255,.08)',
      flexShrink: 0,
    }}>
      <div style={{
        position: 'absolute', inset: 0,
        background: 'radial-gradient(circle at 70% 30%, rgba(255,255,255,.10), transparent 60%)',
        mixBlendMode: 'overlay',
      }} />
      <div style={{
        position: 'absolute', inset: 0,
        backgroundImage: 'repeating-linear-gradient(45deg, rgba(255,255,255,.03) 0 1px, transparent 1px 2px), repeating-linear-gradient(-45deg, rgba(0,0,0,.04) 0 1px, transparent 1px 2px)',
      }} />
      {showBadge && (
        <div style={{
          position: 'absolute', top: 8, left: 8,
          padding: '2px 6px',
          background: 'rgba(255,245,225,.92)',
          color: c3,
          fontFamily: '"JetBrains Mono", monospace',
          fontSize: Math.max(8, height * 0.028),
          fontWeight: 700,
          letterSpacing: '0.05em',
          borderRadius: 2,
        }}>
          VOL.{series.vol}
        </div>
      )}
      {showTitle && (
        <div style={{
          position: 'absolute', bottom: 0, left: 0, right: 0,
          padding: '24px 8px 8px',
          background: 'linear-gradient(transparent, rgba(0,0,0,.7))',
          fontFamily: '"Space Grotesk", sans-serif',
          fontSize: Math.max(9, height * 0.036),
          fontWeight: 700,
          color: '#fff',
          letterSpacing: '-0.01em',
          lineHeight: 1.2,
        }}>
          {series.title}
        </div>
      )}
    </div>
  );
}
