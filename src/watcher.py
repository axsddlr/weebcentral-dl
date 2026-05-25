"""File watcher for Docker mode with hot reload support"""
import time
import sys
import subprocess
import os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from src.config import ConfigLoader
from src.utils import resolve_safe_path


class ConfigWatcher(FileSystemEventHandler):
    """Watch config.toml for changes"""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config_loader = ConfigLoader(str(config_path))
        self.last_modified = os.path.getmtime(config_path) if config_path.exists() else 0

    def on_modified(self, event):
        if event.src_path == str(self.config_path):
            current_mtime = os.path.getmtime(self.config_path)
            if current_mtime > self.last_modified:
                self.last_modified = current_mtime
                print("\n[RELOAD] Config file changed, reloading...")
                self.config_loader.reload()


class MangaListWatcher(FileSystemEventHandler):
    """Watch manga list file for changes and trigger downloads"""

    def __init__(self, filepath: Path, config_loader: ConfigLoader):
        self.filepath = filepath
        self.config_loader = config_loader
        self.last_modified = os.path.getmtime(filepath) if filepath.exists() else 0

    def on_modified(self, event):
        if event.src_path == str(self.filepath):
            current_mtime = os.path.getmtime(self.filepath)
            if current_mtime > self.last_modified:
                self.last_modified = current_mtime
                print(f"\n[RELOAD] Detected changes in {self.filepath}")
                self.process_file()

    def build_command(self) -> list:
        """Build python command with config options"""
        config = self.config_loader.get_downloader_config()
        cmd = [sys.executable, "-m", "src.cli", "-b", str(self.filepath)]

        # Add CLI arguments from config
        if config.latest:
            cmd.append('-l')

        if config.sequence:
            cmd.append('-s')

        if config.zip:
            cmd.append('-z')

        if config.verbose:
            cmd.append('-v')

        if config.use_english_title:
            cmd.append('--en')

        # Integer/string arguments
        if config.rlc != 10:
            cmd.extend(['--rlc', str(config.rlc)])

        if config.max_sleep != 120:
            cmd.extend(['--max-sleep', str(config.max_sleep)])

        if config.max_retries != 5:
            cmd.extend(['--max-retries', str(config.max_retries)])

        if config.parallel_workers != 99:
            cmd.extend(['--parallel-workers', str(config.parallel_workers)])

        if config.output_dir != "./manga_downloads":
            cmd.extend(['-o', config.output_dir])

        return cmd

    def build_tracked_command(self) -> list:
        """Build python command for tracked DB mode (--tracked)."""
        cmd = [sys.executable, "-m", "src.cli", "--tracked"]
        config = self.config_loader.get_downloader_config()
        if config.latest:
            cmd.append('-l')
        if config.sequence:
            cmd.append('-s')
        if config.zip:
            cmd.append('-z')
        if config.verbose:
            cmd.append('-v')
        if config.use_english_title:
            cmd.append('--en')
        if config.rlc != 10:
            cmd.extend(['--rlc', str(config.rlc)])
        if config.max_sleep != 120:
            cmd.extend(['--max-sleep', str(config.max_sleep)])
        if config.max_retries != 5:
            cmd.extend(['--max-retries', str(config.max_retries)])
        if config.parallel_workers != 99:
            cmd.extend(['--parallel-workers', str(config.parallel_workers)])
        if config.output_dir != "./manga_downloads":
            cmd.extend(['-o', config.output_dir])
        return cmd

    def process_tracked(self):
        """Download latest for all tracked manga from DB."""
        cmd = self.build_tracked_command()
        print(f"[DOWNLOAD] Running: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, timeout=3600, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"[ERROR] Download process exited with code {result.returncode}")
                if result.stderr:
                    print(f"[ERROR stderr] {result.stderr[:500]}")
        except subprocess.TimeoutExpired:
            print("[ERROR] Download process timed out after 1 hour")
        print("[DONE] Finished processing. Watching for changes...")

    def process_file(self):
        """Process manga list file with current config"""
        cmd = self.build_command()
        print(f"[DOWNLOAD] Running: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, timeout=3600, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"[ERROR] Download process exited with code {result.returncode}")
                if result.stderr:
                    print(f"[ERROR stderr] {result.stderr[:500]}")
        except subprocess.TimeoutExpired:
            print("[ERROR] Download process timed out after 1 hour")
        print("[DONE] Finished processing. Watching for changes...")


def run_watcher():
    """Main watcher loop for Docker mode"""
    cwd = os.getcwd()
    use_tracked = os.getenv("WATCH_TRACKED", "").lower() in ("1", "true", "yes")
    manga_file = Path(os.getenv("MANGA_LIST", "manga_list.txt"))
    config_file = Path(os.getenv("CONFIG_FILE", "config.toml"))

    for env_name, file_path in [("CONFIG_FILE", config_file)]:
        if not file_path.is_absolute():
            try:
                resolve_safe_path(cwd, str(file_path))
            except ValueError:
                print(f"[ERROR] {env_name} path '{file_path}' escapes working directory!")
                exit(1)

    config_watcher = ConfigWatcher(config_file)
    manga_watcher = MangaListWatcher(manga_file, config_watcher.config_loader)

    config = config_watcher.config_loader.get_downloader_config()
    check_interval = config.check_interval

    if use_tracked:
        print("[STARTUP] Tracked DB mode — processing all tracked manga")
        manga_watcher.process_tracked()
    else:
        if not os.getenv("MANGA_LIST") and not manga_file.exists():
            print(f"[ERROR] {manga_file} not found! Set MANGA_LIST env or create the file.")
            exit(1)
        print(f"[STARTUP] Processing initial list from {manga_file}")
        manga_watcher.process_file()

    observer = Observer()
    observer.schedule(manga_watcher, str(manga_file.parent), recursive=False)
    if config_file.exists():
        observer.schedule(config_watcher, str(config_file.parent), recursive=False)

    observer.start()

    if use_tracked and check_interval > 0:
        print(f"[WATCH] Auto-checking tracked manga every {check_interval} minutes")
        next_check = time.time() + check_interval * 60
        try:
            while True:
                time.sleep(1)
                if time.time() >= next_check:
                    print(f"\n[CHECK] Auto-check interval reached — re-checking tracked manga")
                    manga_watcher.process_tracked()
                    next_check = time.time() + check_interval * 60
        except KeyboardInterrupt:
            observer.stop()
    else:
        print(f"[WATCH] Monitoring {manga_file} and {config_file} for changes (Ctrl+C to stop)...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
    observer.join()


if __name__ == "__main__":
    run_watcher()
