"""
Download and install Splunk MCP Server app (Splunkbase #7931).

Usage:
  set SPLUNKBASE_USERNAME=your_splunkbase_email
  set SPLUNKBASE_PASSWORD=your_splunkbase_password
  py scripts/install_splunk_mcp.py

Or if you already downloaded the package:
  py scripts/install_splunk_mcp.py --package "C:\path\to\splunk-mcp-server.tgz"
"""

import argparse
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
PACKAGES_DIR = ROOT / "packages"
DEFAULT_PACKAGE = PACKAGES_DIR / "splunk-mcp-server.tgz"
SPLUNKBASE_URL = "https://splunkbase.splunk.com"
MCP_APP_ID = 7931

# Common Splunk install paths on Windows
SPLUNK_BIN_CANDIDATES = [
    Path(r"C:\Program Files\Splunk\bin\splunk.exe"),
    Path(r"C:\Splunk\bin\splunk.exe"),
]


def load_dotenv() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def download_mcp_package(dest: Path) -> Path:
    username = os.environ.get("SPLUNKBASE_USERNAME") or os.environ.get("SPLUNK_USERNAME")
    password = os.environ.get("SPLUNKBASE_PASSWORD") or os.environ.get("SPLUNK_PASSWORD")
    if not username or not password:
        raise RuntimeError(
            "Set SPLUNKBASE_USERNAME and SPLUNKBASE_PASSWORD in .env "
            "(Splunkbase login), or pass --package with a local file."
        )

    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading MCP Server from Splunkbase to {dest}...")

    with httpx.Client(follow_redirects=True, timeout=120.0) as client:
        login = client.post(
            f"{SPLUNKBASE_URL}/api/account:login",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"username": username, "password": password},
        )
        login.raise_for_status()
        token = next(
            elem.text for elem in ET.fromstring(login.text) if elem.tag.endswith("id")
        )
        if not token:
            raise RuntimeError("Splunkbase login failed — check SPLUNKBASE credentials.")

        meta = client.get(f"{SPLUNKBASE_URL}/api/v1/app/{MCP_APP_ID}/?include=release")
        meta.raise_for_status()
        release_path = meta.json()["release"]["path"]

        pkg = client.get(release_path, headers={"Authorization": f"Bearer {token}"})
        pkg.raise_for_status()
        dest.write_bytes(pkg.content)

    print(f"Downloaded {len(dest.read_bytes())} bytes.")
    return dest


def find_splunk_bin() -> Path | None:
    for candidate in SPLUNK_BIN_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def install_via_cli(package: Path, splunk_user: str, splunk_pass: str) -> bool:
    splunk_bin = find_splunk_bin()
    if not splunk_bin:
        print("splunk.exe not found — trying REST API install...")
        return False

    cmd = [
        str(splunk_bin),
        "install",
        "app",
        str(package.resolve()),
        "-update",
        "1",
        "-auth",
        f"{splunk_user}:{splunk_pass}",
    ]
    print("Running:", " ".join(cmd[:4]), "...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print("CLI install failed:", result.stderr)
        return False

    restart = subprocess.run(
        [str(splunk_bin), "restart"],
        capture_output=True,
        text=True,
    )
    print(restart.stdout or restart.stderr)
    return restart.returncode == 0


def install_via_rest(package: Path, splunk_user: str, splunk_pass: str) -> bool:
    sys.path.insert(0, str(ROOT))
    from core.splunk_connection import connect_splunk

    service = connect_splunk()
    abs_path = str(package.resolve())
    print(f"Installing via REST API: {abs_path}")

    try:
        service.post(
            path_segment="apps/local",
            name="Splunk_MCP_Server",
            filename=abs_path,
            update=True,
        )
    except Exception as exc:
        print(f"REST install failed: {exc}")
        return False

    print("App uploaded. Restarting Splunk...")
    try:
        service.post(path_segment="server/control/restart", restart=True)
        print("Restart requested — waiting 45s for Splunk to come back...")
        time.sleep(45)
    except Exception as exc:
        print(f"Restart via REST failed: {exc}. Please restart Splunk manually.")
    return True


def verify_mcp() -> bool:
    sys.path.insert(0, str(ROOT))
    import asyncio
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    from core.splunk_connection import connect_splunk
    from core.splunk_mcp_client import SplunkMCPClient

    service = connect_splunk()
    client = SplunkMCPClient(service, os.environ.get("SPLUNK_USERNAME", "admin"))
    ok = asyncio.run(client.initialize())
    print("MCP available:", ok)
    print("MCP tools:", client.tools)
    return ok


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Install Splunk MCP Server")
    parser.add_argument("--package", type=Path, help="Local MCP package path")
    parser.add_argument("--skip-download", action="store_true")
    args = parser.parse_args()

    package = args.package or DEFAULT_PACKAGE
    if not package.exists() and not args.skip_download:
        try:
            package = download_mcp_package(DEFAULT_PACKAGE)
        except Exception as exc:
            print(f"Download failed: {exc}")
            print("Place the downloaded .tgz file at:", DEFAULT_PACKAGE)
            return 1

    if not package.exists():
        print(f"Package not found: {package}")
        return 1

    splunk_user = os.environ.get("SPLUNK_USERNAME", "admin")
    splunk_pass = os.environ.get("SPLUNK_PASSWORD", "")
    if not splunk_pass:
        print("SPLUNK_PASSWORD not set in .env")
        return 1

    installed = install_via_cli(package, splunk_user, splunk_pass)
    if not installed:
        installed = install_via_rest(package, splunk_user, splunk_pass)

    if not installed:
        print("Install failed. Try running PowerShell as Administrator.")
        return 1

    ok = verify_mcp()
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
