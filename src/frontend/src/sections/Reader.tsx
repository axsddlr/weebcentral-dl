import { useState, useEffect, useCallback, useRef } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  X,
  Maximize,
  Minimize,
  ZoomIn,
  ZoomOut,
  BookOpen,
  List,
  Columns,
  ArrowLeftRight,
  Type,
  Palette,
  RotateCcw
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';
import type { LibraryManga, LibraryChapter, ReaderSettings, View } from '@/types';
import { toast } from 'sonner';
import * as api from '@/services/api';

interface ReaderProps {
  manga: LibraryManga | null;
  chapter: LibraryChapter | null;
  onViewChange: (view: View) => void;
}

const defaultSettings: ReaderSettings = {
  readingMode: 'long-strip',
  readingDirection: 'ltr',
  fitMode: 'fit-screen',
  backgroundColor: 'black',
  showPageNumber: true,
  preloadPages: 3,
};

export function Reader({ manga, chapter, onViewChange }: ReaderProps) {
  const [currentPage, setCurrentPage] = useState(0);
  const [settings, setSettings] = useState<ReaderSettings>(defaultSettings);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [zoom, setZoom] = useState(100);
  const [showControls, setShowControls] = useState(true);
  const [pageUrls, setPageUrls] = useState<string[]>([]);
  const controlsTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (manga && chapter) {
      api.getPages(manga.path, chapter.path).then(data => {
        const urls = data.pages.map((_, i) =>
          api.getPageUrl(manga.path, chapter.path, i)
        );
        setPageUrls(urls);

        api.getProgress(manga.path).then(p => {
          const saved = p.progress[chapter.path];
          setCurrentPage(saved > 0 ? saved - 1 : 0);
        }).catch(() => {
          setCurrentPage(chapter.lastReadPage > 0 ? chapter.lastReadPage - 1 : 0);
        });
      }).catch(e => {
        toast.error('Failed to load pages');
        console.error(e);
      });
    }
  }, [manga, chapter]);

  const handleMouseMove = useCallback(() => {
    setShowControls(true);
    if (controlsTimeoutRef.current) {
      clearTimeout(controlsTimeoutRef.current);
    }
    controlsTimeoutRef.current = setTimeout(() => {
      if (!isFullscreen) {
        setShowControls(false);
      }
    }, 3000);
  }, [isFullscreen]);

  useEffect(() => {
    return () => {
      if (controlsTimeoutRef.current) {
        clearTimeout(controlsTimeoutRef.current);
      }
    };
  }, []);

  const saveRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    if (manga && chapter && pageUrls.length > 0) {
      if (saveRef.current) clearTimeout(saveRef.current);
      saveRef.current = setTimeout(() => {
        api.saveProgress(manga.path, chapter.path, currentPage + 1).catch(() => {});
      }, 1000);
    }
    return () => { if (saveRef.current) clearTimeout(saveRef.current); };
  }, [currentPage, manga, chapter, pageUrls.length]);

  const handleNextPage = useCallback(() => {
    if (currentPage < pageUrls.length - 1) {
      setCurrentPage(prev => prev + 1);
    } else {
      api.saveProgress(manga!.path, chapter!.path, currentPage + 1).catch(() => {});
      toast.success('Chapter completed!');
    }
  }, [currentPage, pageUrls.length, manga, chapter]);

  const handlePrevPage = useCallback(() => {
    if (currentPage > 0) {
      setCurrentPage(prev => prev - 1);
    }
  }, [currentPage]);

  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  }, []);

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'ArrowRight' || e.key === ' ') {
      handleNextPage();
    } else if (e.key === 'ArrowLeft') {
      handlePrevPage();
    } else if (e.key === 'Escape') {
      if (isFullscreen) {
        setIsFullscreen(false);
      } else {
        onViewChange('library');
      }
    } else if (e.key === 'f') {
      toggleFullscreen();
    }
  }, [handleNextPage, handlePrevPage, isFullscreen, onViewChange, toggleFullscreen]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  const getBackgroundColor = () => {
    switch (settings.backgroundColor) {
      case 'black': return 'bg-black';
      case 'white': return 'bg-white';
      case 'gray': return 'bg-gray-900';
      default: return 'bg-black';
    }
  };

  const getFitModeClass = () => {
    switch (settings.fitMode) {
      case 'fit-width': return 'w-full h-auto';
      case 'fit-height': return 'h-full w-auto';
      case 'fit-screen': return 'max-w-full max-h-full';
      case 'original': return '';
      default: return 'w-full h-auto';
    }
  };

  if (!manga || !chapter) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <BookOpen className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground">Select a manga to start reading</p>
          <Button className="mt-4" onClick={() => onViewChange('library')}>
            Go to Library
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={cn("relative h-full flex flex-col", getBackgroundColor())}
      onMouseMove={handleMouseMove}
    >
      {/* Top Bar */}
      <div
        className={cn(
          "absolute top-0 left-0 right-0 z-50 flex items-center justify-between px-4 py-3 bg-gradient-to-b from-black/80 to-transparent transition-opacity duration-300",
          showControls ? 'opacity-100' : 'opacity-0 pointer-events-none'
        )}
      >
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" className="text-white hover:bg-white/20" onClick={() => onViewChange('library')}>
            <X className="h-5 w-5" />
          </Button>
          <div>
            <h2 className="text-white font-semibold">{manga.title}</h2>
            <p className="text-white/70 text-sm">Chapter {chapter.number}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="text-white hover:bg-white/20">
                {settings.readingMode === 'single' && <BookOpen className="h-5 w-5" />}
                {settings.readingMode === 'long-strip' && <List className="h-5 w-5" />}
                {settings.readingMode === 'double' && <Columns className="h-5 w-5" />}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>Reading Mode</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => setSettings(s => ({ ...s, readingMode: 'single' }))}>
                <BookOpen className="h-4 w-4 mr-2" /> Single Page {settings.readingMode === 'single' && <span className="ml-auto">✓</span>}
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setSettings(s => ({ ...s, readingMode: 'long-strip' }))}>
                <List className="h-4 w-4 mr-2" /> Long Strip {settings.readingMode === 'long-strip' && <span className="ml-auto">✓</span>}
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setSettings(s => ({ ...s, readingMode: 'double' }))}>
                <Columns className="h-4 w-4 mr-2" /> Double Page {settings.readingMode === 'double' && <span className="ml-auto">✓</span>}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="text-white hover:bg-white/20"><ArrowLeftRight className="h-5 w-5" /></Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>Reading Direction</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => setSettings(s => ({ ...s, readingDirection: 'ltr' }))}>Left to Right {settings.readingDirection === 'ltr' && <span className="ml-auto">✓</span>}</DropdownMenuItem>
              <DropdownMenuItem onClick={() => setSettings(s => ({ ...s, readingDirection: 'rtl' }))}>Right to Left {settings.readingDirection === 'rtl' && <span className="ml-auto">✓</span>}</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="text-white hover:bg-white/20"><Type className="h-5 w-5" /></Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>Fit Mode</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => setSettings(s => ({ ...s, fitMode: 'fit-width' }))}>Fit Width {settings.fitMode === 'fit-width' && <span className="ml-auto">✓</span>}</DropdownMenuItem>
              <DropdownMenuItem onClick={() => setSettings(s => ({ ...s, fitMode: 'fit-height' }))}>Fit Height {settings.fitMode === 'fit-height' && <span className="ml-auto">✓</span>}</DropdownMenuItem>
              <DropdownMenuItem onClick={() => setSettings(s => ({ ...s, fitMode: 'fit-screen' }))}>Fit Screen {settings.fitMode === 'fit-screen' && <span className="ml-auto">✓</span>}</DropdownMenuItem>
              <DropdownMenuItem onClick={() => setSettings(s => ({ ...s, fitMode: 'original' }))}>Original {settings.fitMode === 'original' && <span className="ml-auto">✓</span>}</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="text-white hover:bg-white/20"><Palette className="h-5 w-5" /></Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>Background</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => setSettings(s => ({ ...s, backgroundColor: 'black' }))}><div className="w-4 h-4 bg-black border rounded mr-2" /> Black {settings.backgroundColor === 'black' && <span className="ml-auto">✓</span>}</DropdownMenuItem>
              <DropdownMenuItem onClick={() => setSettings(s => ({ ...s, backgroundColor: 'gray' }))}><div className="w-4 h-4 bg-gray-900 border rounded mr-2" /> Dark Gray {settings.backgroundColor === 'gray' && <span className="ml-auto">✓</span>}</DropdownMenuItem>
              <DropdownMenuItem onClick={() => setSettings(s => ({ ...s, backgroundColor: 'white' }))}><div className="w-4 h-4 bg-white border rounded mr-2" /> White {settings.backgroundColor === 'white' && <span className="ml-auto">✓</span>}</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          <Button variant="ghost" size="icon" className="text-white hover:bg-white/20" onClick={toggleFullscreen}>
            {isFullscreen ? <Minimize className="h-5 w-5" /> : <Maximize className="h-5 w-5" />}
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex items-center justify-center overflow-hidden">
        {settings.readingMode === 'long-strip' ? (
          <div className="w-full h-full overflow-y-auto">
            <div className="flex flex-col items-center py-4 space-y-0">
              {pageUrls.map((url, index) => (
                <img key={index} src={url} alt={`Page ${index + 1}`} loading="lazy" className={cn("max-w-full", getFitModeClass())} />
              ))}
            </div>
          </div>
        ) : settings.readingMode === 'double' ? (
          <div className="flex items-center justify-center gap-1">
            {currentPage > 0 && pageUrls[currentPage - 1] && (
              <img src={pageUrls[currentPage - 1]} alt={`Page ${currentPage}`}
                className={cn("max-h-[85vh] object-contain", settings.readingDirection === 'rtl' ? 'order-2' : 'order-1')}
                style={{ maxWidth: '45vw' }} />
            )}
            {pageUrls[currentPage] && (
              <img src={pageUrls[currentPage]} alt={`Page ${currentPage + 1}`}
                className={cn("max-h-[85vh] object-contain", settings.readingDirection === 'rtl' ? 'order-1' : 'order-2')}
                style={{ maxWidth: '45vw' }} />
            )}
          </div>
        ) : (
          <div className="relative w-full h-full flex items-center justify-center">
            {pageUrls[currentPage] && (
              <img
                src={pageUrls[currentPage]}
                alt={`Page ${currentPage + 1}`}
                className={cn("object-contain transition-transform", getFitModeClass())}
                style={{ transform: `scale(${zoom / 100})`, maxHeight: '85vh' }}
              />
            )}
            <div className="absolute left-0 top-0 bottom-0 w-1/4 cursor-pointer"
              onClick={settings.readingDirection === 'rtl' ? handleNextPage : handlePrevPage} />
            <div className="absolute right-0 top-0 bottom-0 w-1/4 cursor-pointer"
              onClick={settings.readingDirection === 'rtl' ? handlePrevPage : handleNextPage} />
          </div>
        )}
      </div>

      {/* Bottom Bar */}
      <div className={cn(
        "absolute bottom-0 left-0 right-0 z-50 flex flex-col gap-2 px-4 py-3 bg-gradient-to-t from-black/80 to-transparent transition-opacity duration-300",
        showControls ? 'opacity-100' : 'opacity-0 pointer-events-none'
      )}>
        {settings.readingMode !== 'long-strip' && (
          <div className="flex items-center gap-3">
            <span className="text-white text-sm min-w-[3rem]">{currentPage + 1} / {pageUrls.length}</span>
            <Slider
              value={[currentPage + 1]}
              min={1}
              max={pageUrls.length || 1}
              step={1}
              onValueChange={([value]) => setCurrentPage(value - 1)}
              className="flex-1"
            />
          </div>
        )}

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" className="text-white hover:bg-white/20" onClick={() => setZoom(prev => Math.max(prev - 25, 50))}><ZoomOut className="h-5 w-5" /></Button>
            <span className="text-white text-sm min-w-[3rem] text-center">{zoom}%</span>
            <Button variant="ghost" size="icon" className="text-white hover:bg-white/20" onClick={() => setZoom(prev => Math.min(prev + 25, 200))}><ZoomIn className="h-5 w-5" /></Button>
            <Button variant="ghost" size="icon" className="text-white hover:bg-white/20" onClick={() => setZoom(100)}><RotateCcw className="h-4 w-4" /></Button>
          </div>

          {settings.readingMode !== 'long-strip' && (
            <div className="flex items-center gap-2">
              <Button variant="ghost" className="text-white hover:bg-white/20" onClick={handlePrevPage} disabled={currentPage === 0}>
                <ChevronLeft className="h-5 w-5 mr-1" /> Previous
              </Button>
              <Button variant="ghost" className="text-white hover:bg-white/20" onClick={handleNextPage} disabled={currentPage >= pageUrls.length - 1}>
                Next <ChevronRight className="h-5 w-5 ml-1" />
              </Button>
            </div>
          )}

          <Badge variant="secondary" className="bg-white/20 text-white border-0">
            {pageUrls.length > 0 ? Math.round(((currentPage + 1) / pageUrls.length) * 100) : 0}%
          </Badge>
        </div>
      </div>
    </div>
  );
}
