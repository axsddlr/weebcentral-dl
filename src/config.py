"""Configuration management for WeebCentral Downloader"""
import os
import tomli
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class DownloaderConfig:
    """Configuration for downloader behavior"""
    # Download options
    latest: bool = False
    sequence: bool = False
    zip: bool = False
    verbose: bool = False
    use_english_title: bool = False

    # Rate limiting & retries
    rlc: int = 10
    max_sleep: int = 120
    max_retries: int = 5

    # Paths
    output_dir: str = "./manga_downloads"

    # Bulk/Docker mode
    bulk_file: Optional[str] = None

    # Direct search/ID
    query: Optional[str] = None
    series_id: Optional[str] = None
    chapters: Optional[str] = None


class ConfigLoader:
    """Load configuration from TOML file with override support"""

    def __init__(self, config_path: str = "config.toml"):
        self.config_path = Path(config_path)
        self.raw_config: Dict[str, Any] = {}

        if self.config_path.exists():
            self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from TOML file"""
        try:
            with open(self.config_path, 'rb') as f:
                self.raw_config = tomli.load(f)
                return self.raw_config
        except Exception as e:
            print(f"[WARN] Failed to load config from {self.config_path}: {e}")
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
        for field in DownloaderConfig.__dataclass_fields__.keys():
            value = None

            # Priority 1: CLI overrides (if provided and not None)
            if cli_overrides and field in cli_overrides and cli_overrides[field] is not None:
                value = cli_overrides[field]

            # Priority 2: TOML config
            elif field in toml_config:
                value = toml_config[field]

            # Priority 3: Defaults (handled by dataclass)
            if value is not None:
                config_dict[field] = value

        return DownloaderConfig(**config_dict)

    def reload(self):
        """Reload configuration from file"""
        if self.config_path.exists():
            self.load_config()


def load_config(config_path: str = "config.toml", cli_overrides: Optional[Dict[str, Any]] = None) -> DownloaderConfig:
    """
    Convenience function to load configuration

    Args:
        config_path: Path to TOML config file
        cli_overrides: Dictionary of CLI arguments to override TOML config

    Returns:
        DownloaderConfig instance with merged configuration
    """
    loader = ConfigLoader(config_path)
    return loader.get_downloader_config(cli_overrides)
