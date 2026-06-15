"""Install MCP via Splunk REST using local package path."""
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")


def main():
    package = ROOT / "packages" / "splunk-mcp-server.tgz"
    if not package.exists():
        print(f"Package missing: {package}")
        print("Save your downloaded MCP file to that path first.")
        return 1

    from core.splunk_connection import connect_splunk

    service = connect_splunk()
    path = str(package.resolve())
    print(f"Installing from {path} ({package.stat().st_size} bytes)...")

    try:
        # Splunk REST: name = path to .tgz on server, filename=true
        service.post(
            path_segment="apps/local",
            name=str(package.resolve()),
            filename=True,
            update=True,
        )
        print("Install POST succeeded.")
    except Exception as exc:
        print(f"Install failed: {exc}")
        return 1

    try:
        service.post(path_segment="server/control/restart", restart=True)
        print("Restarting Splunk (wait ~60s)...")
        time.sleep(60)
    except Exception as exc:
        print(f"Restart failed: {exc}")

    import asyncio
    from core.splunk_mcp_client import SplunkMCPClient

    client = SplunkMCPClient(service, os.environ.get("SPLUNK_USERNAME", "admin"))
    ok = asyncio.run(client.initialize())
    print("MCP OK:", ok, "tools:", client.tools)
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
