import os
from pathlib import Path

roots = [
    Path(os.path.expanduser("~/.splunk")),
    Path(os.path.expanduser("~/Documents")),
    Path(os.path.expanduser("~/OneDrive")),
    Path("D:/FinGuard-Copilot"),
]
for root in roots:
    if not root.exists():
        continue
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in (".tgz", ".gz", ".spl", ".zip", ".tar"):
            continue
        n = p.name.lower()
        if any(k in n for k in ("mcp", "splunk", "7931")):
            print(p.stat().st_size, p)
