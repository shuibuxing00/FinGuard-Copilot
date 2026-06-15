# Copyright © 2026 FinGuard Copilot
# Splunk AI local MCP tools — executed via splunklib.ai ToolRegistry.
#
# These tools are loaded by splunklib.ai.Agent at runtime and provide
# real Splunk data access for the investigation agent.

import json
import os
import re
import sys

# Ensure splunklib is importable when run as MCP stdio subprocess
sys.path.insert(0, os.path.dirname(__file__))

from splunklib.ai.registry import ToolContext, ToolRegistry
from splunklib.results import JSONResultsReader

registry = ToolRegistry()

DEFAULT_INDEX = os.getenv("SPLUNK_INDEX", "main")

_USER_ID_PATTERN = re.compile(r"USER_\d+", re.IGNORECASE)


def _template_spl_from_nl(natural_language_query: str) -> str:
    """Rule-based NL → SPL for finguard sourcetypes (local generate_spl fallback)."""
    q = natural_language_query.lower()
    if "transaction" in q or "txn" in q or "payment" in q:
        base = f"search index={DEFAULT_INDEX} sourcetype=finguard:transactions"
    elif "device" in q or "login" in q or "access" in q:
        base = f"search index={DEFAULT_INDEX} sourcetype=finguard:devices"
    elif "user" in q or "profile" in q or "account" in q:
        base = f"search index={DEFAULT_INDEX} sourcetype=finguard:users"
    else:
        base = f"search index={DEFAULT_INDEX} sourcetype=finguard:*"

    user_match = _USER_ID_PATTERN.search(natural_language_query)
    if user_match:
        uid = user_match.group().upper()
        base += f' (display_user_id="{uid}" OR user_id="{uid}")'

    if "high risk" in q or "high-risk" in q or "critical" in q:
        base += " risk_score>=70"
    if "anomal" in q or "suspicious" in q:
        base += ' anomaly_type!="none"'

    if "24" in q and "hour" in q:
        base += " earliest=-24h"
    elif "7 day" in q or "week" in q:
        base += " earliest=-7d"

    if "count" in q or "how many" in q:
        return base + " | stats count by anomaly_type, risk_score"

    return base + " | sort - timestamp | head 50"


def _openai_spl_from_nl(natural_language_query: str) -> str | None:
    """Optional OpenAI-backed SPL generation when OPENAI_API_KEY is set."""
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key.startswith("your_"):
        return None

    try:
        import httpx

        prompt = (
            "Convert this compliance investigation question into Splunk SPL. "
            f"Use index={DEFAULT_INDEX} and sourcetypes finguard:users, "
            "finguard:transactions, finguard:devices. Return ONLY the SPL, no markdown.\n\n"
            f"Question: {natural_language_query}"
        )
        response = httpx.post(
            f"{os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"].strip()
        if content.lower().startswith("search"):
            return content
        return f"search {content}"
    except Exception:
        return None


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
    name="generate_spl",
    description=(
        "Generate Splunk SPL from natural language for finguard compliance data. "
        "Use when you need custom SPL beyond the built-in profile/transaction/device tools."
    ),
    tags=["splunk", "investigation", "ai", "spl"],
)
def generate_spl(ctx: ToolContext, natural_language_query: str) -> dict:
    """NL → SPL via OpenAI (if configured) or local template rules."""
    ctx.logger.info("generate_spl: %s", natural_language_query[:120])
    openai_spl = _openai_spl_from_nl(natural_language_query)
    spl = openai_spl or _template_spl_from_nl(natural_language_query)
    return {
        "natural_language_query": natural_language_query,
        "spl": spl,
        "source": "openai" if openai_spl else "template",
        "note": "Execute with run_splunk_query or use splunk_run_query via MCP when available.",
    }


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
