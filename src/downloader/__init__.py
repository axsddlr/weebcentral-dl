"""WeebCentral Downloader — backward-compatible facade."""
import os
from typing import Optional, List, Tuple, Set

from src.config import DownloaderConfig
from src.downloader.http_client import HttpClient
from src.downloader.series_resolver import SeriesResolver
from src.downloader.chapter_fetcher import ChapterFetcher
from src.downloader.title_resolver import TitleResolver
from src.downloader.metadata import MetadataExtractor
from src.downloader.chapter_tracker import ChapterTracker
from src.downloader.image_downloader import ImageDownloader
from src.downloader.cover_manager import CoverManager
from src.downloader.archiver import Archiver
from src.downloader.orchestrator import DownloadOrchestrator


class WeebCentralDownloader:
    def __init__(self, config: DownloaderConfig):
        self.config = config

        self.http = HttpClient(config.output_dir)
        self.chapter_fetcher = ChapterFetcher(self.http)
        self.title_resolver = TitleResolver(self.http, getattr(config, 'use_english_title', False))
        self.series_resolver = SeriesResolver(self.http, self.title_resolver, getattr(config, 'use_english_title', False))
        self.metadata = MetadataExtractor(self.http)
        self.chapter_tracker = ChapterTracker(os.path.abspath(config.output_dir))
        self.image_downloader = ImageDownloader(
            self.http, getattr(config, 'max_retries', 5), getattr(config, 'max_sleep', 120),
            getattr(config, 'parallel_workers', 99), getattr(config, 'sequence', False),
        )
        self.cover_manager = CoverManager(self.http, self.image_downloader, os.path.abspath(config.output_dir))
        self.archiver = Archiver(self.cover_manager, os.path.abspath(config.output_dir), getattr(config, 'zip', False))
        self.orchestrator = DownloadOrchestrator(
            config, self.http, self.series_resolver, self.chapter_fetcher,
            self.chapter_tracker, self.image_downloader, self.cover_manager, self.archiver,
        )

        self._output_dir = os.path.abspath(config.output_dir)
        os.makedirs(self._output_dir, exist_ok=True)

    @property
    def output_dir(self):
        return self._output_dir

    @output_dir.setter
    def output_dir(self, value):
        self._output_dir = value
        self.chapter_tracker.output_dir = value
        self.cover_manager.output_dir = value
        self.archiver.output_dir = value
        self.orchestrator.output_dir = value
        self.http.output_dir = value

    @property
    def scraper(self):
        return self.http.scraper

    def _request(self, method: str, url: str, **kwargs):
        return self.http.request(method, url, **kwargs)

    def log_not_found(self, msg: str):
        self.http.log_not_found(msg)

    def get_series_id_from_query(self, query: str) -> Optional[Tuple[str, str]]:
        return self.series_resolver.get_series_id_from_query(query)

    def fetch_chapter_list(self, series_id: str) -> List[Tuple[str, str, str]]:
        return self.chapter_fetcher.fetch_chapter_list(series_id)

    def get_series_title_by_id(self, series_id: str) -> str:
        return self.title_resolver.get_series_title_by_id(series_id)

    def get_series_metadata(self, series_id: str) -> dict:
        return self.metadata.get_series_metadata(series_id)

    def get_latest_downloaded_chapter(self, series_title: str) -> Optional[float]:
        return self.chapter_tracker.get_latest_downloaded_chapter(series_title)

    def chapter_already_downloaded(self, chap_num: str, out_dir: str) -> bool:
        return self.chapter_tracker.chapter_already_downloaded(chap_num, out_dir)

    def download_image(self, img_url: str, dest_folder: str, referer: str):
        return self.image_downloader.download_image(img_url, dest_folder, referer)

    def download_chapter_images(self, chapter_id: str, chapter_num: str, outdir: str, chapter_dir_name: str):
        return self.image_downloader.download_chapter_images(chapter_id, chapter_num, outdir, chapter_dir_name)

    def get_cover_image_path(self, series_title: str) -> Optional[str]:
        return self.cover_manager.get_cover_image_path(series_title)

    def archive_chapter(self, chapter_dir: str, series_title: str, chapter_num: str, chapter_type: str):
        self.archiver.archive_chapter(chapter_dir, series_title, chapter_num, chapter_type)

    def download_chapters(self, chapters, chapters_to_download, series_title):
        self.orchestrator.download_chapters(chapters, chapters_to_download, series_title)

    def process_manga(self, title=None, series_id=None, chapters_to_download=None):
        self.orchestrator.process_manga(title, series_id, chapters_to_download)

    def download_cover_image_and_convert(self, series_id: str, series_title: str):
        self.cover_manager.download_and_convert(series_id, series_title)

    def download_cover_image(self, series_id: str, series_title: str):
        return self.cover_manager.download(series_id, series_title)
