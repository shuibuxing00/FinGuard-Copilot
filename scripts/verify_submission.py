#!/usr/bin/env python3
"""
Verify Splunk Agentic Ops Hackathon submission requirements locally.

Usage:
    python scripts/verify_submission.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_FILES = [
    "LICENSE",
    "README.md",
    "requirements.txt",
    ".env.example",
    "architecture_diagram.md",
    "core/splunk_ai_agent.py",
    "core/splunk_connection.py",
    "core/splunk_mcp_client.py",
    "data/splunk_ingest.py",
    "splunk_app/finguard_copilot/bin/tools.py",
    "app/streamlit_app.py",
]

ARCHITECTURE_ASSETS = [
    "architecture_diagram.md",
    "architecture_diagram.png",
    "architecture.png",
]

OPTIONAL_BUT_RECOMMENDED = [
    "SUBMISSION.md",
    "HACKATHON_UPDATES.md",
    "ARCHITECTURE.md",
    "scripts/INSTALL_SPLUNK_MCP.md",
    "scripts/prove_splunk_ai_runtime.py",
]

DISQUALIFICATION_CHECKS = [
    (
        "Splunk AI code path (not mock-only investigation)",
        lambda: "SplunkInvestigationAgent" in (ROOT / "app/streamlit_app.py").read_text(encoding="utf-8")
        and "splunklib.ai" in (ROOT / "core/splunk_ai_agent.py").read_text(encoding="utf-8"),
    ),
    (
        "Investigation requires Splunk connection gate",
        lambda: "splunk_connected" in (ROOT / "app/streamlit_app.py").read_text(encoding="utf-8"),
    ),
    (
        "MIT LICENSE at repo root",
        lambda: (ROOT / "LICENSE").read_text(encoding="utf-8").startswith("MIT License"),
    ),
    (
        "Hackathon updates documented",
        lambda: (ROOT / "HACKATHON_UPDATES.md").is_file(),
    ),
]


def check(name: str, ok: bool, detail: str = "") -> bool:
    mark = "OK" if ok else "MISSING"
    suffix = f" — {detail}" if detail else ""
    print(f"  [{mark}] {name}{suffix}")
    return ok


def main() -> int:
    print("FinGuard — Hackathon submission verification\n")
    all_ok = True

    print("Required repository files:")
    for rel in REQUIRED_FILES:
        path = ROOT / rel
        all_ok &= check(rel, path.is_file())

    print("\nArchitecture diagram assets (need at least one architecture_diagram.*):")
    has_diagram = any((ROOT / name).is_file() for name in ARCHITECTURE_ASSETS)
    all_ok &= check("architecture_diagram.* present", has_diagram)
    for name in ARCHITECTURE_ASSETS:
        check(name, (ROOT / name).is_file())

    print("\nSplunk AI integration markers:")
    agent_src = (ROOT / "core/splunk_ai_agent.py").read_text(encoding="utf-8")
    tools_src = (ROOT / "splunk_app/finguard_copilot/bin/tools.py").read_text(encoding="utf-8")
    all_ok &= check("splunklib.ai.Agent", "splunklib.ai" in agent_src and "Agent" in agent_src)
    all_ok &= check("generate_spl local tool", "def generate_spl" in tools_src)
    all_ok &= check("Splunk ingest module", "def ingest" in (ROOT / "data/splunk_ingest.py").read_text(encoding="utf-8"))

    print("\nDisqualification risk checks (official criteria):")
    for label, fn in DISQUALIFICATION_CHECKS:
        all_ok &= check(label, fn())

    print("\nRecommended extras:")
    for rel in OPTIONAL_BUT_RECOMMENDED:
        check(rel, (ROOT / rel).is_file())

    print("\nManual steps (cannot verify from repo):")
    print("  [ ] GitHub repo public with MIT license in About section")
    print("  [ ] Splunk Enterprise running with .env credentials configured")
    print("  [ ] OPENAI_API_KEY set in local .env (not committed)")

    if all_ok:
        print("\nRepository checks passed.")
        return 0

    print("\nSome repository checks failed — fix items marked MISSING.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
