"""Download manga page images (parallel + sequential modes)."""
import os
import re
import time
import random
import concurrent.futures
from typing import Optional
from src.logging_utils import logger
from src.downloader.http_client import HttpClient, WEEBCENTRAL_URL


class ImageDownloader:
    def __init__(self, http: HttpClient, max_retries: int = 5, max_sleep: int = 120,
                 parallel_workers: int = 99, sequence: bool = False):
        self.http = http
        self.max_retries = max_retries
        self.max_sleep = max_sleep
        self.parallel_workers = parallel_workers
        self.sequence = sequence

    def download_image(self, img_url: str, dest_folder: str, referer: str) -> Optional[str]:
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                headers = {"Referer": referer}
                resp = self.http.scraper.get(
                    img_url, headers=headers, stream=True, timeout=15
                )
                resp.raise_for_status()
                filename = os.path.basename(img_url.split("?")[0])
                out_path = os.path.join(dest_folder, filename)
                with open(out_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                logger.debug(f"Downloaded: {img_url}")
                return out_path
            except Exception as e:
                logger.debug(f"Error downloading {img_url}: {e}")
                error_text = str(e).lower()
                if any(err in error_text
                       for err in ["beacon", "connection refused", "max retries exceeded"]):
                    sleep_time = random.randint(15, self.max_sleep)
                    logger.warning(f"Connection error on {img_url}. Sleeping for {sleep_time}s...")
                    time.sleep(sleep_time)
                    self.http.reset_scraper()
                    retry_count += 1
                else:
                    break
        logger.error(f"Failed to download {img_url} after {self.max_retries} retries")
        return None

    def download_chapter_images(
        self, chapter_id: str, chapter_num: str, outdir: str, chapter_dir_name: str
    ) -> Optional[str]:
        chapter_dir = os.path.join(outdir, chapter_dir_name)
        os.makedirs(chapter_dir, exist_ok=True)
        url = f"{WEEBCENTRAL_URL}/chapters/{chapter_id}/images?is_prev=False&current_page=1&reading_style=long_strip"
        try:
            resp = self.http.request("GET", url)
        except Exception as e:
            logger.error(f"Failed to fetch image list for chapter {chapter_num}: {e}")
            return None

        img_urls = self._extract_image_urls(resp)
        if not img_urls:
            logger.error(f"No images found in chapter {chapter_num}!")
            return None

        max_workers = 1 if self.sequence else self.parallel_workers
        if max_workers == 1:
            for img_url in img_urls:
                self.download_image(img_url, chapter_dir, url)
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(self.download_image, img_url, chapter_dir, url)
                    for img_url in img_urls
                ]
                concurrent.futures.wait(futures)
        return chapter_dir

    @staticmethod
    def _extract_image_urls(resp) -> list:
        srcs = []
        try:
            data = resp.json()
            srcs = [img.get("src") for img in data.get("images", []) if img.get("src")]
            if srcs:
                logger.debug(f"Found {len(srcs)} images via JSON API")
                return srcs
        except (ValueError, KeyError) as e:
            logger.debug(f"JSON API failed for images, falling back to HTML: {e}")
        srcs = re.findall(r'src="([^"]+)"', resp.text)
        logger.debug(f"Found {len(srcs)} images via HTML parsing")
        return srcs
