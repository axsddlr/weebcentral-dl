export interface Series {
  id: string;
  title: string;
  jp: string;
  ch: number;
  read: number;
  vol: number;
  lastRead: string;
  progress: number;
  status: 'reading' | 'caught-up' | 'complete';
  tags: string[];
  size: string;
  author: string;
  c: [string, string, string];
}

export const SERIES: Series[] = [
  { id: 's1',  title: '2.5 Dimensional Seduction', jp: '２.５次元の誘惑', ch: 378, read: 312, vol: 17, lastRead: '2h ago', progress: 0.83, status: 'reading', tags: ['Romance','Comedy','School'], size: '4.2 GB', author: 'Yu Hashimoto', c: ['#FF2D87','#7A1FFF','#0A0A14'] },
  { id: 's2',  title: 'Harem Ou no Isekai Press Manyuuki', jp: 'ハーレム王の異世界プレス漫遊記', ch: 4, read: 4, vol: 1, lastRead: '1h ago', progress: 1.0, status: 'caught-up', tags: ['Isekai','Adult','Comedy'], size: '180 MB', author: 'Haibanemumi', c: ['#FF1F6D','#FF6BAA','#1A0A1A'] },
  { id: 's3',  title: 'Shangri-La Frontier', jp: 'シャングリラ・フロンティア', ch: 124, read: 89, vol: 13, lastRead: 'yesterday', progress: 0.72, status: 'reading', tags: ['Action','Fantasy','Game'], size: '1.8 GB', author: 'Katarina', c: ['#00E5FF','#1F66FF','#0A0F1F'] },
  { id: 's4',  title: 'A Betrayed S-Rank Adventurer', jp: '裏切られたＳランク冒険者', ch: 75, read: 28, vol: 11, lastRead: '3d ago', progress: 0.37, status: 'reading', tags: ['Action','Fantasy'], size: '920 MB', author: 'Hiiragi', c: ['#FF6B00','#FFB800','#1F0F08'] },
  { id: 's5',  title: 'A Harem in the Fantasy Dungeon', jp: '異世界迷宮でハーレムを', ch: 101, read: 101, vol: 11, lastRead: '6h ago', progress: 1.0, status: 'caught-up', tags: ['Isekai','Adult','Adventure'], size: '1.4 GB', author: 'Soga Suteji', c: ['#A855F7','#EC4899','#1A0A1F'] },
  { id: 's6',  title: 'Ao Ashi', jp: 'アオアシ', ch: 411, read: 200, vol: 39, lastRead: 'last week', progress: 0.49, status: 'reading', tags: ['Sports','Drama'], size: '5.1 GB', author: 'Yugo Kobayashi', c: ['#22D3EE','#0EA5E9','#0A1018'] },
  { id: 's7',  title: "Frieren: Beyond Journey's End", jp: '葬送のフリーレン', ch: 132, read: 132, vol: 14, lastRead: '4h ago', progress: 1.0, status: 'caught-up', tags: ['Fantasy','Drama','Slice'], size: '1.6 GB', author: 'Kanehito Yamada', c: ['#E5E7EB','#A78BFA','#0F0A1A'] },
  { id: 's8',  title: 'Chainsaw Man', jp: 'チェンソーマン', ch: 165, read: 158, vol: 17, lastRead: '12h ago', progress: 0.95, status: 'reading', tags: ['Action','Horror','Dark'], size: '2.0 GB', author: 'Tatsuki Fujimoto', c: ['#F97316','#DC2626','#0A0805'] },
  { id: 's9',  title: 'Dandadan', jp: 'ダンダダン', ch: 178, read: 140, vol: 16, lastRead: '2d ago', progress: 0.78, status: 'reading', tags: ['Action','Romance','Occult'], size: '2.3 GB', author: 'Yukinobu Tatsu', c: ['#FBBF24','#EF4444','#1A0A0A'] },
  { id: 's10', title: 'Solo Leveling', jp: '俺だけレベルアップな件', ch: 200, read: 200, vol: 18, lastRead: '2 weeks', progress: 1.0, status: 'complete', tags: ['Action','Fantasy'], size: '3.1 GB', author: 'Chugong', c: ['#3B82F6','#1E1B4B','#0A0A1F'] },
  { id: 's11', title: 'Vinland Saga', jp: 'ヴィンランド・サガ', ch: 210, read: 95, vol: 28, lastRead: '5d ago', progress: 0.45, status: 'reading', tags: ['Action','Historical','Drama'], size: '4.7 GB', author: 'Makoto Yukimura', c: ['#FCD34D','#92400E','#1A1108'] },
  { id: 's12', title: 'Tengoku de Akuma ga Boku wo Miwaku', jp: '天国で悪魔が僕を魅惑する', ch: 60, read: 12, vol: 6, lastRead: '4d ago', progress: 0.20, status: 'reading', tags: ['Adult','Ecchi','Comedy'], size: '540 MB', author: 'Gingami Meteor', c: ['#F472B6','#BE185D','#1A0A14'] },
  { id: 's13', title: 'Ore wa Lolicon ja nai', jp: '俺はロリコンじゃない', ch: 80, read: 80, vol: 8, lastRead: 'last month', progress: 1.0, status: 'complete', tags: ['Comedy','Slice'], size: '720 MB', author: 'URAN', c: ['#34D399','#059669','#06170F'] },
  { id: 's14', title: 'Sekai Saikyou no Kishi', jp: '世界最強の騎士', ch: 24, read: 6, vol: 3, lastRead: 'today', progress: 0.25, status: 'reading', tags: ['Action','Fantasy','Drama'], size: '320 MB', author: 'Isobe Kazuma', c: ['#60A5FA','#7C3AED','#0A0A1F'] },
];

export const ACTIVITY_14D = [12, 28, 18, 45, 8, 22, 67, 34, 19, 52, 41, 14, 88, 23];

export const QUEUE_SAMPLE = [
  { id: 'q1', series: 's3', ch: 90,  status: 'downloading', progress: 0.42, eta: '00:48', speed: '2.4 MB/s', pages: 30, page: 13 },
  { id: 'q2', series: 's6', ch: 201, status: 'downloading', progress: 0.18, eta: '02:14', speed: '1.8 MB/s', pages: 36, page: 7 },
  { id: 'q3', series: 's11', ch: 96, status: 'pending',     progress: 0,    eta: '—',     speed: '—',        pages: 32, page: 0 },
  { id: 'q4', series: 's12', ch: 13, status: 'pending',     progress: 0,    eta: '—',     speed: '—',        pages: 28, page: 0 },
  { id: 'q5', series: 's14', ch: 7,  status: 'pending',     progress: 0,    eta: '—',     speed: '—',        pages: 26, page: 0 },
  { id: 'q6', series: 's4',  ch: 29, status: 'complete',    progress: 1.0,  eta: '—',     speed: '—',        pages: 30, page: 0 },
];

export const NEW_AVAILABLE = [
  { series: 's3',  count: 35,  latest: 124, since: '3d ago' },
  { series: 's6',  count: 211, latest: 411, since: '6h ago' },
  { series: 's11', count: 115, latest: 210, since: '5d ago' },
  { series: 's14', count: 18,  latest: 24,  since: '2h ago' },
  { series: 's8',  count: 7,   latest: 165, since: '12h ago' },
];

export const READER_PAGES = [
  { n: 1, c: ['#FF2D87','#7A1FFF'] as [string,string], caption: 'CHAPTER OPENING' },
  { n: 2, c: ['#1F1F2E','#0A0A14'] as [string,string], caption: 'EXTERIOR · DAY' },
  { n: 3, c: ['#FF6BAA','#FF1F6D'] as [string,string], caption: 'REACTION SHOT' },
  { n: 4, c: ['#0A0A14','#1F1F2E'] as [string,string], caption: 'DIALOGUE PAGE' },
  { n: 5, c: ['#7A1FFF','#00E5FF'] as [string,string], caption: 'ACTION SPREAD' },
  { n: 6, c: ['#1F1F2E','#0A0A14'] as [string,string], caption: 'CHAPTER CLOSE' },
];

export const LOG_LINES = [
  { t: '14:32:08.124', lvl: 'info',  src: 'queue',   msg: 'Started download: Shangri-La Frontier ch 90 (30 pages)' },
  { t: '14:32:09.482', lvl: 'debug', src: 'fetcher', msg: 'GET /series/shangri-la-frontier/chapter/90 → 200 (218ms)' },
  { t: '14:32:10.001', lvl: 'debug', src: 'fetcher', msg: 'Parsed 30 image URLs from chapter manifest' },
  { t: '14:32:11.330', lvl: 'info',  src: 'tracker', msg: 'New chapter found: Ao Ashi ch 411 (last seen 410)' },
  { t: '14:32:12.018', lvl: 'warn',  src: 'fetcher', msg: 'Slow response on page 4/30 (1.8s) — retrying' },
  { t: '14:32:13.224', lvl: 'info',  src: 'queue',   msg: 'Page 4/30 complete (1.4 MB, 2nd attempt)' },
  { t: '14:32:14.882', lvl: 'debug', src: 'storage', msg: 'CBZ assembly: 13 pages buffered' },
  { t: '14:32:16.140', lvl: 'error', src: 'fetcher', msg: 'Connection reset on page 18/30 — backing off 4s' },
  { t: '14:32:20.401', lvl: 'info',  src: 'fetcher', msg: 'Resumed page 18/30 successfully' },
  { t: '14:32:22.118', lvl: 'info',  src: 'tracker', msg: 'Scan complete — 3 series updated, 1 new chapter' },
  { t: '14:32:23.776', lvl: 'debug', src: 'library', msg: 'Indexed 59 series, 10,774 chapters, 80.2 GB' },
  { t: '14:32:24.901', lvl: 'info',  src: 'queue',   msg: 'Queue paused by user (active: 2, pending: 3)' },
];

export const seriesById: Record<string, Series> = {};
SERIES.forEach((s) => { seriesById[s.id] = s; });
