import time
import subprocess
import os
import tomli
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ConfigHandler(FileSystemEventHandler):
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = self.load_config()
        self.last_modified = os.path.getmtime(config_path) if os.path.exists(config_path) else 0

    def load_config(self):
        """Load configuration from TOML file"""
        if not os.path.exists(self.config_path):
            print(f"[WARN] Config file {self.config_path} not found, using defaults")
            return {}

        try:
            with open(self.config_path, 'rb') as f:
                config = tomli.load(f)
                print(f"[CONFIG] Loaded configuration from {self.config_path}")
                return config.get('downloader', {})
        except Exception as e:
            print(f"[ERROR] Failed to load config: {e}")
            return {}

    def on_modified(self, event):
        if event.src_path == str(self.config_path):
            current_mtime = os.path.getmtime(self.config_path)
            if current_mtime > self.last_modified:
                self.last_modified = current_mtime
                print(f"\n[RELOAD] Config file changed, reloading...")
                self.config = self.load_config()

class MangaListHandler(FileSystemEventHandler):
    def __init__(self, filepath, config_handler):
        self.filepath = filepath
        self.config_handler = config_handler
        self.last_modified = os.path.getmtime(filepath) if os.path.exists(filepath) else 0

    def on_modified(self, event):
        if event.src_path == str(self.filepath):
            current_mtime = os.path.getmtime(self.filepath)
            if current_mtime > self.last_modified:
                self.last_modified = current_mtime
                print(f"\n[RELOAD] Detected changes in {self.filepath}")
                self.process_file()

    def build_command(self):
        """Build command with config options"""
        config = self.config_handler.config
        cmd = ["python", "main.py", "-b", str(self.filepath)]

        # Add CLI arguments from config
        if config.get('latest', False):
            cmd.append('-l')

        if config.get('sequence', False):
            cmd.append('-s')

        if config.get('zip', False):
            cmd.append('-z')

        if config.get('verbose', False):
            cmd.append('-v')

        if config.get('use_english_title', False):
            cmd.append('--en')

        # Integer/string arguments
        if 'rlc' in config:
            cmd.extend(['--rlc', str(config['rlc'])])

        if 'max_sleep' in config:
            cmd.extend(['--max-sleep', str(config['max_sleep'])])

        if 'max_retries' in config:
            cmd.extend(['--max-retries', str(config['max_retries'])])

        return cmd

    def process_file(self):
        cmd = self.build_command()
        print(f"[DOWNLOAD] Running: {' '.join(cmd)}")
        subprocess.run(cmd)
        print(f"[DONE] Finished processing. Watching for changes...")

if __name__ == "__main__":
    manga_file = Path(os.getenv("MANGA_LIST", "manga_list.txt"))
    config_file = Path(os.getenv("CONFIG_FILE", "config.toml"))

    if not manga_file.exists():
        print(f"[ERROR] {manga_file} not found!")
        exit(1)

    # Setup config handler
    config_handler = ConfigHandler(config_file)

    # Setup manga list handler
    manga_handler = MangaListHandler(manga_file, config_handler)

    # Initial processing
    print(f"[STARTUP] Processing initial list from {manga_file}")
    manga_handler.process_file()

    # Watch for changes
    observer = Observer()

    # Watch manga list file
    observer.schedule(manga_handler, str(manga_file.parent), recursive=False)

    # Watch config file if it exists
    if config_file.exists():
        observer.schedule(config_handler, str(config_file.parent), recursive=False)

    observer.start()

    print(f"[WATCH] Monitoring {manga_file} and {config_file} for changes (Ctrl+C to stop)...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
