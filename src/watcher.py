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
                print(f"\n[RELOAD] Config file changed, reloading...")
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
        print(f"[DONE] Finished processing. Watching for changes...")


def run_watcher():
    """Main watcher loop for Docker mode"""
    cwd = os.getcwd()
    manga_file = Path(os.getenv("MANGA_LIST", "manga_list.txt"))
    config_file = Path(os.getenv("CONFIG_FILE", "config.toml"))

    for env_name, file_path in [("MANGA_LIST", manga_file), ("CONFIG_FILE", config_file)]:
        if not file_path.is_absolute():
            try:
                resolve_safe_path(cwd, str(file_path))
            except ValueError:
                print(f"[ERROR] {env_name} path '{file_path}' escapes working directory!")
                exit(1)
        else:
            print(f"[WARNING] {env_name} is an absolute path '{file_path}'; ensure it is trusted.")

    if not manga_file.exists():
        print(f"[ERROR] {manga_file} not found!")
        exit(1)

    # Setup config watcher
    config_watcher = ConfigWatcher(config_file)

    # Setup manga list watcher
    manga_watcher = MangaListWatcher(manga_file, config_watcher.config_loader)

    # Initial processing
    print(f"[STARTUP] Processing initial list from {manga_file}")
    manga_watcher.process_file()

    # Watch for changes
    observer = Observer()

    # Watch manga list file
    observer.schedule(manga_watcher, str(manga_file.parent), recursive=False)

    # Watch config file if it exists
    if config_file.exists():
        observer.schedule(config_watcher, str(config_file.parent), recursive=False)

    observer.start()

    print(f"[WATCH] Monitoring {manga_file} and {config_file} for changes (Ctrl+C to stop)...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    run_watcher()
