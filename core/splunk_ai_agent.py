"""
Splunk AI Investigation Agent.

Uses Splunk Python SDK AI capabilities (splunklib.ai.Agent) with:
- Local MCP tools for real Splunk data queries (splunk_app/finguard_copilot/bin/tools.py)
- Remote Splunk MCP Server tools when installed (generate_spl, run_splunk_query via AI Assistant)

This replaces the standalone LangChain agent for hackathon compliance.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import splunklib.ai.agent as splunk_agent_module
from splunklib.ai import Agent, OpenAIModel
from splunklib.ai.messages import HumanMessage
from splunklib.ai.tool_settings import (
    LocalToolSettings,
    RemoteToolSettings,
    ToolAllowlist,
    ToolSettings,
)
from splunklib.client import Service

from core.splunk_connection import connect_splunk, get_splunk_status
from core.splunk_mcp_client import SplunkMCPClient
from security.llm_guard import LLMGuard

logger = logging.getLogger(__name__)

TOOLS_PATH = (
    Path(__file__).resolve().parent.parent
    / "splunk_app"
    / "finguard_copilot"
    / "bin"
    / "tools.py"
)

SYSTEM_PROMPT = """You are a financial compliance investigation agent powered by Splunk AI.

Your role:
1. Use Splunk tools to gather user profiles, transactions, and device history
2. Use generate_spl (Splunk AI Assistant) when you need custom SPL queries
3. Identify anomalies and cite compliance concerns
4. NEVER make absolute legal conclusions or authorize enforcement actions

Investigation workflow:
1. get_user_profile — establish user baseline
2. get_recent_transactions — review 24h activity
3. get_device_history — check access patterns
4. run_splunk_query or generate_spl — deeper Splunk analysis when needed

Format your final response with:
- **Risk Score**: (Low/Medium/High/Critical)
- **Anomalies Detected**: (list with evidence from Splunk data)
- **Compliance Basis**: (relevant regulations)
- **Recommended Action**: (human analyst review required)
- **Splunk Evidence**: (which Splunk queries/tools were used)
"""


class SplunkInvestigationAgent:
    """
    Compliance investigation agent using Splunk SDK AI (splunklib.ai).

    Integrates Splunk AI capabilities at runtime:
    - splunklib.ai Agent agentic loop
    - Splunk MCP Server generate_spl (Splunk AI Assistant) when available
    - Local Splunk query tools backed by real indexed data
    """

    def __init__(
        self,
        llm_guard: LLMGuard,
        service: Optional[Service] = None,
    ) -> None:
        self.llm_guard = llm_guard
        self._service = service
        self._mcp_client: Optional[SplunkMCPClient] = None
        self._splunk_status: Dict[str, Any] = {}
        self._mcp_tools: List[str] = []
        self._initialized = False

    async def initialize(self) -> Dict[str, Any]:
        """Connect to Splunk and probe Splunk AI / MCP capabilities."""
        if self._service is None:
            self._service = connect_splunk()

        self._splunk_status = get_splunk_status(self._service)

        # Point splunklib.ai to our local tools.py (Splunk SDK AI local MCP tools)
        splunk_agent_module._testing_local_tools_path = str(TOOLS_PATH)
        splunk_agent_module._testing_app_id = "finguard_copilot"

        # Probe Splunk MCP Server for AI Assistant generate_spl
        username = os.getenv("SPLUNK_USERNAME", "admin")
        self._mcp_client = SplunkMCPClient(self._service, username)
        mcp_ok = await self._mcp_client.initialize()
        self._mcp_tools = self._mcp_client.tools if mcp_ok else []

        self._initialized = True
        return {
            "splunk_connected": True,
            "splunk_version": self._splunk_status.get("version"),
            "splunk_mcp_available": mcp_ok,
            "splunk_mcp_tools": self._mcp_tools,
            "splunk_ai_sdk": "splunklib.ai.Agent",
            "local_tools_path": str(TOOLS_PATH),
        }

    def investigate(self, user_input: str) -> Dict[str, Any]:
        """Synchronous wrapper for Streamlit — runs async Splunk AI agent."""
        if not self._initialized:
            try:
                init_result = asyncio.run(self.initialize())
                logger.info("Splunk AI initialized: %s", init_result)
            except Exception as exc:
                return {
                    "success": False,
                    "report": "",
                    "reasoning": [],
                    "error": f"Splunk AI initialization failed: {exc}",
                    "splunk_ai": {},
                }

        is_valid, validation_msg = self.llm_guard.validate_input(user_input)
        if not is_valid:
            return {
                "success": False,
                "report": "",
                "reasoning": [],
                "error": validation_msg,
                "splunk_ai": {},
            }

        try:
            result = asyncio.run(self._async_investigate(user_input))
            sanitized = self.llm_guard.sanitize_output(result["report"])
            result["report"] = sanitized
            return result
        except Exception as exc:
            logger.exception("Splunk AI investigation failed")
            return {
                "success": False,
                "report": "",
                "reasoning": [],
                "error": f"Splunk AI investigation failed: {exc}",
                "splunk_ai": self._ai_metadata(),
            }

    async def _async_investigate(self, user_input: str) -> Dict[str, Any]:
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for Splunk AI Agent LLM backend")

        model = OpenAIModel(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            api_key=api_key,
            temperature=0.1,
        )

        remote_settings = None
        if self._mcp_client and self._mcp_client.available:
            remote_settings = RemoteToolSettings(
                allowlist=ToolAllowlist(
                    names=[
                        "generate_spl",
                        "splunk_generate_spl",
                        "run_splunk_query",
                        "splunk_run_query",
                        "get_splunk_info",
                        "splunk_get_info",
                        "get_indexes",
                        "splunk_get_indexes",
                    ]
                )
            )

        local_allowlist = ToolAllowlist(
            names=[
                "generate_spl",
                "run_splunk_query",
                "get_user_profile",
                "get_recent_transactions",
                "get_device_history",
                "get_splunk_info",
            ]
        )

        reasoning_steps: List[str] = []

        async with Agent(
            model=model,
            system_prompt=SYSTEM_PROMPT,
            service=self._service,
            tool_settings=ToolSettings(
                local=LocalToolSettings(allowlist=local_allowlist),
                remote=remote_settings,
            ),
            logger=logger,
        ) as agent:
            logger.info("Invoking Splunk AI Agent for: %s", user_input[:80])
            response = await agent.invoke([HumanMessage(content=user_input)])

            for msg in response.messages:
                if hasattr(msg, "calls") and msg.calls:
                    for call in msg.calls:
                        call_name = getattr(call, "name", str(call))
                        call_args = getattr(call, "args", {})
                        reasoning_steps.append(
                            f"Splunk AI Tool: {call_name}({json.dumps(call_args, default=str)[:120]})"
                        )

            final = response.final_message
            report = _extract_text_content(final.content)

            return {
                "success": True,
                "report": report,
                "reasoning": reasoning_steps or ["Splunk AI Agent completed investigation"],
                "error": None,
                "splunk_ai": self._ai_metadata(),
            }

    def _ai_metadata(self) -> Dict[str, Any]:
        return {
            "sdk": "splunklib.ai.Agent (Splunk Python SDK 3.0 AI)",
            "splunk_version": self._splunk_status.get("version"),
            "mcp_server_available": bool(self._mcp_client and self._mcp_client.available),
            "mcp_tools": self._mcp_tools,
            "generate_spl_mcp": (
                "generate_spl" in self._mcp_tools
                or "splunk_generate_spl" in self._mcp_tools
            ),
            "generate_spl_local": True,
            "generate_spl_available": True,
            "local_tools": [
                "generate_spl",
                "get_user_profile",
                "get_recent_transactions",
                "get_device_history",
                "run_splunk_query",
            ],
        }


def _extract_text_content(content: Any) -> str:
    """Extract plain text from splunklib.ai message content blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif hasattr(block, "text"):
                parts.append(block.text)
        return "\n".join(parts)
    return str(content)
