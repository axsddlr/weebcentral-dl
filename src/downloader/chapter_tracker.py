"""Track downloaded chapters on the filesystem."""
import os
import re
from typing import Optional


class ChapterTracker:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir

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
        if "." in str(chap_num):
            dec = str(chap_num).split(".")[-1]
            if dec != "0":
                patt = re.compile(rf"vol_0*{base}-0*{dec}\.zip$")
                return any(patt.fullmatch(f) for f in os.listdir(out_dir))
        patt = re.compile(rf"vol_0*{base}\.zip$")
        return any(patt.fullmatch(f) for f in os.listdir(out_dir))
