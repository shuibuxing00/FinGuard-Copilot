# Splunk Agentic Ops Hackathon — Submission Guide

**Project:** FinGuard Compliance Copilot  
**Track:** Security  
**Repo:** https://github.com/shuibuxing00/FinGuard-Copilot  
**Devpost:** https://splunk.devpost.com/

---

## Submission Checklist

| Requirement | Status | Notes |
|-------------|--------|-------|
| Public open-source repo | ✅ | MIT [LICENSE](LICENSE) |
| README with setup & run | ✅ | [README.md](README.md) |
| Dependencies & example config | ✅ | `requirements.txt`, [.env.example](.env.example) |
| Example datasets | ✅ | `data/compliance_laws/`, synthetic generator |
| Architecture diagram at repo root | ✅ | [architecture_diagram.md](architecture_diagram.md), [architecture_diagram.png](architecture_diagram.png) |
| Splunk AI at runtime | ✅ | `splunklib.ai.Agent` + MCP + indexed Splunk data |
| Demo video (<3 min) | ⬜ **You** | Script below — record & upload to YouTube |
| Devpost form submitted | ⬜ **You** | Before **Jun 15, 2026 9:00 AM PDT** |

Run local verification:

```bash
python scripts/verify_submission.py
```

---

## Devpost Form — Suggested Text (English)

**Project name:** FinGuard Compliance Copilot

**Tagline:** AI-powered suspicious transaction investigation for compliance teams — Security track.

**Problem:** Compliance analysts spend 10+ minutes manually correlating user profiles, transactions, and device logs across siloed tools.

**Solution:** FinGuard uses **Splunk AI** (`splunklib.ai.Agent`) to autonomously query indexed compliance data in Splunk, generate SPL from natural language, and produce auditable investigation reports with RBAC and tamper-proof audit trails.

**Splunk AI capabilities used:**
- `splunklib.ai.Agent` (Splunk Python SDK 3.0) — agentic investigation loop
- Splunk MCP Server — `splunk_run_query`, metadata tools
- Local MCP tools — `generate_spl`, `run_splunk_query`, profile/transaction/device queries
- Real indexed data — `data/splunk_ingest.py` writes to Splunk `main` index

**How to run (judges):**
1. Install Splunk Enterprise + configure `.env` from `.env.example`
2. `pip install -r requirements.txt`
3. `streamlit run app/streamlit_app.py`
4. Sign in (Analyst: `ANA-1001` / `analyst-secure-42`)
5. Click **Load & Index to Splunk**
6. Open **Investigation** tab and ask: *Investigate user USER_00001*

---

## Demo Video Script (~2:30, English)

Record screen + voiceover. Show Streamlit on localhost.

| Time | Scene | Narration |
|------|-------|-----------|
| 0:00–0:20 | Title slide + problem | "Compliance teams waste minutes triaging suspicious transactions. FinGuard cuts review time using Splunk AI." |
| 0:20–0:40 | Sign in as Analyst | "Analysts authenticate with verified employee credentials — no arbitrary role switching." |
| 0:40–1:00 | Click **Load & Index to Splunk** | "Synthetic compliance data is indexed into Splunk in real time — users, transactions, and devices." |
| 1:00–1:30 | Dashboard tab | "Risk metrics and fund-flow views give context before deep investigation." |
| 1:30–2:10 | Investigation tab — ask *Investigate USER_00001* | "The Splunk AI agent uses splunklib.ai to call Splunk tools — profile, transactions, generate_spl, and run_splunk_query — against live indexed data." Expand **Splunk AI Investigation Steps**. |
| 2:10–2:30 | Audit tab + architecture.png in repo | "Every action is auditable. Architecture shows Splunk, AI agents, and data flow. FinGuard — Security track, Splunk Agentic Ops Hackathon." |

**Upload:** YouTube or Vimeo (public). Paste URL into Devpost.

---

## GitHub About Section

In repo **Settings → General → Social preview**, set:
- **License:** MIT (should auto-detect from LICENSE file)

---

## Pre-submission Commands

```bash
# Verify repo structure
python scripts/verify_submission.py

# Regenerate architecture PNGs (optional)
python scripts/generate_architecture.py
```

*Synthetic data only — no real customer information.*
