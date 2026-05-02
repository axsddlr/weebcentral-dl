import type * as api from '@/services/api';

export interface LibraryManga extends api.LibrarySeries {
  downloadedChapters: number;
  readChapters: number;
  lastReadAt?: string;
}

export interface LibraryChapter extends api.LibraryChapter {
  read: boolean;
  lastReadPage: number;
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

export type View = 'dashboard' | 'search' | 'queue' | 'library' | 'reader' | 'settings' | 'logs';
