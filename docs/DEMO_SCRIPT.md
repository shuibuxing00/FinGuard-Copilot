# FinGuard — 5-Minute Live Demo Script

Use this script for Moonshot Vision Presentation or judge walkthrough.

**Duration:** ~5 minutes  
**Modes:** Demo Mode (no Splunk) or Full Path (Splunk AI)

---

## Before You Start

```bash
streamlit run app/streamlit_app.py
# Demo Mode: set FINGUARD_DEMO_MODE=1 or toggle in sidebar
```

| Role | Employee ID | Passcode |
|------|-------------|----------|
| Analyst (L1) | `ANA-1001` | `analyst-secure-42` |
| Auditor (L2) | `AUD-2002` | `auditor-secure-88` |
| Admin (L3) | `ADM-3003` | `admin-secure-99` |

---

## Minute 0:00 — Frame the Problem (spoken, not in app)

> "Compliance is framed as a staffing problem — hire more analysts, add more rules.  
> The real bottleneck is **integrating evidence** across KYC, transactions, devices, and regulations.  
> FinGuard re-architects that integration step."

---

## Minute 0:30 — Identity Verification

1. Open **http://localhost:8501**
2. Sidebar → enter **Analyst** credentials (`ANA-1001` / `analyst-secure-42`)
3. **Say:** "Roles cannot be switched without verified credentials — no arbitrary role dropdown."

---

## Minute 1:00 — Load Data

### Demo Mode (recommended for live presentation)

1. Enable **Demo Mode** in sidebar
2. Click **Load Synthetic Data**
3. **Say:** "500 synthetic transactions, seed=42 — same dataset as the paper. No Splunk required."

### Full Path

1. Click **Load & Index to Splunk**
2. **Say:** "Evidence substrate: Splunk `main` index with users, transactions, devices."

---

## Minute 1:30 — Dashboard (Tab 1)

1. Open **Dashboard** tab
2. Point to risk metrics and fund-flow graph
3. **Say:** "Only **1.8%** of transactions cross the escalation threshold — the signal is rare; sustained human attention on the other 98% is structurally unsustainable."

---

## Minute 2:30 — Investigation (Tab 3)

1. Open **Investigation** tab
2. Confirm banner:
   - Demo Mode: `LangChain ReAct Agent · Demo Mode`
   - Full Path: `Splunk AI active · splunklib.ai Agent`
3. Type: **`Investigate user USER_00001`**
4. Wait for response (~10–30 seconds)
5. Expand **Investigation Steps** / **Splunk AI Capabilities Used**
6. **Say:** "The agent plans tool calls over a bounded registry — profile, transactions, devices, regulations. Every call is logged to the hash chain."

**Backup queries if first query is slow:**

- `Review high-risk transactions for USER_00003`
- `Check device anomalies for USER_00001`

---

## Minute 3:30 — Audit (Tab 4)

1. Open **Audit** tab
2. Show **Total Entries** increased after investigation
3. Show **Status: OK — INTACT**
4. **Say:** "Auditability is a substrate, not a feature. The regulator gets a trial transcript, not just a verdict."

---

## Minute 4:00 — RBAC Contrast (Tab 2)

1. Open **Data Output** tab — note visible columns for Analyst
2. Sidebar → sign out → sign in as **Auditor** (`AUD-2002` / `auditor-secure-88`)
3. Return to **Data Output** — more fields visible
4. **Say:** "Privacy and utility are not in tension — pseudonyms for the agent, real fields only when role permits."

---

## Minute 4:30 — Close

> "This is not a faster rule engine. It is a blueprint for compliance as verifiable infrastructure —  
> the same architectural pattern that could make cross-border supervision tractable and compliance a public good.  
> Paper: `FinGuard_Beyond_Rule_Engines.pdf`. Code: open source, MIT."

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Investigation tab blocked | Enable Demo Mode + Load Synthetic Data |
| OpenAI error | Set `OPENAI_API_KEY` in `.env` |
| Splunk connection failed | Use Demo Mode; Full Path needs Splunk on port 8089 |
| LangChain import error | `pip install langchain langchain-openai openai` |
| Empty investigation response | Retry with `Investigate user USER_00001` |

---

## Deployment Modes Summary

| Mode | Evidence Substrate | Agent | When to Use |
|------|-------------------|-------|-------------|
| **Demo** | In-memory mock | LangChain ReAct + keyword RAG | Moonshot live demo, no Splunk |
| **Full** | Splunk Enterprise index | `splunklib.ai.Agent` + MCP tools | Production-like evaluation |

Both modes enforce the same four axioms: RBAC, pseudonymization, LLM guard, hash-chain audit.
