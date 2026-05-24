# FinGuard Compliance Copilot — Architecture

This document describes how the application interacts with **Splunk**, how **AI agents** are integrated, and the **data flow** across components.

> **Visual diagram (repo root):** [`architecture.svg`](architecture.svg)  
> GitHub also renders the Mermaid diagrams below.

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
        FE[React Dashboard<br/>frontend/]
    end

    subgraph Security["Security Layer"]
        Auth[Identity Verification<br/>identity_auth.py]
        RBAC[RBAC Field Filtering<br/>rbac.py]
        Anon[PBKDF2 Pseudonymization<br/>anonymizer.py]
        Guard[LLM Input/Output Guard<br/>llm_guard.py]
        Audit[Hash-Chain Audit Trail<br/>audit_trail.py]
    end

    subgraph Agent["AI Agent Layer"]
        LC[LangChain ReAct Agent<br/>agent.py]
        OAI[OpenAI GPT-4o-mini API]
    end

    subgraph Data["Data & Knowledge"]
        Splunk[Splunk Tools Interface<br/>splunk_tools.py]
        Mock[(In-Memory Mock Splunk<br/>users / txns / devices)]
        RAG[Compliance RAG<br/>rag_tools.py]
        Laws[(Regulation Corpus<br/>data/compliance_laws/*.txt)]
        Synth[(Synthetic Generator<br/>data/generate.py)]
    end

    Analyst --> ST
    Auditor --> ST
    Admin --> ST
    Analyst --> FE

    ST --> Auth
    Auth --> RBAC
    ST --> Splunk
    ST --> LC
    LC --> OAI
    LC --> Splunk
    LC --> RAG
    RAG --> Laws

    Splunk --> Anon
    Splunk --> RBAC
    Splunk --> Audit
    Splunk --> Mock
    Synth --> Mock

    LC --> Guard
    ST --> Guard
    ST --> Audit
```

---

## Splunk Integration

The project targets the **Splunk Agentic Ops** use case. Production deployments connect to Splunk Enterprise/Cloud via the Splunk SDK; this repository ships a **mock Splunk layer** so judges and developers can run everything locally without a Splunk cluster.

| Layer | File | Role |
|-------|------|------|
| **Splunk API (production path)** | `splunk-sdk` in `requirements.txt` | Official SDK for real `connect()`, `jobs.create()`, `results()` |
| **Agentic tool wrapper** | `core/splunk_tools.py` | Exposes `get_user_profile`, `get_recent_transactions`, `get_device_history`, `search_transactions` |
| **Mock data store** | In-memory Pandas DataFrames | Loaded from `data/generate.py` or CSV; simulates Splunk indexes `users`, `transactions`, `devices` |
| **Security on every query** | `splunk_tools._audit_and_filter()` | Pseudonymize → query → hash result → audit log → RBAC filter |

```mermaid
sequenceDiagram
    participant UI as Streamlit UI
    participant Agent as Investigation Agent
    participant ST as SplunkTools
    participant Sec as Security Layer
    participant Mock as Mock Splunk Indexes

    UI->>Agent: User query (validated by LLM Guard)
    Agent->>ST: get_recent_transactions(user_id)
    ST->>Sec: pseudonymize(user_id)
    ST->>Mock: Query transactions DataFrame
    Mock-->>ST: Raw records
    ST->>Sec: SHA256 hash + audit_trail.add_entry()
    ST->>Sec: RBAC.filter_record() per role
    ST-->>Agent: Filtered fields only
    Agent->>ST: search_compliance(anomaly_type)
    Agent-->>UI: Report + reasoning steps
```

**Mapping to real Splunk:** Replace `load_mock_data()` with SDK calls that run SPL such as:

```spl
index=transactions user_id=$pseudonym$ earliest=-24h
| table amount, timestamp, risk_score, anomaly_type
```

---

## AI Model & Agent Integration

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Orchestration** | LangChain ReAct | Multi-step reasoning: plan → tool call → observe → answer |
| **Model** | OpenAI `gpt-4o-mini` | Natural-language investigation reports |
| **Tools (4)** | Wrapped `SplunkTools` + `ComplianceRAG` | Structured data access, not raw SQL/SPL in the prompt |
| **RAG** | ChromaDB (optional) or keyword fallback | Retrieve AML / PIPL / reporting clauses |
| **Safety** | `LLMGuard` | Blocks prompt injection; sanitizes output; adds disclaimer |

```mermaid
flowchart LR
    Q[User Question] --> V{LLM Guard<br/>validate_input}
    V -->|reject| E[Error to UI]
    V -->|ok| A[ReAct Agent]
    A --> T1[get_user_profile]
    A --> T2[get_recent_transactions]
    A --> T3[get_device_history]
    A --> T4[search_compliance]
    T1 & T2 & T3 --> Splunk[SplunkTools]
    T4 --> RAG[ComplianceRAG]
    A --> M[OpenAI API]
    M --> S{LLM Guard<br/>sanitize_output}
    S --> R[Investigation Report]
```

**Note:** The Investigation tab requires `OPENAI_API_KEY`. Dashboard, Data Output, and Audit tabs run without it.

---

## Data Flow Summary

| Step | Data | Transformation |
|------|------|----------------|
| 1 | Raw user ID in chat | Validated, never sent to model if PII pattern detected |
| 2 | Query to Splunk tool | `Anonymizer.pseudonymize()` → irreversible token |
| 3 | Mock index lookup | Pandas filter on `users_df` / `transactions_df` / `devices_df` |
| 4 | Result | SHA256 chained into `.audit_chain.json` |
| 5 | Response to UI | Columns removed per RBAC role (analyst / auditor / admin) |
| 6 | Export (Data Output tab) | CSV manifest with visible fields only |
| 7 | React frontend | Reads `frontend/mock/transactions.json`; client-side RBAC demo |

---

## Repository Layout (runtime)

```
app/streamlit_app.py     → Entry point (auth, tabs, orchestration)
core/splunk_tools.py     → Splunk-shaped API + audit + RBAC
core/agent.py            → LangChain agent (optional)
core/rag_tools.py        → Regulation retrieval
core/audit_trail.py      → Tamper-evident log
security/*               → Auth, RBAC, anonymizer, LLM guard
ui/*                     → Dashboards, auth panel, data export
data/generate.py         → Synthetic dataset builder
data/compliance_laws/    → Example regulation text corpus
frontend/                → Optional React compliance dashboard
```

---

## Deployment Modes

| Mode | Splunk | OpenAI | ChromaDB |
|------|--------|--------|----------|
| **Demo (default)** | Mock in-memory | Optional | Keyword fallback |
| **Production** | Splunk SDK + SPL | Required | Chroma or enterprise vector DB |

See [README.md](README.md) for setup commands.
