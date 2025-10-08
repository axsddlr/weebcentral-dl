#!/usr/bin/env python3
"""
WeebCentral Manga Downloader - Main Entry Point

This script automatically detects the run mode:
- CLI Mode: When run directly (python main.py ...)
- Docker Mode: When DOCKER_MODE env var is set (uses file watcher)
"""
import os
import sys


def main():
    """Main entry point - routes to CLI or Docker mode"""
    if os.getenv("DOCKER_MODE"):
        # Docker mode: run file watcher
        from src.watcher import run_watcher
        run_watcher()
    else:
        # CLI mode: run normal CLI interface
        from src.cli import main as cli_main
        cli_main()


if __name__ == "__main__":
    main()
