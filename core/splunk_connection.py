"""
Shared Splunk connection utilities for FinGuard Copilot.
Connects to Splunk Enterprise via the Splunk Python SDK (splunklib).
"""

import os
from typing import Any, Dict, Optional

import splunklib.client as splunk_client
from splunklib.client import Service


def load_splunk_config() -> Dict[str, Any]:
    """Load Splunk connection settings from environment variables."""
    return {
        "host": os.getenv("SPLUNK_HOST", "localhost"),
        "port": int(os.getenv("SPLUNK_PORT", "8089")),
        "username": os.getenv("SPLUNK_USERNAME", "admin"),
        "password": os.getenv("SPLUNK_PASSWORD", ""),
        "index": os.getenv("SPLUNK_INDEX", "main"),
        "scheme": os.getenv("SPLUNK_SCHEME", "https"),
        "verify_ssl": os.getenv("SPLUNK_VERIFY_SSL", "false").lower() in ("1", "true", "yes"),
        "timeout": int(os.getenv("SPLUNK_SEARCH_TIMEOUT", "60")),
        "web_port": int(os.getenv("SPLUNK_WEB_PORT", "8000")),
    }


def connect_splunk(config: Optional[Dict[str, Any]] = None) -> Service:
    """
    Create an authenticated Splunk Service connection.

    Raises:
        ConnectionError: If authentication or connection fails.
    """
    cfg = config or load_splunk_config()
    if not cfg["password"]:
        raise ConnectionError(
            "SPLUNK_PASSWORD is not set. Configure credentials in .env before connecting."
        )

    try:
        service = splunk_client.connect(
            host=cfg["host"],
            port=cfg["port"],
            username=cfg["username"],
            password=cfg["password"],
            scheme=cfg["scheme"],
            verify=cfg["verify_ssl"],
        )
        service.timeout = cfg["timeout"]
        return service
    except Exception as exc:
        raise ConnectionError(f"Failed to connect to Splunk: {exc}") from exc


def get_splunk_status(service: Service) -> Dict[str, Any]:
    """Return basic Splunk instance metadata for UI display."""
    info = service.info
    return {
        "version": info.get("version", "unknown"),
        "server_name": info.get("serverName", "unknown"),
        "host": service.host,
        "port": service.port,
    }
