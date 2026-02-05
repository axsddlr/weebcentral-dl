import { useState, useEffect } from 'react';
import {
  Download,
  BookOpen,
  HardDrive,
  Clock,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import * as api from '@/services/api';
import { useWebSocket } from '@/hooks/useWebSocket';

export function Dashboard() {
  const [stats, setStats] = useState<api.DashboardStats | null>(null);
  const [queue, setQueue] = useState<api.QueueState | null>(null);

  const fetchData = async () => {
    try {
      const [s, q] = await Promise.all([api.getStats(), api.getQueue()]);
      setStats(s);
      setQueue(q);
    } catch (e) {
      console.error('Failed to fetch dashboard data:', e);
    }
  };

  useEffect(() => { fetchData(); }, []);

  useWebSocket({
    path: '/ws/queue',
    onMessage: (msg) => {
      if (msg.type === 'queue_update') {
        setQueue(msg.data);
        api.getStats().then(setStats).catch(() => {});
      }
    },
  });

  useWebSocket({
    path: '/ws/progress',
    onMessage: (msg) => {
      if (msg.type === 'progress' && queue) {
        setQueue(prev => {
          if (!prev) return prev;
          const tasks = prev.tasks.map(t => t.id === msg.data.id ? msg.data : t);
          return { ...prev, tasks };
        });
      }
    },
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'downloading':
        return <div className="h-3 w-3 rounded-full bg-blue-500 animate-pulse" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-muted-foreground" />;
      default:
        return null;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, string> = {
      downloading: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
      completed: 'bg-green-500/10 text-green-500 border-green-500/20',
      failed: 'bg-red-500/10 text-red-500 border-red-500/20',
      pending: 'bg-muted text-muted-foreground',
      paused: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
    };
    return (
      <Badge variant="outline" className={variants[status] || variants.pending}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  const activeTasks = queue?.tasks.filter(t => ['downloading', 'pending'].includes(t.status)) || [];
  const completedTasks = queue?.tasks.filter(t => t.status === 'completed').slice(0, 5) || [];

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Overview of your manga download activity
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Series</CardTitle>
            <Download className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.totalSeries ?? '—'}</div>
            <p className="text-xs text-muted-foreground">In your library</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Chapters Downloaded</CardTitle>
            <BookOpen className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.totalChapters?.toLocaleString() ?? '—'}</div>
            <p className="text-xs text-muted-foreground">Across all series</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Storage Used</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.storageUsed ?? '—'}</div>
            <p className="text-xs text-muted-foreground">Disk usage</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Queue Status</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.queueActive ?? 0}</div>
            <p className="text-xs text-muted-foreground">Active downloads</p>
          </CardContent>
        </Card>
      </div>

      {/* Bottom Row */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Active Downloads</CardTitle>
            <CardDescription>Currently downloading chapters</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {activeTasks.map((task) => (
                <div key={task.id} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(task.status)}
                      <span className="font-medium">{task.mangaTitle}</span>
                      <span className="text-muted-foreground">Ch. {task.chapterNumber}</span>
                    </div>
                    {getStatusBadge(task.status)}
                  </div>
                  {task.status === 'downloading' && (
                    <div className="space-y-1">
                      <Progress value={task.progress} className="h-2" />
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>{task.downloadedPages} / {task.totalPages} pages</span>
                        <span>{task.progress.toFixed(0)}%</span>
                      </div>
                    </div>
                  )}
                </div>
              ))}
              {activeTasks.length === 0 && (
                <p className="text-center text-muted-foreground py-4">No active downloads</p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Downloads</CardTitle>
            <CardDescription>Recently completed downloads</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[280px]">
              <div className="space-y-3">
                {completedTasks.map((task) => (
                  <div key={task.id} className="flex items-center justify-between py-2">
                    <div className="flex items-center gap-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded bg-primary/10">
                        <BookOpen className="h-4 w-4 text-primary" />
                      </div>
                      <div>
                        <p className="font-medium text-sm">{task.mangaTitle}</p>
                        <p className="text-xs text-muted-foreground">Chapter {task.chapterNumber}</p>
                      </div>
                    </div>
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  </div>
                ))}
                {completedTasks.length === 0 && (
                  <p className="text-center text-muted-foreground py-4">No completed downloads yet</p>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
