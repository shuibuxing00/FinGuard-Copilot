# Requires Administrator — installs Splunk MCP Server into local Splunk Enterprise
# Usage: Right-click PowerShell -> Run as Administrator, then:
#   cd D:\FinGuard-Copilot
#   .\scripts\install_mcp_admin.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not (Test-Path "$Root\.env")) { $Root = "D:\FinGuard-Copilot" }

$Package = Join-Path $Root "packages\splunk-mcp-server.tgz"
$SplunkBin = "C:\Program Files\Splunk\bin\splunk.exe"

# Load credentials from .env
$envFile = Join-Path $Root ".env"
$SplunkUser = "admin"
$SplunkPass = ""
Get-Content $envFile | ForEach-Object {
    if ($_ -match '^SPLUNK_USERNAME=(.+)$') { $SplunkUser = $matches[1].Trim() }
    if ($_ -match '^SPLUNK_PASSWORD=(.+)$') { $SplunkPass = $matches[1].Trim() }
}

if (-not (Test-Path $Package)) {
    Write-Host "MCP package not found: $Package"
    Write-Host "Download from Splunkbase and save as packages\splunk-mcp-server.tgz"
    Write-Host "URL: https://splunkbase.splunk.com/app/7931/release/1.2.0/download/"
    exit 1
}

if (-not (Test-Path $SplunkBin)) {
    Write-Host "Splunk not found at $SplunkBin"
    exit 1
}

Write-Host "Installing MCP Server from $Package ..."
& $SplunkBin install app $Package -update 1 -auth "${SplunkUser}:$SplunkPass"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Restarting Splunk..."
& $SplunkBin restart

Write-Host "Done. Verify with:"
Write-Host "  py scripts/install_splunk_mcp.py --skip-download --package $Package"
