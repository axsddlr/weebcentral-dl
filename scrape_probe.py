"""Repeatable probe for the WeebCentral scraping path.

Measures, per operation, whether the REAL production code path succeeds,
how long it takes, how many browser sessions it creates, and whether the
result is identical across iterations.

Usage (from the repo root):
    uv run python scrape_probe.py --mode read --iterations 3
    uv run python scrape_probe.py --mode images --iterations 2
    uv run python scrape_probe.py --mode chapter --workers 4
    uv run python scrape_probe.py --mode sessions --workers 4
    uv run python scrape_probe.py --mode all --iterations 3 --json out.json

It is read-only against the network and writes only into its temp dir.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import threading
import time
import traceback

REPO = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO)

from src.config import DownloaderConfig                       # noqa: E402
from src.downloader import WeebCentralDownloader              # noqa: E402
from src.downloader.chapter_fetcher import ChapterFetcher     # noqa: E402
from src.downloader.http_client import HttpClient, WEEBCENTRAL_URL  # noqa: E402
from src.downloader.image_downloader import ImageDownloader   # noqa: E402
from src.downloader.metadata import MetadataExtractor         # noqa: E402
from src.utils import get_vol_and_chapter_names               # noqa: E402

IMAGE_MAGIC = {b"\xff\xd8\xff": "jpeg", b"\x89PNG": "png", b"RIFF": "webp", b"GIF8": "gif"}

# --- session instrumentation -------------------------------------------------
_SESSION_LOCK = threading.Lock()
_SESSIONS = {"created": 0, "threads": set()}
_ORIG_GET_SESSION = HttpClient._get_session


def _counting_get_session(self):
    ident = threading.get_ident()
    had = getattr(self._local, "session", None) is not None
    session = _ORIG_GET_SESSION(self)
    if not had:
        with _SESSION_LOCK:
            _SESSIONS["created"] += 1
            _SESSIONS["threads"].add(ident)
    return session


HttpClient._get_session = _counting_get_session


def reset_sessions():
    with _SESSION_LOCK:
        _SESSIONS["created"] = 0
        _SESSIONS["threads"] = set()


def session_stats():
    with _SESSION_LOCK:
        return {"sessions_created": _SESSIONS["created"], "threads_used": len(_SESSIONS["threads"])}


def magic_of(data: bytes) -> str:
    for sig, name in IMAGE_MAGIC.items():
        if data.startswith(sig):
            return name
    return f"UNKNOWN({data[:6]!r})"


class Probe:
    def __init__(self, series_id: str, workdir: str):
        self.series_id = series_id
        self.workdir = workdir
        self.tmp = tempfile.mkdtemp(prefix="scrape_probe_")
        config = DownloaderConfig(output_dir=self.tmp, zip=False, verbose=False)
        self.downloader = WeebCentralDownloader(config)
        self.http = self.downloader.http
        self.chapter_fetcher = ChapterFetcher(self.http)
        self.metadata = MetadataExtractor(self.http)

    # -- helpers ----------------------------------------------------------
    def _op(self, name, fn):
        reset_sessions()
        start = time.perf_counter()
        rec = {"op": name}
        try:
            detail = fn()
            rec["ok"] = True
            rec["detail"] = detail
        except Exception as exc:  # noqa: BLE001
            rec["ok"] = False
            rec["error"] = f"{type(exc).__name__}: {exc}"[:400]
            rec["traceback_tail"] = traceback.format_exc().strip().splitlines()[-1][:300]
        rec["ms"] = round((time.perf_counter() - start) * 1000)
        rec.update(session_stats())
        return rec

    def _chapters(self):
        chapters = self.chapter_fetcher.fetch_chapter_list(self.series_id)
        return list(chapters), []

    # -- operations -------------------------------------------------------
    def op_series_page(self):
        def fn():
            resp = self.http.request("GET", f"{WEEBCENTRAL_URL}/series/{self.series_id}")
            html = resp.text
            return {
                "status": resp.status_code,
                "bytes": len(html),
                "has_h1": "<h1" in html,
                "has_chapter_list": "full-chapter-list" in html or "chapter" in html.lower(),
                "title_guess": html.split("<h1")[1].split(">")[1].split("<")[0].strip()[:80]
                if "<h1" in html else None,
            }
        return self._op("series_page", fn)

    def op_chapter_list(self):
        def fn():
            chapters = self.chapter_fetcher.fetch_chapter_list(self.series_id)
            return {
                "count": len(chapters),
                "first": chapters[0] if chapters else None,
                "last": chapters[-1] if chapters else None,
            }
        return self._op("chapter_list", fn)

    def op_metadata(self):
        def fn():
            md = self.metadata.get_series_metadata(self.series_id)
            return {
                "title": md.get("title"),
                "authors": md.get("authors"),
                "tags_count": len(md.get("tags") or []),
                "coverUrl": (md.get("coverUrl") or "")[:100],
            }
        return self._op("metadata", fn)

    def op_image_list(self, chapter_id, chapter_num):
        def fn():
            url = (f"{WEEBCENTRAL_URL}/chapters/{chapter_id}/images"
                   "?is_prev=False&current_page=1&reading_style=long_strip")
            resp = self.http.request("GET", url, headers={"HX-Request": "true"})
            json_ok, json_count = False, 0
            try:
                data = resp.json()
                json_ok = isinstance(data, dict)
                json_count = len(data.get("images", [])) if json_ok else 0
            except Exception:  # noqa: BLE001
                pass
            urls = ImageDownloader._extract_image_urls(resp)
            if not urls:
                raise RuntimeError("no image urls extracted")
            if all("broken_image" in u for u in urls):
                raise RuntimeError(f"only placeholder urls: {urls[:2]}")
            return {
                "chapter_num": chapter_num,
                "json_body_is_dict": json_ok,
                "json_images": json_count,
                "extracted": len(urls),
                "first_url": (urls[0][:120] if urls else None),
                "html_len": len(resp.text),
            }
        return self._op("image_list", fn)

    def op_download_images(self, img_urls, referer, n=3):
        def fn():
            dl = ImageDownloader(self.http, max_retries=2, max_sleep=20, parallel_workers=1, sequence=True)
            results = []
            for url in img_urls[:n]:
                path = dl.download_image(url, self.tmp, referer)
                if not path or not os.path.exists(path):
                    results.append({"url": url[:80], "ok": False})
                    continue
                with open(path, "rb") as fh:
                    head = fh.read(16)
                results.append({
                    "url": url[:80],
                    "ok": True,
                    "bytes": os.path.getsize(path),
                    "magic": magic_of(head),
                })
            succeeded = sum(1 for r in results if r.get("ok"))
            if results and succeeded == 0:
                raise RuntimeError(f"all {len(results)} image downloads failed: {results[0]}")
            return {"attempted": len(results), "succeeded": succeeded, "results": results}
        return self._op("download_images", fn)

    def op_full_chapter(self, chapter_id, chapter_num, workers):
        def fn():
            vol_name, chapter_dir_name = get_vol_and_chapter_names(chapter_num)
            dl = ImageDownloader(self.http, max_retries=2, max_sleep=20,
                                 parallel_workers=workers, sequence=(workers == 1))
            outdir = os.path.join(self.tmp, "chapter_probe")
            os.makedirs(outdir, exist_ok=True)
            chapter_dir = dl.download_chapter_images(chapter_id, chapter_num, outdir, chapter_dir_name)
            if not chapter_dir:
                return {"returned_none": True, "workers": workers, "vol_name": vol_name}
            files = [f for f in os.listdir(chapter_dir)]
            good = 0
            for f in files:
                with open(os.path.join(chapter_dir, f), "rb") as fh:
                    if not magic_of(fh.read(16)).startswith("UNKNOWN"):
                        good += 1
            return {
                "workers": workers,
                "vol_name": vol_name,
                "files": len(files),
                "valid_images": good,
                "dir": chapter_dir,
            }
        return self._op("full_chapter", fn)

    def op_sessions(self, workers):
        def fn():
            errors = []

            def one(_i):
                try:
                    self.http.request("GET", f"{WEEBCENTRAL_URL}/series/{self.series_id}")
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{type(exc).__name__}: {exc}"[:200])

            threads = [threading.Thread(target=one, args=(i,)) for i in range(workers)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            return {"workers": workers, "errors": errors[:3], "error_count": len(errors)}
        return self._op("sessions", fn)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--series-id", default="01J76XYCPSY3C4BNPBRY8JMCBE")
    ap.add_argument("--mode", default="read",
                    choices=["read", "images", "chapter", "sessions", "all"])
    ap.add_argument("--iterations", type=int, default=1)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--json", dest="json_path", default=None)
    args = ap.parse_args()

    print(f"[probe] mode={args.mode} iterations={args.iterations} workers={args.workers} "
          f"series={args.series_id}", flush=True)
    probe = Probe(args.series_id, os.getcwd())
    report = {"series_id": args.series_id, "mode": args.mode, "iterations": []}

    for i in range(1, args.iterations + 1):
        print(f"\n[probe] ---- iteration {i}/{args.iterations} ----", flush=True)
        ops = []
        if args.mode in ("read", "all"):
            ops.append(probe.op_series_page())
            rec = probe.op_chapter_list()
            ops.append(rec)
            ops.append(probe.op_metadata())
        if args.mode in ("read", "images", "chapter", "all"):
            chapters = probe.chapter_fetcher.fetch_chapter_list(args.series_id) or []
        if args.mode in ("images", "all") and chapters:
            ct, cnum, cid = chapters[0]
            ops.append(probe.op_image_list(cid, cnum))
            resp = probe.http.request(
                "GET",
                f"{WEEBCENTRAL_URL}/chapters/{cid}/images?is_prev=False&current_page=1&reading_style=long_strip",
                headers={"HX-Request": "true"},
            )
            urls = ImageDownloader._extract_image_urls(resp)
            if urls:
                ops.append(probe.op_download_images(
                    urls,
                    f"{WEEBCENTRAL_URL}/chapters/{cid}/images?is_prev=False&current_page=1&reading_style=long_strip",
                ))
        if args.mode == "chapter" and chapters:
            ct, cnum, cid = chapters[0]
            ops.append(probe.op_full_chapter(cid, cnum, args.workers))
        if args.mode == "sessions":
            ops.append(probe.op_sessions(args.workers))

        for rec in ops:
            flag = "OK " if rec.get("ok") else "FAIL"
            extra = rec.get("detail") if rec.get("ok") else rec.get("error")
            print(f"[probe] {flag} {rec['op']:<16} {rec['ms']:>7}ms  "
                  f"sessions={rec.get('sessions_created')} threads={rec.get('threads_used')}  {extra}",
                  flush=True)
        report["iterations"].append(ops)

    summary = {}
    for ops in report["iterations"]:
        for rec in ops:
            key = rec["op"]
            s = summary.setdefault(key, {"runs": 0, "ok": 0, "ms": [], "details": []})
            s["runs"] += 1
            s["ok"] += 1 if rec.get("ok") else 0
            s["ms"].append(rec["ms"])
            if rec.get("ok"):
                s["details"].append(rec.get("detail"))
    print("\n[probe] ================= SUMMARY =================", flush=True)
    for key, s in summary.items():
        counts = [d.get("count") or d.get("extracted") or d.get("files")
                  for d in s["details"] if isinstance(d, dict)]
        counts = [c for c in counts if c is not None]
        consistent = (len(set(counts)) == 1) if counts else None
        print(f"[probe] {key:<16} ok={s['ok']}/{s['runs']}  "
              f"ms(min/med/max)={min(s['ms'])}/{sorted(s['ms'])[len(s['ms']) // 2]}/{max(s['ms'])}  "
              f"counts={counts}  identical={consistent}", flush=True)
    report["summary"] = {
        k: {"runs": v["runs"], "ok": v["ok"], "ms": v["ms"]} for k, v in summary.items()
    }
    if args.json_path:
        with open(args.json_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, default=str)
        print(f"[probe] json written to {args.json_path}", flush=True)
    any_fail = any(not rec.get("ok") for ops in report["iterations"] for rec in ops)
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())
