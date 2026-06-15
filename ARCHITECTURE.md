# FinGuard Compliance Copilot — Architecture

This document describes how the application interacts with **Splunk**, how **AI agents** are integrated, and the **data flow** across components — as required by the [Splunk Agentic Ops Hackathon](https://splunk.devpost.com/) submission rules.

> **Visual diagram (repo root):** [`architecture_diagram.md`](architecture_diagram.md) · [`architecture.png`](architecture.png) · [`architecture_diagram.png`](architecture_diagram.png)

---

## System Overview

```mermaid
flowchart TB
    subgraph Users
        Analyst[Compliance Analyst]
        Auditor[Senior Auditor]
        Admin[Administrator]
    end

    subgraph Presentation
        ST[Streamlit App<br/>app/streamlit_app.py]
        FE[React Dashboard<br/>frontend/ — optional]
    end

    subgraph Security["Security Layer"]
        Auth[Identity Verification<br/>identity_auth.py]
        RBAC[RBAC Field Filtering<br/>rbac.py]
        Anon[PBKDF2 Pseudonymization<br/>anonymizer.py]
        Guard[LLM Input/Output Guard<br/>llm_guard.py]
        Audit[Hash-Chain Audit Trail<br/>audit_trail.py]
    end

    subgraph Agent["Splunk AI Agent Layer"]
        SAI[splunklib.ai Agent<br/>core/splunk_ai_agent.py]
        OAI[OpenAI GPT-4o-mini<br/>LLM backend]
    end

    subgraph SplunkAI["Splunk AI Tools"]
        LocalTools[Local MCP Tools<br/>splunk_app/.../tools.py]
        MCPServer[Splunk MCP Server<br/>splunk_run_query, etc.]
        AIAsst[Splunk AI Assistant<br/>generate_spl via MCP when enabled]
    end

    subgraph Splunk["Splunk Enterprise"]
        Index[(main index<br/>finguard:* sourcetypes)]
        Ingest[data/splunk_ingest.py]
    end

    Analyst --> ST
    Auditor --> ST
    Admin --> ST
    Analyst --> FE

    ST --> Auth
    Auth --> RBAC
    ST --> SAI
    SAI --> OAI
    SAI --> LocalTools
    SAI --> MCPServer
    MCPServer --> AIAsst
    LocalTools --> Index
    MCPServer --> Index
    Ingest --> Index
    ST --> Guard
    ST --> Audit
```

---

## Splunk Integration

FinGuard uses **real Splunk Enterprise** at runtime (management API port **8089**). Synthetic compliance data is indexed into the `main` index with sourcetypes `finguard:users`, `finguard:transactions`, and `finguard:devices`.

| Layer | File | Role |
|-------|------|------|
| **Connection** | `core/splunk_connection.py` | SDK `connect()`, config from `.env` |
| **Data ingestion** | `data/splunk_ingest.py` | Index synthetic users / transactions / devices at runtime |
| **Splunk AI Agent** | `core/splunk_ai_agent.py` | `splunklib.ai.Agent` agentic investigation loop |
| **Local MCP tools** | `splunk_app/finguard_copilot/bin/tools.py` | `generate_spl`, `run_splunk_query`, profile/txn/device queries |
| **Remote MCP client** | `core/splunk_mcp_client.py` | HTTP MCP to Splunk MCP Server (`splunk_run_query`, …) |
| **Legacy mock path** | `core/splunk_tools.py` | Pandas fallback for dashboard when Splunk unavailable |

```mermaid
sequenceDiagram
    participant UI as Streamlit UI
    participant Agent as splunklib.ai Agent
    participant Local as Local tools.py
    participant MCP as Splunk MCP Server
    participant Splunk as Splunk Enterprise

    UI->>Agent: Investigation query (LLM Guard validated)
    Agent->>Local: get_user_profile(USER_00001)
    Local->>Splunk: SPL search index=main sourcetype=finguard:users
    Splunk-->>Local: JSON results
    Local-->>Agent: User profile
    Agent->>Local: get_recent_transactions(USER_00001)
    Local->>Splunk: SPL search finguard:transactions
    Splunk-->>Local: Transaction events
    Agent->>Local: generate_spl("high risk transactions last 24h")
    Local-->>Agent: Generated SPL
    Agent->>Local: run_splunk_query(SPL)
    opt MCP Server installed
        Agent->>MCP: splunk_run_query(SPL)
        MCP->>Splunk: Execute search
    end
    Agent-->>UI: Risk report + Splunk evidence
```

**Example SPL** (executed via local tools or MCP):

```spl
search index=main sourcetype=finguard:transactions display_user_id="USER_00001" earliest=-24h
| sort - timestamp
| table transaction_id amount timestamp anomaly_type risk_score violation_flags
```

---

## AI Model & Agent Integration

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Orchestration** | `splunklib.ai.Agent` (Splunk SDK 3.0) | Agentic loop: plan → Splunk tool call → observe → answer |
| **LLM backend** | OpenAI `gpt-4o-mini` via `OpenAIModel` | Reasoning and report generation |
| **NL → SPL** | Local `generate_spl` tool + optional MCP `generate_spl` | Natural language to SPL for compliance queries |
| **Splunk queries** | Local + MCP `run_splunk_query` / `splunk_run_query` | Execute SPL on indexed finguard data |
| **Safety** | `LLMGuard` | Blocks prompt injection; sanitizes output; adds disclaimer |

```mermaid
flowchart LR
    Q[User Question] --> V{LLM Guard validate}
    V -->|reject| E[Error to UI]
    V -->|ok| A[splunklib.ai Agent]
    A --> T1[get_user_profile]
    A --> T2[get_recent_transactions]
    A --> T3[get_device_history]
    A --> T4[generate_spl]
    A --> T5[run_splunk_query]
    T1 & T2 & T3 & T4 & T5 --> Splunk[Splunk Enterprise]
    A --> M[OpenAI API]
    M --> S{LLM Guard sanitize}
    S --> R[Investigation Report]
```

**Note:** The Investigation tab requires `OPENAI_API_KEY` and a running Splunk instance with credentials in `.env`.

---

## Data Flow Summary

| Step | Data | Transformation |
|------|------|----------------|
| 1 | Sidebar: Load & Index to Splunk | `generate.py` → `splunk_ingest.py` → Splunk `main` index |
| 2 | User chat input | `LLMGuard.validate_input()` |
| 3 | Agent tool calls | SPL against real Splunk indexes (not in-memory mock) |
| 4 | Results | Optional audit entries; RBAC applies to dashboard/export tabs |
| 5 | Agent report | `LLMGuard.sanitize_output()` → UI with reasoning steps |
| 6 | React frontend (optional) | Reads `frontend/mock/transactions.json` for demo dashboard |

---

## Repository Layout (runtime)

```
app/streamlit_app.py              → Entry point (auth, tabs, Splunk AI investigation)
core/splunk_ai_agent.py           → splunklib.ai Agent wrapper
core/splunk_mcp_client.py         → Splunk MCP Server HTTP client
core/splunk_connection.py         → Splunk SDK connection
data/splunk_ingest.py             → Index synthetic data to Splunk
splunk_app/finguard_copilot/      → Local MCP tools for splunklib.ai
security/*                        → Auth, RBAC, anonymizer, LLM guard
ui/*                              → Dashboards, auth panel, data export
```

---

## Deployment

| Component | Required for Investigation | Notes |
|-----------|---------------------------|-------|
| Splunk Enterprise | Yes | Port 8089, credentials in `.env` |
| Splunk MCP Server app | Recommended | Enables remote `splunk_run_query`; local tools work without it |
| OpenAI API key | Yes | Powers `splunklib.ai` LLM backend |
| ChromaDB / LangChain | No | Legacy optional path in `core/agent.py` |

See [README.md](README.md) and [scripts/INSTALL_SPLUNK_MCP.md](scripts/INSTALL_SPLUNK_MCP.md) for setup.
