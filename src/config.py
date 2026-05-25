"""Configuration management for WeebCentral Downloader"""
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict, field
from src.logging_utils import logger

try:
    import tomllib as tomli
except ImportError:  # pragma: no cover - Python < 3.11 fallback
    import tomli


@dataclass
class DownloaderConfig:
    """Configuration for downloader behavior"""
    # Download options
    latest: bool = False
    sequence: bool = False
    zip: bool = True
    verbose: bool = False
    use_english_title: bool = False
    comicinfo: bool = False

    # Rate limiting & retries
    rlc: int = 10
    max_sleep: int = 120
    max_retries: int = 5

    # Parallel download settings
    # Default: 99 workers (empirically determined as optimal for WeebCentral)
    # Reasoning: High worker count maximizes throughput for image downloads
    # where network latency dominates over CPU/memory usage. WeebCentral's
    # CDN handles high concurrency well. Reduce if experiencing connection
    # issues or rate limiting. Set to 1 for sequential downloads (same as --sequence).
    parallel_workers: int = 99

    # Paths
    output_dir: str = "./manga_downloads"
    library_paths: List[str] = field(default_factory=list)

    # Auto-check interval for tracked manga (minutes, 0 = disabled)
    check_interval: int = 0

    # Bulk/Docker mode
    bulk_file: Optional[str] = None

    # Direct search/ID
    query: Optional[str] = None
    series_id: Optional[str] = None
    chapters: Optional[str] = None


class ConfigLoader:
    """Load configuration from TOML file with override support"""

    def __init__(self, config_path: str | None = None):
        if config_path is None:
            config_path = os.getenv("CONFIG_FILE", "config.toml")
        self.config_path = Path(config_path)
        self.raw_config: Dict[str, Any] = {}

        if self.config_path.exists():
            self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from TOML file.

        Returns:
            Dict of raw config values, or empty dict if file doesn't exist.
        Raises:
            tomli.TOMLDecodeError: If the config file is malformed.
        """
        try:
            with open(self.config_path, 'rb') as f:
                self.raw_config = tomli.load(f)
                return self.raw_config
        except FileNotFoundError:
            logger.info(f"No config file found at {self.config_path}, using defaults.")
            return {}
        except tomli.TOMLDecodeError:
            logger.error(f"Malformed TOML in {self.config_path}. Fix the syntax or delete it to use defaults.")
            raise
        except Exception as e:
            logger.warning(f"Failed to load config from {self.config_path}: {type(e).__name__}: {e}")
            return {}

    def get_downloader_config(self, cli_overrides: Optional[Dict[str, Any]] = None) -> DownloaderConfig:
        """
        Get downloader config with priority: CLI args > TOML config > defaults

        Args:
            cli_overrides: Dictionary of CLI arguments to override TOML config
        """
        # Start with defaults from TOML
        toml_config = self.raw_config.get('downloader', {})

        # Build config dict with priority
        config_dict = {}

        # Get all DownloaderConfig fields
        for key in DownloaderConfig.__dataclass_fields__.keys():
            value = None

            # Priority 1: CLI overrides (if provided and not None)
            if cli_overrides and key in cli_overrides and cli_overrides[key] is not None:
                value = cli_overrides[key]

            # Priority 2: TOML config
            elif key in toml_config:
                value = toml_config[key]

            # Priority 3: Defaults (handled by dataclass)
            if value is not None:
                config_dict[key] = value

        return DownloaderConfig(**config_dict)

    def get_external_server_config(self):
        from src.integrations import ExternalServerConfig
        raw = self.raw_config.get('external_server', {})
        return ExternalServerConfig(
            url=raw.get('url', ''),
            api_key=raw.get('api_key', ''),
            library_id=raw.get('library_id', ''),
        )

    def reload(self):
        """Reload configuration from file"""
        if self.config_path.exists():
            self.load_config()


def load_external_server_config(config_path: str | None = None):
    if config_path is None:
        config_path = os.getenv("CONFIG_FILE", "config.toml")
    loader = ConfigLoader(config_path)
    return loader.get_external_server_config()


def load_config(config_path: str | None = None, cli_overrides: Optional[Dict[str, Any]] = None) -> DownloaderConfig:
    """
    Convenience function to load configuration

    Args:
        config_path: Path to TOML config file (defaults to CONFIG_FILE env var or config.toml)
        cli_overrides: Dictionary of CLI arguments to override TOML config

    Returns:
        DownloaderConfig instance with merged configuration
    """
    if config_path is None:
        config_path = os.getenv("CONFIG_FILE", "config.toml")
    loader = ConfigLoader(config_path)
    return loader.get_downloader_config(cli_overrides)


def save_config(config: DownloaderConfig, config_path: str | None = None):
    """Save configuration to TOML file.

    Args:
        config: DownloaderConfig instance to save
        config_path: Path to TOML config file (defaults to CONFIG_FILE env var or config.toml)
    """
    import tomli_w

    if config_path is None:
        config_path = os.getenv("CONFIG_FILE", "config.toml")

    # Only save persistent settings (not runtime-specific ones like query, series_id, etc.)
    persistent_fields = {
        'latest', 'sequence', 'zip', 'verbose', 'use_english_title', 'comicinfo',
        'rlc', 'max_sleep', 'max_retries', 'parallel_workers', 'output_dir',
        'library_paths', 'check_interval',
    }
    config_dict = {k: v for k, v in asdict(config).items() if k in persistent_fields}
    toml_data = {'downloader': config_dict}

    with open(config_path, 'wb') as f:
        tomli_w.dump(toml_data, f)
