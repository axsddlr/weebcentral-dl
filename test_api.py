#!/usr/bin/env python3
"""
Test script to verify JSON API improvements and metadata extraction.
Tests without actually downloading images.

Usage:
    python test_api.py                    # Test with default series
    python test_api.py <series_id>        # Test specific series
    python test_api.py --bulk test_manga.txt  # Test bulk file
"""

import sys
import argparse
from src.downloader import WeebCentralDownloader
from src.config import DownloaderConfig

# Test configuration
TEST_SERIES = {
    "Solo Leveling": "01J76XYCPSY3C4BNPBRY8JMCBE",
    "Blue Lock": "01J76XYD7E91K8QP6CY0Y53900",
    "Chainsaw Man": "01J76XYCRVY3QGYAMRR3STW941",
}


def test_metadata(downloader, series_id, series_name):
    """Test metadata extraction"""
    print(f"\n{'=' * 70}")
    print(f"Testing Metadata Extraction: {series_name}")
    print('=' * 70)

    metadata = downloader.get_series_metadata(series_id)

    print(f"\n📚 Title: {metadata['title']}")
    print(f"✍️  Authors: {', '.join(metadata['authors']) if metadata['authors'] else 'N/A'}")
    print(f"🏷️  Tags: {', '.join(metadata['tags'][:5]) if metadata['tags'] else 'N/A'}")
    if len(metadata['tags']) > 5:
        print(f"       ...and {len(metadata['tags']) - 5} more")
    print(f"📝 Description: {metadata['description'][:200]}{'...' if len(metadata['description']) > 200 else ''}")

    return metadata


def test_chapter_list(downloader, series_id, series_name):
    """Test chapter list fetching (JSON vs HTML)"""
    print(f"\n{'=' * 70}")
    print(f"Testing Chapter List Fetch: {series_name}")
    print('=' * 70)

    chapters = downloader.fetch_chapter_list(series_id)

    if chapters:
        print(f"\n✅ Found {len(chapters)} chapters")
        print(f"\nFirst 5 chapters:")
        for i, (chap_type, chap_num, chap_id) in enumerate(chapters[:5], 1):
            print(f"  {i}. {chap_type} {chap_num} (ID: {chap_id})")

        if len(chapters) > 5:
            print(f"\nLast 3 chapters:")
            for i, (chap_type, chap_num, chap_id) in enumerate(chapters[-3:], len(chapters) - 2):
                print(f"  {i}. {chap_type} {chap_num} (ID: {chap_id})")
    else:
        print("❌ No chapters found!")

    return chapters


def test_image_list(downloader, chapter_id, chapter_name):
    """Test image list fetching (JSON vs HTML)"""
    print(f"\n{'=' * 70}")
    print(f"Testing Image List Fetch: {chapter_name}")
    print('=' * 70)

    # We'll call the internal fetching logic without downloading
    import tempfile
    import os

    temp_dir = tempfile.mkdtemp(prefix="test_")
    url = f"https://weebcentral.com/chapters/{chapter_id}/images?is_prev=False&current_page=1&reading_style=long_strip"

    try:
        resp = downloader.scraper.get(url)
        img_urls = []

        # Try JSON first
        try:
            data = resp.json()
            img_urls = [img.get("src") for img in data.get("images", []) if img.get("src")]
            if img_urls:
                print(f"\n✅ [JSON] Found {len(img_urls)} images")
        except:
            pass

        # Fallback to HTML
        if not img_urls:
            import re
            img_urls = re.findall(r'src="([^"]+)"', resp.text)
            if img_urls:
                print(f"\n✅ [HTML] Found {len(img_urls)} images")

        if img_urls:
            print(f"\nFirst 3 image URLs:")
            for i, url in enumerate(img_urls[:3], 1):
                # Truncate long URLs
                display_url = url if len(url) < 80 else url[:77] + "..."
                print(f"  {i}. {display_url}")
        else:
            print("❌ No images found!")

        return img_urls
    finally:
        # Cleanup temp dir
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)


def test_search(downloader, query):
    """Test search functionality"""
    print(f"\n{'=' * 70}")
    print(f"Testing Search: '{query}'")
    print('=' * 70)

    result = downloader.get_series_id_from_query(query)

    if result and result[0]:
        series_id, series_title = result
        print(f"\n✅ Found series:")
        print(f"   ID: {series_id}")
        print(f"   Title: {series_title}")
        return series_id, series_title
    else:
        print("❌ No results found!")
        return None, None


def run_single_series_test(series_id, series_name):
    """Run all tests on a single series"""
    print(f"\n{'#' * 70}")
    print(f"# Testing Series: {series_name}")
    print(f"# Series ID: {series_id}")
    print('#' * 70)

    # Create downloader with verbose mode
    config = DownloaderConfig(
        output_dir="./test_output",
        verbose=True,
        max_retries=3,
        max_sleep=10,
        rlc=10,
        zip=False,
        sequence=False,
        latest=False,
        use_english_title=False,
    )
    downloader = WeebCentralDownloader(config)

    # Test 1: Metadata
    metadata = test_metadata(downloader, series_id, series_name)

    # Test 2: Chapter list
    chapters = test_chapter_list(downloader, series_id, series_name)

    # Test 3: Image list (test first chapter if available)
    if chapters:
        first_chapter = chapters[0]
        chap_type, chap_num, chap_id = first_chapter
        chapter_name = f"{chap_type} {chap_num}"
        test_image_list(downloader, chap_id, chapter_name)

    print(f"\n{'=' * 70}")
    print(f"✅ All tests completed for {series_name}")
    print('=' * 70)


def run_bulk_test(bulk_file):
    """Test bulk file processing"""
    print(f"\n{'#' * 70}")
    print(f"# Testing Bulk File: {bulk_file}")
    print('#' * 70)

    config = DownloaderConfig(
        output_dir="./test_output",
        verbose=True,
        max_retries=3,
        max_sleep=10,
        rlc=10,
        zip=False,
        sequence=False,
        latest=False,
        use_english_title=False,
    )
    downloader = WeebCentralDownloader(config)

    try:
        with open(bulk_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

        print(f"\nFound {len(lines)} entries to test\n")

        for idx, line in enumerate(lines, 1):
            if '=' in line:
                series_id, title = line.split('=', 1)
                series_id = series_id.strip()
                series_name = title.strip()
                print(f"\n[{idx}/{len(lines)}] Testing: {series_name} (ID provided)")
            else:
                series_name = line.strip()
                print(f"\n[{idx}/{len(lines)}] Testing: {series_name} (search required)")
                series_id, _ = test_search(downloader, series_name)
                if not series_id:
                    print(f"⚠️ Skipping {series_name} - not found")
                    continue

            # Test metadata only for bulk (faster)
            test_metadata(downloader, series_id, series_name)

            # Test chapter list
            chapters = test_chapter_list(downloader, series_id, series_name)

            print(f"\n{'─' * 70}\n")

        print(f"\n{'=' * 70}")
        print(f"✅ Bulk test completed: {len(lines)} series tested")
        print('=' * 70)

    except FileNotFoundError:
        print(f"❌ Error: File '{bulk_file}' not found!")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Test WeebCentral API improvements (JSON vs HTML parsing)"
    )
    parser.add_argument(
        'series_id',
        nargs='?',
        help='Series ID to test (default: tests all predefined series)'
    )
    parser.add_argument(
        '--bulk', '-b',
        type=str,
        help='Test bulk file processing'
    )
    parser.add_argument(
        '--search', '-s',
        type=str,
        help='Test search functionality with query'
    )

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("WeebCentral API Improvement Test Suite")
    print("=" * 70)
    print("\nThis script tests:")
    print("  ✓ JSON API vs HTML parsing")
    print("  ✓ Metadata extraction")
    print("  ✓ Chapter list fetching")
    print("  ✓ Image list fetching")
    print("  ✓ Search functionality")
    print("\nNote: No images will be downloaded\n")

    if args.bulk:
        run_bulk_test(args.bulk)
    elif args.search:
        config = DownloaderConfig(
            output_dir="./test_output",
            verbose=True,
            max_retries=3,
            max_sleep=10,
            rlc=10,
            zip=False,
            sequence=False,
            latest=False,
            use_english_title=False,
        )
        downloader = WeebCentralDownloader(config)
        series_id, series_title = test_search(downloader, args.search)
        if series_id:
            run_single_series_test(series_id, series_title)
    elif args.series_id:
        # Test specific series ID
        run_single_series_test(args.series_id, f"Series {args.series_id}")
    else:
        # Test all predefined series
        for series_name, series_id in TEST_SERIES.items():
            run_single_series_test(series_id, series_name)
            print("\n" + "█" * 70 + "\n")

    print("\n✅ All tests finished!")


if __name__ == "__main__":
    main()
