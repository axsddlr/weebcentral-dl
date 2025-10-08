#!/usr/bin/env python3
"""
Manga utilities script for managing downloaded manga folders.

Features:
- Remove duplicate manga folders based on series ID
- Rename folders to English titles from WeebCentral
- Merge chapters from duplicate folders

Duplicates are identified by finding the series ID cover image (*.jpg/*.webp)
which contains the series ID in the filename.
"""

import os
import sys
import shutil
import re
import html
import argparse
from pathlib import Path
from collections import defaultdict
from loguru import logger

try:
    import cloudscraper
except ImportError:
    cloudscraper = None


def find_series_id(folder_path):
    """Extract series ID from cover image filename in the folder."""
    for file in os.listdir(folder_path):
        if file.endswith(('.jpg', '.webp')) and len(file.split('.')[0]) == 26:
            # Series IDs are 26 characters long (e.g., 01J76XYHEWTDVAMWPMEQS89C3Y)
            return file.split('.')[0]
    return None


def get_english_title(series_id):
    """Fetch English title from WeebCentral series page.

    Tries in order:
    1. <h1> tag if it looks English (no romaji particles)
    2. Associated Name(s) if H1 is romaji
    3. Falls back to H1 title if no Associated Names exist
    """
    if not cloudscraper:
        logger.warning("cloudscraper not installed, cannot fetch English titles")
        return None

    try:
        scraper = cloudscraper.create_scraper()
        scraper.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36'
        })

        url = f"https://weebcentral.com/series/{series_id}"
        resp = scraper.get(url, timeout=10)

        # Extract H1 title
        h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', resp.text)
        if not h1_match:
            return None

        h1_title = html.unescape(h1_match.group(1).strip())

        # Check if title looks like romaji (has Japanese particles)
        has_romaji = re.search(r'\b(de|wo|ga|no|ni|wa)\b', h1_title, re.IGNORECASE)

        if has_romaji:
            # Try to get Associated Name(s) for English title
            assoc_pattern = r'Associated Name\(s\).*?<ul[^>]*>(.*?)</ul>'
            assoc_match = re.search(assoc_pattern, resp.text, re.DOTALL | re.IGNORECASE)

            if assoc_match:
                ul_content = assoc_match.group(1)
                li_items = re.findall(r'<li>([^<]+)</li>', ul_content)
                if li_items:
                    # Use first associated name (usually English)
                    title = html.unescape(li_items[0].strip())
                    title = re.sub(r'[<>:"/\\|?*]', '', title)
                    title = title.replace(' ', '-')
                    return title

        # Either H1 is English, or no Associated Names found - use H1
        title = re.sub(r'[<>:"/\\|?*]', '', h1_title)
        title = title.replace(' ', '-')
        return title

    except Exception as e:
        logger.warning(f"Could not fetch English title for {series_id}: {e}")

    return None


def get_folder_priority(folder_name, folder_path):
    """
    Determine priority for keeping a folder.
    Higher score = higher priority to keep.
    Prioritizes newer folders (longer names, newer dates) from updated code.
    """
    score = 0

    # Prefer properly capitalized titles (has uppercase letters)
    if any(c.isupper() for c in folder_name):
        score += 100

    # Prefer longer folder names (newer code preserves full titles)
    score += len(folder_name) * 2

    # Prefer newer modification dates (most recently updated)
    try:
        mtime = os.path.getmtime(folder_path)
        score += mtime / 1000000  # Normalize timestamp to reasonable range
    except:
        pass

    # Prefer folders with more chapters (tiebreaker)
    try:
        chapter_count = len([f for f in os.listdir(folder_path)
                            if f.endswith(('.cbz', '.zip'))])
        score += chapter_count * 10
    except:
        pass

    return score


def find_duplicates(manga_dir):
    """Find duplicate manga folders based on series ID."""
    series_id_map = defaultdict(list)

    # Scan all folders
    for folder_name in os.listdir(manga_dir):
        folder_path = os.path.join(manga_dir, folder_name)

        if not os.path.isdir(folder_path):
            continue

        series_id = find_series_id(folder_path)

        if series_id:
            priority = get_folder_priority(folder_name, folder_path)
            series_id_map[series_id].append({
                'name': folder_name,
                'path': folder_path,
                'priority': priority
            })

    # Find duplicates (series with multiple folders)
    duplicates = {sid: folders for sid, folders in series_id_map.items()
                  if len(folders) > 1}

    return duplicates


def merge_folders(keep_folder, remove_folder):
    """Merge chapters from remove_folder into keep_folder."""
    print(f"  Merging chapters from '{remove_folder['name']}' into '{keep_folder['name']}'")

    for file in os.listdir(remove_folder['path']):
        if file.endswith(('.cbz', '.zip')):
            src = os.path.join(remove_folder['path'], file)
            dst = os.path.join(keep_folder['path'], file)

            # Only copy if file doesn't exist in destination
            if not os.path.exists(dst):
                print(f"    Moving: {file}")
                shutil.move(src, dst)


def remove_duplicates_command(manga_dir, dry_run=False, use_english=False):
    """Remove duplicate manga folders."""
    print(f"Scanning for duplicates in: {manga_dir}")
    mode_str = "DRY RUN (no changes will be made)" if dry_run else "LIVE (will delete duplicates)"
    if use_english:
        mode_str += " + ENGLISH TITLES"
    print(f"Mode: {mode_str}\n")

    duplicates = find_duplicates(manga_dir)

    if not duplicates:
        print("No duplicates found!")
        return

    print(f"Found {len(duplicates)} series with duplicate folders:\n")

    total_to_remove = 0

    for series_id, folders in duplicates.items():
        # Sort by priority (highest first)
        folders.sort(key=lambda x: x['priority'], reverse=True)

        keep = folders[0]
        remove_list = folders[1:]

        print(f"Series ID: {series_id}")

        # Fetch English title if --en flag is used
        new_name = None
        if use_english:
            new_name = get_english_title(series_id)
            if new_name and new_name != keep['name']:
                print(f"  English title: {new_name}")

        print(f"  KEEP:   '{keep['name']}' (priority: {keep['priority']})")

        for folder in remove_list:
            print(f"  REMOVE: '{folder['name']}' (priority: {folder['priority']})")
            total_to_remove += 1

        print()

        if not dry_run:
            # Merge chapters before removing
            for folder in remove_list:
                merge_folders(keep, folder)

            # Remove duplicate folders
            for folder in remove_list:
                print(f"  Deleting folder: {folder['name']}")
                shutil.rmtree(folder['path'])

            # Rename to English title if requested
            if use_english and new_name and new_name != keep['name']:
                old_path = keep['path']
                new_path = os.path.join(os.path.dirname(old_path), new_name)
                if not os.path.exists(new_path):
                    print(f"  Renaming: '{keep['name']}' -> '{new_name}'")
                    os.rename(old_path, new_path)
                else:
                    print(f"  Warning: Cannot rename to '{new_name}' (already exists)")

            print()

    print(f"\nSummary: {total_to_remove} duplicate folder(s) {'would be' if dry_run else 'were'} removed.")

    if dry_run:
        print("\nThis was a DRY RUN. Run without --dry-run to actually remove duplicates.")


def add_covers_to_archives_command(manga_dir, dry_run=False, verbose=False):
    """Add cover images to existing archives as the first page."""
    import zipfile
    import tempfile

    logger.info(f"Scanning manga folders in: {manga_dir}")
    logger.info(f"Mode: {'DRY RUN (no changes will be made)' if dry_run else 'LIVE (will add covers to archives)'}\n")

    updated_count = 0
    skipped_count = 0

    for folder_name in sorted(os.listdir(manga_dir)):
        folder_path = os.path.join(manga_dir, folder_name)

        if not os.path.isdir(folder_path):
            continue

        # Find cover image
        cover_path = None
        for file in os.listdir(folder_path):
            if file.endswith(('.jpg', '.webp')) and len(file.split('.')[0]) == 26:
                cover_path = os.path.join(folder_path, file)
                break

        if not cover_path:
            logger.debug(f"Skipping '{folder_name}': No cover image found")
            skipped_count += 1
            continue

        # Find all archives
        archives = [f for f in os.listdir(folder_path) if f.endswith(('.cbz', '.zip'))]

        if not archives:
            logger.debug(f"Skipping '{folder_name}': No archives found")
            skipped_count += 1
            continue

        logger.debug(f"Processing '{folder_name}' ({len(archives)} archives)...")

        for archive_name in archives:
            archive_path = os.path.join(folder_path, archive_name)

            try:
                # Check if cover already exists in archive
                with zipfile.ZipFile(archive_path, 'r') as zf:
                    existing_files = zf.namelist()
                    has_cover = any(f.startswith('000-cover') for f in existing_files)

                if has_cover:
                    logger.debug(f"  Skip '{archive_name}': Already has cover")
                    continue

                if dry_run:
                    logger.info(f"  Would add cover to: '{archive_name}'")
                    updated_count += 1
                else:
                    # Create temporary file in the same directory as target (for same-drive operations)
                    tmp_fd, tmp_path = tempfile.mkstemp(suffix='.zip', dir=folder_path)
                    os.close(tmp_fd)

                    try:
                        # Copy archive with cover prepended
                        cover_ext = os.path.splitext(cover_path)[1]
                        with zipfile.ZipFile(tmp_path, 'w', zipfile.ZIP_DEFLATED) as new_zf:
                            # Add cover as first file
                            new_zf.write(cover_path, arcname=f'000-cover{cover_ext}')

                            # Copy existing files
                            with zipfile.ZipFile(archive_path, 'r') as old_zf:
                                for item in old_zf.namelist():
                                    new_zf.writestr(item, old_zf.read(item))

                        # Replace original archive
                        os.replace(tmp_path, archive_path)
                        logger.success(f"  Added cover to: '{archive_name}'")
                        updated_count += 1
                    except Exception as e:
                        # Clean up temp file if something went wrong
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
                        raise e

            except PermissionError as e:
                logger.error(f"  Error processing '{archive_name}': Permission denied (file may be locked or read-only)")
                skipped_count += 1
            except Exception as e:
                logger.error(f"  Error processing '{archive_name}': {e}")
                skipped_count += 1

    logger.info(f"\nSummary: {updated_count} archive(s) {'would be' if dry_run else 'were'} updated, {skipped_count} skipped.")

    if dry_run:
        logger.info("\nThis was a DRY RUN. Run without --dry-run to actually add covers.")


def rename_to_english_command(manga_dir, dry_run=False, verbose=False):
    """Rename all manga folders to English titles from WeebCentral."""
    if not cloudscraper:
        logger.error("This command requires cloudscraper. Install with: pip install cloudscraper")
        return

    logger.info(f"Scanning manga folders in: {manga_dir}")
    logger.info(f"Mode: {'DRY RUN (no changes will be made)' if dry_run else 'LIVE (will rename folders)'}\n")

    renamed_count = 0
    skipped_count = 0

    for folder_name in sorted(os.listdir(manga_dir)):
        folder_path = os.path.join(manga_dir, folder_name)

        if not os.path.isdir(folder_path):
            continue

        series_id = find_series_id(folder_path)
        if not series_id:
            logger.debug(f"Skipping '{folder_name}': No series ID found")
            skipped_count += 1
            continue

        logger.debug(f"Processing '{folder_name}' (ID: {series_id})...")

        try:
            english_title = get_english_title(series_id)
        except Exception as e:
            logger.error(f"Skipping '{folder_name}': Error fetching title - {e}")
            skipped_count += 1
            continue

        if not english_title:
            logger.warning(f"Skipping '{folder_name}': Could not fetch English title")
            skipped_count += 1
            continue

        if english_title == folder_name:
            logger.debug(f"Already English: '{folder_name}'")
            skipped_count += 1
            continue

        new_path = os.path.join(manga_dir, english_title)

        if os.path.exists(new_path):
            logger.warning(f"Skipping '{folder_name}': Target '{english_title}' already exists")
            skipped_count += 1
            continue

        logger.info(f"{'Would rename' if dry_run else 'Renaming'}: '{folder_name}' -> '{english_title}'")

        if not dry_run:
            os.rename(folder_path, new_path)
        renamed_count += 1

    logger.info(f"\nSummary: {renamed_count} folder(s) {'would be' if dry_run else 'were'} renamed, {skipped_count} skipped.")

    if dry_run:
        logger.info("\nThis was a DRY RUN. Run without --dry-run to actually rename folders.")


def main():
    parser = argparse.ArgumentParser(
        description="Manga utilities for managing downloaded manga folders",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Remove duplicates (preview)
  python manga_utils.py remove-duplicates Y:\\manga\\main --dry-run

  # Remove duplicates and rename to English
  python manga_utils.py remove-duplicates Y:\\manga\\main --en

  # Rename all folders to English titles
  python manga_utils.py rename-english Y:\\manga\\main --dry-run

  # Add covers to existing archives (preview)
  python manga_utils.py add-covers Y:\\manga\\main --dry-run

  # Add covers to existing archives (live)
  python manga_utils.py add-covers Y:\\manga\\main -v
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Remove duplicates command
    dup_parser = subparsers.add_parser('remove-duplicates', help='Remove duplicate manga folders')
    dup_parser.add_argument('directory', help='Manga directory path')
    dup_parser.add_argument('--dry-run', action='store_true', help='Preview changes without making them')
    dup_parser.add_argument('--en', action='store_true', help='Rename folders to English titles')

    # Rename to English command
    rename_parser = subparsers.add_parser('rename-english', help='Rename all folders to English titles')
    rename_parser.add_argument('directory', help='Manga directory path')
    rename_parser.add_argument('--dry-run', action='store_true', help='Preview changes without making them')
    rename_parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed output')

    # Add covers command
    covers_parser = subparsers.add_parser('add-covers', help='Add cover images to existing archives as first page')
    covers_parser.add_argument('directory', help='Manga directory path')
    covers_parser.add_argument('--dry-run', action='store_true', help='Preview changes without making them')
    covers_parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed output')

    args = parser.parse_args()

    # Configure loguru based on verbose flag
    verbose = getattr(args, 'verbose', False)
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

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Validate directory
    if not os.path.isdir(args.directory):
        logger.error(f"Directory not found: {args.directory}")
        sys.exit(1)

    # Check cloudscraper for --en commands
    if (args.command == 'remove-duplicates' and args.en) or args.command == 'rename-english':
        if not cloudscraper:
            logger.error("This command requires cloudscraper. Install with: pip install cloudscraper")
            sys.exit(1)

    # Execute command
    if args.command == 'remove-duplicates':
        remove_duplicates_command(args.directory, args.dry_run, args.en)
    elif args.command == 'rename-english':
        rename_to_english_command(args.directory, args.dry_run, verbose)
    elif args.command == 'add-covers':
        add_covers_to_archives_command(args.directory, args.dry_run, verbose)


if __name__ == "__main__":
    main()
