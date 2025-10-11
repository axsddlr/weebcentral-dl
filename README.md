# WeebCentral Manga Downloader

A powerful and efficient Python script for downloading manga from WeebCentral, designed for ease of use, performance, and flexibility.

This tool allows you to search for manga, download specific chapters, resume downloads, and archive chapters into `.cbz` or `.zip` formats. It features parallel image downloading, robust error handling, and rate-limiting to ensure smooth and reliable operation.

Available as both a **CLI tool** for manual downloads and a **Docker container** for automated, hands-off manga collection management.

## Features

- **Manga Search**: Find manga by title or use a direct series ID
- **Chapter Selection**: Download all chapters, specific chapters, or only new chapters since your last download
- **High-Speed Downloads**: Utilizes parallel image downloading (99 workers) to significantly speed up the process
- **Sequential Mode**: Option to download images one by one for sites that are sensitive to high traffic
- **Flexible Archiving**: Save chapters as `.cbz` (default) or `.zip` archives
- **Bulk Processing**: Download multiple series at once from a text file
- **Smart Resuming**: Automatically detect the last downloaded chapter and continue from there
- **Docker Support**: Run as a container with automatic file watching and hot reload
- **Config File Support**: Configure all settings via TOML file (hot-reloadable in Docker mode)
- **Error Handling**: Robust error handling and retry mechanisms for network issues
- **Rate-Limiting**: Avoids overwhelming the server by pausing between chapter downloads
- **Verbose Logging**: Optional detailed output for debugging and monitoring

---

## Table of Contents

- [Quick Start](#quick-start)
  - [Docker (Recommended)](#docker-recommended)
  - [CLI Usage](#cli-usage)
- [Installation](#installation)
  - [Docker Setup](#docker-setup)
  - [Local Python Setup](#local-python-setup)
- [Usage Guides](#usage-guides)
  - [Docker Mode](#docker-mode)
  - [CLI Mode](#cli-mode)
- [Configuration](#configuration)
- [Manga Management Utilities](#manga-management-utilities)
- [Code Structure](#code-structure)

---

## Quick Start

### Docker (Recommended)

Best for automated, hands-off manga collection management.

```bash
# 1. Clone and navigate to repository
git clone https://github.com/your-username/weebcentral-dl.git
cd weebcentral-dl

# 2. Create config file (optional - uses defaults if not present)
cp example.config.toml config.toml

# 3. Create manga list
echo "One-Punch Man" > manga_list.txt
echo "Jujutsu Kaisen" >> manga_list.txt

# 4. Start container
docker-compose up -d

# 5. View logs
docker-compose logs -f
```

Downloads will be saved to `./manga_downloads/`. Edit `manga_list.txt` or `config.toml` anytime - changes are detected automatically!

### CLI Usage

Best for one-off downloads or when you need fine-grained control.

```bash
# 1. Clone and install
git clone https://github.com/your-username/weebcentral-dl.git
cd weebcentral-dl
pip install -r requirements.txt

# 2. Download a manga
python main.py "Solo Leveling"

# 3. Download specific chapters
python main.py "Kagurabachi" -c 1,2,3.5

# 4. Resume from latest chapter
python main.py "Sakamoto Days" -l
```

---

## Installation

### Docker Setup

**Prerequisites**: Docker and Docker Compose installed on your system.

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-username/weebcentral-dl.git
   cd weebcentral-dl
   ```

2. **Create configuration file (optional):**

   ```bash
   cp example.config.toml config.toml
   # Edit config.toml to customize settings (or use defaults)
   ```

3. **Create manga list file:**

   ```bash
   touch manga_list.txt
   # Add manga titles (one per line) or use series IDs
   ```

4. **Build and start the container:**

   ```bash
   docker-compose up -d
   ```

That's it! The container is now running and watching for changes to `manga_list.txt` and `config.toml`.

### Local Python Setup

**Prerequisites**: Python 3.8+ installed on your system.

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-username/weebcentral-dl.git
   cd weebcentral-dl
   ```

2. **Install the required dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **You're ready to use the CLI!**

   ```bash
   python main.py --help
   ```

---

## Usage Guides

### Docker Mode

Docker mode is designed for **automated, hands-off manga collection management**. The container continuously monitors files and automatically downloads manga when changes are detected.

#### How It Works

1. **File Watching**: The container watches two files:
   - `manga_list.txt` - List of manga to download
   - `config.toml` - Download configuration settings

2. **Automatic Downloads**: When `manga_list.txt` is modified (or on container start), the downloader processes all entries in the file.

3. **Hot Reload**: Changes to `config.toml` are automatically applied to the next download batch.

#### Managing Your Manga List

Edit `manga_list.txt` to add/remove manga. The container detects changes within seconds.

**Format options:**

```text
# Method 1: Search by title (finds first match)
One-Punch Man
Jujutsu Kaisen

# Method 2: Direct series ID (most reliable)
01H9S3T35N14MQR314X4J1V4B1

# Method 3: Series ID with custom title
01J76XYFM1TWGNNQ2Y2T8V7E8Y=Custom Manga Name

# Method 4: Series ID with URL slug (legacy format)
01J76XYDXH7KT6AABVG3JAT3ZP/Shangri-La-Frontier
```

**Tips:**
- Use series IDs for reliability (avoids search ambiguity)
- Find series IDs in WeebCentral URLs: `https://weebcentral.com/series/[SERIES-ID]/...`
- Lines starting with `#` are ignored (use for comments)
- Empty lines are ignored

#### Configuring Download Behavior

Edit `config.toml` to customize how the downloader behaves. All settings have sensible defaults.

**Common configurations:**

```toml
# Download only new chapters (resume mode)
[downloader]
latest = true
verbose = true

# Fast downloads (may trigger rate limits)
[downloader]
sequence = false  # parallel mode
rlc = 20          # 20 chapters before rate limit
max_retries = 3

# Safe/slow downloads (reliable)
[downloader]
sequence = true   # sequential mode
rlc = 5           # 5 chapters before rate limit
max_sleep = 180
max_retries = 10

# Use English titles and .cbz format
[downloader]
use_english_title = true
zip = false  # false = .cbz, true = .zip
```

See `example.config.toml` for all available options with detailed comments.

#### Docker Commands

```bash
# Start container
docker-compose up -d

# View live logs
docker-compose logs -f

# Stop container
docker-compose down

# Restart container (if config changes aren't detected)
docker-compose restart

# Rebuild container (after code updates)
docker-compose up -d --build

# View container status
docker-compose ps
```

#### Customizing docker-compose.yml

**Change download location:**

```yaml
volumes:
  - /path/to/your/manga:/app/manga_downloads  # Change left side
```

**Use a different manga list file:**

```yaml
volumes:
  - ./my_custom_list.txt:/app/manga_list.txt  # Change left side

environment:
  - MANGA_LIST=manga_list.txt  # Keep this as-is (internal path)
```

**Use a different config file:**

```yaml
volumes:
  - ./my_config.toml:/app/config.toml  # Change left side

environment:
  - CONFIG_FILE=config.toml  # Keep this as-is (internal path)
```

**Run with specific series ID list:**

```yaml
volumes:
  - ./series_ids.txt:/app/manga_list.txt

environment:
  - MANGA_LIST=manga_list.txt
```

#### Troubleshooting Docker

**Container not detecting changes:**
```bash
# Check if files are mounted correctly
docker-compose exec manga-downloader ls -la /app/

# Restart container
docker-compose restart
```

**Downloads not appearing:**
```bash
# Check volume mounts
docker-compose config

# Verify download directory permissions
ls -la ./manga_downloads/
```

**Container keeps restarting:**
```bash
# Check logs for errors
docker-compose logs --tail=50

# Check if manga_list.txt exists
ls -la manga_list.txt
```

---

### CLI Mode

CLI mode provides **fine-grained control** for manual downloads and one-off tasks.

#### Basic Syntax

```bash
python main.py [query] [options]
```

#### Command-Line Arguments

| Argument              | Short | Description                                                                                                 |
| --------------------- | ----- | ----------------------------------------------------------------------------------------------------------- |
| `query`               |       | The title of the manga to search for (e.g., `"Solo Leveling"`). Ignored if using `--bulk` or `--series-id`.      |
| `--chapter`           | `-c`  | Download specific chapters, separated by commas (e.g., `12,14.5,16`).                                       |
| `--output`            | `-o`  | The directory where downloaded manga will be saved. Defaults to `./manga_downloads`.                       |
| `--latest`            | `-l`  | Download only chapters newer than the latest one found in the output directory.                             |
| `--zip`               | `-z`  | Archive chapters as `.zip` files instead of the default `.cbz` format.                                      |
| `--verbose`           | `-v`  | Enable verbose logging for detailed debug output.                                                           |
| `--bulk`              | `-b`  | Path to a text file containing manga titles or series IDs (one per line).                                   |
| `--sequence`          | `-s`  | Disable parallel downloading and download images sequentially.                                              |
| `--rlc`               |       | The number of chapters to download before pausing for rate-limiting. Defaults to `10`.                      |
| `--max-sleep`         |       | The maximum time (in seconds) to sleep for rate-limiting or retries. Defaults to `120`.                   |
| `--max-retries`       |       | The maximum number of times to retry downloading a failed image. Defaults to `5`.                           |
| `--series-id`         | `-id` | Bypass the search and download directly using a WeebCentral series ID.                                      |
| `--en`                |       | Use English title from series page instead of URL slug (for better folder naming).                          |

#### CLI Examples

**Download all chapters of a manga:**

```bash
python main.py "Wistoria: Wand and Sword"
```

**Download specific chapters:**

```bash
python main.py "Kagurabachi" -c 1,2,3.5
```

**Resume from latest chapter and save as .zip:**

```bash
python main.py "Sakamoto Days" -l -z
```

**Download using series ID (most reliable):**

```bash
python main.py -id 01J76XYFM1TWGNNQ2Y2T8V7E8Y
```

**Bulk download from text file:**

Create `manga_list.txt`:
```text
One-Punch Man
01H9S3T35N14MQR314X4J1V4B1=Jujutsu Kaisen
01J76XYDXH7KT6AABVG3JAT3ZP/Shangri-La-Frontier
My Hero Academia
```

Then run:
```bash
python main.py -b manga_list.txt
```

**Use English titles instead of romaji:**

```bash
python main.py -id 01J76XYH7K8F4J5TEBFVVFTAZ4 --en
# Downloads as "Betrothed-to-a-Fox-Demon" instead of "Kyouganeke-no-Hanayome"
```

**Sequential downloads (rate-limit friendly):**

```bash
python main.py "One Piece" -s --rlc 5
```

**Verbose mode for debugging:**

```bash
python main.py "Tower of God" -v
```

---

## Configuration

### Config File (config.toml)

Both Docker and CLI modes support configuration via `config.toml`. In Docker mode, config changes are hot-reloaded automatically. In CLI mode, settings from `config.toml` are used as defaults (CLI arguments override them).

**Create your config:**

```bash
cp example.config.toml config.toml
```

**Example configurations:**

```toml
# Resume mode - only download new chapters
[downloader]
latest = true
verbose = true
use_english_title = true

# Fast mode - parallel downloads, higher rate limits
[downloader]
sequence = false
rlc = 20
max_retries = 3

# Safe mode - sequential downloads, conservative rate limits
[downloader]
sequence = true
rlc = 5
max_sleep = 180
max_retries = 10
```

See `example.config.toml` for complete documentation of all options.

### Priority System

When using both config file and CLI arguments, the priority is:

**CLI arguments > config.toml > defaults**

Example:
```bash
# config.toml has: latest = false
# This command overrides it:
python main.py "Manga Name" -l  # Uses latest = true
```

### Output Structure

Downloads are organized into the following structure:

**Default (.cbz format):**
```
manga_downloads/
└── [manga-title]/
    ├── [manga-title]-1.cbz
    ├── [manga-title]-2.cbz
    ├── [manga-title]-12.5.cbz  # Decimal chapters supported
    └── ...
```

**With --zip flag (.zip format):**
```
manga_downloads/
└── [manga-title]/
    ├── vol_1.zip
    ├── vol_2.zip
    ├── vol_12-5.zip  # Decimal becomes hyphen
    └── ...
```

**Notes:**
- `.cbz` is recommended for comic book readers (Komga, Kavita, Tachiyomi)
- Folder name is based on the manga title (sanitized for filesystem)
- Use `--en` flag to use English titles instead of romaji

## Manga Management Utilities

The `manga_utils.py` script provides tools for managing your downloaded manga collection, including removing duplicates and renaming folders to English titles.

### Features

- **Remove Duplicates**: Detect and merge duplicate manga folders based on series ID
- **English Renaming**: Convert folder names from romaji to English titles
- **Add Cover Images**: Embed cover images into existing archives as the first page for manga readers
- **Smart Prioritization**: Keeps the folder with longer names (newer format) and more chapters
- **Dry Run Mode**: Preview all changes before applying them

### Usage

```bash
# Show help and available commands
python manga_utils.py --help

# Remove duplicates (preview mode)
python manga_utils.py remove-duplicates Y:\manga\main --dry-run

# Remove duplicates and rename kept folders to English
python manga_utils.py remove-duplicates Y:\manga\main --en

# Remove duplicates (live - actually deletes)
python manga_utils.py remove-duplicates Y:\manga\main

# Rename all manga folders to English titles (preview)
python manga_utils.py rename-english Y:\manga\main --dry-run

# Rename all manga folders to English titles (live)
python manga_utils.py rename-english Y:\manga\main

# Add cover images to existing archives (preview)
python manga_utils.py add-covers Y:\manga\main --dry-run

# Add cover images to existing archives (live)
python manga_utils.py add-covers Y:\manga\main -v
```

### How It Works

**Duplicate Detection:**
- Identifies duplicates by finding the series ID in cover image filenames (26-character `.jpg`/`.webp` files)
- Prioritizes folders based on:
  - Longer folder names (newer code format with full titles)
  - Newer modification dates
  - More downloaded chapters
- Merges chapters from duplicate folders before removal

**English Renaming:**
- Fetches the English title from WeebCentral's `<h1>` tag on the series page
- Falls back to "Associated Name(s)" if the H1 is in romaji
- Examples:
  - `Kyouganeke-no-Hanayome` → `Betrothed-to-a-Fox-Demon`
  - `Tensei-Shitara-Slime-Datta-Ken` → `That-Time-I-Got-Reincarnated-as-a-Slime`
  - `Mahou-Shoujo-ni-Akogarete` → `Gushing-Over-Magical-Girls`
  - `Zombie-Sekai-de-Harem-wo-Tsukurou` → `Lets-Build-a-Harem-in-a-Zombie-World!`

**Cover Image Embedding:**
- Finds the series cover image (26-character series ID filename: `.jpg` or `.webp`)
- Opens each CBZ/ZIP archive and adds the cover as `000-cover.jpg` (first file)
- Manga readers (Komga, Kavita, Tachiyomi, etc.) automatically use the first page as the cover thumbnail
- Skips archives that already have a cover embedded
- Works with both `.cbz` and `.zip` formats

**Important:** Always use `--dry-run` first to preview changes before making any modifications!

---

## Code Structure

The project uses a modular architecture with clear separation of concerns:

```
weebcentral-dl/
├── src/                      # Core source code package
│   ├── downloader.py         # WeebCentralDownloader class (core logic)
│   ├── utils.py              # Helper functions (sanitize, formatting)
│   ├── config.py             # Configuration loader (TOML support)
│   ├── cli.py                # CLI argument parsing
│   └── watcher.py            # Docker file watcher (hot reload)
├── main.py                   # Entry point (auto-detects CLI/Docker mode)
├── manga_utils.py            # Manga management utilities (duplicates, rename)
├── config.toml               # User configuration (optional)
├── example.config.toml       # Config template with documentation
├── manga_list.txt            # Bulk download list (Docker/CLI)
├── requirements.txt          # Python dependencies
├── Dockerfile                # Docker image definition
└── docker-compose.yml        # Docker orchestration

manga_downloads/              # Output directory (created automatically)
└── [manga-title]/
    ├── [series-id].jpg       # Cover image
    └── *.cbz / *.zip         # Chapter archives
```

**Key modules:**

- **main.py**: Entry point that detects CLI vs Docker mode automatically
- **src/downloader.py**: Core download logic (search, fetch, parallel downloads, resume)
- **src/config.py**: Centralized config loader with priority system (CLI > TOML > defaults)
- **src/watcher.py**: Docker file watcher for hot reload of `manga_list.txt` and `config.toml`
- **manga_utils.py**: Standalone utility for post-processing (duplicates, English titles, covers)