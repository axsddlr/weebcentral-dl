"""Shared logger import with a stdlib fallback."""

from __future__ import annotations

import logging
import sys

try:
    from loguru import logger as logger  # type: ignore
except ImportError:

    class _FallbackLogger:
        def __init__(self) -> None:
            self._logger = logging.getLogger("weebcentral-dl")
            self._logger.setLevel(logging.INFO)
            self._logger.propagate = False

        def remove(self) -> None:
            for handler in list(self._logger.handlers):
                self._logger.removeHandler(handler)

        def add(self, sink, level="INFO", format=None, colorize=None):
            handler = logging.StreamHandler(sink if hasattr(sink, "write") else sys.stderr)
            handler.setLevel(getattr(logging, str(level).upper(), logging.INFO))
            handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(handler)
            self._logger.setLevel(getattr(logging, str(level).upper(), logging.INFO))
            return handler

        def debug(self, msg, *args, **kwargs):
            self._logger.debug(msg, *args, **kwargs)

        def info(self, msg, *args, **kwargs):
            self._logger.info(msg, *args, **kwargs)

        def warning(self, msg, *args, **kwargs):
            self._logger.warning(msg, *args, **kwargs)

        def error(self, msg, *args, **kwargs):
            self._logger.error(msg, *args, **kwargs)

        def success(self, msg, *args, **kwargs):
            self._logger.info(msg, *args, **kwargs)

    logger = _FallbackLogger()
