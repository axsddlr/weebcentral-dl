#!/usr/bin/env python3
import argparse
import os
import re
import sys
import tempfile
import zipfile
import shutil
import concurrent.futures
import random
import time
import html
import unicodedata
from urllib.parse import quote_plus
import cloudscraper
from typing import List, Optional, Tuple, Set

# --- Constants ---
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
PARALLEL_DOWNLOAD = 99
WEEBCENTRAL_URL = "https://weebcentral.com"


# --- Utility Functions ---
def sanitize_title(title: str) -> str:
    """Sanitizes a title to be used as a valid directory name."""
    title = title.replace(" ", "-")
    title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode()
    title = re.sub(r'[^A-Za-z0-9\-_]', '', title)
    return re.sub(r'-+', '-', title).strip('-')

def get_vol_and_chapter_names(chap_num: str) -> Tuple[str, str]:
    """Generates volume and chapter directory names from a chapter number."""
    base = int(float(chap_num))
    dec = None
    if '.' in str(chap_num):
        dec = str(chap_num).split('.')[-1]
        if dec != "0":
            return f"vol_{{base}}-{{dec}}", f"chapter_{{base}}-{{dec}}"
    return f"vol_{{base:03d}}", f"chapter_{{base:03d}}"

def has_images(folder: str) -> bool:
    """Checks if a directory contains any image files."""
    exts = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif")
    if not os.path.exists(folder):
        return False
    for f in os.listdir(folder):
        if f.lower().endswith(exts):
            return True
    return False


class WeebCentralDownloader:
    def __init__(self, config: argparse.Namespace):
        self.config = config
        self.scraper = cloudscraper.create_scraper()
        self.scraper.headers.update({"User-Agent": USER_AGENT})
        self.output_dir = os.path.abspath(config.output)
        os.makedirs(self.output_dir, exist_ok=True)

    def vprint(self, *args, **kwargs):
        if self.config.verbose:
            print(*args, **kwargs)

    def log_not_found(self, msg: str):
        try:
            logfile = os.path.join(self.output_dir, 'not_found.log')
            with open(logfile, 'a', encoding='utf-8') as f:
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
            print(f"Warning: Multiple unique search results for '{query}', picking the first: {unique_results[0]}")
            self.log_not_found(msg)

        series_id, series_title = unique_results[0].split('/')
        return series_id, series_title

    def fetch_chapter_list(self, series_id: str) -> List[Tuple[str, str, str]]:
        series_id = series_id.upper()
        url = f"{WEEBCENTRAL_URL}/series/{series_id}/full-chapter-list"
        resp = self.scraper.get(url)
        pattern = re.compile(r'>([#A-Za-z ]+) (\d+\.?\d*)[^\\]*\'([A-Z0-9]+)')
        chapters = [
            (m.group(1).strip(), m.group(2), m.group(3))
            for m in pattern.finditer(resp.text)
        ]
        chapters.sort(key=lambda x: float(x[1]), reverse=True)
        return chapters

    def get_series_title_by_id(self, series_id: str) -> str:
        url = f"{WEEBCENTRAL_URL}/series/{series_id}"
        try:
            resp = self.scraper.get(url)
            m = re.search(r'<h1[^>]*>([^<]+)</h1>', resp.text)
            if m:
                title = html.unescape(m.group(1).strip())
                return sanitize_title(title)
        except Exception as e:
            self.vprint(f"Could not fetch manga title for series_id {series_id}: {e}")
        return series_id

    def get_latest_downloaded_chapter(self, series_title: str) -> Optional[float]:
        out_dir = os.path.join(self.output_dir, series_title)
        if not os.path.exists(out_dir):
            return None

        chapter_nums = []
        patterns = [
            re.compile(r"vol_0*(\d+)(?:-(\d+))?\.zip$"),
            re.compile(rf"{re.escape(series_title)}-(\d+)(?:\.(\d+))?.*\.cbz$")
        ]

        for f in os.listdir(out_dir):
            for pattern in patterns:
                m = pattern.match(f)
                if m:
                    try:
                        val_str = f"{m.group(1)}.{m.group(2)}" if m.group(2) else m.group(1)
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
                resp = self.scraper.get(img_url, headers=headers, stream=True, timeout=15)
                resp.raise_for_status()
                filename = os.path.basename(img_url.split('?')[0])
                out_path = os.path.join(dest_folder, filename)
                with open(out_path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                self.vprint(f"Downloaded: {img_url}")
                return
            except Exception as e:
                self.vprint(f"Error downloading {img_url}: {e}")
                error_text = str(e).lower()
                if any(err in error_text for err in ["beacon", "connection refused", "max retries exceeded"]):
                    sleep_time = random.randint(15, self.config.max_sleep)
                    print(f"\n[WARN] Connection error on {img_url}. Sleeping for {sleep_time}s and retrying...\n")
                    time.sleep(sleep_time)
                    retry_count += 1
                else:
                    break
        self.vprint(f"[FAIL] Giving up on {img_url} after {self.config.max_retries} retries.")

    def download_chapter_images(self, chapter_id: str, chapter_num: str, outdir: str, chapter_dir_name: str) -> Optional[str]:
        chapter_dir = os.path.join(outdir, chapter_dir_name)
        os.makedirs(chapter_dir, exist_ok=True)
        url = f"{WEEBCENTRAL_URL}/chapters/{chapter_id}/images?is_prev=False&current_page=1&reading_style=long_strip"
        resp = self.scraper.get(url)
        img_urls = re.findall(r'src="([^"]+)"', resp.text)

        if not img_urls:
            print(f"No images found in chapter {chapter_num}!")
            return None

        if self.config.sequence:
            for img_url in img_urls:
                self.download_image(img_url, chapter_dir, url)
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=PARALLEL_DOWNLOAD) as executor:
                futures = [executor.submit(self.download_image, img_url, chapter_dir, url) for img_url in img_urls]
                concurrent.futures.wait(futures)
        return chapter_dir

    def archive_chapter(self, chapter_dir: str, series_title: str, chapter_num: str, chapter_type: str):
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
            out_file = os.path.join(out_dir, f"{series_title}-{chapter_num}{('-'+chapter_type) if chapter_type else ''}.cbz")
            with zipfile.ZipFile(out_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, _, files in os.walk(chapter_dir):
                    for file in files:
                        zf.write(os.path.join(root, file), arcname=file)
            print(f"Wrote {out_file}")
        shutil.rmtree(chapter_dir)

    def download_chapters(self, chapters: List[Tuple[str, str, str]], chapters_to_download: Optional[Set[str]], series_title: str, is_fresh: bool):
        out_dir = os.path.join(self.output_dir, series_title)
        chap_counter = 0
        for chap_type, chap_num, chap_id in reversed(chapters):
            chap_num_str = str(float(chap_num)).rstrip('0').rstrip('.') if '.' in chap_num else chap_num
            if chapters_to_download is not None and chap_num_str not in chapters_to_download:
                continue

            ct = "" if chap_type in ["Chapter", "#"] else chap_type
            _, chapter_dir_name = get_vol_and_chapter_names(chap_num)

            if self.config.zip and self.chapter_already_downloaded(chap_num, out_dir):
                print(f"Skipping already-downloaded chapter {chap_num} (zip found)")
                continue

            print(f"Downloading chapter {chap_num}")
            temp_dir = tempfile.mkdtemp(prefix=f"{series_title}-{chap_num}_")
            try:
                chapter_dir = self.download_chapter_images(chap_id, chap_num, temp_dir, chapter_dir_name)
                if chapter_dir:
                    self.archive_chapter(chapter_dir, series_title, chap_num, ct)
            finally:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)

            chap_counter += 1
            if is_fresh and chap_counter % self.config.rlc == 0:
                wait = random.randint(15, self.config.max_sleep)
                print(f"\n[INFO] Rate limiting: sleeping for {wait} seconds after {chap_counter} chapters\n")
                time.sleep(wait)

    def process_manga(self, title: Optional[str] = None, series_id: Optional[str] = None, chapters_to_download: Optional[Set[str]] = None):
        if series_id:
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

        out_dir = os.path.join(self.output_dir, series_title)
        is_fresh = not os.path.exists(out_dir) or not os.listdir(out_dir)

        if self.config.latest and chapters_to_download is None:
            latest = self.get_latest_downloaded_chapter(series_title)
            if latest is not None:
                chapters_to_download = {chap[1] for chap in chapters if float(chap[1]) > latest}
                if not chapters_to_download:
                    print(f"No new chapters after {latest}")
                    return
                print(f"Will download chapters after {latest}: {sorted(list(chapters_to_download))}")
            else:
                print("No chapters found in output directory; will download ALL chapters.")
                chapters_to_download = None
        
        self.vprint(f"Downloading chapters: {chapters_to_download if chapters_to_download else 'ALL'} (zip mode: {self.config.zip})")
        self.download_chapters(chapters, chapters_to_download, series_title, is_fresh)


def parse_chapter_arg(chapter_arg: Optional[str]) -> Optional[Set[str]]:
    if not chapter_arg:
        return None
    return {p.strip() for p in chapter_arg.split(",") if p.strip()}

def main():
    parser = argparse.ArgumentParser(description="Manga downloader script (WeebCentral)")
    parser.add_argument('query', nargs='*', help="Manga title to search for (ignored if --bulk or --series-id is used)")
    parser.add_argument('-c', '--chapter', type=str, default=None, help="Specific chapter(s) to download, e.g. 12,12.5,13 (comma-separated)")
    parser.add_argument('-o', '--output', dest='output', default="./manga_downloads", help="Output directory for downloads")
    parser.add_argument('-l', '--latest', action='store_true', help="Download only chapters after the latest one in the output directory")
    parser.add_argument('-z', '--zip', action='store_true', help="Create zip archives for chapters (vol_NNN.zip)")
    parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose debug output")
    parser.add_argument('-b', '--bulk', type=str, help="Path to text file containing manga titles (one per line; you can use seriesid=optional-title)")
    parser.add_argument('-s', '--sequence', action='store_true', help="Download images in sequence (disable parallel downloading)")
    parser.add_argument('--rlc', type=int, default=10, help="Chapters between rate limits (default: 10)")
    parser.add_argument('--max-sleep', type=int, default=120, help="Max sleep time for rate limit/retry (default: 120)")
    parser.add_argument('--max-retries', type=int, default=5, help="Max retries for image download (default: 5)")
    parser.add_argument('-id', '--series-id', type=str, help="Direct WeebCentral series ID (bypasses search)")
    args = parser.parse_args()

    downloader = WeebCentralDownloader(args)
    chapters_to_download = parse_chapter_arg(args.chapter)

    if args.bulk:
        try:
            with open(args.bulk, "r", encoding='utf-8') as f:
                manga_list = [line.strip() for line in f if line.strip()]
            print(f"Found {len(manga_list)} manga titles in {args.bulk}")
            for line in manga_list:
                if '=' in line:
                    series_id, _ = line.split('=', 1)
                    downloader.process_manga(series_id=series_id.strip(), chapters_to_download=chapters_to_download)
                else:
                    downloader.process_manga(title=line, chapters_to_download=chapters_to_download)
        except FileNotFoundError:
            print(f"Error: Could not find bulk file: {args.bulk}")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading bulk file: {e}")
            sys.exit(1)

    elif args.series_id:
        downloader.process_manga(series_id=args.series_id, chapters_to_download=chapters_to_download)
    elif args.query:
        title = " ".join(args.query).strip()
        downloader.process_manga(title=title, chapters_to_download=chapters_to_download)
    else:
        print("No manga title, series ID, or bulk file specified. Use -h for help.")
        sys.exit(1)

if __name__ == "__main__":
    main()