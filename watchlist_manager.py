from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent
WATCHLIST_FILE = BASE_DIR / "watchlist.json"


def load_watchlist():
    if not WATCHLIST_FILE.exists():
        return []

    try:
        with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []


def save_watchlist(symbols):
    try:
        with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
            json.dump(sorted(list(set(symbols))), f, indent=2)
    except Exception as e:
        raise RuntimeError(f"Failed to save watchlist: {e}")