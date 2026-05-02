"""Orchestrate the full download pipeline: search → fetch → download → archive."""
import os
import random
import time
import tempfile
import shutil
from typing import Optional, List, Tuple, Set
from loguru import logger

from src.config import DownloaderConfig
from src.downloader.http_client import HttpClient
from src.downloader.series_resolver import SeriesResolver
from src.downloader.chapter_fetcher import ChapterFetcher
from src.downloader.chapter_tracker import ChapterTracker
from src.downloader.image_downloader import ImageDownloader
from src.downloader.cover_manager import CoverManager
from src.downloader.archiver import Archiver
from src.utils import get_vol_and_chapter_names


class DownloadOrchestrator:
    def __init__(
        self,
        config: DownloaderConfig,
        http: HttpClient,
        series_resolver: SeriesResolver,
        chapter_fetcher: ChapterFetcher,
        chapter_tracker: ChapterTracker,
        image_downloader: ImageDownloader,
        cover_manager: CoverManager,
        archiver: Archiver,
    ):
        self.config = config
        self.http = http
        self.series_resolver = series_resolver
        self.chapter_fetcher = chapter_fetcher
        self.chapter_tracker = chapter_tracker
        self.image_downloader = image_downloader
        self.cover_manager = cover_manager
        self.archiver = archiver
        self.output_dir = os.path.abspath(config.output_dir)

    def process_manga(
        self,
        title: Optional[str] = None,
        series_id: Optional[str] = None,
        chapters_to_download: Optional[Set[str]] = None,
    ):
        result = self.series_resolver.resolve_series_info(title, series_id)
        if not result:
            return
        series_id, series_title = result

        chapters = self.chapter_fetcher.fetch_chapter_list(series_id)
        if not chapters:
            logger.warning(f"No chapters found for '{title or series_id}'.")
            return

        self.cover_manager.download_and_convert(series_id, series_title)

        out_dir = os.path.join(self.output_dir, series_title)
        is_fresh = not os.path.exists(out_dir) or not os.listdir(out_dir)

        chapters_to_download = self._determine_chapters_to_download(
            chapters, series_title, chapters_to_download
        )
        if chapters_to_download is not None and not chapters_to_download:
            return

        logger.debug(
            f"Downloading chapters: {chapters_to_download if chapters_to_download else 'ALL'} "
            f"(zip mode: {self.config.zip})"
        )
        self.download_chapters(chapters, chapters_to_download, series_title, is_fresh)

    def download_chapters(
        self,
        chapters: List[Tuple[str, str, str]],
        chapters_to_download: Optional[Set[str]],
        series_title: str,
        is_fresh: bool,
    ):
        out_dir = os.path.join(self.output_dir, series_title)
        chap_counter = 0
        for chap_type, chap_num, chap_id in reversed(chapters):
            chap_num_str = (
                str(float(chap_num)).rstrip("0").rstrip(".")
                if "." in chap_num
                else chap_num
            )
            if (
                chapters_to_download is not None
                and chap_num_str not in chapters_to_download
            ):
                continue

            ct = "" if chap_type in ["Chapter", "#"] else chap_type
            _, chapter_dir_name = get_vol_and_chapter_names(chap_num)

            if self.config.zip and self.chapter_tracker.chapter_already_downloaded(chap_num, out_dir):
                logger.info(f"Skipping already-downloaded chapter {chap_num} (zip found)")
                continue

            logger.info(f"Downloading chapter {chap_num}")
            temp_dir = tempfile.mkdtemp(prefix=f"{series_title}-{chap_num}_")
            try:
                chapter_dir = self.image_downloader.download_chapter_images(
                    chap_id, chap_num, temp_dir, chapter_dir_name
                )
                if chapter_dir:
                    self.archiver.archive_chapter(chapter_dir, series_title, chap_num, ct)
            finally:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)

            chap_counter += 1
            if is_fresh and chap_counter % self.config.rlc == 0:
                wait = random.randint(15, self.config.max_sleep)
                logger.info(
                    f"Rate limiting: sleeping for {wait} seconds after {chap_counter} chapters"
                )
                time.sleep(wait)

    def _determine_chapters_to_download(
        self,
        chapters: List[Tuple[str, str, str]],
        series_title: str,
        chapters_to_download: Optional[Set[str]],
    ) -> Optional[Set[str]]:
        if not self.config.latest or chapters_to_download is not None:
            return chapters_to_download

        latest = self.chapter_tracker.get_latest_downloaded_chapter(series_title)
        if latest is None:
            logger.info("No downloaded chapters found, downloading all chapters.")
            return {chap[1] for chap in chapters}

        new_chapters = {chap[1] for chap in chapters if float(chap[1]) > latest}
        if not new_chapters:
            logger.info(f"No new chapters found after chapter {latest}.")
            return None

        logger.info(
            f"Downloading new chapters after chapter {latest}: {sorted(list(new_chapters))}"
        )
        return new_chapters
