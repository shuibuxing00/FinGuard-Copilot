FinGuard Compliance Copilot — Full Package
==========================================

This folder is a complete copy and includes:
- Python virtual environment (.venv312)
- Frontend dependencies (frontend/node_modules)
- Portable Node.js (tools/node-portable) — used to run the frontend
- Git history (.git)
- All source code and mock data

Quick Start
-----------

1) Streamlit app (identity verification + data export)
   Double-click: START-STREAMLIT.bat
   After the browser opens, sign in from the sidebar using a demo account.

2) React compliance dashboard
   Double-click: START-FRONTEND.bat
   Open http://localhost:5173 in your browser.

Demo Accounts
-------------
Analyst  — ID: ANA-1001  Passcode: analyst-secure-42
Auditor  — ID: AUD-2002  Passcode: auditor-secure-88
Admin    — ID: ADM-3003  Passcode: admin-secure-99

Notes
-----
- If you move this folder to another PC, run:
  .venv312\Scripts\python.exe -m pip install -r requirements.txt
- You can also start the frontend manually:
  cd frontend && npm run dev (requires Node.js on the system, or use the portable Node in tools/)
