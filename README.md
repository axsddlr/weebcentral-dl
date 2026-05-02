# WeebCentral Downloader

Download manga from [WeebCentral](https://weebcentral.com) as `.cbz`/`.zip` archives. CLI for one-off and bulk downloads, plus a React web UI with a queue manager, local reader, and tracked series database.

## Quick Start

```bash
pip install -r requirements.txt
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

```bash
docker-compose up -d              # API + UI on :8000
docker-compose --profile watcher up -d  # + auto-download watcher
```

To read existing manga collections from other host folders, mount them as volumes in `docker-compose.yml`:

```yaml
services:
  manga-downloader:
    volumes:
      - ./manga_downloads:/app/manga_downloads
      - /path/to/kavita/manga:/app/external/manga:ro    # add this
```

Then add the **container path** to `library_paths` in `config.toml`:

```toml
library_paths = ["/app/external/manga"]
```

The folder structure should be `<manga_series>/<vol_001.cbz or chapter.cbz>`. The Library page merges all paths into one view. Use `:ro` (read-only) for collections you don't want the downloader to modify.

## Library Reader

The Library page scans your output directory and any additional folders configured in `library_paths`. Supports `.cbz`/`.zip` archives. Reading modes: long-strip, single page, double page. Keyboard navigation, zoom, fit modes, light/dark theme.

Add external collections via Settings > Library Paths (use **container paths** in Docker, **host paths** when running locally).

## Configuration

Copy `example.config.toml` to `config.toml`:

```toml
[downloader]
output_dir = "./manga_downloads"
library_paths = []       # extra folders for the Library reader
use_english_title = false
zip = false              # false = .cbz, true = .zip
latest = false           # only new chapters
rlc = 10                 # chapters between rate-limit pauses
max_sleep = 120          # max pause (seconds)
max_retries = 5          # image download retries
parallel_workers = 99    # 1 = sequential
```

Settings are editable from the Web UI and saved automatically.

## Watcher Mode

Automatically downloads new chapters for tracked series:

```bash
# Docker
docker-compose --profile watcher up -d

# Manual (env var switches to DB-tracked mode)
WATCH_TRACKED=true python -m src.watcher
```

Without `WATCH_TRACKED`, the watcher monitors `manga_list.txt` for changes.

## Development

```bash
cd src/frontend && npm run dev    # Vite dev server
cd src/frontend && npm run lint   # ESLint
python -m pytest -q               # tests
```
