"""
utils/history.py
────────────────
Lightweight JSON-file persistence for query history.
All I/O is isolated here so the rest of the app never touches the filesystem
directly for history management.
"""

import json
import os
from datetime import datetime

from config.settings import HISTORY_FILE, HISTORY_MAX_ENTRIES


def load_history() -> list[dict]:
    """Return the saved query history, or an empty list if none exists."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, IOError):
        return []


def save_to_history(question: str, sql: str) -> None:
    """
    Append a new entry to history, deduplicating consecutive identical questions
    and capping total entries at HISTORY_MAX_ENTRIES.
    """
    history = load_history()

    # Skip duplicate consecutive entries
    if history and history[-1]["question"] == question:
        return

    history.append(
        {
            "question": question,
            "sql": sql,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )
    history = history[-HISTORY_MAX_ENTRIES:]

    try:
        with open(HISTORY_FILE, "w") as fh:
            json.dump(history, fh, indent=2)
    except IOError as exc:
        # Non-fatal – callers can handle or ignore
        raise RuntimeError(f"Could not save history: {exc}") from exc


def clear_history() -> None:
    """Delete the history file if it exists."""
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
