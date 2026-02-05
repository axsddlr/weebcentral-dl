export interface Manga {
  id: string;
  title: string;
  englishTitle?: string;
  coverUrl?: string;
  description?: string;
  status?: string;
  chapters?: Chapter[];
  author?: string[];
  tags?: string[];
}

export interface Chapter {
  id: string;
  number: string;
  title?: string;
  volume?: string;
  pages?: number;
  downloaded?: boolean;
  read?: boolean;
  lastReadPage?: number;
}

export interface DownloadTask {
  id: string;
  mangaId: string;
  mangaTitle: string;
  chapterNumber: string;
  status: 'pending' | 'downloading' | 'completed' | 'failed' | 'paused';
  progress: number;
  totalPages: number;
  downloadedPages: number;
  speed?: string;
  eta?: string;
  error?: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface DownloadQueue {
  tasks: DownloadTask[];
  isRunning: boolean;
  totalTasks: number;
  completedTasks: number;
  failedTasks: number;
}

export interface Config {
  outputDir: string;
  latest: boolean;
  sequence: boolean;
  zip: boolean;
  verbose: boolean;
  useEnglishTitle: boolean;
  rlc: number;
  maxSleep: number;
  maxRetries: number;
  bulkFile?: string;
}

export interface LogEntry {
  id: string;
  timestamp: Date;
  level: 'info' | 'debug' | 'warning' | 'error';
  message: string;
  source?: string;
}

export interface Stats {
  totalDownloads: number;
  totalChapters: number;
  totalPages: number;
  downloadSpeed: number;
  storageUsed: string;
  successRate: number;
  recentDownloads: RecentDownload[];
  downloadHistory: DownloadHistoryPoint[];
}

export interface RecentDownload {
  id: string;
  mangaTitle: string;
  chapterNumber: string;
  completedAt: Date;
  size: string;
}

export interface DownloadHistoryPoint {
  date: string;
  downloads: number;
  chapters: number;
}

// Manga Reader Types
export interface LibraryManga {
  id: string;
  title: string;
  coverUrl?: string;
  description?: string;
  author?: string[];
  tags?: string[];
  status?: string;
  totalChapters: number;
  downloadedChapters: number;
  readChapters: number;
  lastReadAt?: Date;
  path: string;
}

export interface LibraryChapter {
  id: string;
  number: string;
  title?: string;
  volume?: string;
  totalPages: number;
  read: boolean;
  lastReadPage: number;
  path: string;
  images: string[];
}

export interface ReaderSettings {
  readingMode: 'single' | 'long-strip' | 'double';
  readingDirection: 'ltr' | 'rtl';
  fitMode: 'fit-width' | 'fit-height' | 'fit-screen' | 'original';
  backgroundColor: 'black' | 'white' | 'gray';
  showPageNumber: boolean;
  preloadPages: number;
}

export interface ReadingProgress {
  mangaId: string;
  chapterId: string;
  currentPage: number;
  totalPages: number;
  updatedAt: Date;
}

export type View = 'dashboard' | 'search' | 'queue' | 'library' | 'reader' | 'settings' | 'logs';
