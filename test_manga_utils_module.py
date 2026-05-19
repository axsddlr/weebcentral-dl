"""Tests for the relocated manga utilities module."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest import TestCase

import manga_utils as wrapper
from src import manga_utils as module


class MangaUtilsModuleTests(TestCase):
    def test_wrapper_reexports_package_functions(self):
        self.assertIs(wrapper.find_series_id, module.find_series_id)
        self.assertIs(wrapper.remove_duplicates_command, module.remove_duplicates_command)

    def test_find_series_id_works_from_package_module(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "01ABCDEF1234567890ABCDEF12.jpg").write_bytes(b"cover")
            self.assertEqual(module.find_series_id(tmpdir), "01ABCDEF1234567890ABCDEF12")

    def test_migrate_covers_command_renames_legacy_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir, "Series")
            folder.mkdir()
            legacy = folder / "01ABCDEF1234567890ABCDEF34.jpg"
            legacy.write_bytes(b"cover")

            result = module.migrate_covers_command(tmpdir, dry_run=False, verbose=False)

            self.assertEqual(result["migrated"], 1)
            self.assertTrue((folder / "01ABCDEF1234567890ABCDEF34-cover.jpg").exists())
