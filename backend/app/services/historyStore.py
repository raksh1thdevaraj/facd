"""Compatibility shim for HistoryStore.

Allows importing via `app.services.historyStore` or `services.historyStore`.
"""

from services.historyStore import (
    DEFAULT_DATA_DIR,
    DEFAULT_HISTORY_FILE,
    HistoryStore,
    append_record,
    clear_history,
    delete_record,
    get_history_store,
    get_record_by_id,
    history_store,
    read_history,
)

__all__ = [
    "DEFAULT_DATA_DIR",
    "DEFAULT_HISTORY_FILE",
    "HistoryStore",
    "append_record",
    "clear_history",
    "delete_record",
    "get_history_store",
    "get_record_by_id",
    "history_store",
    "read_history",
]
