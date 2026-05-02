"""Manage manga cover images (find, download, convert)."""
import os
import re
from typing import Optional
from PIL import Image
from loguru import logger
from src.downloader.http_client import HttpClient, WEEBCENTRAL_URL
from src.downloader.image_downloader import ImageDownloader
from src.utils import find_cover_in_dir


class CoverManager:
    def __init__(self, http: HttpClient, image_downloader: ImageDownloader, output_dir: str):
        self.http = http
        self.image_downloader = image_downloader
        self.output_dir = output_dir

    def get_cover_image_path(self, series_title: str) -> Optional[str]:
        series_dir = os.path.join(self.output_dir, series_title)
        return find_cover_in_dir(series_dir)

    def download_and_convert(self, series_id: str, series_title: str):
        cover_path = self.download(series_id, series_title)
        if cover_path and cover_path.endswith(".webp"):
            try:
                img = Image.open(cover_path).convert("RGB")
                new_path = os.path.splitext(cover_path)[0] + ".jpg"
                img.save(new_path, "jpeg")
                os.remove(cover_path)
                logger.debug(f"Converted {cover_path} to {new_path}")
            except Exception as e:
                logger.warning(f"Could not convert cover image {cover_path}: {e}")

    def download(self, series_id: str, series_title: str) -> Optional[str]:
        out_dir = os.path.join(self.output_dir, series_title)
        if os.path.exists(out_dir) and any(f.lower().endswith(".jpg") for f in os.listdir(out_dir)):
            logger.debug(f"Cover image already exists for {series_title}, skipping download")
            return None
        url = f"{WEEBCENTRAL_URL}/series/{series_id}"
        try:
            resp = self.http.request("GET", url)
            text = resp.text
            if "<h1" not in text and "series/index" in text.lower():
                logger.warning(
                    f"Cover page for {series_id} returned unexpected content "
                    f"(possible captcha or redirect)"
                )
                return None
            m = re.search(r'<source srcset="([^"]+)"', text)
            if m:
                cover_url = m.group(1)
                os.makedirs(out_dir, exist_ok=True)
                return self.image_downloader.download_image(cover_url, out_dir, url)
        except Exception as e:
            logger.warning(f"Could not download cover image for series_id {series_id}: {type(e).__name__}: {e}")
        return None
