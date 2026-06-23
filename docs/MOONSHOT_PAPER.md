# Beyond Rule Engines — Moonshot Paper (Editable Canonical)

**Full PDF:** [`FinGuard_Beyond_Rule_Engines.pdf`](../FinGuard_Beyond_Rule_Engines.pdf)  
**Author:** Wang Manye · Faculty of Economics, FinTech Programme · June 2026

This document is the **editable canonical** for Moonshot submission. Sections 1–4, 6–8 match the PDF. **Section 5 and 5.4** are updated to align with the current reference implementation (`splunklib.ai.Agent` + Demo Mode fallback).

---

## Abstract

Compliance is widely treated as a staffing problem. We argue the crisis is an **information-architecture problem**: analysts spend ten minutes per alert integrating evidence across disconnected systems. We propose an AI-native compliance copilot in which a reasoning agent orchestrates retrieval from a unified evidence substrate, executes an auditable plan over pseudonymized data, and emits a cryptographically verifiable decision record — resting on four axioms and six engineering pillars instantiated in **FinGuard**.

---

## 1. The Misunderstood Crisis

*(See PDF Sections 1.1–1.2 — unchanged.)*

- Compliance is not a people-and-rules problem; the bottleneck is cross-system evidence integration.
- Fatigue, un-auditable judgments, and the paperwork façade are architectural consequences.
- Synthetic evaluation: 500 transactions, 9 alerts ≥ risk 70 (1.8% irreducible signal rate).

---

## 2. The Architectural Flaw in Existing Solutions

*(See PDF Sections 2.1–2.2 — unchanged.)*

Four generations — rule engines, statistical scoring, data centralization, LLM copilots — each preserved the fragmented evidence layer.

---

## 3. First Principles: Four Axioms

*(See PDF Section 3 — unchanged.)*

1. Information architecture precedes decision quality  
2. Auditability is a substrate, not a feature  
3. Privacy is not in tension with utility  
4. AI agents must operate over a bounded action space  

---

## 4. Scientific and Technical Foundations

*(See PDF Section 4 — unchanged.)*

Six pillars: ReAct tool-using agents, RAG over regulatory corpora, hash-chained audit ledgers, PBKDF2 pseudonymization, RBAC/ABAC, prompt-injection guards.

---

## 5. From Principles to Practice: The FinGuard Reference Architecture

The four axioms and six pillars are necessary but not sufficient. Integration choices determine whether the system is real or aspirational. FinGuard is a concrete reference implementation tested against synthetic but representative data (500 transactions, seed=42).

### 5.1 The Evidence Substrate

FinGuard normalizes four data classes — customer KYC profiles, transaction records, device fingerprints, and regulatory text — into a **single queryable substrate**.

**Production deployment:** Splunk Enterprise `main` index with sourcetypes `finguard:users`, `finguard:transactions`, `finguard:devices`. Runtime ingestion via `data/splunk_ingest.py` writes pseudonymized events at demo and evaluation time.

**Demo deployment:** In-memory pandas store via `core/splunk_tools.py` — same schema, no external infrastructure.

Customer identifiers in the substrate are **PBKDF2-HMAC-SHA256 pseudonyms** (salt per deployment, 100,000 iterations). Human-readable `display_user_id` values (e.g. `USER_00001`) map to pseudonyms for analyst queries while the agent's join keys remain irreversible tokens.

Raw PII is held in a separate access-controlled tier reached only via typed retrieval tools whose invocation is checked against the calling role (Axiom 3).

### 5.2 The Reasoning Loop

An investigation begins when an authenticated analyst enters a natural-language question in the Streamlit interface (`app/streamlit_app.py`).

**Primary path — Splunk AI Agent (`core/splunk_ai_agent.py`):**

- Uses `splunklib.ai.Agent` (Splunk Python SDK 3.0) with OpenAI `gpt-4o-mini` backend
- Operates over a **published tool registry**:
  - Local MCP tools: `get_user_profile`, `get_recent_transactions`, `get_device_history`, `run_splunk_query`, `generate_spl`
  - Remote Splunk MCP Server tools when installed: `splunk_run_query`, metadata tools
- Each tool invocation is logged to the hash-chain audit ledger before execution
- LLM input validated and output sanitized via `security/llm_guard.py`
- Terminates with structured report: risk score, anomalies, compliance basis, recommended human review

**Fallback path — LangChain ReAct Agent (`core/agent.py`):**

- Activated in **Demo Mode** (`FINGUARD_DEMO_MODE=1`) or when Splunk is unavailable
- Same four-tool registry semantics: profile, transactions, devices, regulation retrieval
- Regulation retrieval via `core/rag_tools.py` (ChromaDB vector index or keyword fallback over `data/compliance_laws/`)
- Implements the ReAct pattern described in Section 4.1; tool calls remain the load-bearing audit record

Both paths enforce the same security envelope: identity auth, RBAC field filtering, pseudonymization, hash-chain logging.

### 5.3 Security and Audit Envelope

| Layer | Module | Axiom |
|-------|--------|-------|
| Identity verification | `security/identity_auth.py` | Bounded action (who may invoke) |
| Field-level RBAC | `security/rbac.py` | Privacy + bounded action |
| PBKDF2 pseudonymization | `security/anonymizer.py` | Axiom 3 |
| LLM input/output guard | `security/llm_guard.py` | Axiom 4 |
| Hash-chain audit trail | `core/audit_trail.py` | Axiom 2 |

Every state transition — data load, tool call, export, investigation — appends to the SHA256-chained ledger. Integrity verification is exposed in the Audit tab and available to external regulators offline.

### 5.4 Deployment Modes

| Mode | Evidence Substrate | Reasoning Agent | Requirements |
|------|-------------------|-----------------|--------------|
| **Full** | Splunk Enterprise index | `splunklib.ai.Agent` + MCP | Splunk :8089, `OPENAI_API_KEY` |
| **Demo** | In-memory mock | LangChain ReAct + keyword RAG | `OPENAI_API_KEY` only |

Demo Mode exists so evaluators can verify the axioms compose into a working system **without** provisioning Splunk. The Full path demonstrates production-grade integration with Splunk AI capabilities at runtime.

**Evaluation result:** Manual baseline ~600 s per non-trivial alert (median at tier-1 retail banks); agent path ~10 s wall-clock on synthetic dataset with GPT-4o-mini; human fallback path ~90 s when agent confidence is low. See `docs/figures/fig3_time_compression.png`.

---

## 6. Long-Term Impact: Four Structural Transformations

*(See PDF Section 6 — unchanged.)*

1. Compliance as design constraint  
2. Auditor as systems auditor  
3. Cross-border compliance tractable  
4. Symmetry of information between regulator and institution  

---

## 7. The Future: Compliance as a Public Good

*(See PDF Section 7 — unchanged.)*

Shared regulatory corpus, tool registry, and audit pattern — marginal cost of adding an institution approaches pseudonymization salt cost.

---

## 8. Conclusion

The compliance industry approaches an architectural inflection point. FinGuard demonstrates that four axioms compose into a working, verifiable system. The choice is between a deliberate transition built on first principles and an accidental one built on whichever model ships first.

---

## Figures (Generated from Codebase)

| Figure | File |
|--------|------|
| Fig 1 — Risk distribution | `docs/figures/fig1_risk_distribution.png` |
| Fig 2 — Rule triggers | `docs/figures/fig2_rule_triggers.png` |
| Fig 3 — Time compression | `docs/figures/fig3_time_compression.png` |
| Fig 4 — Anomaly composition | `docs/figures/fig4_anomaly_composition.png` |
| Fig 5 — Audit ledger growth | `docs/figures/fig5_audit_ledger_growth.png` |
| Fig 6 — PBKDF2 cost curve | `docs/figures/fig6_pbkdf2_cost_curve.png` |

Regenerate: `python scripts/generate_paper_figures.py`

---

## References

See PDF pages 25–27 for full bibliography (FATF, FinCEN, Lewis et al. 2020 RAG, Yao et al. 2022 ReAct, NIST SP 800-132/162, OWASP LLM Top 10, etc.).
