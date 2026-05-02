import { useState, useEffect } from 'react';
import {
  Download,
  Trash2,
  RefreshCw,
  Filter,
  Search,
  AlertCircle,
  Info,
  AlertTriangle,
  Terminal
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import * as api from '@/services/api';
import { useWebSocket } from '@/hooks/useWebSocket';

export function Logs() {
  const [logs, setLogs] = useState<api.LogEntry[]>([]);
  const [filter, setFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const fetchLogs = async () => {
    try {
      const data = await api.getLogs();
      setLogs(data);
    } catch (e) {
      console.error('Failed to fetch logs:', e);
    }
  };

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await api.getLogs();
        if (!cancelled) setLogs(data);
      } catch (e) {
        if (!cancelled) console.error('Failed to fetch logs:', e);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  useWebSocket({
    path: '/ws/logs',
    onMessage: (msg) => {
      if (msg.type === 'log') {
        setLogs(prev => [msg.data as api.LogEntry, ...prev].slice(0, 500));
      }
    },
  });

  const filteredLogs = logs.filter(log => {
    const matchesFilter = filter === 'all' || log.level === filter;
    const matchesSearch = searchQuery === '' ||
      log.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.source?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'info':
        return <Info className="h-4 w-4 text-blue-500" />;
      case 'debug':
        return <Terminal className="h-4 w-4 text-muted-foreground" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Info className="h-4 w-4" />;
    }
  };

  const getLevelBadge = (level: string) => {
    const variants: Record<string, string> = {
      info: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
      debug: 'bg-muted text-muted-foreground',
      warning: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
      error: 'bg-red-500/10 text-red-500 border-red-500/20',
    };
    return (
      <Badge variant="outline" className={variants[level] || variants.info}>
        {level.toUpperCase()}
      </Badge>
    );
  };

  const handleClear = async () => {
    try {
      await api.clearLogs();
      setLogs([]);
      toast.success('Logs cleared');
    } catch {
      toast.error('Failed to clear logs');
    }
  };

  const handleExport = () => {
    const logText = logs.map(log =>
      `[${log.timestamp}] [${log.level.toUpperCase()}] [${log.source || ''}] ${log.message}`
    ).join('\n');

    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `weebcentral-dl-logs-${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Logs exported');
  };

  const stats = {
    total: logs.length,
    info: logs.filter(l => l.level === 'info').length,
    debug: logs.filter(l => l.level === 'debug').length,
    warning: logs.filter(l => l.level === 'warning').length,
    error: logs.filter(l => l.level === 'error').length,
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Logs</h1>
          <p className="text-muted-foreground">View and manage download activity logs</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleExport}>
            <Download className="h-4 w-4 mr-2" /> Export
          </Button>
          <Button variant="outline" onClick={handleClear}>
            <Trash2 className="h-4 w-4 mr-2" /> Clear
          </Button>
          <Button variant="outline" onClick={fetchLogs}>
            <RefreshCw className="h-4 w-4 mr-2" /> Refresh
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-5 gap-4">
        <Card><CardContent className="pt-4"><p className="text-2xl font-bold">{stats.total}</p><p className="text-xs text-muted-foreground">Total</p></CardContent></Card>
        <Card><CardContent className="pt-4"><p className="text-2xl font-bold text-blue-500">{stats.info}</p><p className="text-xs text-muted-foreground">Info</p></CardContent></Card>
        <Card><CardContent className="pt-4"><p className="text-2xl font-bold text-muted-foreground">{stats.debug}</p><p className="text-xs text-muted-foreground">Debug</p></CardContent></Card>
        <Card><CardContent className="pt-4"><p className="text-2xl font-bold text-yellow-500">{stats.warning}</p><p className="text-xs text-muted-foreground">Warnings</p></CardContent></Card>
        <Card><CardContent className="pt-4"><p className="text-2xl font-bold text-red-500">{stats.error}</p><p className="text-xs text-muted-foreground">Errors</p></CardContent></Card>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search logs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={filter} onValueChange={setFilter}>
              <SelectTrigger className="w-[150px]">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Filter" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Levels</SelectItem>
                <SelectItem value="info">Info</SelectItem>
                <SelectItem value="debug">Debug</SelectItem>
                <SelectItem value="warning">Warning</SelectItem>
                <SelectItem value="error">Error</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Log Entries</CardTitle>
          <CardDescription>Showing {filteredLogs.length} of {logs.length} entries</CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[500px] border rounded-md">
            <div className="space-y-0">
              {filteredLogs.map((log) => (
                <div
                  key={log.id}
                  className="flex items-start gap-3 p-3 hover:bg-muted/50 transition-colors border-b last:border-b-0"
                >
                  <div className="mt-0.5">{getLevelIcon(log.level)}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      {getLevelBadge(log.level)}
                      <span className="text-xs text-muted-foreground">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </span>
                      {log.source && (
                        <Badge variant="secondary" className="text-xs">{log.source}</Badge>
                      )}
                    </div>
                    <p className="text-sm">{log.message}</p>
                  </div>
                </div>
              ))}
              {filteredLogs.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  <Terminal className="h-12 w-12 mx-auto mb-3 opacity-50" />
                  <p>No logs match your filters</p>
                </div>
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
