import json
from pathlib import Path
import os


def get_hosts_fpath() -> str:
    BASE_DIR = Path(__file__).resolve().parent

    DEFAULT_HOSTS_PATH = BASE_DIR / "hosts.json"
    HOSTS_FILE_PATH = os.getenv("HOSTS_CONFIG_PATH", str(DEFAULT_HOSTS_PATH))
    return HOSTS_FILE_PATH


def load_config(fpath: str):
    try:
        with open(fpath, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Configuration file not found at {fpath}")
        return []
