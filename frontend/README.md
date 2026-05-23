# FinGuard Compliance Frontend

Deliverables for mock data, AML rules, RBAC table, fund flow graph, case export, and stats cards.

## Quick Start (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — full dashboard with all 6 features integrated.

## File Map

| Item | Path |
|------|------|
| 1️⃣ Synthetic JSON (30 txns) | `mock/transactions.json` |
| 2️⃣ AML rules | `mock/aml-rules.json`, `docs/AML_RULES.md` |
| 3️⃣ RBAC role table | `src/components/RoleTransactionTable.jsx` |
| 4️⃣ Fund flow (ECharts) | `src/components/FundFlowGraph.jsx`, `demos/fund-flow-echarts.html` |
| 5️⃣ Case export | `src/components/ExportCaseSummary.jsx`, `src/utils/exportCaseSummary.js` |
| 6️⃣ Stats cards | `src/components/StatsCards.jsx`, `demos/stats-cards-standalone.html` |

## Standalone Demos (no build)

- Fund flow: open `demos/fund-flow-echarts.html` in a browser
- Stats cards: serve folder and open `demos/stats-cards-standalone.html` (needs local server for JSON fetch)

```bash
npx serve .
```

## Mock Data Summary

- **30** transaction records
- **6** high-risk (`risk_score >= 80`, 20%)
- **anomaly_type**: `short_time_high_freq`, `new_device`, `location_mismatch`, `amount_peak`
- Anomalous rows include `risk_explanation` (one sentence)

## Demo Credentials (Streamlit app)

See main project `app/streamlit_app.py` for identity-verified roles.
