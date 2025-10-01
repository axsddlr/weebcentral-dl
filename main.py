#!/usr/bin/env python3
import argparse
import sys
from typing import Optional, Set

from downloader import WeebCentralDownloader


def parse_chapter_arg(chapter_arg: Optional[str]) -> Optional[Set[str]]:
    if not chapter_arg:
        return None
    return {p.strip() for p in chapter_arg.split(",") if p.strip()}


def main():
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
        dest="output",
        default="./manga_downloads",
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
        help="Path to text file containing manga titles (one per line; you can use seriesid=optional-title)",
    )
    parser.add_argument(
        "-s",
        "--sequence",
        action="store_true",
        help="Download images in sequence (disable parallel downloading)",
    )
    parser.add_argument(
        "--rlc", type=int, default=10, help="Chapters between rate limits (default: 10)"
    )
    parser.add_argument(
        "--max-sleep",
        type=int,
        default=120,
        help="Max sleep time for rate limit/retry (default: 120)",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=5,
        help="Max retries for image download (default: 5)",
    )
    parser.add_argument(
        "-id",
        "--series-id",
        type=str,
        help="Direct WeebCentral series ID (bypasses search)",
    )
    args = parser.parse_args()

    downloader = WeebCentralDownloader(args)
    chapters_to_download = parse_chapter_arg(args.chapter)

    if args.bulk:
        try:
            with open(args.bulk, "r", encoding="utf-8") as f:
                manga_list = [line.strip() for line in f if line.strip()]
            print(f"Found {len(manga_list)} manga titles in {args.bulk}")
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
            print(f"Error: Could not find bulk file: {args.bulk}")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading bulk file: {e}")
            sys.exit(1)

    elif args.series_id:
        downloader.process_manga(
            series_id=args.series_id, chapters_to_download=chapters_to_download
        )
    elif args.query:
        title = " ".join(args.query).strip()
        downloader.process_manga(title=title, chapters_to_download=chapters_to_download)
    else:
        print("No manga title, series ID, or bulk file specified. Use -h for help.")
        sys.exit(1)


if __name__ == "__main__":
    main()
