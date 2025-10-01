#!/usr/bin/env python3
"""
Script to detect and remove duplicate manga folders.
Duplicates are identified by finding the series ID cover image (*.jpg/*.webp)
which contains the series ID in the filename.
"""

import os
import sys
import shutil
from pathlib import Path
from collections import defaultdict


def find_series_id(folder_path):
    """Extract series ID from cover image filename in the folder."""
    for file in os.listdir(folder_path):
        if file.endswith(('.jpg', '.webp')) and len(file.split('.')[0]) == 26:
            # Series IDs are 26 characters long (e.g., 01J76XYHEWTDVAMWPMEQS89C3Y)
            return file.split('.')[0]
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


def main():
    if len(sys.argv) < 2:
        print("Usage: python remove_duplicates.py <manga_directory> [--dry-run]")
        print("\nExample:")
        print("  python remove_duplicates.py Y:\\manga\\main --dry-run")
        print("  python remove_duplicates.py Y:\\manga\\main")
        sys.exit(1)

    manga_dir = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    if not os.path.isdir(manga_dir):
        print(f"Error: Directory not found: {manga_dir}")
        sys.exit(1)

    print(f"Scanning for duplicates in: {manga_dir}")
    print(f"Mode: {'DRY RUN (no changes will be made)' if dry_run else 'LIVE (will delete duplicates)'}\n")

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
            print()

    print(f"\nSummary: {total_to_remove} duplicate folder(s) {'would be' if dry_run else 'were'} removed.")

    if dry_run:
        print("\nThis was a DRY RUN. Run without --dry-run to actually remove duplicates.")


if __name__ == "__main__":
    main()
