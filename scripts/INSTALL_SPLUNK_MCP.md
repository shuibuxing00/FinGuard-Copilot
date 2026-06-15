# Install Splunk MCP Server for generate_spl AI capability

FinGuard uses Splunk MCP Server's `generate_spl` tool (Splunk AI Assistant) when available.

## Steps

1. **Download** Splunk MCP Server from Splunkbase:
   https://splunkbase.splunk.com/app/7931

2. **Install** (run as Administrator on Windows):
   ```powershell
   & "C:\Program Files\Splunk\bin\splunk.exe" install app <path-to-mcp-server.tar.gz> -update 1 -auth shuibuxing00:<password>
   & "C:\Program Files\Splunk\bin\splunk.exe" restart
   ```

3. **Configure RBAC** — add to `authorize.conf` or via Splunk UI:
   ```ini
   [role_mcp_user]
   mcp_tool_admin = enabled
   mcp_tool_execute = enabled
   ```

4. **Assign role** to your Splunk user (`shuibuxing00`).

5. **Verify** MCP endpoint:
   ```powershell
   curl -k -u shuibuxing00:<password> https://localhost:8089/services/mcp
   ```
   Should NOT return 404.

6. **Optional**: Install FinGuard Splunk app for in-Splunk deployment:
   ```powershell
   Copy-Item -Recurse splunk_app\finguard_copilot "C:\Program Files\Splunk\etc\apps\finguard_copilot"
   & "C:\Program Files\Splunk\bin\splunk.exe" restart
   ```

## Verify from Python

```python
from core.splunk_connection import connect_splunk
from core.splunk_mcp_client import SplunkMCPClient
import asyncio

service = connect_splunk()
client = SplunkMCPClient(service, "shuibuxing00")
ok = asyncio.run(client.initialize())
print("MCP available:", ok, "tools:", client.tools)
```
