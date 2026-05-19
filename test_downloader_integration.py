"""Integration tests for the modular downloader pipeline."""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock

from src.config import DownloaderConfig
from src.downloader.archiver import Archiver
from src.downloader.chapter_tracker import ChapterTracker
from src.downloader.metadata import MetadataExtractor
from src.downloader.orchestrator import DownloadOrchestrator


class FakeSeriesResolver:
    def __init__(self, result):
        self.result = result

    def resolve_series_info(self, title, series_id):
        return self.result


class FakeChapterFetcher:
    def __init__(self, chapters):
        self.chapters = chapters

    def fetch_chapter_list(self, series_id):
        return list(self.chapters)


class FakeImageDownloader:
    def __init__(self):
        self.calls = []

    def download_chapter_images(self, chapter_id, chapter_num, outdir, chapter_dir_name):
        self.calls.append((chapter_id, chapter_num))
        chapter_dir = Path(outdir) / chapter_dir_name
        chapter_dir.mkdir(parents=True, exist_ok=True)
        (chapter_dir / "001.jpg").write_bytes(b"page-1")
        (chapter_dir / "002.png").write_bytes(b"page-2")
        return str(chapter_dir)


class DownloaderIntegrationTests(TestCase):
    def _build_config(self, output_dir: str, latest: bool = False) -> DownloaderConfig:
        return DownloaderConfig(
            output_dir=output_dir,
            latest=latest,
            sequence=False,
            zip=False,
            verbose=False,
            use_english_title=False,
            comicinfo=False,
            rlc=10,
            max_sleep=5,
            max_retries=3,
        )

    def test_process_manga_creates_archives_with_cover(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._build_config(tmpdir)
            series_id = "01ABCDEF1234567890ABCDEF12"
            series_title = "Series-Title"
            chapters = [("Chapter", "1", "CH1"), ("Chapter", "2", "CH2")]

            cover_manager = Mock()

            def _write_cover(_series_id, _series_title):
                cover_dir = Path(tmpdir) / series_title
                cover_dir.mkdir(parents=True, exist_ok=True)
                cover_path = cover_dir / f"{series_id}-cover.jpg"
                cover_path.write_bytes(b"cover")
                return str(cover_path)

            cover_manager.download_and_convert.side_effect = _write_cover
            cover_manager.get_cover_image_path.side_effect = (
                lambda requested_title: str(Path(tmpdir) / requested_title / f"{series_id}-cover.jpg")
            )

            orchestrator = DownloadOrchestrator(
                config=config,
                http=Mock(),
                series_resolver=FakeSeriesResolver((series_id, series_title)),
                chapter_fetcher=FakeChapterFetcher(chapters),
                chapter_tracker=ChapterTracker(tmpdir),
                image_downloader=FakeImageDownloader(),
                cover_manager=cover_manager,
                archiver=Archiver(cover_manager, tmpdir, use_zip=False),
                metadata_extractor=Mock(),
            )

            orchestrator.process_manga(title="Ignored by fake resolver")

            series_dir = Path(tmpdir) / series_title
            archive_1 = series_dir / f"{series_title}-1.cbz"
            archive_2 = series_dir / f"{series_title}-2.cbz"

            self.assertTrue(archive_1.exists())
            self.assertTrue(archive_2.exists())

            with zipfile.ZipFile(archive_1, "r") as zf:
                self.assertIn("000-cover.jpg", zf.namelist())
                self.assertIn("001.jpg", zf.namelist())
                self.assertIn("002.png", zf.namelist())

            with zipfile.ZipFile(archive_2, "r") as zf:
                self.assertIn("000-cover.jpg", zf.namelist())
                self.assertIn("001.jpg", zf.namelist())
                self.assertIn("002.png", zf.namelist())

    def test_process_manga_latest_only_downloads_new_chapters(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._build_config(tmpdir, latest=True)
            series_id = "01ABCDEF1234567890ABCDEF34"
            series_title = "Series-Title"
            chapters = [("Chapter", "1", "CH1"), ("Chapter", "2", "CH2")]

            series_dir = Path(tmpdir) / series_title
            series_dir.mkdir(parents=True, exist_ok=True)
            (series_dir / f"{series_title}-1.cbz").write_bytes(b"existing archive")

            cover_manager = Mock()

            def _write_cover(_series_id, _series_title):
                cover_path = series_dir / f"{series_id}-cover.jpg"
                cover_path.write_bytes(b"cover")
                return str(cover_path)

            cover_manager.download_and_convert.side_effect = _write_cover
            cover_manager.get_cover_image_path.side_effect = (
                lambda requested_title: str(Path(tmpdir) / requested_title / f"{series_id}-cover.jpg")
            )

            image_downloader = FakeImageDownloader()
            orchestrator = DownloadOrchestrator(
                config=config,
                http=Mock(),
                series_resolver=FakeSeriesResolver((series_id, series_title)),
                chapter_fetcher=FakeChapterFetcher(chapters),
                chapter_tracker=ChapterTracker(tmpdir),
                image_downloader=image_downloader,
                cover_manager=cover_manager,
                archiver=Archiver(cover_manager, tmpdir, use_zip=False),
                metadata_extractor=Mock(),
            )

            orchestrator.process_manga(title="Ignored by fake resolver")

            self.assertEqual(image_downloader.calls, [("CH2", "2")])
            self.assertTrue((series_dir / f"{series_title}-1.cbz").exists())
            self.assertTrue((series_dir / f"{series_title}-2.cbz").exists())

    def test_metadata_extractor_parses_series_page(self):
        http = Mock()
        response = SimpleNamespace(
            text=(
                "<html><body>"
                "<h1>Series Title</h1>"
                "<strong>Description</strong><p>Series summary</p>"
                "<strong>Author</strong><ul><li><a href='/a'>Author One</a></li></ul>"
                "<strong>Tags</strong><ul><li><a href='/t'>Action</a></li><li><a href='/t2'>Drama</a></li></ul>"
                "<source srcset=\"https://example.test/cover.webp\">"
                "</body></html>"
            )
        )
        http.request.return_value = response

        extractor = MetadataExtractor(http)
        metadata = extractor.get_series_metadata("SERIES123")

        self.assertEqual(metadata["title"], "Series Title")
        self.assertEqual(metadata["description"], "Series summary")
        self.assertEqual(metadata["authors"], ["Author One"])
        self.assertEqual(metadata["tags"], ["Action", "Drama"])
        self.assertEqual(metadata["coverUrl"], "https://example.test/cover.webp")

    def test_process_manga_writes_comicinfo_xml_when_enabled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._build_config(tmpdir)
            config.comicinfo = True
            series_id = "01ABCDEF1234567890ABCDEF56"
            series_title = "Series-Title"
            chapters = [("Chapter", "1", "CH1")]

            cover_manager = Mock()

            def _write_cover(_series_id, _series_title):
                cover_dir = Path(tmpdir) / series_title
                cover_dir.mkdir(parents=True, exist_ok=True)
                cover_path = cover_dir / f"{series_id}-cover.jpg"
                cover_path.write_bytes(b"cover")
                return str(cover_path)

            cover_manager.download_and_convert.side_effect = _write_cover
            cover_manager.get_cover_image_path.side_effect = (
                lambda requested_title: str(Path(tmpdir) / requested_title / f"{series_id}-cover.jpg")
            )

            metadata_extractor = Mock()
            metadata_extractor.get_series_metadata.return_value = {
                "title": "Series Title",
                "description": "Series summary",
                "authors": ["Author One"],
                "tags": ["Action"],
                "coverUrl": "https://example.test/cover.webp",
            }

            orchestrator = DownloadOrchestrator(
                config=config,
                http=Mock(),
                series_resolver=FakeSeriesResolver((series_id, series_title)),
                chapter_fetcher=FakeChapterFetcher(chapters),
                chapter_tracker=ChapterTracker(tmpdir),
                image_downloader=FakeImageDownloader(),
                cover_manager=cover_manager,
                archiver=Archiver(cover_manager, tmpdir, use_zip=False),
                metadata_extractor=metadata_extractor,
            )

            orchestrator.process_manga(title="Ignored by fake resolver")

            archive = Path(tmpdir) / series_title / f"{series_title}-1.cbz"
            self.assertTrue(archive.exists())

            with zipfile.ZipFile(archive, "r") as zf:
                self.assertIn("ComicInfo.xml", zf.namelist())
                xml = zf.read("ComicInfo.xml").decode("utf-8")
                self.assertIn("<Series>Series Title</Series>", xml)
                self.assertIn("<Title>1</Title>", xml)
                self.assertIn("<Number>1</Number>", xml)
                self.assertIn("<Summary>Series summary</Summary>", xml)
