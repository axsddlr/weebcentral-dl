/**
 * Centralized API client for WeebCentral Downloader backend.
 * All fetch calls go through this module.
 * Supports request timeout (default 30s) and AbortSignal for unmount cancellation.
 */

const BASE = '';  // Same origin in production, proxied in dev
const DEFAULT_TIMEOUT = 30_000;
const MAX_RETRIES = 2;

interface RequestOptions extends RequestInit {
  timeout?: number;
}

export async function login(token: string): Promise<{ status: string }> {
  return request('/api/auth/login', { method: 'POST', body: JSON.stringify({ token }) });
}

export async function logout(): Promise<{ status: string }> {
  return request('/api/auth/logout', { method: 'POST' });
}

export async function getAuthStatus(): Promise<{ enabled: boolean; authenticated: boolean }> {
  return request('/api/auth/status');
}

async function request<T>(path: string, options?: RequestOptions): Promise<T> {
  const { timeout = DEFAULT_TIMEOUT, ...fetchOptions } = options ?? {};

  let lastError: Error | null = null;
  for (let attempt = 1; attempt <= MAX_RETRIES + 1; attempt++) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const res = await fetch(`${BASE}${path}`, {
        headers: { 'Content-Type': 'application/json', ...(fetchOptions.headers as Record<string, string> | undefined) },
        ...fetchOptions,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (!res.ok) {
        const text = await res.text().catch(() => res.statusText);
        const error = new Error(`API ${res.status}: ${text}`);
        if (res.status >= 500 && attempt <= MAX_RETRIES) {
          lastError = error;
          continue;
        }
        throw error;
      }
      return res.json();
    } catch (err) {
      clearTimeout(timeoutId);
      lastError = err instanceof Error ? err : new Error(String(err));
      if (attempt > MAX_RETRIES || (err instanceof DOMException && err.name === 'AbortError')) {
        throw lastError;
      }
    }
  }
  throw lastError ?? new Error('Request failed');
}

// --- Search ---

export interface SearchResult {
  id: string;
  title: string;
  englishTitle?: string;
  coverUrl?: string;
  description?: string;
  author?: string[];
  tags?: string[];
}

export interface ChapterInfo {
  id: string;
  number: string;
  type: string;
}

export async function search(query: string): Promise<SearchResult[]> {
  const data = await request<{ results: SearchResult[] }>(
    `/api/search?q=${encodeURIComponent(query)}`
  );
  return data.results;
}

export async function getSeriesChapters(seriesId: string): Promise<ChapterInfo[]> {
  const data = await request<{ seriesId: string; chapters: ChapterInfo[] }>(
    `/api/series/${seriesId}/chapters`
  );
  return data.chapters;
}

// --- Queue ---

export interface QueueTask {
  id: string;
  mangaId: string;
  mangaTitle: string;
  chapterId: string;
  chapterNumber: string;
  status: 'pending' | 'downloading' | 'completed' | 'failed' | 'paused';
  progress: number;
  totalPages: number;
  downloadedPages: number;
  error?: string;
  createdAt: string;
  updatedAt: string;
}

export interface QueueState {
  tasks: QueueTask[];
  isRunning: boolean;
  totalTasks: number;
  completedTasks: number;
  failedTasks: number;
}

export async function getQueue(): Promise<QueueState> {
  return request<QueueState>('/api/queue');
}

export async function addToQueue(seriesId: string, mangaTitle: string, chapters: string[]): Promise<{ added: number }> {
  return request('/api/queue/add', {
    method: 'POST',
    body: JSON.stringify({ seriesId, mangaTitle, chapters }),
  });
}

export async function pauseQueue(): Promise<void> {
  await request('/api/queue/pause', { method: 'POST' });
}

export async function resumeQueue(): Promise<void> {
  await request('/api/queue/resume', { method: 'POST' });
}

export async function removeTask(taskId: string): Promise<void> {
  await request(`/api/queue/${taskId}`, { method: 'DELETE' });
}

export async function retryTask(taskId: string): Promise<void> {
  await request(`/api/queue/${taskId}/retry`, { method: 'POST' });
}

export async function clearCompleted(): Promise<void> {
  await request('/api/queue/completed', { method: 'DELETE' });
}

export async function retryAllFailed(): Promise<void> {
  await request('/api/queue/retry-failed', { method: 'POST' });
}

// --- Library ---

export interface LibrarySeries {
  id: string;
  title: string;
  coverUrl?: string | null;
  totalChapters: number;
  path: string;
}

export interface LibraryChapter {
  id: string;
  number: string;
  filename: string;
  totalPages: number;
  path: string;
  mtime?: number;
}

export interface RecentChapter extends LibraryChapter {
  series_title: string;
  series_path: string;
  cover_url?: string | null;
}

export async function getLibrary(): Promise<LibrarySeries[]> {
  const data = await request<{ series: LibrarySeries[] }>('/api/library');
  return data.series;
}

export async function refreshLibrary(): Promise<LibrarySeries[]> {
  const data = await request<{ series: LibrarySeries[] }>('/api/library/refresh', { method: 'POST' });
  return data.series;
}

export async function getLibraryChapters(seriesDir: string): Promise<LibraryChapter[]> {
  const data = await request<{ chapters: LibraryChapter[] }>(
    `/api/library/${encodeURIComponent(seriesDir)}/chapters`
  );
  return data.chapters;
}

export async function getRecentChapters(limit = 20): Promise<RecentChapter[]> {
  const data = await request<{ chapters: RecentChapter[] }>(`/api/library/recent?limit=${limit}`);
  return data.chapters;
}

export async function deleteSeries(seriesDir: string): Promise<void> {
  await request(`/api/library/${encodeURIComponent(seriesDir)}`, { method: 'DELETE' });
}

export interface MaintenanceResult {
  updated?: number;
  migrated?: number;
  skipped?: number;
  dry_run: boolean;
}

export async function addCoversMaintenance(dryRun: boolean): Promise<MaintenanceResult> {
  return request<MaintenanceResult>(`/api/library/maintenance/add-covers?dry_run=${dryRun ? 'true' : 'false'}`, {
    method: 'POST',
  });
}

export async function migrateCoversMaintenance(dryRun: boolean): Promise<MaintenanceResult> {
  return request<MaintenanceResult>(`/api/library/maintenance/migrate-covers?dry_run=${dryRun ? 'true' : 'false'}`, {
    method: 'POST',
  });
}

// --- Reader ---

export interface PageList {
  pages: string[];
  totalPages: number;
}

export async function getPages(seriesDir: string, archive: string): Promise<PageList> {
  return request<PageList>(
    `/api/reader/${encodeURIComponent(seriesDir)}/${encodeURIComponent(archive)}/pages`
  );
}

export function getPageUrl(seriesDir: string, archive: string, pageIndex: number): string {
  return `/api/reader/${encodeURIComponent(seriesDir)}/${encodeURIComponent(archive)}/page/${pageIndex}`;
}

export function getCoverUrl(seriesDir: string): string {
  return `/api/reader/${encodeURIComponent(seriesDir)}/cover`;
}

// --- Config ---

export interface AppConfig {
  outputDir: string;
  latest: boolean;
  sequence: boolean;
  zip: boolean;
  verbose: boolean;
  useEnglishTitle: boolean;
  comicinfo: boolean;
  rlc: number;
  maxSleep: number;
  maxRetries: number;
  parallelWorkers: number;
  libraryPaths: string[];
}

export async function getConfig(): Promise<AppConfig> {
  return request<AppConfig>('/api/config');
}

export async function updateConfig(config: Partial<AppConfig>): Promise<AppConfig> {
  return request<AppConfig>('/api/config', {
    method: 'PUT',
    body: JSON.stringify(config),
  });
}

export async function resetConfig(): Promise<AppConfig> {
  return request<AppConfig>('/api/config/reset', { method: 'POST' });
}

// --- Stats ---

export interface DashboardStats {
  totalSeries: number;
  totalChapters: number;
  storageUsed: string;
  queueActive: number;
  queueCompleted: number;
  queueFailed: number;
}

export async function getStats(): Promise<DashboardStats> {
  return request<DashboardStats>('/api/stats');
}

// --- Logs ---

export interface LogEntry {
  id: string;
  timestamp: string;
  level: string;
  message: string;
  source?: string;
}

export async function getLogs(): Promise<LogEntry[]> {
  const data = await request<{ logs: LogEntry[] }>('/api/logs');
  return data.logs;
}

export async function clearLogs(): Promise<void> {
  await request('/api/logs', { method: 'DELETE' });
}

// --- Tracked ---

export interface TrackedManga {
  series_id: string;
  title: string;
  added_at: string;
  last_checked_at: string | null;
  cover_url: string | null;
}

export async function getTracked(): Promise<{ series: TrackedManga[]; total: number }> {
  return request('/api/tracked');
}

export async function addTracked(seriesId: string, title: string, coverUrl?: string): Promise<void> {
  await request('/api/tracked', {
    method: 'POST',
    body: JSON.stringify({ seriesId, title, coverUrl }),
  });
}

export async function removeTracked(seriesId: string): Promise<void> {
  await request(`/api/tracked/${encodeURIComponent(seriesId)}`, { method: 'DELETE' });
}

export async function importTracked(): Promise<{ added: number; skipped: number }> {
  return request('/api/tracked/import', { method: 'POST' });
}
