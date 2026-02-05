import { useState, useEffect } from 'react';
import {
  BookOpen,
  Search,
  MoreVertical,
  Play,
  Grid3X3,
  List,
  Trash2,
  Loader2
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import type { LibraryManga, LibraryChapter, View } from '@/types';
import { toast } from 'sonner';
import * as api from '@/services/api';

interface LibraryProps {
  onViewChange: (view: View) => void;
  onMangaSelect: (manga: LibraryManga, chapter: LibraryChapter) => void;
}

export function Library({ onViewChange, onMangaSelect }: LibraryProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [library, setLibrary] = useState<api.LibrarySeries[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSeries, setSelectedSeries] = useState<api.LibrarySeries | null>(null);
  const [chapters, setChapters] = useState<api.LibraryChapter[]>([]);
  const [showChaptersDialog, setShowChaptersDialog] = useState(false);
  const [loadingChapters, setLoadingChapters] = useState(false);

  const fetchLibrary = async () => {
    try {
      const data = await api.getLibrary();
      setLibrary(data);
    } catch (e) {
      console.error('Failed to fetch library:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchLibrary(); }, []);

  const filteredLibrary = library.filter(s =>
    s.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleMangaClick = async (series: api.LibrarySeries) => {
    setSelectedSeries(series);
    setShowChaptersDialog(true);
    setLoadingChapters(true);
    try {
      const chs = await api.getLibraryChapters(series.path);
      setChapters(chs);
    } catch (e) {
      toast.error('Failed to load chapters');
    } finally {
      setLoadingChapters(false);
    }
  };

  const handleReadChapter = (chapter: api.LibraryChapter) => {
    if (selectedSeries) {
      const libraryManga: LibraryManga = {
        id: selectedSeries.id,
        title: selectedSeries.title,
        coverUrl: selectedSeries.coverUrl || undefined,
        totalChapters: selectedSeries.totalChapters,
        downloadedChapters: selectedSeries.totalChapters,
        readChapters: 0,
        path: selectedSeries.path,
      };
      const libraryChapter: LibraryChapter = {
        id: chapter.id,
        number: chapter.number,
        totalPages: chapter.totalPages,
        read: false,
        lastReadPage: 0,
        path: chapter.path,
        images: [],
      };
      onMangaSelect(libraryManga, libraryChapter);
      onViewChange('reader');
    }
  };

  const handleDeleteSeries = async (seriesPath: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.deleteSeries(seriesPath);
      toast.success('Series removed from library');
      fetchLibrary();
    } catch (e) {
      toast.error('Failed to delete series');
    }
  };

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
          <h1 className="text-2xl font-bold tracking-tight">Library</h1>
          <p className="text-muted-foreground">Browse and read your downloaded manga collection</p>
        </div>
      </div>

      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search manga..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <div className="flex border rounded-md">
          <Button
            variant={viewMode === 'grid' ? 'secondary' : 'ghost'}
            size="icon"
            onClick={() => setViewMode('grid')}
          >
            <Grid3X3 className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === 'list' ? 'secondary' : 'ghost'}
            size="icon"
            onClick={() => setViewMode('list')}
          >
            <List className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <Card><CardContent className="pt-4"><p className="text-2xl font-bold">{library.length}</p><p className="text-xs text-muted-foreground">Total Series</p></CardContent></Card>
        <Card><CardContent className="pt-4"><p className="text-2xl font-bold">{library.reduce((acc, m) => acc + m.totalChapters, 0)}</p><p className="text-xs text-muted-foreground">Chapters</p></CardContent></Card>
        <Card><CardContent className="pt-4"><p className="text-2xl font-bold">{filteredLibrary.length}</p><p className="text-xs text-muted-foreground">Showing</p></CardContent></Card>
      </div>

      {viewMode === 'grid' ? (
        <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
          {filteredLibrary.map((series) => (
            <Card
              key={series.id}
              className="cursor-pointer hover:border-primary/50 transition-colors overflow-hidden group"
              onClick={() => handleMangaClick(series)}
            >
              <div className="aspect-[2/3] relative overflow-hidden bg-muted">
                {series.coverUrl ? (
                  <img
                    src={series.coverUrl}
                    alt={series.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <BookOpen className="h-12 w-12 text-muted-foreground" />
                  </div>
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                <Badge className="absolute top-2 right-2 bg-primary">
                  {series.totalChapters} ch
                </Badge>
              </div>
              <CardContent className="p-3">
                <h3 className="font-semibold truncate">{series.title}</h3>
                <p className="text-xs text-muted-foreground">
                  {series.totalChapters} chapters
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="space-y-2">
          {filteredLibrary.map((series) => (
            <Card
              key={series.id}
              className="cursor-pointer hover:border-primary/50 transition-colors"
              onClick={() => handleMangaClick(series)}
            >
              <CardContent className="p-4 flex items-center gap-4">
                <div className="w-16 h-24 bg-muted rounded overflow-hidden flex-shrink-0">
                  {series.coverUrl ? (
                    <img src={series.coverUrl} alt={series.title} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <BookOpen className="h-6 w-6 text-muted-foreground" />
                    </div>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold">{series.title}</h3>
                  <span className="text-xs text-muted-foreground">{series.totalChapters} chapters</span>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" onClick={(e) => e.stopPropagation()}>
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={(e) => handleDeleteSeries(series.path, e as unknown as React.MouseEvent)}>
                      <Trash2 className="h-4 w-4 mr-2" />
                      Remove
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {filteredLibrary.length === 0 && !loading && (
        <div className="text-center py-12">
          <BookOpen className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium mb-2">No manga found</h3>
          <p className="text-muted-foreground">Download some manga first or adjust your search</p>
        </div>
      )}

      <Dialog open={showChaptersDialog} onOpenChange={setShowChaptersDialog}>
        <DialogContent className="max-w-2xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>{selectedSeries?.title}</DialogTitle>
          </DialogHeader>

          {selectedSeries && (
            <div className="flex gap-4 mb-4">
              <div className="w-24 h-36 bg-muted rounded overflow-hidden flex-shrink-0">
                {selectedSeries.coverUrl ? (
                  <img src={selectedSeries.coverUrl} alt={selectedSeries.title} className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <BookOpen className="h-8 w-8 text-muted-foreground" />
                  </div>
                )}
              </div>
              <div className="flex-1">
                <p className="text-xs text-muted-foreground mt-2">
                  {selectedSeries.totalChapters} chapters downloaded
                </p>
              </div>
            </div>
          )}

          <ScrollArea className="h-[400px] border rounded-md">
            {loadingChapters ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : (
              <div className="space-y-1 p-2">
                {chapters.map((chapter) => (
                  <div
                    key={chapter.id}
                    className="flex items-center justify-between p-3 rounded hover:bg-muted transition-colors"
                  >
                    <div>
                      <p className="font-medium text-sm">Chapter {chapter.number}</p>
                      <p className="text-xs text-muted-foreground">{chapter.totalPages} pages</p>
                    </div>
                    <Button
                      size="sm"
                      onClick={() => handleReadChapter(chapter)}
                    >
                      <Play className="h-4 w-4 mr-1" />
                      Read
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </DialogContent>
      </Dialog>
    </div>
  );
}
