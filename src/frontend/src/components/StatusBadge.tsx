import { Clock, CheckCircle, AlertCircle, Pause } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export type TaskStatus = 'downloading' | 'completed' | 'failed' | 'pending' | 'paused';

const STATUS_VARIANTS: Record<string, string> = {
  downloading: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
  completed: 'bg-green-500/10 text-green-500 border-green-500/20',
  failed: 'bg-red-500/10 text-red-500 border-red-500/20',
  pending: 'bg-muted text-muted-foreground',
  paused: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
};

export function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case 'downloading':
      return <div className="h-3 w-3 rounded-full bg-blue-500 animate-pulse" />;
    case 'completed':
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    case 'failed':
      return <AlertCircle className="h-4 w-4 text-red-500" />;
    case 'pending':
      return <Clock className="h-4 w-4 text-muted-foreground" />;
    case 'paused':
      return <Pause className="h-4 w-4 text-yellow-500" />;
    default:
      return null;
  }
}

export function StatusBadge({ status }: { status: string }) {
  return (
    <Badge variant="outline" className={STATUS_VARIANTS[status] || STATUS_VARIANTS.pending}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </Badge>
  );
}
