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

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
PARALLEL_DOWNLOAD = 99

scraper = cloudscraper.create_scraper()
scraper.headers.update({"User-Agent": USER_AGENT})

def vprint(*args, **kwargs):
    if VERBOSE:
        print(*args, **kwargs)

def ensure_dirs(base_dir):
    os.makedirs(base_dir, exist_ok=True)

def log_not_found(msg, output_dir):
    try:
        logfile = os.path.join(output_dir, 'not_found.log')
        with open(logfile, 'a', encoding='utf-8') as f:
            f.write(msg + "\n")
    except Exception as e:
        print(f"[WARN] Could not write to not_found.log: {e}")

def get_series_id_from_query(query, output_dir):
    encoded = quote_plus(query)
    url = f"https://weebcentral.com/search/data?author=&text={encoded}&sort=Best%20Match&order=Descending&official=Any&anime=Any&adult=Any&display_mode=Full%20Display"
    resp = scraper.get(url)
    results = re.findall(r'/series/([^"/]+/[^"]+)', resp.text)
    if not results:
        msg = f"NOT FOUND: {query}"
        print(msg)
        log_not_found(msg, output_dir)
        return None, None
    # Deduplicate (preserve order)
    seen = set()
    unique_results = []
    for r in results:
        if r not in seen:
            seen.add(r)
            unique_results.append(r)
    if not unique_results:
        msg = f"NO UNIQUE LINKS: {query}"
        print(msg)
        log_not_found(msg, output_dir)
        return None, None
    if len(unique_results) > 1:
        msg = f"MULTIPLE UNIQUE: {query} => {unique_results}"
        print(f"Warning: Multiple unique search results for '{query}', picking the first: {unique_results[0]}")
        log_not_found(msg, output_dir)
    series_id, series_title = unique_results[0].split('/')
    return series_id, series_title

def fetch_chapter_list(series_id):
    series_id = series_id.upper()
    url = f"https://weebcentral.com/series/{series_id}/full-chapter-list"
    resp = scraper.get(url)
    pattern = re.compile(r'>([#A-Za-z ]+) (\d+\.?\d*)[^\']*\'([A-Z0-9]+)')
    chapters = []
    for m in pattern.finditer(resp.text):
        chap_type = m.group(1).strip()
        chap_num = m.group(2)
        chap_id = m.group(3)
        chapters.append((chap_type, chap_num, chap_id))
    chapters.sort(key=lambda x: float(x[1]), reverse=True)
    return chapters

def get_series_title_by_id(series_id):
    """Fetches the official manga title from the series page using the series_id, formats for filesystem/folder."""
    url = f"https://weebcentral.com/series/{series_id}"
    try:
        resp = scraper.get(url)
        m = re.search(r'<h1[^>]*>([^<]+)</h1>', resp.text)
        if m:
            title = html.unescape(m.group(1).strip())
            title = title.replace(" ", "-")
            title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode()
            title = re.sub(r'[^A-Za-z0-9\-_]', '', title)
            title = re.sub(r'-+', '-', title).strip('-')
            return title
    except Exception as e:
        vprint(f"Could not fetch manga title for series_id {series_id}: {e}")
    return series_id

def get_latest_downloaded_chapter(base_dir, series_title, zip_mode=False):
    out_dir = os.path.join(base_dir, series_title)
    if not os.path.exists(out_dir):
        return None
    chapter_nums = []
    if zip_mode:
        for f in os.listdir(out_dir):
            m = re.match(r"vol_0*(\d+)(?:-(\d+))?\.zip$", f)
            if m:
                try:
                    if m.group(2):
                        val = float(f"{m.group(1)}.{m.group(2)}")
                    else:
                        val = float(m.group(1))
                    chapter_nums.append(val)
                except Exception:
                    continue
    else:
        for f in os.listdir(out_dir):
            m = re.match(rf"{re.escape(series_title)}-(\d+)(?:\.(\d+))?.*\.cbz$", f)
            if m:
                try:
                    if m.group(2):
                        val = float(f"{m.group(1)}.{m.group(2)}")
                    else:
                        val = float(m.group(1))
                    chapter_nums.append(val)
                except Exception:
                    continue
    return max(chapter_nums) if chapter_nums else None

def chapter_already_downloaded(chap_num, out_dir):
    """Return True if any zip for this chapter exists, ignoring zero-padding or decimals."""
    if not os.path.exists(out_dir):
        return False  # Directory not there means nothing is downloaded
    base = int(float(chap_num))
    patt = re.compile(rf"vol_0*{base}(?:-[0-9]+)?\.zip$")
    for fname in os.listdir(out_dir):
        if patt.fullmatch(fname):
            return True
    return False


def download_image(img_url, dest_folder, referer=None, max_sleep=120, max_retries=5):
    retry_count = 0
    while retry_count < max_retries:
        try:
            headers = {"Referer": referer or "https://weebcentral.com/"}
            resp = scraper.get(img_url, headers=headers, stream=True, timeout=15)
            if resp.ok:
                filename = os.path.basename(img_url.split('?')[0])
                out_path = os.path.join(dest_folder, filename)
                with open(out_path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                vprint(f"Downloaded: {img_url}")
                return
        except Exception as e:
            vprint(f"Error downloading {img_url}: {e}")
            error_text = str(e)
            if (
                "beacon" in img_url
                or "connection refused" in error_text.lower()
                or "max retries exceeded" in error_text.lower()
            ):
                sleep_time = random.randint(15, max_sleep)
                print(f"\n[WARN] Hit a connection error on {img_url}. Sleeping for {sleep_time}s and retrying (retry {retry_count + 1}/5)\n")
                time.sleep(sleep_time)
                retry_count += 1
            else:
                break
    vprint(f"[FAIL] Giving up on {img_url} after {max_retries} retries.")

def get_vol_and_chapter_names(chap_num):
    base = int(float(chap_num))
    dec = None
    if '.' in str(chap_num):
        dec = str(chap_num).split('.')[-1]
        if dec != "0":
            return f"vol_{base}-{dec}", f"chapter_{base}-{dec}"
    # always pad with 3 digits
    return f"vol_{base:03d}", f"chapter_{base:03d}"

def has_images(folder):
    exts = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif")
    for f in os.listdir(folder):
        if f.lower().endswith(exts):
            return True
    return False

def download_chapter_images(chapter_id, chapter_num, chapter_type, series_title, outdir, chapter_dir_name, sequence=False, max_sleep=120):
    chapter_dir = os.path.join(outdir, chapter_dir_name)
    os.makedirs(chapter_dir, exist_ok=True)
    url = f"https://weebcentral.com/chapters/{chapter_id}/images?is_prev=False&current_page=1&reading_style=long_strip"
    resp = scraper.get(url)
    img_urls = re.findall(r'src="([^"]+)"', resp.text)
    if not img_urls:
        print(f"No images found in chapter {chapter_num}!")
        return None
    if sequence:
        for img_url in img_urls:
            download_image(img_url, chapter_dir, url, max_sleep=max_sleep)
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=PARALLEL_DOWNLOAD) as executor:
            futures = [executor.submit(download_image, img_url, chapter_dir, url, max_sleep) for img_url in img_urls]
            for future in concurrent.futures.as_completed(futures):
                pass
    return chapter_dir

def zip_chapter_cbz(tmp_dir, base_dir, series_title, chapter_num, chapter_type):
    out_dir = os.path.join(base_dir, series_title)
    os.makedirs(out_dir, exist_ok=True)
    if not has_images(tmp_dir):
        print(f"Warning: No images found in {tmp_dir} (skipping archive)")
        shutil.rmtree(tmp_dir)
        return
    out_file = os.path.join(out_dir, f"{series_title}-{chapter_num}{('-'+chapter_type) if chapter_type else ''}.cbz")
    with zipfile.ZipFile(out_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(tmp_dir):
            for file in files:
                zf.write(os.path.join(root, file), arcname=file)
    print(f"Wrote {out_file}")
    shutil.rmtree(tmp_dir)

def zip_chapter_zip(chapter_dir, out_dir, vol_name):
    if not has_images(chapter_dir):
        print(f"Warning: No images found in {chapter_dir} (skipping archive)")
        shutil.rmtree(chapter_dir)
        return
    zip_path = os.path.join(out_dir, f"{vol_name}.zip")
    shutil.make_archive(os.path.splitext(zip_path)[0], "zip", chapter_dir)
    print(f"Created zip archive: {zip_path}")
    shutil.rmtree(chapter_dir)

def download_chapters(chapters, chapters_to_download, base_dir, series_title, zip_mode, verbose, sequence=False, rate_limit_every=10, max_sleep=120, is_fresh=True):
    out_dir = os.path.join(base_dir, series_title)
    chap_counter = 0
    for chap_type, chap_num, chap_id in reversed(chapters):
        chap_num_str = str(float(chap_num)).rstrip('0').rstrip('.') if '.' in chap_num else chap_num
        if chapters_to_download is not None and (chap_num not in chapters_to_download and chap_num_str not in chapters_to_download):
            continue
        ct = "" if chap_type in ["Chapter", "#"] else chap_type
        vol_name, chapter_dir_name = get_vol_and_chapter_names(chap_num)
        # --- skip if already exists (with any padding) ---
        if zip_mode and chapter_already_downloaded(chap_num, out_dir):
            print(f"Skipping already-downloaded chapter {chap_num} (zip found)")
            continue
        print(f"Downloading chapter {chap_num}")
        if zip_mode:
            chapter_dir = download_chapter_images(chap_id, chap_num, ct, series_title, out_dir, chapter_dir_name, sequence=sequence, max_sleep=max_sleep)
            if chapter_dir:
                zip_chapter_zip(chapter_dir, out_dir, vol_name)
        else:
            tmp_dir = tempfile.mkdtemp(prefix=f"{series_title}-{chap_num}_")
            chapter_dir = download_chapter_images(chap_id, chap_num, ct, series_title, tmp_dir, chapter_dir_name, sequence=sequence, max_sleep=max_sleep)
            if chapter_dir:
                zip_chapter_cbz(chapter_dir, base_dir, series_title, chap_num, ct)
        chap_counter += 1
        if is_fresh and chap_counter % rate_limit_every == 0:
            wait = random.randint(15, max_sleep)
            print(f"\n[INFO] Rate limiting: sleeping for {wait} seconds after {chap_counter} chapters\n")
            time.sleep(wait)

def process_manga_title(title, args, chapters_to_download=None):
    output_dir = os.path.abspath(args.output)
    if getattr(args, "series_id", None):
        series_id = args.series_id.strip()
        chapters = fetch_chapter_list(series_id)
        if not chapters:
            print(f"No chapters found for series id '{series_id}'.")
            return
        series_title = get_series_title_by_id(series_id)
        print(f"\nProcessing series id: {series_id} (title: {series_title})")
    else:
        search_title = title.replace("-", " ").strip()
        series_id, series_title = get_series_id_from_query(search_title, output_dir)
        if not series_id:
            print(f"Skipping '{title}': not found.")
            return
        chapters = fetch_chapter_list(series_id)
        if not chapters:
            print(f"No chapters found for '{title}'.")
            return

    base_dir = output_dir
    ensure_dirs(base_dir)
    out_dir = os.path.join(base_dir, series_title)
    is_fresh = not os.path.exists(out_dir) or not os.listdir(out_dir)

    if args.latest and chapters_to_download is None:
        latest = get_latest_downloaded_chapter(base_dir, series_title, zip_mode=args.zip)
        if latest is not None:
            chapters_to_download = set()
            for chap in chapters:
                try:
                    chap_float = float(chap[1])
                    if chap_float > latest:
                        chapters_to_download.add(chap[1])
                except Exception:
                    continue
            if not chapters_to_download:
                print(f"No new chapters after {latest}")
                return
            print(f"Will download chapters after {latest}: {sorted(chapters_to_download)}")
        else:
            print("No chapters found in output directory; will download ALL chapters.")
            chapters_to_download = None
    elif chapters_to_download is None and not args.latest:
        chapters_to_download = None  # download all

    vprint(f"Downloading chapters: {chapters_to_download if chapters_to_download else 'ALL'} (zip mode: {args.zip})")
    download_chapters(
        chapters,
        chapters_to_download,
        base_dir,
        series_title,
        zip_mode=args.zip,
        verbose=args.verbose,
        sequence=args.sequence,
        rate_limit_every=args.rlc,
        max_sleep=args.max_sleep,
        is_fresh=is_fresh
    )

def parse_chapter_arg(chapter_arg):
    if not chapter_arg:
        return None
    chapters = set()
    for part in chapter_arg.split(","):
        p = part.strip()
        if p:
            chapters.add(p)
    return chapters if chapters else None

def main():
    global VERBOSE
    parser = argparse.ArgumentParser(description="Manga downloader script (WeebCentral)")
    parser.add_argument('query', nargs='*', help="Manga title to search for (ignored if --bulk or --series-id is used)")
    parser.add_argument('-c', '--chapter', type=str, default=None, help="Specific chapter(s) to download, e.g. 12,12.5,13 (comma-separated)")
    parser.add_argument('-o', '--output', dest='output', default="./manga_downloads", help="Output directory for downloads")
    parser.add_argument('-l', '--latest', action='store_true', help="Download only chapters after the latest one in the output directory")
    parser.add_argument('-z', '--zip', action='store_true', help="Create zip archives for chapters (vol_NNN.zip)")
    parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose debug output")
    parser.add_argument('-b', '--bulk', type=str, help="Path to text file containing manga titles (one per line; you can use seriesid=optional-title)")
    parser.add_argument('-s', '--sequence', action='store_true', help="Download images in sequence (disable parallel downloading, useful for slow or rate-limited sites)")
    parser.add_argument('--rlc', type=int, default=10, help="How many chapters between random rate limits (default: 10)")
    parser.add_argument('--max-sleep', type=int, default=120, help="Maximum sleep time (seconds) for rate limit or error retry (default: 120)")
    parser.add_argument('-id', '--series-id', type=str, help="Direct WeebCentral series ID (bypasses search)")
    args = parser.parse_args()
    VERBOSE = args.verbose

    chapters_to_download = parse_chapter_arg(args.chapter)

    if args.bulk:
        encodings = ["utf-8", "utf-16", "latin-1", "cp1252"]
        manga_titles = None
        for encoding in encodings:
            try:
                with open(args.bulk, "r", encoding=encoding) as f:
                    manga_titles = [line.strip() for line in f if line.strip()]
                print(f"Successfully read file using {encoding} encoding")
                break
            except UnicodeDecodeError:
                continue
        if manga_titles is None:
            print("Error: Could not read file with any supported encoding")
            exit(1)
        print(f"Found {len(manga_titles)} manga titles in {args.bulk}")

        for line in manga_titles:
            if '=' in line:
                series_id = line.split('=', 1)[0].strip()
                args.series_id = series_id
                process_manga_title(series_id, args, chapters_to_download)
                args.series_id = None  # Reset for next
            else:
                args.series_id = None
                process_manga_title(line, args, chapters_to_download)
    else:
        if args.series_id:
            process_manga_title(" ".join(args.query).strip() if args.query else args.series_id, args, chapters_to_download)
        elif args.query:
            title = " ".join(args.query).strip()
            process_manga_title(title, args, chapters_to_download)
        else:
            print("No manga title specified!")
            sys.exit(1)

if __name__ == "__main__":
    VERBOSE = False
    main()
