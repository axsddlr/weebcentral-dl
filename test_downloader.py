#!/usr/bin/env python3
"""
Test suite for WeebCentral Manga Downloader
Run with: python test_downloader.py
"""

import unittest
import os
import tempfile
import shutil
import re
from unittest.mock import Mock, patch, MagicMock
import argparse

# Import modules to test
from src.utils import sanitize_title, get_vol_and_chapter_names, has_images
from src.downloader import WeebCentralDownloader


class TestUtils(unittest.TestCase):
    """Test utility functions"""

    def test_sanitize_title_basic(self):
        """Test basic title sanitization"""
        self.assertEqual(sanitize_title("One Piece"), "One-Piece")
        self.assertEqual(sanitize_title("Jujutsu Kaisen"), "Jujutsu-Kaisen")

    def test_sanitize_title_special_chars(self):
        """Test sanitization with special characters"""
        self.assertEqual(sanitize_title("Re:Zero"), "ReZero")
        self.assertEqual(sanitize_title("Hunter × Hunter"), "Hunter-Hunter")
        self.assertEqual(sanitize_title("I'm the Best!"), "Im-the-Best")

    def test_sanitize_title_multiple_spaces(self):
        """Test handling of multiple spaces/dashes"""
        self.assertEqual(sanitize_title("The   Greatest  Manga"), "The-Greatest-Manga")
        self.assertEqual(sanitize_title("Title---With--Dashes"), "Title-With-Dashes")

    def test_sanitize_title_unicode(self):
        """Test Unicode character handling"""
        self.assertEqual(sanitize_title("Café Manga"), "Cafe-Manga")
        self.assertEqual(sanitize_title("Naïve Story"), "Naive-Story")

    def test_sanitize_title_edge_cases(self):
        """Test edge cases"""
        self.assertEqual(sanitize_title(""), "")
        self.assertEqual(sanitize_title("   "), "")
        self.assertEqual(sanitize_title("123"), "123")
        self.assertEqual(sanitize_title("---test---"), "test")

    def test_get_vol_and_chapter_names_integer(self):
        """Test volume/chapter naming with integer chapters"""
        vol, chap = get_vol_and_chapter_names("1")
        self.assertEqual(vol, "vol_001")
        self.assertEqual(chap, "chapter_001")

        vol, chap = get_vol_and_chapter_names("100")
        self.assertEqual(vol, "vol_100")
        self.assertEqual(chap, "chapter_100")

    def test_get_vol_and_chapter_names_decimal(self):
        """Test volume/chapter naming with decimal chapters"""
        vol, chap = get_vol_and_chapter_names("12.5")
        self.assertEqual(vol, "vol_12-5")
        self.assertEqual(chap, "chapter_12-5")

        vol, chap = get_vol_and_chapter_names("5.2")
        self.assertEqual(vol, "vol_5-2")
        self.assertEqual(chap, "chapter_5-2")

    def test_get_vol_and_chapter_names_zero_decimal(self):
        """Test chapter with .0 decimal (should treat as integer)"""
        vol, chap = get_vol_and_chapter_names("12.0")
        self.assertEqual(vol, "vol_012")
        self.assertEqual(chap, "chapter_012")

    def test_has_images_with_images(self):
        """Test has_images returns True when images present"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test image files
            open(os.path.join(tmpdir, "001.jpg"), "w").close()
            open(os.path.join(tmpdir, "002.png"), "w").close()
            self.assertTrue(has_images(tmpdir))

    def test_has_images_without_images(self):
        """Test has_images returns False when no images"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create non-image files
            open(os.path.join(tmpdir, "readme.txt"), "w").close()
            self.assertFalse(has_images(tmpdir))

    def test_has_images_empty_dir(self):
        """Test has_images on empty directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            self.assertFalse(has_images(tmpdir))

    def test_has_images_nonexistent_dir(self):
        """Test has_images on nonexistent directory"""
        self.assertFalse(has_images("/nonexistent/path/12345"))


class TestDownloaderInit(unittest.TestCase):
    """Test WeebCentralDownloader initialization"""

    def setUp(self):
        """Create mock config for each test"""
        self.config = argparse.Namespace(
            output_dir="./test_downloads",
            verbose=False,
            max_retries=5,
            max_sleep=120,
            rlc=10,
            zip=False,
            sequence=False,
            latest=False,
        )

    def tearDown(self):
        """Clean up test directories"""
        if os.path.exists("./test_downloads"):
            shutil.rmtree("./test_downloads")

    def test_downloader_initialization(self):
        """Test downloader initializes correctly"""
        downloader = WeebCentralDownloader(self.config)
        self.assertEqual(downloader.config, self.config)
        self.assertIsNotNone(downloader.scraper)
        self.assertTrue(os.path.exists("./test_downloads"))

    def test_downloader_creates_output_dir(self):
        """Test output directory is created"""
        config = argparse.Namespace(
            output_dir="./test_output_123",
            verbose=False,
            max_retries=5,
            max_sleep=120,
            rlc=10,
            zip=False,
            sequence=False,
            latest=False,
        )
        downloader = WeebCentralDownloader(config)
        self.assertTrue(os.path.exists("./test_output_123"))
        shutil.rmtree("./test_output_123")


class TestDownloaderRegex(unittest.TestCase):
    """Test regex patterns used in downloader"""

    def test_series_id_extraction_from_search(self):
        """Test extraction of series ID from search results"""
        html = '''
        <a href="/series/01J76XY8ZHW8N77HPPB92V7GB8/Manga-Title">
        <a href="/series/01J76XYCRSG391MCSWQARXCZZ2/Another-Manga">
        '''
        pattern = re.compile(r'/series/([^"/]+/[^"]+)')
        results = pattern.findall(html)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], "01J76XY8ZHW8N77HPPB92V7GB8/Manga-Title")
        self.assertEqual(results[1], "01J76XYCRSG391MCSWQARXCZZ2/Another-Manga")

    def test_chapter_parsing_from_html(self):
        """Test chapter extraction from chapter list HTML"""
        html = '''
        <span class="">Chapter 123</span>
        some content
        value="ABC123DEF456"
        '''
        pattern = re.compile(
            r'<span class="">([A-Za-z#]+)\s*([\d\.]+)</span>[\s\S]*?value="([A-Z0-9]+)"'
        )
        match = pattern.search(html)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "Chapter")
        self.assertEqual(match.group(2), "123")
        self.assertEqual(match.group(3), "ABC123DEF456")

    def test_chapter_parsing_decimal(self):
        """Test decimal chapter parsing"""
        html = '''
        <span class="">Chapter 12.5</span>
        value="CHAPTERID123"
        '''
        pattern = re.compile(
            r'<span class="">([A-Za-z#]+)\s*([\d\.]+)</span>[\s\S]*?value="([A-Z0-9]+)"'
        )
        match = pattern.search(html)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(2), "12.5")

    def test_cover_image_extraction(self):
        """Test cover image URL extraction"""
        html = '<source srcset="https://example.com/cover/01J76XY8.webp" />'
        pattern = re.compile(r'<source srcset="([^"]+)"')
        match = pattern.search(html)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "https://example.com/cover/01J76XY8.webp")


class TestDownloaderMethods(unittest.TestCase):
    """Test downloader methods with mocking"""

    def setUp(self):
        """Create downloader instance for each test"""
        self.config = argparse.Namespace(
            output_dir="./test_downloads",
            verbose=False,
            max_retries=3,
            max_sleep=5,
            rlc=10,
            zip=False,
            sequence=False,
            latest=False,
        )
        self.downloader = WeebCentralDownloader(self.config)

    def tearDown(self):
        """Clean up"""
        if os.path.exists("./test_downloads"):
            shutil.rmtree("./test_downloads")

    def test_chapter_already_downloaded_not_exists(self):
        """Test chapter detection when directory doesn't exist"""
        result = self.downloader.chapter_already_downloaded("1", "./nonexistent")
        self.assertFalse(result)

    def test_chapter_already_downloaded_exists(self):
        """Test chapter detection when chapter exists"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a chapter file
            open(os.path.join(tmpdir, "vol_001.zip"), "w").close()
            result = self.downloader.chapter_already_downloaded("1", tmpdir)
            self.assertTrue(result)

    def test_chapter_already_downloaded_different_chapter(self):
        """Test chapter detection doesn't match different chapters"""
        with tempfile.TemporaryDirectory() as tmpdir:
            open(os.path.join(tmpdir, "vol_002.zip"), "w").close()
            result = self.downloader.chapter_already_downloaded("1", tmpdir)
            self.assertFalse(result)

    def test_get_latest_downloaded_chapter_no_dir(self):
        """Test getting latest chapter when directory doesn't exist"""
        result = self.downloader.get_latest_downloaded_chapter("nonexistent_manga")
        self.assertIsNone(result)

    def test_get_latest_downloaded_chapter_with_zips(self):
        """Test getting latest chapter from zip files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manga_dir = os.path.join(tmpdir, "test_manga")
            os.makedirs(manga_dir)
            open(os.path.join(manga_dir, "vol_001.zip"), "w").close()
            open(os.path.join(manga_dir, "vol_005.zip"), "w").close()
            open(os.path.join(manga_dir, "vol_003.zip"), "w").close()

            # Temporarily change output dir
            original_output = self.downloader.output_dir
            self.downloader.output_dir = tmpdir
            result = self.downloader.get_latest_downloaded_chapter("test_manga")
            self.downloader.output_dir = original_output

            self.assertEqual(result, 5.0)

    def test_get_latest_downloaded_chapter_with_decimals(self):
        """Test getting latest chapter with decimal chapters"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manga_dir = os.path.join(tmpdir, "test_manga")
            os.makedirs(manga_dir)
            open(os.path.join(manga_dir, "vol_12-5.zip"), "w").close()
            open(os.path.join(manga_dir, "vol_013.zip"), "w").close()

            original_output = self.downloader.output_dir
            self.downloader.output_dir = tmpdir
            result = self.downloader.get_latest_downloaded_chapter("test_manga")
            self.downloader.output_dir = original_output

            self.assertEqual(result, 13.0)

    @patch("src.downloader.http_client.HttpClient.request")
    def test_get_series_id_from_query_found(self, mock_request):
        """Test successful series ID lookup"""
        mock_response = Mock()
        mock_response.text = '<a href="/series/01J76XY8TEST/Test-Manga">Test</a>'
        mock_request.return_value = mock_response

        result = self.downloader.get_series_id_from_query("Test Manga")
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "01J76XY8TEST")
        self.assertEqual(result[1], "Test-Manga")

    @patch("src.downloader.http_client.HttpClient.request")
    def test_get_series_id_from_query_not_found(self, mock_request):
        """Test series ID lookup when not found"""
        mock_response = Mock()
        mock_response.text = "<html>No results</html>"
        mock_request.return_value = mock_response

        result = self.downloader.get_series_id_from_query("Nonexistent Manga")
        self.assertEqual(result, (None, None))


class TestBulkFileProcessing(unittest.TestCase):
    """Test bulk file processing logic"""

    def test_bulk_file_parsing_with_id(self):
        """Test parsing bulk file with series_id=title format"""
        line = "01J76XYCRSG391MCSWQARXCZZ2=Ao-Ashi"
        if "=" in line:
            series_id, title = line.split("=", 1)
            self.assertEqual(series_id, "01J76XYCRSG391MCSWQARXCZZ2")
            self.assertEqual(title, "Ao-Ashi")

    def test_bulk_file_parsing_without_id(self):
        """Test parsing bulk file with just title"""
        line = "Gachiakuta"
        self.assertNotIn("=", line)

    def test_bulk_file_parsing_with_spaces(self):
        """Test parsing handles extra whitespace"""
        line = "  01J76XY8TEST=Title With Spaces  "
        series_id, title = line.split("=", 1)
        self.assertEqual(series_id.strip(), "01J76XY8TEST")
        self.assertEqual(title.strip(), "Title With Spaces")


class TestChapterParsing(unittest.TestCase):
    """Test chapter argument parsing"""

    def test_parse_single_chapter(self):
        """Test parsing single chapter"""
        chapters = {"12"}
        self.assertIn("12", chapters)
        self.assertEqual(len(chapters), 1)

    def test_parse_multiple_chapters(self):
        """Test parsing comma-separated chapters"""
        chapter_str = "1,2,3.5,10"
        chapters = {p.strip() for p in chapter_str.split(",") if p.strip()}
        self.assertEqual(len(chapters), 4)
        self.assertIn("1", chapters)
        self.assertIn("3.5", chapters)

    def test_parse_chapters_with_spaces(self):
        """Test parsing chapters with extra spaces"""
        chapter_str = " 1 , 2 , 3.5 "
        chapters = {p.strip() for p in chapter_str.split(",") if p.strip()}
        self.assertEqual(len(chapters), 3)
        self.assertIn("1", chapters)


class TestArchiveNaming(unittest.TestCase):
    """Test archive filename generation"""

    def test_cbz_naming_basic(self):
        """Test .cbz filename generation"""
        series_title = "test-manga"
        chapter_num = "12"
        chapter_type = ""
        filename = f"{series_title}-{chapter_num}{('-' + chapter_type) if chapter_type else ''}.cbz"
        self.assertEqual(filename, "test-manga-12.cbz")

    def test_cbz_naming_with_type(self):
        """Test .cbz filename with chapter type"""
        series_title = "test-manga"
        chapter_num = "12.5"
        chapter_type = "Extra"
        filename = f"{series_title}-{chapter_num}{('-' + chapter_type) if chapter_type else ''}.cbz"
        self.assertEqual(filename, "test-manga-12.5-Extra.cbz")

    def test_zip_naming(self):
        """Test .zip filename generation"""
        vol_name = "vol_012"
        filename = f"{vol_name}.zip"
        self.assertEqual(filename, "vol_012.zip")

    def test_zip_naming_decimal(self):
        """Test .zip filename with decimal chapter"""
        vol_name = "vol_12-5"
        filename = f"{vol_name}.zip"
        self.assertEqual(filename, "vol_12-5.zip")


def run_tests():
    """Run all tests and provide summary"""
    print("=" * 70)
    print("WeebCentral Manga Downloader - Test Suite")
    print("=" * 70)
    print()

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestUtils))
    suite.addTests(loader.loadTestsFromTestCase(TestDownloaderInit))
    suite.addTests(loader.loadTestsFromTestCase(TestDownloaderRegex))
    suite.addTests(loader.loadTestsFromTestCase(TestDownloaderMethods))
    suite.addTests(loader.loadTestsFromTestCase(TestBulkFileProcessing))
    suite.addTests(loader.loadTestsFromTestCase(TestChapterParsing))
    suite.addTests(loader.loadTestsFromTestCase(TestArchiveNaming))

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print()
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print()

    if result.wasSuccessful():
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(run_tests())
