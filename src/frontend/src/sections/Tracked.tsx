import { useState, useEffect } from "react";
import {
  Trash2, Download, Upload, RefreshCw, Loader2,
  BookOpen, Search, Play, CircleCheck, Eye,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import * as api from "@/services/api";

export function Tracked() {
  const [tracked, setTracked] = useState<api.TrackedManga[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [importing, setImporting] = useState(false);
  const [checking, setChecking] = useState(false);

  const fetchTracked = async (status?: string) => {
    try {
      const params = status ? `?status=${encodeURIComponent(status)}` : '';
      const data = await api.getTracked(params);
      setTracked(data.series);
      setTotal(data.total);
    } catch {
      toast.error("Failed to load tracked manga");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchTracked(statusFilter); }, [statusFilter]);

  const handleRemove = async (seriesId: string) => {
    try {
      await api.removeTracked(seriesId);
      setTracked(prev => prev.filter(s => s.series_id !== seriesId));
      setTotal(prev => prev - 1);
      toast.success("Removed from tracked");
    } catch {
      toast.error("Failed to remove");
    }
  };

  const handleDownload = async (series: api.TrackedManga) => {
    try {
      const chapters = await api.getSeriesChapters(series.series_id);
      if (chapters.length === 0) {
        toast.info("No chapters found");
        return;
      }
      await api.addToQueue(series.series_id, series.title, chapters.map(c => c.id));
      toast.success(`Queued ${chapters.length} chapters for ${series.title}`);
    } catch {
      toast.error("Failed to queue download");
    }
  };

  const handleImport = async () => {
    setImporting(true);
    try {
      const result = await api.importTracked();
      toast.success(`Imported ${result.added} entries (${result.skipped} skipped)`);
      fetchTracked(statusFilter);
    } catch {
      toast.error("manga_list.txt not found or import failed");
    } finally {
      setImporting(false);
    }
  };

  const handleCheck = async () => {
    setChecking(true);
    try {
      await api.checkTracked();
      toast.success("Checking tracked manga for new chapters...");
    } catch {
      toast.error("Failed to start check");
    } finally {
      setChecking(false);
    }
  };

  const displayList = searchQuery
    ? tracked.filter(s => s.title.toLowerCase().includes(searchQuery.toLowerCase()) || s.series_id.toLowerCase().includes(searchQuery.toLowerCase()))
    : tracked;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Tracked Manga</h1>
          <p className="text-muted-foreground">Manage your followed series for bulk downloading</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleCheck} disabled={checking}>
            {checking ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Play className="h-4 w-4 mr-2" />}
            Check Now
          </Button>
          <Button variant="outline" onClick={handleImport} disabled={importing}>
            {importing ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Upload className="h-4 w-4 mr-2" />}
            Import
          </Button>
          <Button variant="outline" onClick={() => fetchTracked(statusFilter)}>
            <RefreshCw className="h-4 w-4 mr-2" /> Refresh
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg">{total} Tracked Series</CardTitle>
          <CardDescription>
            Use the Search page to find new manga and add them, or import from manga_list.txt.
            Run python main.py --tracked to download all.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-1 mb-3 flex-wrap">
            {["", "reading", "downloading", "complete"].map((s) => {
              const iconMap: Record<string, JSX.Element> = {
                reading: <Eye className="h-3.5 w-3.5" />,
                downloading: <Download className="h-3.5 w-3.5" />,
                complete: <CircleCheck className="h-3.5 w-3.5" />,
              };
              return (
                <Button
                  key={s}
                  size="sm"
                  variant={statusFilter === s ? "default" : "outline"}
                  onClick={() => setStatusFilter(s)}
                  className="text-xs"
                >
                  {s ? <>{iconMap[s]} <span className="ml-1 capitalize">{s}</span></> : "All"}
                </Button>
              );
            })}
          </div>

          <div className="relative mb-4">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Filter tracked manga..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          {displayList.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <BookOpen className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>{searchQuery ? "No matching tracked manga" : "No tracked manga yet"}</p>
              <p className="text-sm mt-1">
                {!searchQuery && "Import from manga_list.txt to get started"}
              </p>
            </div>
          ) : (
            <ScrollArea className="h-[460px]">
              <div className="space-y-2">
                {displayList.map((series) => (
                  <div
                    key={series.series_id}
                    className="flex items-center gap-4 p-3 rounded-md border hover:bg-accent/50 transition-colors"
                  >
                    <div className="w-12 h-16 bg-muted rounded overflow-hidden flex-shrink-0">
                      {series.cover_url ? (
                        <img
                          src={series.cover_url}
                          alt={series.title}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <BookOpen className="h-5 w-5 text-muted-foreground" />
                        </div>
                      )}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <p className="font-medium truncate">{series.title}</p>
                        {series.status && (
                          <span className={[
                            "text-[10px] px-1.5 py-0.5 rounded font-medium uppercase shrink-0",
                            series.status === 'reading' ? 'bg-blue-500/10 text-blue-500' : '',
                            series.status === 'downloading' ? 'bg-amber-500/10 text-amber-500' : '',
                            series.status === 'complete' ? 'bg-green-500/10 text-green-500' : '',
                          ].join(' ')}>
                            {series.status}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground font-mono">{series.series_id}</p>
                      <p className="text-xs text-muted-foreground">
                        Added {new Date(series.added_at).toLocaleDateString()}
                        {series.last_checked_at && " * Checked " + new Date(series.last_checked_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex items-center gap-2 ml-4 shrink-0">
                      <Button size="sm" variant="outline" onClick={() => handleDownload(series)}>
                        <Download className="h-4 w-4 mr-1" />
                        Queue
                      </Button>
                      <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => handleRemove(series.series_id)}>
                        <Trash2 className="h-4 w-4 text-muted-foreground hover:text-red-500" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
