import json
from pathlib import Path
import os


def get_hosts_fpath() -> str:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    HOSTS_FILE_PATH = PROJECT_ROOT / os.getenv("HOSTS_CONFIG_PATH", "hosts.json")
    return HOSTS_FILE_PATH


def load_config(fpath: str):
    try:
        with open(fpath, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Configuration file not found at {fpath}")
        return []
