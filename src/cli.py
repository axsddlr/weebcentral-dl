#!/usr/bin/env python3
"""CLI interface for WeebCentral Downloader"""
import argparse
import sys
from typing import Optional, Set
from loguru import logger

from src.downloader import WeebCentralDownloader
from src.config import load_config


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
        "--config",
        type=str,
        default="config.toml",
        help="Path to config file (default: config.toml)",
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
        'output_dir': args.output_dir,
        'bulk_file': args.bulk_file,
        'series_id': args.series_id,
        'chapters': args.chapter,
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
        print("No manga title, series ID, or bulk file specified. Use -h for help.")
        sys.exit(1)


def process_bulk_mode(downloader: WeebCentralDownloader, bulk_file: str, chapters_to_download: Optional[Set[str]]):
    """Process manga from bulk file"""
    try:
        with open(bulk_file, "r", encoding="utf-8") as f:
            manga_list = [line.strip() for line in f if line.strip()]
        print(f"Found {len(manga_list)} manga titles in {bulk_file}")
        for line in manga_list:
            if "=" in line:
                series_id, title = line.split("=", 1)
                downloader.process_manga(
                    title=title.strip(),
                    series_id=series_id.strip(),
                    chapters_to_download=chapters_to_download,
                )
            elif "/" in line:
                series_id, title = line.split("/", 1)
                downloader.process_manga(
                    title=title.strip(),
                    series_id=series_id.strip(),
                    chapters_to_download=chapters_to_download,
                )
            else:
                downloader.process_manga(
                    title=line, chapters_to_download=chapters_to_download
                )
    except FileNotFoundError:
        print(f"Error: Could not find bulk file: {bulk_file}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading bulk file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
