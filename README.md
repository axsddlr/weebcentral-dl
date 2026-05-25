# WeebCentral Downloader

Download manga from [WeebCentral](https://weebcentral.com) as `.cbz`/`.zip` archives. CLI for one-off and bulk downloads, plus a React web UI with a queue manager, local reader, and tracked series database.

## Quick Start

```bash
uv sync
python main.py "Solo Leveling"
```

## CLI

```bash
# Search and download
python main.py "Solo Leveling"

# Direct by series ID (skips search)
python main.py -id 01J76XYCPSY3C4BNPBRY8JMCBE

# Latest chapters only
python main.py "Solo Leveling" -l

# Bulk from file (series_id=Title or bare title, one per line)
python main.py -b manga_list.txt

# Tracked database — replace manga_list.txt with SQLite
python main.py --track-add 01J76XY... "Solo Leveling"
python main.py --track-import manga_list.txt
python main.py --tracked            # download all tracked
python main.py --track-list         # show tracked series

# Other flags
python main.py -z                   # .zip instead of .cbz
python main.py -s                   # sequential (no parallel)
python main.py --en                 # use English title
python main.py -c "12,12.5,13"     # specific chapters
```

## Web UI

```bash
cd src/frontend && npm install && npm run build   # one-time
python server.py                                   # http://localhost:8000
```

Pages: Dashboard, Search (typeahead dropdown), **Tracked Manga**, Download Queue, Library (local reader), Settings, Logs.

### Docker

Pre-built multi-arch image (amd64 + arm64):

```bash
docker pull ghcr.io/axsddlr/weebcentral-dl:ui
```

Then run with `docker-compose` (remove `build:` from compose to use the pulled image):

```bash
docker-compose up -d              # API + UI on :8000
docker-compose --profile watcher up -d  # + auto-download watcher
```

For local builds, use `build: .` in `docker-compose.yml`.

### How the Library works

The Library reader scans `manga_downloads/` by default — **the same folder the downloader writes to**. Downloaded manga appear in the Library automatically. No moving files, no extra config.

To also read manga collections you already have from other sources (not downloaded by this tool), mount them separately:

```bash
mkdir library
cp -r /path/to/kavita/manga library/kavita
```

Then add `/app/library` to `library_paths` in `config.toml`:

```toml
library_paths = ["/app/library"]
```

Or mount specific folders directly in `docker-compose.yml`:

```yaml
volumes:
  - /path/to/manga:/app/external/manga:ro
```

The folder structure should be `<manga_series>/<vol_001.cbz or chapter.cbz>`. The Library page merges all paths into one view. Use `:ro` (read-only) for collections you don't want the downloader to modify.

## Library Reader

The Library page scans `manga_downloads/` (your download destination) plus any extra folders in `library_paths`. Supports `.cbz`/`.zip` archives. Reading modes: long-strip, single page, double page. Keyboard navigation, zoom, fit modes, light/dark theme.

Add external collections via Settings > Library Paths (use **container paths** in Docker, **host paths** when running locally).

## Configuration

Copy `example.config.toml` to `config.toml`:

```toml
[downloader]
output_dir = "./manga_downloads"
library_paths = []       # extra folders for the Library reader
use_english_title = false
comicinfo = false        # write ComicInfo.xml into chapter archives
zip = false              # false = .cbz, true = .zip
latest = false           # only new chapters
rlc = 10                 # chapters between rate-limit pauses
max_sleep = 120          # max pause (seconds)
max_retries = 5          # image download retries
parallel_workers = 99    # 1 = sequential
```

Settings are editable from the Web UI and saved automatically.

To enable ComicInfo output from the UI, turn on `ComicInfo Metadata` in Settings or set `comicinfo = true` in `config.toml`.

The Settings page also includes library maintenance actions for adding archive covers and migrating legacy cover filenames in place.

## Watcher Mode

Automatically downloads new chapters for tracked series:

```bash
# Docker
docker-compose --profile watcher up -d

# Manual (env var switches to DB-tracked mode)
WATCH_TRACKED=true python -m src.watcher
```

Without `WATCH_TRACKED`, the watcher monitors `manga_list.txt` for changes.

## API Authentication

The Web UI can be protected with an API token to prevent unauthorized access on shared networks.

### Setting up

**Docker Compose (CLI):** Add env vars to a `.env` file or inline in `docker-compose.yml`:

```bash
# Create .env from the example
cp .env.example .env
# Edit .env and set: API_TOKEN="your-secret-token"

# Or set inline in docker-compose.yml under environment:
#   - API_TOKEN=your-secret-token

# Then restart
docker compose up -d
```

**Portainer:** Edit the container's **Environment variables** section (not the stack's) and add `API_TOKEN` with your value. Then redeploy the stack.

### How it works

Once `API_TOKEN` is set:

| Access type | Protected? | How to authenticate |
|-------------|-----------|-------------------|
| Web UI (browser) | State-changing actions only | Enter token in Settings → API Authentication (sent as httpOnly cookie) |
| HTTP API (curl) | All POST/PUT/DELETE routes | Pass `X-API-Token: your-secret-token` header |
| WebSocket (live updates) | All WebSocket connections | Cookie sent automatically on handshake |
| GET routes (library, reader, search) | **Not** protected | Public read access — covers, chapters, and search are open |
| CLI / local usage | **Not** protected | Only enforced over HTTP; local Python usage is unaffected |

### Browser setup

Open the Web UI, go to **Settings → Advanced → API Authentication**, enter your token, and click **Login**. The backend sets an **httpOnly cookie** — JavaScript can't read it, preventing XSS-based token theft. The cookie is sent automatically with all subsequent requests and WebSocket handshakes. Click **Logout** to clear it.

### API examples

```bash
# Read routes (no auth needed)
curl http://localhost:8000/api/library
curl http://localhost:8000/api/stats

# State-changing routes (auth required)
curl -X POST http://localhost:8000/api/library/refresh \
  -H "X-API-Token: your-secret-token"

curl -X POST http://localhost:8000/api/tracked/import \
  -H "X-API-Token: your-secret-token"

# Login (sets httpOnly cookie for browser sessions)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"token":"your-secret-token"}' \
  -c cookies.txt

# Subsequent requests with cookie
curl -X POST http://localhost:8000/api/library/refresh \
  -b cookies.txt
```

## Environment Variables

All configuration is optional — default values are used if not set.

| Variable | Default | Description |
|----------|---------|-------------|
| `API_TOKEN` | (none) | If set, all non-GET API routes and WebSocket connections require this token |
| `HOST` | (none) | Server hostname/domain for CORS allowlist (for remote access) |
| `CONFIG_FILE` | `config.toml` | Path to TOML configuration file |
| `MANGA_LIST` | `manga_list.txt` | Path to manga list file for the file-based watcher |
| `WATCH_TRACKED` | (none) | Set to `true` to watch the SQLite-tracked database instead of a file list |

## Development

```bash
cd src/frontend && npm run dev    # Vite dev server
cd src/frontend && npm run lint   # ESLint
python -m pytest -q               # tests
```

## Manga Utilities

The manga maintenance commands now live in `src/manga_utils.py`. The top-level `manga_utils.py` file remains as a compatibility wrapper, so both of these work:

```bash
python manga_utils.py --help
python -m src.manga_utils --help
```
