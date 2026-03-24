"""Configuration management for fetch-fish."""
import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".fetch-fish"
CONFIG_FILE = CONFIG_DIR / "config.json"
CACHE_DIR = CONFIG_DIR / "cache"


def ensure_dirs():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    ensure_dirs()
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def save_config(config: dict):
    ensure_dirs()
    CONFIG_FILE.write_text(json.dumps(config, indent=2))