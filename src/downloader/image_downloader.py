"""Download manga page images (parallel + sequential modes)."""
import os
import re
import time
import random
import concurrent.futures
from typing import Optional
from src.logging_utils import logger
from src.downloader.http_client import HttpClient, WEEBCENTRAL_URL

# Substrings (lower-cased) of a transport error message that justify another
# attempt from download_image's outer retry loop. Mixes the cloudscraper-era
# strings (kept: existing callers/tests rely on them) with the modern
# Playwright/scrapling shapes ("net::ERR_CONNECTION_REFUSED", "target closed", ...).
CONNECTION_ERROR_MARKERS = (
    "beacon",
    "connection refused",
    "connection reset",
    "max retries exceeded",
    "err_connection",
    "net::",
    "timeout",
    "timed out",
    "failed to fetch",
    "target closed",
    # 5xx responses are worth another attempt; 4xx statuses are not.
    "http error 5",
)

# Extensions that mark a URL as a page image rather than a script/tracker.
IMAGE_URL_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".gif")


def _looks_like_image_url(url: str) -> bool:
    """True when the URL path (query/fragment stripped) ends in an image extension."""
    path = url.split("?")[0].split("#")[0].lower()
    return path.endswith(IMAGE_URL_EXTENSIONS)


def _dedupe(urls: list) -> list:
    """Deduplicate URLs while preserving first-seen order."""
    seen = set()
    ordered = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            ordered.append(url)
    return ordered


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
                # The outer loop owns the retry budget, so ask the transport for
                # a single attempt: --max-retries must be authoritative here.
                resp = self.http.request("GET", img_url, headers={"Referer": referer}, retries=1)
                resp.raise_for_status()
                filename = os.path.basename(img_url.split("?")[0])
                if not filename:
                    logger.error(f"Empty filename from URL: {img_url}")
                    return None
                out_path = os.path.join(dest_folder, filename)
                with open(out_path, "wb") as f:
                    f.write(resp.content)
                logger.debug(f"Downloaded: {img_url}")
                return out_path
            except Exception as e:
                if isinstance(e, KeyboardInterrupt):
                    raise
                logger.error(f"Error downloading {img_url}: {type(e).__name__}: {e}")
                error_text = str(e).lower()
                if any(err in error_text for err in CONNECTION_ERROR_MARKERS):
                    sleep_time = random.randint(15, max(15, self.max_sleep))
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
            resp = self.http.request("GET", url, headers={"HX-Request": "true"})
        except Exception as e:
            logger.error(f"Failed to fetch image list for chapter {chapter_num}: {e}")
            return None

        img_urls = self._extract_image_urls(resp)
        if not img_urls:
            logger.error(f"No images found in chapter {chapter_num}!")
            return None

        max_workers = 1 if self.sequence else self.parallel_workers
        downloaded = 0
        failures = []
        if max_workers == 1:
            for img_url in img_urls:
                result = self.download_image(img_url, chapter_dir, url)
                if result is None:
                    failures.append("download_image returned None")
                else:
                    downloaded += 1
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(self.download_image, img_url, chapter_dir, url)
                    for img_url in img_urls
                ]
                # Collect results explicitly: a worker exception must be counted
                # as a failed page, never silently discarded (and never abort
                # the rest of the chapter).
                for future in futures:
                    try:
                        result = future.result()
                    except Exception as e:
                        failures.append(f"{type(e).__name__}: {e}")
                        continue
                    if result is None:
                        failures.append("download_image returned None")
                    else:
                        downloaded += 1

        if failures:
            last_failure = failures[-1]
            if downloaded == 0:
                logger.error(
                    f"All {len(img_urls)} image downloads failed for chapter "
                    f"{chapter_num} ({chapter_id}); last failure: {last_failure}"
                )
                return None
            logger.warning(
                f"{len(failures)} of {len(img_urls)} image downloads failed for chapter "
                f"{chapter_num}; last failure: {last_failure}"
            )
        return chapter_dir

    @staticmethod
    def _extract_image_urls(resp) -> list:
        try:
            data = resp.json()
            srcs = [img.get("src") for img in data.get("images", []) if img.get("src")]
            if srcs:
                logger.debug(f"Found {len(srcs)} images via JSON API")
                return srcs
        except (ValueError, KeyError, AttributeError, TypeError) as e:
            logger.debug(f"JSON API failed for images, falling back to HTML: {e}")
        candidates = re.findall(r'src="([^"]+)"', resp.text)
        image_candidates = [url for url in candidates if _looks_like_image_url(url)]
        if image_candidates:
            srcs = _dedupe(image_candidates)
            logger.debug(
                f"Found {len(srcs)} image URLs via HTML parsing "
                f"(kept {len(image_candidates)} extension matches of "
                f"{len(candidates)} candidates)"
            )
        else:
            # No image-extension URL at all: never drop the page's real images,
            # so fall back to every candidate.
            srcs = _dedupe(candidates)
            logger.debug(
                f"Found {len(srcs)} URLs via HTML parsing (no image extensions found)"
            )
        return srcs
