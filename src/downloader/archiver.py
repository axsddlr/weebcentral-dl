"""Create zip/cbz archives from downloaded chapter images."""
import os
import shutil
import zipfile
from src.utils import get_vol_and_chapter_names, has_images
from src.downloader.cover_manager import CoverManager
from src.logging_utils import logger


class Archiver:
    def __init__(self, cover_manager: CoverManager, output_dir: str, use_zip: bool = False):
        self.cover_manager = cover_manager
        self.output_dir = output_dir
        self.use_zip = use_zip

    def archive_chapter(
        self,
        chapter_dir: str,
        series_title: str,
        chapter_num: str,
        chapter_type: str,
        comicinfo_xml: str | None = None,
    ):
        out_dir = os.path.join(self.output_dir, series_title)
        os.makedirs(out_dir, exist_ok=True)

        if not has_images(chapter_dir):
            logger.warning(f"No images found in {chapter_dir} (skipping archive)")
            shutil.rmtree(chapter_dir)
            return

        image_files = self._collect_images(chapter_dir)
        if self.use_zip:
            self._create_zip(out_dir, chapter_num, series_title, image_files, comicinfo_xml)
        else:
            self._create_cbz(out_dir, chapter_num, chapter_type, series_title, image_files, comicinfo_xml)

        shutil.rmtree(chapter_dir)

    @staticmethod
    def _collect_images(chapter_dir: str) -> list:
        image_files = []
        for f in sorted(os.listdir(chapter_dir)):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif')):
                image_files.append(os.path.join(chapter_dir, f))
        return image_files

    def _write_archive_with_cover(self, zf: zipfile.ZipFile, image_files: list, series_title: str, comicinfo_xml: str | None):
        cover_path = self.cover_manager.get_cover_image_path(series_title)
        if cover_path and os.path.exists(cover_path):
            ext = os.path.splitext(cover_path)[1]
            zf.write(cover_path, arcname=f"000-cover{ext}")
        if comicinfo_xml:
            zf.writestr("ComicInfo.xml", comicinfo_xml)
        for img_file in image_files:
            zf.write(img_file, arcname=os.path.basename(img_file))

    def _create_zip(self, out_dir: str, chapter_num: str, series_title: str, image_files: list, comicinfo_xml: str | None):
        vol_name, _ = get_vol_and_chapter_names(chapter_num)
        zip_path = os.path.join(out_dir, f"{vol_name}.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            self._write_archive_with_cover(zf, image_files, series_title, comicinfo_xml)
        logger.info(f"Created zip archive: {zip_path}")

    def _create_cbz(self, out_dir: str, chapter_num: str, chapter_type: str,
                    series_title: str, image_files: list, comicinfo_xml: str | None):
        out_file = os.path.join(
            out_dir,
            f"{series_title}-{chapter_num}{('-' + chapter_type) if chapter_type else ''}.cbz",
        )
        with zipfile.ZipFile(out_file, "w", zipfile.ZIP_DEFLATED) as zf:
            self._write_archive_with_cover(zf, image_files, series_title, comicinfo_xml)
        logger.info(f"Wrote {out_file}")
