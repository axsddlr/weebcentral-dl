import { useState } from 'react';
import { Sidebar } from '@/components/Sidebar';
import { Dashboard } from '@/sections/Dashboard';
import { Search } from '@/sections/Search';
import { Queue } from '@/sections/Queue';
import { Library } from '@/sections/Library';
import { Reader } from '@/sections/Reader';
import { Settings } from '@/sections/Settings';
import { Logs } from '@/sections/Logs';
import { Tracked } from '@/sections/Tracked';
import type { View, LibraryManga, LibraryChapter } from '@/types';
import { Toaster } from '@/components/ui/sonner';
import { ThemeProvider } from '@/hooks/useTheme';

function App() {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const [selectedManga, setSelectedManga] = useState<LibraryManga | null>(null);
  const [selectedChapter, setSelectedChapter] = useState<LibraryChapter | null>(null);

  const handleMangaSelect = (manga: LibraryManga, chapter: LibraryChapter) => {
    setSelectedManga(manga);
    setSelectedChapter(chapter);
  };

  const handleViewChange = (view: View) => {
    setCurrentView(view);
  };

  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard />;
      case 'search':
        return <Search />;
      case 'queue':
        return <Queue />;
      case 'library':
        return <Library onViewChange={handleViewChange} onMangaSelect={handleMangaSelect} />;
      case 'reader':
        return <Reader manga={selectedManga} chapter={selectedChapter} onViewChange={handleViewChange} />;
      case 'settings':
        return <Settings />;
      case 'logs':
        return <Logs />;
      case 'tracked':
        return <Tracked />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <ThemeProvider>
      <div className="flex h-screen bg-background text-foreground">
        <Sidebar currentView={currentView} onViewChange={handleViewChange} />
        <main className="flex-1 overflow-auto">
          {renderView()}
        </main>
        <Toaster />
      </div>
    </ThemeProvider>
  );
}

export default App;
