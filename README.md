# WeebCentral Downloader

Download manga from [WeebCentral](https://weebcentral.com) as `.cbz`/`.zip` archives. A single CLI covers one-off, bulk, and tracked-series downloads, plus a headless watcher for unattended runs.

## Quick Start

```bash
uv sync
python main.py "Solo Leveling"
```

Downloads land in `./manga_downloads/`, one folder per series and one archive per chapter.

### Docker

A pre-built image is published as `ghcr.io/axsddlr/weebcentral-dl:cli`.

```bash
docker compose up -d
```

This runs one long-running service named `manga-downloader`, whose command is the headless watcher (`python -m src.watcher`). `docker-compose.yml` bind-mounts `config.toml`, `manga_list.txt`, `manga_downloads/`, and `weebcentral.db` so state lives on the host. No ports are exposed.

One-off CLI run in the same image:

```bash
docker compose run --rm manga-downloader python main.py "Manga Title" -l
```

## CLI

`main.py` is the entry point; every mode is a flag on it.

```bash
# Search by title and download
python main.py "Solo Leveling"

# Direct by series ID (skips search)
python main.py -id 01J76XYCPSY3C4BNPBRY8JMCBE

# Latest chapters only
python main.py "Solo Leveling" -l

# Specific chapters
python main.py "Solo Leveling" -c "12,12.5,13"

# Bulk file: one entry per line (series_id=Title, bare series ID, title, or # comment)
python main.py -b manga_list.txt

# Output directory, .zip instead of .cbz, sequential image downloads
python main.py "Solo Leveling" -o ./manga_downloads -z -s

# English titles and ComicInfo.xml inside each archive
python main.py "Solo Leveling" --en --comicinfo

# Rate limiting, retries, parallelism
python main.py "Solo Leveling" --rlc 10 --max-sleep 120 --max-retries 5 --parallel-workers 99

# Tracked-series database
python main.py --track-add 01J76XYFM1TWGNNQ2Y2T8V7E8Y "Solo Leveling"
python main.py --track-import manga_list.txt
python main.py --track-list
python main.py --track-remove 01J76XYFM1TWGNNQ2Y2T8V7E8Y
python main.py --tracked     # download latest chapters for every tracked series
```

Use `-v` for debug output, `--config PATH` to load a config file other than `config.toml`.

| Flag | Description |
|------|-------------|
| `query` | Manga title to search for (positional; ignored with `-b` or `-id`) |
| `-c`, `--chapter` | Chapters to download, e.g. `12,12.5,13` |
| `-o`, `--output` | Output directory for downloads |
| `-l`, `--latest` | Only chapters after the latest one already in the output directory |
| `-z`, `--zip` | `.zip` archives instead of `.cbz` |
| `-v`, `--verbose` | Verbose debug output |
| `-b`, `--bulk` | Path to a text file of titles/IDs, one per line |
| `-s`, `--sequence` | Download images in sequence (no parallel image downloads) |
| `--rlc` | Chapters between rate-limit pauses (default: 10) |
| `--max-sleep` | Max sleep time for rate limit/retry (default: 120) |
| `--max-retries` | Max retries for image downloads (default: 5) |
| `--parallel-workers` | Parallel download workers (default: 99, `1` = sequential) |
| `-id`, `--series-id` | Direct series ID, bypasses search |
| `--en` | Use the English title from the series page |
| `--comicinfo` | Embed `ComicInfo.xml` in chapter archives |
| `--config` | Path to the config file (default: `config.toml`) |
| `--tracked` | Download latest chapters for all tracked series |
| `--track-add` | Add a series: `--track-add SERIES_ID TITLE` |
| `--track-remove` | Remove a series by ID |
| `--track-list` | List all tracked series |
| `--track-import` | Import tracked series from a file |

## Configuration

Configuration is optional — defaults apply when no file is present. To customize, copy the template:

```bash
cp example.config.toml config.toml
```

```toml
[downloader]
output_dir = "./manga_downloads"
latest = false           # only chapters newer than the latest downloaded
sequence = false         # true = download images sequentially
zip = true               # false = .cbz, true = .zip
use_english_title = false
comicinfo = false        # write ComicInfo.xml into chapter archives
verbose = false
rlc = 10                 # chapters between rate-limit pauses
max_sleep = 120          # max pause (seconds)
max_retries = 5          # image download retries
parallel_workers = 99    # 1 = sequential
check_interval = 0       # tracked-mode auto-check interval, minutes (0 = off)
```

CLI flags override the file. `--config PATH` (or the `CONFIG_FILE` variable) selects a different file. Only the `[downloader]` keys shown above are read by the CLI.

## Watcher Mode

The watcher re-runs the CLI when watched files change:

```bash
# File-list mode: re-download whenever manga_list.txt changes
python -m src.watcher

# Tracked-DB mode: process tracked series, re-checking on an interval
WATCH_TRACKED=true python -m src.watcher
```

- It also watches `config.toml` and reloads it on change.
- In tracked mode, `check_interval` (minutes) in `config.toml` controls how often the tracked database is polled; `0` disables polling, so it runs only at startup and on config changes.
- `MANGA_LIST` and `CONFIG_FILE` choose the watched files. Without `MANGA_LIST`, `manga_list.txt` must already exist in file-list mode.
- Ctrl+C stops it.

`docker compose up -d` runs this watcher as the service command.

## Environment Variables

All optional — defaults are used when unset.

| Variable | Default | Description |
|----------|---------|-------------|
| `CONFIG_FILE` | `config.toml` | Path to the TOML configuration file |
| `MANGA_LIST` | `manga_list.txt` | Path to the manga list file watched in file-list mode |
| `WATCH_TRACKED` | (unset) | `true`, `1`, or `yes` watches the SQLite tracked database instead of a file list |

## Development

```bash
uv sync                                                 # create .venv and install dependencies
uv run ruff check src/                                  # lint
uv run python -m unittest discover -p "test_*.py" -v    # tests
```

Dependencies are declared in `pyproject.toml` and locked in `uv.lock`; they include `scrapling[all]`, `Pillow`, `loguru`, `watchdog`, `tomli`, and `tomli-w`. `ruff` is the only dev dependency.

## Manga Utilities

Maintenance commands for folders you already downloaded live in `src/manga_utils.py`; the root `manga_utils.py` is a compatibility wrapper, so both entry points work:

```bash
# Remove duplicate manga folders (matched by series ID); --en also renames to English titles
python -m src.manga_utils remove-duplicates ./manga_downloads --dry-run
python -m src.manga_utils remove-duplicates ./manga_downloads --en

# Rename every folder to its English title
python -m src.manga_utils rename-english ./manga_downloads --dry-run

# Add cover images to existing archives as the first page
python -m src.manga_utils add-covers ./manga_downloads -v

# Same commands through the wrapper
python manga_utils.py add-covers ./manga_downloads --dry-run
```

Subcommands and flags: `remove-duplicates` (`--dry-run`, `--en`), `rename-english` (`--dry-run`, `-v`/`--verbose`), `add-covers` (`--dry-run`, `-v`/`--verbose`). `rename-english` and `remove-duplicates --en` additionally require `cloudscraper`, which `uv sync` does not install.
