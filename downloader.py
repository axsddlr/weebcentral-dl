import argparse
import os
import re
import tempfile
import zipfile
import shutil
import concurrent.futures
import random
import time
import html
from urllib.parse import quote_plus
import cloudscraper
from typing import List, Optional, Tuple, Set
from PIL import Image

from utils import sanitize_title, get_vol_and_chapter_names, has_images

# --- Constants ---
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
PARALLEL_DOWNLOAD = 99
WEEBCENTRAL_URL = "https://weebcentral.com"


class WeebCentralDownloader:
    def __init__(self, config: argparse.Namespace):
        self.config = config
        self.scraper = cloudscraper.create_scraper()
        self.scraper.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "*/*",
            "HX-Request": "true",  # Enable HTMX/JSON responses
        })
        self.output_dir = os.path.abspath(config.output)
        os.makedirs(self.output_dir, exist_ok=True)

    def vprint(self, *args, **kwargs):
        if self.config.verbose:
            print(*args, **kwargs)

    def log_not_found(self, msg: str):
        try:
            logfile = os.path.join(self.output_dir, "not_found.log")
            with open(logfile, "a", encoding="utf-8") as f:
                f.write(msg + "\n")
        except Exception as e:
            print(f"[WARN] Could not write to not_found.log: {e}")

    def get_series_id_from_query(self, query: str) -> Optional[Tuple[str, str]]:
        encoded = quote_plus(query)
        url = f"{WEEBCENTRAL_URL}/search/data?author=&text={encoded}&sort=Best%20Match&order=Descending&official=Any&anime=Any&adult=Any&display_mode=Full%20Display"
        resp = self.scraper.get(url)
        results = re.findall(r'/series/([^"/]+/[^"]+)', resp.text)
        if not results:
            msg = f"NOT FOUND: {query}"
            print(msg)
            self.log_not_found(msg)
            return None, None

        unique_results = sorted(list(set(results)))
        if not unique_results:
            msg = f"NO UNIQUE LINKS: {query}"
            print(msg)
            self.log_not_found(msg)
            return None, None

        if len(unique_results) > 1:
            msg = f"MULTIPLE UNIQUE: {query} => {unique_results}"
            print(
                f"Warning: Multiple unique search results for '{query}', picking the first: {unique_results[0]}"
            )
            self.log_not_found(msg)

        series_id, series_title = unique_results[0].split("/")
        return series_id, series_title

    def fetch_chapter_list(self, series_id: str) -> List[Tuple[str, str, str]]:
        series_id = series_id.upper()
        url = f"{WEEBCENTRAL_URL}/series/{series_id}/full-chapter-list"
        resp = self.scraper.get(url)

        # Try JSON API first
        try:
            data = resp.json()
            chapters = []
            for chap in data.get("chapters", []):
                # Extract chapter type and number from title
                title = chap.get("title", "")
                # Match "Chapter 123" or "Episode 456" or "# 789"
                match = re.search(r'([A-Za-z#]+)\s*([\d\.]+)', title)
                if match:
                    chap_type = match.group(1).strip()
                    chap_num = match.group(2)
                    # Extract chapter ID from URL
                    chap_url = chap.get("url", "")
                    chap_id_match = re.search(r'/chapters/([A-Z0-9]+)', chap_url)
                    if chap_id_match:
                        chap_id = chap_id_match.group(1)
                        chapters.append((chap_type, chap_num, chap_id))
            if chapters:
                chapters.sort(key=lambda x: float(x[1]), reverse=True)
                self.vprint(f"[JSON] Fetched {len(chapters)} chapters via JSON API")
                return chapters
        except (ValueError, KeyError) as e:
            self.vprint(f"[JSON] Failed to parse JSON, falling back to HTML: {e}")

        # Fallback to HTML regex parsing
        pattern = re.compile(
            r'<span class="">([A-Za-z#]+)\s*([\d\.]+)</span>[\s\S]*?value="([A-Z0-9]+)"'
        )
        chapters = [
            (m.group(1).strip(), m.group(2), m.group(3))
            for m in pattern.finditer(resp.text)
        ]
        chapters.sort(key=lambda x: float(x[1]), reverse=True)
        self.vprint(f"[HTML] Fetched {len(chapters)} chapters via HTML parsing")
        return chapters

    def get_series_title_by_id(self, series_id: str) -> str:
        url = f"{WEEBCENTRAL_URL}/series/{series_id}"
        try:
            resp = self.scraper.get(url)
            m = re.search(r"<h1[^>]*>([^<]+)</h1>", resp.text)
            if m:
                title = html.unescape(m.group(1).strip())
                return sanitize_title(title)
        except Exception as e:
            self.vprint(f"Could not fetch manga title for series_id {series_id}: {e}")
        return series_id

    def get_series_metadata(self, series_id: str) -> dict:
        """Extract metadata for series (title, description, authors, tags).

        Useful for future ComicInfo.xml generation or display.
        """
        url = f"{WEEBCENTRAL_URL}/series/{series_id}"
        metadata = {
            "title": "",
            "description": "",
            "authors": [],
            "tags": [],
        }

        try:
            resp = self.scraper.get(url)
            text = resp.text

            # Extract title
            title_match = re.search(r"<h1[^>]*>([^<]+)</h1>", text)
            if title_match:
                metadata["title"] = html.unescape(title_match.group(1).strip())

            # Extract description (look for "Description" heading followed by paragraph)
            desc_match = re.search(r'<strong[^>]*>[^<]*Description[^<]*</strong>\s*\+?\s*<p[^>]*>([^<]+)</p>', text, re.IGNORECASE)
            if desc_match:
                metadata["description"] = html.unescape(desc_match.group(1).strip())

            # Extract authors (links after "Author" heading)
            author_section = re.search(r'<strong[^>]*>[^<]*Author[^<]*</strong>(.*?)(?=<strong|$)', text, re.IGNORECASE | re.DOTALL)
            if author_section:
                author_links = re.findall(r'<a[^>]*>([^<]+)</a>', author_section.group(1))
                metadata["authors"] = [html.unescape(a.strip()) for a in author_links]

            # Extract tags (links after "Tags" heading)
            tags_section = re.search(r'<strong[^>]*>[^<]*Tags[^<]*</strong>(.*?)(?=<strong|$)', text, re.IGNORECASE | re.DOTALL)
            if tags_section:
                tag_links = re.findall(r'<a[^>]*>([^<]+)</a>', tags_section.group(1))
                metadata["tags"] = [html.unescape(t.strip()) for t in tag_links]

            self.vprint(f"[Metadata] Title: {metadata['title']}, Authors: {len(metadata['authors'])}, Tags: {len(metadata['tags'])}")

        except Exception as e:
            self.vprint(f"Could not extract metadata for series_id {series_id}: {e}")

        return metadata

    def get_latest_downloaded_chapter(self, series_title: str) -> Optional[float]:
        out_dir = os.path.join(self.output_dir, series_title)
        if not os.path.exists(out_dir):
            return None

        chapter_nums = []
        patterns = [
            re.compile(r"vol_0*(\d+)(?:-(\d+))?\.zip$"),
            re.compile(rf"{re.escape(series_title)}-(\d+)(?:\.(\d+))?.*\.cbz$"),
        ]

        for f in os.listdir(out_dir):
            for pattern in patterns:
                m = pattern.match(f)
                if m:
                    try:
                        val_str = (
                            f"{m.group(1)}.{m.group(2)}" if m.group(2) else m.group(1)
                        )
                        chapter_nums.append(float(val_str))
                    except (ValueError, IndexError):
                        continue
        return max(chapter_nums) if chapter_nums else None

    def chapter_already_downloaded(self, chap_num: str, out_dir: str) -> bool:
        if not os.path.exists(out_dir):
            return False
        base = int(float(chap_num))
        patt = re.compile(rf"vol_0*{base}(?:-[0-9]+)?\.zip$")
        for fname in os.listdir(out_dir):
            if patt.fullmatch(fname):
                return True
        return False

    def download_image(self, img_url: str, dest_folder: str, referer: str):
        retry_count = 0
        while retry_count < self.config.max_retries:
            try:
                headers = {"Referer": referer}
                resp = self.scraper.get(
                    img_url, headers=headers, stream=True, timeout=15
                )
                resp.raise_for_status()
                filename = os.path.basename(img_url.split("?")[0])
                out_path = os.path.join(dest_folder, filename)
                with open(out_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                self.vprint(f"Downloaded: {img_url}")
                return out_path
            except Exception as e:
                self.vprint(f"Error downloading {img_url}: {e}")
                error_text = str(e).lower()
                if any(
                    err in error_text
                    for err in ["beacon", "connection refused", "max retries exceeded"]
                ):
                    sleep_time = random.randint(15, self.config.max_sleep)
                    print(
                        f"\n[WARN] Connection error on {img_url}. Sleeping for {sleep_time}s and retrying...\n"
                    )
                    time.sleep(sleep_time)
                    self.scraper = cloudscraper.create_scraper()
                    retry_count += 1
                else:
                    break
        self.vprint(
            f"[FAIL] Giving up on {img_url} after {self.config.max_retries} retries."
        )
        return None

    def download_chapter_images(
        self, chapter_id: str, chapter_num: str, outdir: str, chapter_dir_name: str
    ) -> Optional[str]:
        chapter_dir = os.path.join(outdir, chapter_dir_name)
        os.makedirs(chapter_dir, exist_ok=True)
        url = f"{WEEBCENTRAL_URL}/chapters/{chapter_id}/images?is_prev=False&current_page=1&reading_style=long_strip"
        resp = self.scraper.get(url)
        img_urls = []

        # Try JSON API first
        try:
            data = resp.json()
            img_urls = [img.get("src") for img in data.get("images", []) if img.get("src")]
            if img_urls:
                self.vprint(f"[JSON] Found {len(img_urls)} images via JSON API")
        except (ValueError, KeyError) as e:
            self.vprint(f"[JSON] Failed to parse JSON, falling back to HTML: {e}")

        # Fallback to HTML regex parsing
        if not img_urls:
            img_urls = re.findall(r'src="([^"]+)"', resp.text)
            self.vprint(f"[HTML] Found {len(img_urls)} images via HTML parsing")

        if not img_urls:
            print(f"No images found in chapter {chapter_num}!")
            return None

        if self.config.sequence:
            for img_url in img_urls:
                self.download_image(img_url, chapter_dir, url)
        else:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=PARALLEL_DOWNLOAD
            ) as executor:
                futures = [
                    executor.submit(self.download_image, img_url, chapter_dir, url)
                    for img_url in img_urls
                ]
                concurrent.futures.wait(futures)
        return chapter_dir

    def archive_chapter(
        self, chapter_dir: str, series_title: str, chapter_num: str, chapter_type: str
    ):
        out_dir = os.path.join(self.output_dir, series_title)
        os.makedirs(out_dir, exist_ok=True)

        if not has_images(chapter_dir):
            print(f"Warning: No images found in {chapter_dir} (skipping archive)")
            shutil.rmtree(chapter_dir)
            return

        if self.config.zip:
            vol_name, _ = get_vol_and_chapter_names(chapter_num)
            zip_path = os.path.join(out_dir, f"{vol_name}.zip")
            shutil.make_archive(os.path.splitext(zip_path)[0], "zip", chapter_dir)
            print(f"Created zip archive: {zip_path}")
        else:
            out_file = os.path.join(
                out_dir,
                f"{series_title}-{chapter_num}{('-' + chapter_type) if chapter_type else ''}.cbz",
            )
            with zipfile.ZipFile(out_file, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, _, files in os.walk(chapter_dir):
                    for file in files:
                        zf.write(os.path.join(root, file), arcname=file)
            print(f"Wrote {out_file}")
        shutil.rmtree(chapter_dir)

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

            if self.config.zip and self.chapter_already_downloaded(chap_num, out_dir):
                print(f"Skipping already-downloaded chapter {chap_num} (zip found)")
                continue

            print(f"Downloading chapter {chap_num}")
            temp_dir = tempfile.mkdtemp(prefix=f"{series_title}-{chap_num}_")
            try:
                chapter_dir = self.download_chapter_images(
                    chap_id, chap_num, temp_dir, chapter_dir_name
                )
                if chapter_dir:
                    self.archive_chapter(chapter_dir, series_title, chap_num, ct)
            finally:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)

            chap_counter += 1
            if is_fresh and chap_counter % self.config.rlc == 0:
                wait = random.randint(15, self.config.max_sleep)
                print(
                    f"\n[INFO] Rate limiting: sleeping for {wait} seconds after {chap_counter} chapters\n"
                )
                time.sleep(wait)

    def process_manga(
        self,
        title: Optional[str] = None,
        series_id: Optional[str] = None,
        chapters_to_download: Optional[Set[str]] = None,
    ):
        if series_id and title:
            # Both provided (from bulk file format: series_id=title)
            series_id = series_id.strip()
            series_title = sanitize_title(title.strip())
            print(f"\nProcessing series id: {series_id} (title: {series_title})")
        elif series_id:
            series_id = series_id.strip()
            series_title = self.get_series_title_by_id(series_id)
            print(f"\nProcessing series id: {series_id} (title: {series_title})")
        elif title:
            search_title = title.replace("-", " ").strip()
            result = self.get_series_id_from_query(search_title)
            if not result or not result[0]:
                print(f"Skipping '{title}': not found.")
                return
            series_id, series_title = result
        else:
            print("Error: No title or series_id provided.")
            return

        chapters = self.fetch_chapter_list(series_id)
        if not chapters:
            print(f"No chapters found for '{title or series_id}'.")
            return

        self.download_cover_image_and_convert(series_id, series_title)

        out_dir = os.path.join(self.output_dir, series_title)
        is_fresh = not os.path.exists(out_dir) or not os.listdir(out_dir)

        if self.config.latest and chapters_to_download is None:
            latest = self.get_latest_downloaded_chapter(series_title)
            if latest is None:
                print("No downloaded chapters found, downloading all chapters.")
                # When -l is used and no chapters are downloaded, download all
                chapters_to_download = {chap[1] for chap in chapters}
            else:
                chapters_to_download = {
                    chap[1] for chap in chapters if float(chap[1]) > latest
                }
                if not chapters_to_download:
                    print(f"No new chapters found after chapter {latest}.")
                    return
                print(
                    f"Downloading new chapters after chapter {latest}: {sorted(list(chapters_to_download))}"
                )

        self.vprint(
            f"Downloading chapters: {chapters_to_download if chapters_to_download else 'ALL'} (zip mode: {self.config.zip})"
        )
        self.download_chapters(chapters, chapters_to_download, series_title, is_fresh)

    def download_cover_image_and_convert(self, series_id: str, series_title: str):
        cover_path = self.download_cover_image(series_id, series_title)
        if cover_path and cover_path.endswith(".webp"):
            try:
                img = Image.open(cover_path).convert("RGB")
                new_path = os.path.splitext(cover_path)[0] + ".jpg"
                img.save(new_path, "jpeg")
                os.remove(cover_path)
                self.vprint(f"Converted {cover_path} to {new_path}")
            except Exception as e:
                self.vprint(f"Could not convert cover image {cover_path}: {e}")

    def download_cover_image(self, series_id: str, series_title: str):
        out_dir = os.path.join(self.output_dir, series_title)
        if os.path.exists(out_dir) and any(f.lower().endswith(".jpg") for f in os.listdir(out_dir)):
            self.vprint(f"Cover image already exists for {series_title}, skipping download.")
            return None

        url = f"{WEEBCENTRAL_URL}/series/{series_id}"
        try:
            resp = self.scraper.get(url)
            m = re.search(r'<source srcset="([^"]+)"', resp.text)
            if m:
                cover_url = m.group(1)
                os.makedirs(out_dir, exist_ok=True)
                return self.download_image(cover_url, out_dir, url)
        except Exception as e:
            self.vprint(
                f"Could not download cover image for series_id {series_id}: {e}"
            )
        return None
