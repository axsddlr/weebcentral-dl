#!/usr/bin/env python3
"""Compatibility wrapper for the manga utilities CLI."""

from src.manga_utils import *  # noqa: F401,F403


if __name__ == "__main__":
    from src.manga_utils import main

    main()
