# Copyright © 2026 FinGuard Copilot
# Splunk AI local MCP tools — executed via splunklib.ai ToolRegistry.
#
# These tools are loaded by splunklib.ai.Agent at runtime and provide
# real Splunk data access for the investigation agent.

import json
import os
import sys

# Ensure splunklib is importable when run as MCP stdio subprocess
sys.path.insert(0, os.path.dirname(__file__))

from splunklib.ai.registry import ToolContext, ToolRegistry
from splunklib.results import JSONResultsReader

registry = ToolRegistry()

DEFAULT_INDEX = os.getenv("SPLUNK_INDEX", "main")


def _run_search(ctx: ToolContext, search: str, earliest: str = "-30d", latest: str = "now") -> list:
    service = ctx.service
    job = service.jobs.create(
        search,
        exec_mode="blocking",
        earliest_time=earliest,
        latest_time=latest,
        timeout=60,
    )
    results = [dict(item) for item in JSONResultsReader(job.results(output_mode="json")) if isinstance(item, dict)]
    job.cancel()
    return results


@registry.tool(
    name="run_splunk_query",
    description="Execute a Splunk SPL search and return JSON results. Use for compliance data queries.",
    tags=["splunk", "investigation", "spl"],
)
def run_splunk_query(
    ctx: ToolContext,
    query: str,
    earliest_time: str = "-24h",
    latest_time: str = "now",
) -> dict:
    """Run arbitrary SPL against Splunk indexes."""
    ctx.logger.info("run_splunk_query: %s", query[:120])
    if not query.strip().lower().startswith("search"):
        query = f"search {query}"
    results = _run_search(ctx, query, earliest_time, latest_time)
    return {"query": query, "count": len(results), "results": results[:50]}


@registry.tool(
    name="get_user_profile",
    description="Get user profile from Splunk finguard index by display_user_id (e.g. USER_00001) or pseudonymized user_id.",
    tags=["splunk", "investigation", "compliance"],
)
def get_user_profile(ctx: ToolContext, user_id: str) -> dict:
    """Retrieve user profile from indexed compliance data."""
    search = (
        f"search index={DEFAULT_INDEX} sourcetype=finguard:users "
        f"(display_user_id=\"{user_id}\" OR user_id=\"{user_id}\") "
        "| head 1 | table display_user_id user_id account_type risk_profile "
        "verification_status email phone account_number"
    )
    results = _run_search(ctx, search)
    if not results:
        return {"error": f"No profile found for {user_id}", "user_id": user_id}
    return results[0]


@registry.tool(
    name="get_recent_transactions",
    description="Get recent transactions for a user from Splunk. Input: user_id (USER_00001 format).",
    tags=["splunk", "investigation", "compliance"],
)
def get_recent_transactions(ctx: ToolContext, user_id: str, hours: int = 24) -> dict:
    """Retrieve recent transactions for compliance review."""
    earliest = f"-{hours}h"
    search = (
        f"search index={DEFAULT_INDEX} sourcetype=finguard:transactions "
        f"(display_user_id=\"{user_id}\" OR user_id=\"{user_id}\") "
        f"earliest={earliest} "
        "| sort - timestamp | head 20 "
        "| table transaction_id user_id display_user_id amount timestamp "
        "transaction_type anomaly_type risk_score violation_flags"
    )
    results = _run_search(ctx, search, earliest=earliest)
    return {"user_id": user_id, "count": len(results), "transactions": results}


@registry.tool(
    name="get_device_history",
    description="Get device login history for a user from Splunk. Input: user_id (USER_00001 format).",
    tags=["splunk", "investigation", "compliance"],
)
def get_device_history(ctx: ToolContext, user_id: str) -> dict:
    """Retrieve device access records for anomaly detection."""
    search = (
        f"search index={DEFAULT_INDEX} sourcetype=finguard:devices "
        f"(display_user_id=\"{user_id}\" OR user_id=\"{user_id}\") "
        "| sort - last_login | head 20 "
        "| table user_id display_user_id device_id device_type location "
        "device_ip ip_address is_new last_login"
    )
    results = _run_search(ctx, search)
    return {"user_id": user_id, "count": len(results), "devices": results}


@registry.tool(
    name="get_splunk_info",
    description="Get Splunk instance version and server metadata.",
    tags=["splunk", "metadata"],
)
def get_splunk_info(ctx: ToolContext) -> dict:
    """Return Splunk instance information."""
    info = ctx.service.info
    return {
        "version": info.get("version"),
        "server_name": info.get("serverName"),
        "host": ctx.service.host,
        "port": ctx.service.port,
    }


if __name__ == "__main__":
    registry.run()
