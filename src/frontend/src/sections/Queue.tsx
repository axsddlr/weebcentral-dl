import { useState, useEffect } from 'react';
import {
  Play,
  Pause,
  RotateCcw,
  Trash2,
  Download,
  MoreHorizontal
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { StatusIcon, StatusBadge } from '@/components/StatusBadge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu';
import { toast } from 'sonner';
import * as api from '@/services/api';
import { useWebSocket } from '@/hooks/useWebSocket';

export function Queue() {
  const [queue, setQueue] = useState<api.QueueState>({
    tasks: [], isRunning: true, totalTasks: 0, completedTasks: 0, failedTasks: 0,
  });

  const fetchQueue = async () => {
    try {
      const data = await api.getQueue();
      setQueue(data);
    } catch (e) {
      console.error('Failed to fetch queue:', e);
    }
  };

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await api.getQueue();
        if (!cancelled) setQueue(data);
      } catch (e) {
        if (!cancelled) console.error('Failed to fetch queue:', e);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  useWebSocket({
    path: '/ws/queue',
    onMessage: (msg) => {
      if (msg.type === 'queue_update') setQueue(msg.data as api.QueueState);
    },
  });

  useWebSocket({
    path: '/ws/progress',
    onMessage: (msg) => {
      if (msg.type === 'progress') {
        const task = msg.data as api.QueueTask;
        setQueue(prev => ({
          ...prev,
          tasks: prev.tasks.map(t => t.id === task.id ? task : t),
        }));
      }
    },
  });

  const handleToggleQueue = async () => {
    try {
      if (queue.isRunning) {
        await api.pauseQueue();
        toast.info('Download queue paused');
      } else {
        await api.resumeQueue();
        toast.info('Download queue resumed');
      }
      fetchQueue();
    } catch {
      toast.error('Failed to toggle queue');
    }
  };

  const handleRetry = async (taskId: string) => {
    try {
      await api.retryTask(taskId);
      toast.success('Task queued for retry');
    } catch {
      toast.error('Failed to retry task');
    }
  };

  const handleRemove = async (taskId: string) => {
    try {
      await api.removeTask(taskId);
      toast.success('Task removed from queue');
    } catch {
      toast.error('Failed to remove task');
    }
  };

  const handleClearCompleted = async () => {
    try {
      await api.clearCompleted();
      toast.success('Completed tasks cleared');
    } catch {
      toast.error('Failed to clear completed');
    }
  };

  const handleRetryAllFailed = async () => {
    try {
      await api.retryAllFailed();
      toast.success('All failed tasks queued for retry');
    } catch {
      toast.error('Failed to retry all');
    }
  };

  const tasks = queue.tasks;
  const filteredQueue = {
    all: tasks,
    active: tasks.filter(t => ['downloading', 'pending', 'paused'].includes(t.status)),
    completed: tasks.filter(t => t.status === 'completed'),
    failed: tasks.filter(t => t.status === 'failed'),
  };

  const stats = tasks.reduce(
    (acc, t) => {
      acc.total++;
      if (t.status === 'downloading') acc.downloading++;
      else if (t.status === 'pending') acc.pending++;
      else if (t.status === 'completed') acc.completed++;
      else if (t.status === 'failed') acc.failed++;
      return acc;
    },
    { total: 0, downloading: 0, pending: 0, completed: 0, failed: 0 }
  );

  const renderTaskList = (taskList: api.QueueTask[]) => (
    <div className="space-y-3">
      {taskList.map((task) => (
        <Card key={task.id} className="p-4">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-3">
              <StatusIcon status={task.status} />
              <div>
                <p className="font-medium">{task.mangaTitle}</p>
                <p className="text-sm text-muted-foreground">Chapter {task.chapterNumber}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <StatusBadge status={task.status} />
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  {task.status === 'failed' && (
                    <DropdownMenuItem onClick={() => handleRetry(task.id)}>
                      <RotateCcw className="h-4 w-4 mr-2" />
                      Retry
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuItem onClick={() => handleRemove(task.id)}>
                    <Trash2 className="h-4 w-4 mr-2" />
                    Remove
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>

          {task.status === 'downloading' && (
            <div className="space-y-2">
              <Progress value={task.progress} className="h-2" />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>{task.downloadedPages} / {task.totalPages} pages</span>
                <span>{task.progress.toFixed(0)}%</span>
              </div>
            </div>
          )}

          {task.status === 'failed' && task.error && (
            <p className="text-sm text-red-500 mt-2">Error: {task.error}</p>
          )}
        </Card>
      ))}

      {taskList.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          <Download className="h-12 w-12 mx-auto mb-3 opacity-50" />
          <p>No tasks in this category</p>
        </div>
      )}
    </div>
  );

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Download Queue</h1>
          <p className="text-muted-foreground">Manage and monitor your manga downloads</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleClearCompleted}>
            <Trash2 className="h-4 w-4 mr-2" />
            Clear Completed
          </Button>
          <Button variant="outline" onClick={handleRetryAllFailed}>
            <RotateCcw className="h-4 w-4 mr-2" />
            Retry Failed
          </Button>
          <Button onClick={handleToggleQueue}>
            {queue.isRunning ? (
              <><Pause className="h-4 w-4 mr-2" />Pause</>
            ) : (
              <><Play className="h-4 w-4 mr-2" />Resume</>
            )}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-5 gap-4">
        <Card><CardContent className="pt-4"><p className="text-2xl font-bold">{stats.total}</p><p className="text-xs text-muted-foreground">Total</p></CardContent></Card>
        <Card><CardContent className="pt-4"><p className="text-2xl font-bold text-blue-500">{stats.downloading}</p><p className="text-xs text-muted-foreground">Downloading</p></CardContent></Card>
        <Card><CardContent className="pt-4"><p className="text-2xl font-bold text-muted-foreground">{stats.pending}</p><p className="text-xs text-muted-foreground">Pending</p></CardContent></Card>
        <Card><CardContent className="pt-4"><p className="text-2xl font-bold text-green-500">{stats.completed}</p><p className="text-xs text-muted-foreground">Completed</p></CardContent></Card>
        <Card><CardContent className="pt-4"><p className="text-2xl font-bold text-red-500">{stats.failed}</p><p className="text-xs text-muted-foreground">Failed</p></CardContent></Card>
      </div>

      <Tabs defaultValue="all" className="w-full">
        <TabsList>
          <TabsTrigger value="all">All ({filteredQueue.all.length})</TabsTrigger>
          <TabsTrigger value="active">Active ({filteredQueue.active.length})</TabsTrigger>
          <TabsTrigger value="completed">Completed ({filteredQueue.completed.length})</TabsTrigger>
          <TabsTrigger value="failed">Failed ({filteredQueue.failed.length})</TabsTrigger>
        </TabsList>
        <TabsContent value="all" className="mt-4"><ScrollArea className="h-[500px]">{renderTaskList(filteredQueue.all)}</ScrollArea></TabsContent>
        <TabsContent value="active" className="mt-4"><ScrollArea className="h-[500px]">{renderTaskList(filteredQueue.active)}</ScrollArea></TabsContent>
        <TabsContent value="completed" className="mt-4"><ScrollArea className="h-[500px]">{renderTaskList(filteredQueue.completed)}</ScrollArea></TabsContent>
        <TabsContent value="failed" className="mt-4"><ScrollArea className="h-[500px]">{renderTaskList(filteredQueue.failed)}</ScrollArea></TabsContent>
      </Tabs>
    </div>
  );
}
