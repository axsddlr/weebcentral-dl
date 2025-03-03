# Manga Downloader

A Python script for downloading manga chapters from weebcentral.com with support for parallel image downloading, chapter filtering, and automatic ZIP archive creation.

## Features

- Search and download manga chapters
- Parallel image downloading for faster retrieval
- Create ZIP archives of chapters
- Continue from latest downloaded chapter
- Filter chapters by number
- Verbose debugging output
- Skip existing downloads
- Error notifications via ntfy

## Requirements

```bash
pip install requests selectolax playwright
playwright install chromium
```

## Usage

Basic usage:

```bash
python main.py
```

### Command Line Arguments

- `-o, --output DIR`: Set output directory (default: manga_downloads)
- `-z, --zip`: Create ZIP archives for chapters
- `-v, --verbose`: Enable debug output
- `--no-skip`: Don't skip existing ZIP files
- `--chapter-filter N`: Download only chapters above N
- `-l, --latest`: Continue from latest downloaded chapter
- `-t, --title TEXT`: Specify manga title to search for (default: wistoria)
  - Supports hyphenated titles (e.g., "The-Player-That-Cant-Level-Up")
  - Hyphens are automatically converted to spaces during search
- `-b, --bulk FILE`: Path to text file containing manga titles (one per line)
  - Each title can be space-separated or hyphenated
  - Processes multiple manga titles sequentially

### Examples

1. Search with hyphenated titles (hyphens will be converted to spaces):

```bash
python main.py -t "The-Player-That-Cant-Level-Up" -z
```

2. Download all chapters and create ZIP archives:

```bash
python main.py -z
```

2. Continue downloading from the latest chapter:

```bash
python main.py -l -z
```

3. Download multiple manga titles from a file:

```bash
python main.py -b manga_list.txt -z -v
```

4. Download chapters after chapter 46:

```bash
python main.py --chapter-filter 46 -z
```

5. Download to custom directory with verbose output:

```bash
python main.py -o "my_manga" -v -z
```

### Output Structure

```
manga_downloads/
└── manga-title/
    ├── vol_001.zip
    ├── vol_002.zip
    └── ...
```

## Notes

- ZIP files are named in the format `vol_XXX.zip` where XXX is the chapter number
- The script automatically handles chapter numbering and sorting
- Use verbose mode (-v) for detailed download progress
- The script will skip existing ZIP files unless --no-skip is used

## Error Handling

- Invalid chapter numbers are skipped with warnings
- Network errors are handled gracefully
- Duplicate downloads are prevented

## Error Notifications

The script supports optional error notifications through ntfy. When errors occur during:
- Manga search failures
- Chapter processing issues
- Image download failures

Notifications are sent to the configured ntfy endpoint specified in `config.toml`. To enable notifications:

1. Create a `config.toml` file in the script directory
2. Add your ntfy URL:
```toml
[ntfy]
ntfy_url = "your_ntfy_url_here"
```

Notifications are optional - if `config.toml` is missing or the URL is empty, the script will run without sending notifications.

## Dependencies

- requests: HTTP requests
- selectolax: HTML parsing
- playwright: Dynamic web content loading
- concurrent.futures: Parallel downloading
- tomli: TOML configuration file parsing
