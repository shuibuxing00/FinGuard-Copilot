"""
Splunk MCP Server client for Splunk AI capabilities.

Calls Splunk MCP tools (generate_spl, run_splunk_query, etc.) exposed by the
Splunk MCP Server app at https://<host>:8089/services/mcp.

Requires the Splunk MCP Server app (Splunkbase #7931) to be installed on the
Splunk instance. When unavailable, callers should fall back to local SDK tools.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import httpx
from splunklib.client import Service
from splunklib.binding import HTTPError

logger = logging.getLogger(__name__)

MCP_PROTOCOL_VERSION = "2025-03-26"


class SplunkMCPClient:
    """HTTP MCP client for Splunk MCP Server remote AI tools."""

    def __init__(self, service: Service, username: str) -> None:
        self._service = service
        self._username = username
        self._mcp_url = f"{service.scheme}://{service.host}:{service.port}/services/mcp"
        self._token: Optional[str] = None
        self._available = False
        self._tools: List[str] = []

    @property
    def available(self) -> bool:
        return self._available

    @property
    def tools(self) -> List[str]:
        return list(self._tools)

    async def initialize(self) -> bool:
        """Probe MCP server and cache tool list. Returns True if MCP is reachable."""
        self._token = await asyncio.to_thread(self._fetch_mcp_token)
        if not self._token:
            logger.warning(
                "Splunk MCP Server not detected. Install Splunk MCP Server app "
                "(Splunkbase #7931) to enable generate_spl AI tool."
            )
            self._available = False
            return False

        try:
            result = await self._rpc("initialize", {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "finguard-copilot", "version": "1.0.0"},
            })
            server_info = result.get("serverInfo", {})
            logger.info(
                "Splunk MCP Server connected: %s v%s",
                server_info.get("name", "unknown"),
                server_info.get("version", "unknown"),
            )

            tools_result = await self._rpc("tools/list", {})
            self._tools = [
                t["name"] for t in tools_result.get("tools", []) if "name" in t
            ]
            self._available = True
            logger.info("Splunk MCP tools available: %s", self._tools)
            return True
        except Exception as exc:
            logger.warning("Splunk MCP initialization failed: %s", exc)
            self._available = False
            return False

    async def run_splunk_query(
        self,
        query: str,
        earliest_time: str = "-24h",
        latest_time: str = "now",
        max_results: int = 100,
    ) -> Dict[str, Any]:
        """Execute SPL via Splunk MCP run query tool."""
        tool_name = "splunk_run_query"
        if "run_splunk_query" in self._tools:
            tool_name = "run_splunk_query"
        return await self.call_tool(
            tool_name,
            {
                "query": query,
                "earliest_time": earliest_time,
                "latest_time": latest_time,
                "max_results": max_results,
            },
        )

    async def generate_spl(self, natural_language_query: str) -> Dict[str, Any]:
        """Call Splunk AI generate_spl MCP tool when available."""
        for name in ("generate_spl", "splunk_generate_spl"):
            if name in self._tools:
                return await self.call_tool(name, {"query": natural_language_query})
        raise RuntimeError(
            "generate_spl not available in MCP tools. "
            "Enable Splunk AI Assistant in Splunk MCP Server app settings."
        )

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke any MCP tool by name."""
        if not self._available:
            raise RuntimeError(
                "Splunk MCP Server is not available. Install MCP Server app on Splunk."
            )

        result = await self._rpc("tools/call", {"name": name, "arguments": arguments})

        if result.get("isError"):
            content = result.get("content", [])
            error_text = "MCP tool call failed"
            if content and isinstance(content[0], dict):
                error_text = content[0].get("text", error_text)
            raise RuntimeError(f"MCP tool '{name}' error: {error_text}")

        structured = result.get("structuredContent")
        if structured:
            return structured

        texts = [
            c.get("text", "")
            for c in result.get("content", [])
            if isinstance(c, dict) and c.get("type") == "text"
        ]
        return {"result": "\n".join(texts)}

    def _fetch_mcp_token(self) -> Optional[str]:
        try:
            response = self._service.get(
                path_segment="mcp_token",
                username=self._username,
                output_mode="json",
            )
            body = json.loads(str(response.body))
            if isinstance(body, dict) and body.get("token"):
                return body["token"]
            entries = body.get("entry", [])
            if entries:
                return entries[0].get("content", {}).get("token")
        except HTTPError as exc:
            if exc.status == 404:
                return None
            raise
        except Exception as exc:
            logger.debug("MCP token fetch failed: %s", exc)
        return None

    async def _rpc(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if not self._token:
            raise RuntimeError("MCP token not available")

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        }
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "x-splunk-app-id": "finguard_copilot",
            "x-splunk-trace-id": "finguard-trace",
        }

        async with httpx.AsyncClient(verify=False, timeout=120.0) as client:
            response = await client.post(
                self._mcp_url,
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

        if "error" in data:
            raise RuntimeError(f"MCP RPC error: {data['error']}")

        return data.get("result", {})
