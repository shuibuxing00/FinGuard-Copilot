# Hackathon Updates (May 18, 2026 — Submission Period)

This document explains **what is new** during the [Splunk Agentic Ops Hackathon](https://splunk.devpost.com/) submission period, for judges reviewing eligibility under the *“substantially updated”* rule.

---

## Timeline

| Date | Commit | What changed |
|------|--------|--------------|
| **2026-05-21** | `7488300` | Initial project scaffold (after hackathon start May 18) |
| **2026-05-24** | `34ee1e9`–`132c1e9` | Identity auth, RBAC export, React frontend, open-source docs, root architecture diagram |
| **2026-06-15** | `18c2312` | **Splunk AI integration** — `splunklib.ai.Agent`, MCP client, real Splunk data ingest |
| **2026-06-15** | `fee721e` | Local `generate_spl`, `architecture_diagram.png`, submission guide |

**First commit:** May 21, 2026 (on or after May 18, 2026 hackathon start).

---

## Major additions during hackathon (not pre-existing)

### Splunk AI at runtime (primary investigation path)

| Component | File | Splunk AI capability |
|-----------|------|---------------------|
| Agentic loop | `core/splunk_ai_agent.py` | `splunklib.ai.Agent` + `OpenAIModel` |
| Local MCP tools | `splunk_app/finguard_copilot/bin/tools.py` | `splunklib.ai.registry.ToolRegistry` |
| MCP Server client | `core/splunk_mcp_client.py` | HTTP MCP → `splunk_run_query`, etc. |
| Splunk connection | `core/splunk_connection.py` | Splunk SDK management API (8089) |
| Data indexing | `data/splunk_ingest.py` | Real events → Splunk `main` index |

The **Investigation** tab in `app/streamlit_app.py` calls `SplunkInvestigationAgent` only — not the legacy LangChain/mock path.

### Architecture diagram (repo root)

- `architecture_diagram.png` — visual diagram (hackathon-required filename)
- `architecture_diagram.md` — diagram + Mermaid data-flow
- `architecture.png` / `architecture.svg` — additional assets

### Open source & documentation

- `LICENSE` — MIT (OSI-approved)
- `README.md`, `ARCHITECTURE.md`, `SUBMISSION.md`
- `scripts/prove_splunk_ai_runtime.py` — runtime verification for judges

---

## What is NOT the Splunk AI demo path

| Component | Purpose |
|-----------|---------|
| `core/splunk_tools.py` | Legacy in-memory mock for dashboard fallback when Splunk is offline |
| `core/agent.py` | Legacy LangChain agent — **not used** by Streamlit Investigation tab |

Judges should use the **Investigation** tab after **Load & Index to Splunk** to see Splunk AI in action.

---

## Verify locally

```bash
python scripts/verify_submission.py
python scripts/prove_splunk_ai_runtime.py   # requires .env + running Splunk
```

---

## Commit history

```bash
git log --oneline --since="2026-05-18"
```
