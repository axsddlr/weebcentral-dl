import { useState, useEffect, useRef, useCallback } from 'react';
import { Search as SearchIcon, Download, BookOpen, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import * as api from '@/services/api';

interface MangaWithChapters extends api.SearchResult {
  chapters?: api.ChapterInfo[];
}

export function Search() {
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<MangaWithChapters[]>([]);
  const [suggestions, setSuggestions] = useState<api.SearchResult[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [highlightIndex, setHighlightIndex] = useState(-1);
  const [selectedManga, setSelectedManga] = useState<MangaWithChapters | null>(null);
  const [selectedChapters, setSelectedChapters] = useState<Set<string>>(new Set());
  const [showChapterDialog, setShowChapterDialog] = useState(false);
  const [selectAll, setSelectAll] = useState(false);
  const [loadingChapters, setLoadingChapters] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  // Close dropdown on click outside
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  // Debounced typeahead search
  useEffect(() => {
    const query = searchQuery.trim();
    if (!query || query.length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      try {
        const results = await api.search(query);
        setSuggestions(results.slice(0, 6));
        setShowSuggestions(true);
        setHighlightIndex(-1);
      } catch {
        // Silently ignore typeahead failures
      }
    }, 300);
    return () => clearTimeout(debounceRef.current);
  }, [searchQuery]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setShowSuggestions(false);
    setIsSearching(true);
    try {
      const results = await api.search(searchQuery);
      setSearchResults(results);
      if (results.length === 0) {
        toast.info('No results found');
      }
    } catch (e) {
      toast.error('Search failed: ' + (e instanceof Error ? e.message : 'Unknown error'));
    } finally {
      setIsSearching(false);
    }
  };

  const selectSuggestion = useCallback(async (manga: api.SearchResult) => {
    setShowSuggestions(false);
    setSearchQuery(manga.title);
    const withChapters: MangaWithChapters = { ...manga };
    setSelectedManga(withChapters);
    setSelectedChapters(new Set());
    setSelectAll(false);
    setShowChapterDialog(true);
    setLoadingChapters(true);
    try {
      const chapters = await api.getSeriesChapters(manga.id);
      setSelectedManga({ ...manga, chapters });
    } catch {
      toast.error('Failed to load chapters');
    } finally {
      setLoadingChapters(false);
    }
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showSuggestions || suggestions.length === 0) {
      if (e.key === 'Enter') {
        e.preventDefault();
        handleSearch();
      }
      return;
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlightIndex(i => Math.min(i + 1, suggestions.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlightIndex(i => Math.max(i - 1, -1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (highlightIndex >= 0) {
        selectSuggestion(suggestions[highlightIndex]);
      } else {
        handleSearch();
      }
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
      inputRef.current?.blur();
    }
  };

  const handleMangaSelect = async (manga: MangaWithChapters) => {
    selectSuggestion(manga);
  };

  const handleChapterToggle = (chapterId: string) => {
    const newSelected = new Set(selectedChapters);
    if (newSelected.has(chapterId)) {
      newSelected.delete(chapterId);
    } else {
      newSelected.add(chapterId);
    }
    setSelectedChapters(newSelected);
  };

  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedChapters(new Set());
    } else if (selectedManga?.chapters) {
      setSelectedChapters(new Set(selectedManga.chapters.map(c => c.id)));
    }
    setSelectAll(!selectAll);
  };

  const handleDownload = async () => {
    if (selectedChapters.size === 0 || !selectedManga) {
      toast.error('Please select at least one chapter');
      return;
    }

    try {
      await api.addToQueue(
        selectedManga.id,
        selectedManga.title,
        Array.from(selectedChapters)
      );
      toast.success(`Added ${selectedChapters.size} chapters to download queue`, {
        description: selectedManga.title,
      });
      setShowChapterDialog(false);
      setSelectedChapters(new Set());
      setSelectAll(false);
    } catch (e) {
      toast.error('Failed to add to queue: ' + (e instanceof Error ? e.message : 'Unknown error'));
    }
  };

  const handleQuickDownload = async (e: React.MouseEvent, manga: MangaWithChapters) => {
    e.stopPropagation();
    try {
      let chapters = manga.chapters;
      if (!chapters) {
        chapters = await api.getSeriesChapters(manga.id);
      }
      await api.addToQueue(
        manga.id,
        manga.title,
        chapters.map(c => c.id)
      );
      toast.success(`Added all chapters to download queue`, {
        description: `${manga.title} - ${chapters.length} chapters`,
      });
    } catch {
      toast.error('Failed to add to queue');
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Search Manga</h1>
        <p className="text-muted-foreground">
          Search for manga on WeebCentral and add to download queue
        </p>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="relative" ref={wrapperRef}>
            <div className="flex gap-3">
              <div className="relative flex-1">
                <SearchIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  ref={inputRef}
                  placeholder="Search by manga title or series ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
                  className="pl-10"
                />
              </div>
              <Button onClick={handleSearch} disabled={isSearching}>
                {isSearching ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <SearchIcon className="h-4 w-4 mr-2" />
                )}
                Search
              </Button>
            </div>

            {showSuggestions && suggestions.length > 0 && (
              <div className="absolute z-50 top-full mt-1 w-full rounded-md border bg-popover shadow-md">
                {suggestions.map((s, i) => (
                  <div
                    key={s.id}
                    className={`flex items-center gap-3 px-3 py-2 cursor-pointer ${
                      i === highlightIndex ? 'bg-accent' : 'hover:bg-accent'
                    }`}
                    onMouseDown={() => selectSuggestion(s)}
                    onMouseEnter={() => setHighlightIndex(i)}
                  >
                    {s.coverUrl ? (
                      <img src={s.coverUrl} alt="" className="h-8 w-8 rounded object-cover" />
                    ) : (
                      <BookOpen className="h-8 w-8 p-1 text-muted-foreground" />
                    )}
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate">{s.title}</p>
                      <p className="text-xs text-muted-foreground">{s.id}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {searchResults.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Search Results</h2>
            <Badge variant="secondary">{searchResults.length} found</Badge>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {searchResults.map((manga) => (
              <Card
                key={manga.id}
                className="cursor-pointer hover:border-primary/50 transition-colors"
                onClick={() => handleMangaSelect(manga)}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      {manga.coverUrl ? (
                        <img
                          src={manga.coverUrl}
                          alt={manga.title}
                          className="h-12 w-12 rounded-lg object-cover"
                        />
                      ) : (
                        <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                          <BookOpen className="h-6 w-6 text-primary" />
                        </div>
                      )}
                      <div>
                        <CardTitle className="text-base">{manga.title}</CardTitle>
                        <CardDescription className="text-xs">
                          {manga.author?.join(', ')}
                        </CardDescription>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pb-3">
                  <p className="text-sm text-muted-foreground line-clamp-2">
                    {manga.description}
                  </p>
                  {manga.tags && manga.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {manga.tags.slice(0, 4).map(tag => (
                        <Badge key={tag} variant="secondary" className="text-xs">{tag}</Badge>
                      ))}
                    </div>
                  )}
                </CardContent>
                <CardFooter className="flex justify-between pt-0">
                  <span className="text-sm text-muted-foreground">
                    {manga.chapters?.length ?? '...'} chapters
                  </span>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={(e) => handleQuickDownload(e, manga)}
                  >
                    <Download className="h-4 w-4 mr-1" />
                    Download All
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        </div>
      )}

      {searchResults.length === 0 && !isSearching && searchQuery && (
        <Card className="p-8 text-center">
          <SearchIcon className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium mb-2">No results found</h3>
          <p className="text-muted-foreground">Try searching with a different keyword</p>
        </Card>
      )}

      <Dialog open={showChapterDialog} onOpenChange={setShowChapterDialog}>
        <DialogContent className="max-w-2xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>{selectedManga?.title}</DialogTitle>
            <DialogDescription>Select chapters to download</DialogDescription>
          </DialogHeader>

          <div className="flex items-center justify-between py-2">
            <div className="flex items-center gap-2">
              <Checkbox
                id="select-all"
                checked={selectAll}
                onCheckedChange={handleSelectAll}
                disabled={loadingChapters}
              />
              <Label htmlFor="select-all" className="text-sm font-medium">
                Select All Chapters
              </Label>
            </div>
            <Badge variant="secondary">
              {selectedChapters.size} selected
            </Badge>
          </div>

          <ScrollArea className="h-[400px] border rounded-md p-4">
            {loadingChapters ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                <span className="ml-2 text-muted-foreground">Loading chapters...</span>
              </div>
            ) : (
              <div className="space-y-2">
                {selectedManga?.chapters?.map((chapter) => (
                  <div
                    key={chapter.id}
                    className="flex items-center justify-between p-2 rounded hover:bg-muted transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <Checkbox
                        id={chapter.id}
                        checked={selectedChapters.has(chapter.id)}
                        onCheckedChange={() => handleChapterToggle(chapter.id)}
                      />
                      <Label htmlFor={chapter.id} className="text-sm cursor-pointer">
                        {chapter.type} {chapter.number}
                      </Label>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowChapterDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleDownload} disabled={selectedChapters.size === 0}>
              <Download className="h-4 w-4 mr-2" />
              Download {selectedChapters.size > 0 && `(${selectedChapters.size})`}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
