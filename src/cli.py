#!/usr/bin/env python3
"""CLI interface for WeebCentral Downloader"""
import argparse
import os
import re
import sys
from typing import Optional, Set
from src.logging_utils import logger

from src.downloader import WeebCentralDownloader
from src.config import load_config
from src.database import get_all_tracked, add_tracked, remove_tracked, import_from_file, update_last_checked


SERIES_ID_PATTERN = re.compile(r'^[A-Z0-9]{26}$')


def parse_chapter_arg(chapter_arg: Optional[str]) -> Optional[Set[str]]:
    """Parse comma-separated chapter argument into set"""
    if not chapter_arg:
        return None
    return {p.strip() for p in chapter_arg.split(",") if p.strip()}


def configure_logger(verbose: bool):
    """Configure loguru logger based on verbosity"""
    logger.remove()  # Remove default handler
    if verbose:
        # Verbose mode: show DEBUG and above with detailed formatting
        logger.add(
            sys.stderr,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
            level="DEBUG",
            colorize=True
        )
    else:
        # Normal mode: show INFO and above with simple formatting
        logger.add(
            sys.stderr,
            format="<level>{message}</level>",
            level="INFO",
            colorize=True
        )


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Manga downloader script (WeebCentral)"
    )
    parser.add_argument(
        "query",
        nargs="*",
        help="Manga title to search for (ignored if --bulk or --series-id is used)",
    )
    parser.add_argument(
        "-c",
        "--chapter",
        type=str,
        default=None,
        help="Specific chapter(s) to download, e.g. 12,12.5,13 (comma-separated)",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output_dir",
        default=None,
        help="Output directory for downloads",
    )
    parser.add_argument(
        "-l",
        "--latest",
        action="store_true",
        help="Download only chapters after the latest one in the output directory",
    )
    parser.add_argument(
        "-z",
        "--zip",
        action="store_true",
        help="Create zip archives for chapters (vol_NNN.zip)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose debug output"
    )
    parser.add_argument(
        "-b",
        "--bulk",
        type=str,
        dest="bulk_file",
        help="Path to text file containing manga titles (one per line; you can use seriesid=optional-title)",
    )
    parser.add_argument(
        "-s",
        "--sequence",
        action="store_true",
        help="Download images in sequence (disable parallel downloading)",
    )
    parser.add_argument(
        "--rlc", type=int, default=None, help="Chapters between rate limits (default: 10)"
    )
    parser.add_argument(
        "--max-sleep",
        type=int,
        default=None,
        dest="max_sleep",
        help="Max sleep time for rate limit/retry (default: 120)",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=None,
        dest="max_retries",
        help="Max retries for image download (default: 5)",
    )
    parser.add_argument(
        "--parallel-workers",
        type=int,
        default=None,
        dest="parallel_workers",
        help="Number of parallel download workers (default: 99, set to 1 for sequential)",
    )
    parser.add_argument(
        "-id",
        "--series-id",
        type=str,
        dest="series_id",
        help="Direct WeebCentral series ID (bypasses search)",
    )
    parser.add_argument(
        "--en",
        action="store_true",
        dest="use_english_title",
        help="Use English title from series page instead of URL slug",
    )
    parser.add_argument(
        "--comicinfo",
        action="store_true",
        help="Embed ComicInfo.xml in chapter archives",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=os.environ.get("CONFIG_FILE", "config.toml"),
        help="Path to config file (default: config.toml)",
    )
    parser.add_argument(
        "--tracked",
        action="store_true",
        help="Download latest chapters for all tracked manga in the database",
    )
    parser.add_argument(
        "--track-add",
        type=str,
        nargs=2,
        metavar=("SERIES_ID", "TITLE"),
        help="Add a series to tracked manga DB (e.g. --track-add ID 'Title')",
    )
    parser.add_argument(
        "--track-remove",
        type=str,
        metavar="SERIES_ID",
        help="Remove a series from tracked manga DB",
    )
    parser.add_argument(
        "--track-list",
        action="store_true",
        help="List all tracked manga in the database",
    )
    parser.add_argument(
        "--track-import",
        type=str,
        metavar="FILE",
        help="Import tracked manga from a manga.txt file",
    )
    args = parser.parse_args()

    # Build CLI overrides dict (only include non-None values)
    cli_overrides = {
        'latest': args.latest if args.latest else None,
        'sequence': args.sequence if args.sequence else None,
        'zip': args.zip if args.zip else None,
        'verbose': args.verbose if args.verbose else None,
        'use_english_title': args.use_english_title if args.use_english_title else None,
        'rlc': args.rlc,
        'max_sleep': args.max_sleep,
        'max_retries': args.max_retries,
        'parallel_workers': args.parallel_workers,
        'output_dir': args.output_dir,
        'bulk_file': args.bulk_file,
        'series_id': args.series_id,
        'chapters': args.chapter,
        'comicinfo': args.comicinfo if args.comicinfo else None,
    }

    # Load query from args
    if args.query:
        cli_overrides['query'] = " ".join(args.query).strip()

    # Remove None values
    cli_overrides = {k: v for k, v in cli_overrides.items() if v is not None}

    # Load merged config (CLI args override TOML)
    config = load_config(args.config, cli_overrides)

    # Configure logger
    configure_logger(config.verbose)

    # Create downloader with config
    downloader = WeebCentralDownloader(config)
    chapters_to_download = parse_chapter_arg(config.chapters)

    # --- Tracked manga DB commands ---
    if args.track_add:
        sid, title = args.track_add
        if add_tracked(sid, title):
            logger.info(f"Added '{title}' ({sid}) to tracked manga")
        else:
            logger.error(f"Failed to add {sid}")
        sys.exit(0)

    if args.track_remove:
        if remove_tracked(args.track_remove):
            logger.info(f"Removed {args.track_remove} from tracked manga")
        else:
            logger.warning(f"Series {args.track_remove} not found in tracked manga")
        sys.exit(0)

    if args.track_list:
        series = get_all_tracked()
        if series:
            for s in series:
                logger.info(f"  {s['series_id']}  {s['title']}")
            logger.info(f"Total: {len(series)} tracked")
        else:
            logger.info("No tracked manga.")
        sys.exit(0)

    if args.track_import:
        added, skipped = import_from_file(args.track_import)
        logger.info(f"Imported {added} entries from {args.track_import} ({skipped} skipped)")
        sys.exit(0)

    if args.tracked:
        process_tracked_mode(downloader, chapters_to_download)
        sys.exit(0)

    # Process based on mode
    if config.bulk_file:
        process_bulk_mode(downloader, config.bulk_file, chapters_to_download)
    elif config.series_id:
        downloader.process_manga(
            series_id=config.series_id, chapters_to_download=chapters_to_download
        )
    elif config.query:
        downloader.process_manga(title=config.query, chapters_to_download=chapters_to_download)
    else:
        logger.error("No manga title, series ID, or bulk file specified. Use -h for help.")
        sys.exit(1)


def process_bulk_mode(downloader: WeebCentralDownloader, bulk_file: str, chapters_to_download: Optional[Set[str]]):
    """Process manga from bulk file.

    Accepted line formats:
        series_id=title       Direct ID with optional display title
        series_id/title       Same as =, also handles weebcentral.com/series/ID/title URLs
        A0B1C2... (26 chars)  Bare series ID (auto-detected)
        Manga Title           Search by title on WeebCentral
        # comment             Ignored
    """
    try:
        with open(bulk_file, "r", encoding="utf-8") as f:
            raw_lines = [line.strip() for line in f]
    except FileNotFoundError:
        logger.error(f"Could not find bulk file: {bulk_file}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error reading bulk file: {e}")
        sys.exit(1)

    manga_list = [line for line in raw_lines if line and not line.startswith("#")]
    logger.info(f"Found {len(manga_list)} entries in {bulk_file}")

    for line in manga_list:
        series_id = None
        title = None

        if "=" in line:
            series_id, title = line.split("=", 1)
            series_id = series_id.strip()
            title = title.strip()
            if not title:
                logger.debug(f"Empty title for {series_id}, fetching from WeebCentral")

        elif "/" in line:
            cleaned = line
            if cleaned.startswith("http"):
                cleaned = re.sub(r'^https?://[^/]+/series/', '', cleaned)
            series_id, title = cleaned.split("/", 1)
            series_id = series_id.strip()
            title = title.strip()
            if not title:
                logger.debug(f"Empty title for {series_id}, fetching from WeebCentral")
            if not SERIES_ID_PATTERN.match(series_id):
                logger.warning(f"Skipping unrecognized series ID after '/': {series_id}")
                continue

        elif SERIES_ID_PATTERN.match(line):
            series_id = line
            logger.debug(f"Bare series ID detected: {series_id}")

        else:
            title = line
            logger.info(f"Searching: {title}")

        if series_id and title:
            downloader.process_manga(title=title, series_id=series_id, chapters_to_download=chapters_to_download)
        elif series_id:
            downloader.process_manga(series_id=series_id, chapters_to_download=chapters_to_download)
        elif title:
            downloader.process_manga(title=title, chapters_to_download=chapters_to_download)


def process_tracked_mode(downloader: WeebCentralDownloader, chapters_to_download: Optional[Set[str]]):
    """Download all tracked manga from the database."""
    series = get_all_tracked()
    if not series:
        logger.info("No tracked manga in database. Use --track-add to add series.")
        return

    logger.info(f"Processing {len(series)} tracked manga...")
    for s in series:
        logger.info(f"Tracked: {s['title']} ({s['series_id']})")
        downloader.process_manga(
            title=s["title"],
            series_id=s["series_id"],
            chapters_to_download=chapters_to_download,
        )
        update_last_checked(s["series_id"])


if __name__ == "__main__":
    main()
