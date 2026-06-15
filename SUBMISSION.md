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
| Hackathon-period updates | ✅ | [HACKATHON_UPDATES.md](HACKATHON_UPDATES.md) |
| Splunk AI runtime proof | ✅ | `scripts/prove_splunk_ai_runtime.py` |

Run local verification:

```bash
python scripts/verify_submission.py
python scripts/prove_splunk_ai_runtime.py   # proves Splunk AI at runtime (needs .env + Splunk)
```

---

## Disqualification Self-Check (Official Criteria)

| Risk | Applies to you? | Evidence in this repo |
|------|-----------------|----------------------|
| **Splunk AI not used at runtime** | ❌ No | `core/splunk_ai_agent.py` calls `splunklib.ai.Agent`; Investigation tab only; run `scripts/prove_splunk_ai_runtime.py` |
| **No architecture diagram** | ❌ No | `architecture_diagram.png` + `architecture_diagram.md` at repo root |
| **Not updated during hackathon** | ❌ No | First commit **2026-05-21** (after May 18); see [HACKATHON_UPDATES.md](HACKATHON_UPDATES.md) |
| **No OSI license** | ❌ No | [LICENSE](LICENSE) (MIT) at repo root — confirm visible in GitHub **About** section |
| **Repo not accessible** | ❌ No | Public: https://github.com/shuibuxing00/FinGuard-Copilot (test in incognito) |

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
