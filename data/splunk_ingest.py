"""
Index synthetic compliance data into Splunk for real SPL queries at runtime.
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional, Tuple

import pandas as pd
from splunklib.client import Index, Service

from core.splunk_connection import connect_splunk, load_splunk_config

logger = logging.getLogger(__name__)

SOURCETYPE_USERS = "finguard:users"
SOURCETYPE_TRANSACTIONS = "finguard:transactions"
SOURCETYPE_DEVICES = "finguard:devices"

DEFAULT_INGEST_WORKERS = 16


def _submit_event(index: Index, payload: str, sourcetype: str) -> None:
    index.submit(payload, sourcetype=sourcetype, host="finguard-copilot")


def _parallel_submit_events(
    index: Index,
    events: List[str],
    sourcetype: str,
    max_workers: int = DEFAULT_INGEST_WORKERS,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> int:
    """Submit many events in parallel; each HTTP call is ~1–2s if done sequentially."""
    total = len(events)
    if total == 0:
        return 0

    done = 0
    workers = min(max_workers, total)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [
            pool.submit(_submit_event, index, payload, sourcetype)
            for payload in events
        ]
        for future in as_completed(futures):
            future.result()
            done += 1
            if progress_callback:
                progress_callback(done, total)
    return total


def ingest_dataframes_to_splunk(
    users_df: pd.DataFrame,
    transactions_df: pd.DataFrame,
    devices_df: pd.DataFrame,
    service: Optional[Service] = None,
    index: Optional[str] = None,
    max_workers: int = DEFAULT_INGEST_WORKERS,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> Dict[str, Any]:
    """
    Submit synthetic datasets to Splunk via the SDK receiver API.

    Each row is indexed as a JSON event with a dedicated sourcetype so
  investigation SPL can query real Splunk data instead of mock DataFrames.
    """
    cfg = load_splunk_config()
    svc = service or connect_splunk(cfg)
    target_index = index or cfg["index"]

    if target_index not in [idx.name for idx in svc.indexes]:
        logger.warning("Index '%s' not found; falling back to 'main'", target_index)
        target_index = "main"

    index_obj = svc.indexes[target_index]
    counts = {"users": 0, "transactions": 0, "devices": 0}
    total_events = len(users_df) + len(transactions_df) + len(devices_df)
    completed = 0

    def _track(done: int, _batch_total: int) -> None:
        nonlocal completed
        completed += 1
        if progress_callback:
            progress_callback(completed, total_events)

    user_events = [
        json.dumps(_prepare_user_event(row), default=str) for _, row in users_df.iterrows()
    ]
    txn_events = [
        json.dumps(_prepare_transaction_event(row), default=str)
        for _, row in transactions_df.iterrows()
    ]
    device_events = [
        json.dumps(_prepare_device_event(row), default=str) for _, row in devices_df.iterrows()
    ]

    counts["users"] = _parallel_submit_events(
        index_obj, user_events, SOURCETYPE_USERS, max_workers, _track
    )
    counts["transactions"] = _parallel_submit_events(
        index_obj, txn_events, SOURCETYPE_TRANSACTIONS, max_workers, _track
    )
    counts["devices"] = _parallel_submit_events(
        index_obj, device_events, SOURCETYPE_DEVICES, max_workers, _track
    )

    logger.info(
        "Indexed to Splunk index '%s': %s",
        target_index,
        counts,
    )
    return {"index": target_index, "counts": counts, "success": True}


def ingest_from_session(
    users_df: pd.DataFrame,
    transactions_df: pd.DataFrame,
    devices_df: pd.DataFrame,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> Dict[str, Any]:
    """Convenience wrapper used by the Streamlit UI."""
    try:
        return ingest_dataframes_to_splunk(
            users_df, transactions_df, devices_df, progress_callback=progress_callback
        )
    except Exception as exc:
        logger.error("Splunk ingest failed: %s", exc)
        return {"success": False, "error": str(exc)}


def _prepare_user_event(row: pd.Series) -> Dict[str, Any]:
    event = row.to_dict()
    event["event_type"] = "user_profile"
    if "display_user_id" not in event:
        event["display_user_id"] = event.get("user_id", "")
    return event


def _prepare_transaction_event(row: pd.Series) -> Dict[str, Any]:
    event = row.to_dict()
    event["event_type"] = "transaction"
    return event


def _prepare_device_event(row: pd.Series) -> Dict[str, Any]:
    event = row.to_dict()
    event["event_type"] = "device_access"
    if "device_ip" not in event and "ip_address" in event:
        event["device_ip"] = event["ip_address"]
    return event


def add_display_user_ids(
    users_df: pd.DataFrame,
    transactions_df: pd.DataFrame,
    devices_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Add human-readable USER_xxxxx IDs alongside pseudonymized user_id."""
    users = users_df.copy()
    if "display_user_id" not in users.columns:
        users["display_user_id"] = [f"USER_{i:05d}" for i in range(len(users))]

    id_map = dict(zip(users["user_id"], users["display_user_id"]))

    txns = transactions_df.copy()
    if "display_user_id" not in txns.columns:
        txns["display_user_id"] = txns["user_id"].map(id_map)

    devs = devices_df.copy()
    if "display_user_id" not in devs.columns:
        devs["display_user_id"] = devs["user_id"].map(id_map)

    return users, txns, devs
