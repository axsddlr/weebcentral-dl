import tempfile
import unittest
from pathlib import Path

import manga_utils
from src.utils import (
    build_cover_filename,
    choose_series_title,
    extract_series_id_from_cover_filename,
    find_cover_image_path,
    migrate_legacy_cover_filename,
    migrate_legacy_cover_filenames,
)


class TestUtils(unittest.TestCase):
    def test_build_cover_filename(self):
        self.assertEqual(build_cover_filename("01ABC", ".webp"), "01ABC-cover.webp")

    def test_extract_series_id_from_cover_filename(self):
        self.assertEqual(
            extract_series_id_from_cover_filename("01ABC-cover.jpg"),
            "01ABC",
        )
        self.assertIsNone(extract_series_id_from_cover_filename("01ABC.jpg"))

    def test_choose_series_title_keeps_normal_english_titles(self):
        self.assertEqual(
            choose_series_title(
                "No Game No Life",
                ["English Alternate"],
                prefer_english_title=True,
            ),
            "No Game No Life",
        )

    def test_choose_series_title_uses_alternate_for_cjk_titles(self):
        self.assertEqual(
            choose_series_title(
                "日本語タイトル",
                ["English Alternate"],
                prefer_english_title=True,
            ),
            "English Alternate",
        )


class TestMangaUtils(unittest.TestCase):
    def test_find_series_id_uses_cover_filename_convention(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "01ABC-cover.jpg").write_bytes(b"cover")
            Path(tmpdir, "chapter_001.cbz").write_bytes(b"archive")

            self.assertEqual(manga_utils.find_series_id(tmpdir), "01ABC")

    def test_find_series_id_returns_none_without_cover(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "chapter_001.cbz").write_bytes(b"archive")

            self.assertIsNone(manga_utils.find_series_id(tmpdir))

    def test_migrates_legacy_cover_filename(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            legacy = Path(tmpdir, "01J76XYHEWTDVAMWPMEQS89C3Y.jpg")
            legacy.write_bytes(b"cover")

            migrated = migrate_legacy_cover_filename(tmpdir, legacy.name)

            self.assertEqual(
                migrated,
                str(Path(tmpdir, "01J76XYHEWTDVAMWPMEQS89C3Y-cover.jpg")),
            )
            self.assertFalse(legacy.exists())
            self.assertTrue(Path(migrated).exists())

    def test_find_cover_image_path_migrates_legacy_cover(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "01J76XYHEWTDVAMWPMEQS89C3Y.webp").write_bytes(b"cover")

            cover_path = find_cover_image_path(tmpdir)

            self.assertEqual(
                cover_path,
                str(Path(tmpdir, "01J76XYHEWTDVAMWPMEQS89C3Y-cover.webp")),
            )
            self.assertTrue(Path(cover_path).exists())
            self.assertEqual(
                manga_utils.find_series_id(tmpdir),
                "01J76XYHEWTDVAMWPMEQS89C3Y",
            )

    def test_migrate_legacy_cover_filenames(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "01ABCDEF1234567890ABCDEF12.jpg").write_bytes(b"cover1")
            Path(tmpdir, "01ABCDEF1234567890ABCDEF34.webp").write_bytes(b"cover2")
            Path(tmpdir, "not-a-cover.txt").write_text("ignore")

            migrated = migrate_legacy_cover_filenames(tmpdir, dry_run=True)

            self.assertEqual(migrated, 2)
            self.assertTrue(Path(tmpdir, "01ABCDEF1234567890ABCDEF12.jpg").exists())
            self.assertTrue(Path(tmpdir, "01ABCDEF1234567890ABCDEF34.webp").exists())

            migrated = migrate_legacy_cover_filenames(tmpdir, dry_run=False)

            self.assertEqual(migrated, 2)
            self.assertTrue(Path(tmpdir, "01ABCDEF1234567890ABCDEF12-cover.jpg").exists())
            self.assertTrue(Path(tmpdir, "01ABCDEF1234567890ABCDEF34-cover.webp").exists())


if __name__ == "__main__":
    unittest.main()
