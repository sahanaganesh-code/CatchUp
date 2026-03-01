"""
Data persistence for notes, todos, and calendar events (Person 2).
Uses JSON files under a configurable data dir so data survives restarts.
content_manager can load/save via load_persistence() and save_persistence() to avoid
editing Person 1's file; alternatively we export helpers they can call.
"""
from typing import Dict, Any
from pathlib import Path
import json
import logging
import os

logger = logging.getLogger(__name__)

# Persist under backend data dir (env so Person 3 can override in config later)
PERSIST_DIR = os.environ.get("CATCHUP_PERSIST_DIR", "./data")
NOTES_FILE = "notes.json"
TODOS_FILE = "todos.json"
EVENTS_FILE = "events.json"


def _ensure_dir() -> Path:
    d = Path(PERSIST_DIR)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _load_json(filename: str) -> Dict[str, Any]:
    path = _ensure_dir() / filename
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load {filename}: {e}")
        return {}


def _save_json(filename: str, data: Dict[str, Any]) -> None:
    path = _ensure_dir() / filename
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Could not save {filename}: {e}")


def load_notes_store() -> Dict[str, Any]:
    """Load notes from disk. Returns dict of note_id -> note dict (model_dump compatible)."""
    return _load_json(NOTES_FILE)


def save_notes_store(notes_dict: Dict[str, Any]) -> None:
    """Save notes to disk. Pass dict of note_id -> note (or model_dump())."""
    _save_json(NOTES_FILE, notes_dict)


def load_todos_store() -> Dict[str, Any]:
    """Load todos from disk."""
    return _load_json(TODOS_FILE)


def save_todos_store(todos_dict: Dict[str, Any]) -> None:
    """Save todos to disk."""
    _save_json(TODOS_FILE, todos_dict)


def load_events_store() -> Dict[str, Any]:
    """Load calendar events from disk."""
    return _load_json(EVENTS_FILE)


def save_events_store(events_dict: Dict[str, Any]) -> None:
    """Save calendar events to disk."""
    _save_json(EVENTS_FILE, events_dict)
