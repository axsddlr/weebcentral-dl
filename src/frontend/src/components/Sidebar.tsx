import {
  LayoutDashboard,
  Search,
  Download,
  Library,
  Settings,
  FileText,
  BookOpen,
  Sun,
  Moon
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { View } from '@/types';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { useTheme } from '@/hooks/useTheme';

interface SidebarProps {
  currentView: View;
  onViewChange: (view: View) => void;
}

const navigation = [
  { name: 'Dashboard', view: 'dashboard' as View, icon: LayoutDashboard },
  { name: 'Search Manga', view: 'search' as View, icon: Search },
  { name: 'Download Queue', view: 'queue' as View, icon: Download },
  { name: 'Library', view: 'library' as View, icon: Library },
  { name: 'Settings', view: 'settings' as View, icon: Settings },
  { name: 'Logs', view: 'logs' as View, icon: FileText },
];

export function Sidebar({ currentView, onViewChange }: SidebarProps) {
  const { resolvedTheme, setTheme } = useTheme();

  const toggleTheme = () => {
    setTheme(resolvedTheme === 'dark' ? 'light' : 'dark');
  };

  return (
    <div className="flex h-full w-64 flex-col border-r bg-card">
      {/* Header */}
      <div className="flex h-16 items-center gap-3 px-6">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
          <BookOpen className="h-5 w-5 text-primary-foreground" />
        </div>
        <div>
          <h1 className="font-semibold text-sm leading-tight">WeebCentral</h1>
          <p className="text-xs text-muted-foreground">DL Dashboard</p>
        </div>
      </div>

      <Separator />

      {/* Navigation */}
      <ScrollArea className="flex-1 px-3 py-4">
        <nav className="flex flex-col gap-1">
          {navigation.map((item) => {
            const Icon = item.icon;
            const isActive = currentView === item.view;
            
            return (
              <Button
                key={item.view}
                variant={isActive ? 'secondary' : 'ghost'}
                className={cn(
                  'w-full justify-start gap-3 h-10',
                  isActive && 'bg-secondary font-medium'
                )}
                onClick={() => onViewChange(item.view)}
              >
                <Icon className={cn(
                  'h-4 w-4',
                  isActive ? 'text-primary' : 'text-muted-foreground'
                )} />
                {item.name}
              </Button>
            );
          })}
        </nav>
      </ScrollArea>

      <Separator />

      {/* Footer */}
      <div className="p-4 space-y-3">
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-start gap-2"
          onClick={toggleTheme}
        >
          {resolvedTheme === 'dark' ? (
            <>
              <Sun className="h-4 w-4" />
              Light Mode
            </>
          ) : (
            <>
              <Moon className="h-4 w-4" />
              Dark Mode
            </>
          )}
        </Button>
        <div className="rounded-lg bg-muted p-3">
          <div className="flex items-center gap-2 mb-2">
            <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-xs font-medium">System Online</span>
          </div>
          <p className="text-xs text-muted-foreground">
            Ready to download manga
          </p>
        </div>
      </div>
    </div>
  );
}
