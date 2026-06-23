# FinGuard — Moonshot Submission

**Project:** FinGuard Compliance Copilot  
**Thesis:** Compliance is an **information-architecture problem**, not a staffing problem.  
**Repo:** https://github.com/shuibuxing00/FinGuard-Copilot

---

## Moonshot Submission Checklist

| Deliverable | Status | Location |
|-------------|--------|----------|
| **Prototype / Demo** | ✅ | [`app/streamlit_app.py`](app/streamlit_app.py) — Demo Mode works without Splunk |
| **Moonshot Paper** | ✅ | [`FinGuard_Beyond_Rule_Engines.pdf`](FinGuard_Beyond_Rule_Engines.pdf) |
| **Paper (editable)** | ✅ | [`docs/MOONSHOT_PAPER.md`](docs/MOONSHOT_PAPER.md) — Section 5 aligned with code |
| **Vision Presentation** | ✅ | [`docs/MOONSHOT_PRESENTATION.md`](docs/MOONSHOT_PRESENTATION.md) → export PDF |
| **Demo Script** | ✅ | [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) |
| **Problem & Solution** | ✅ | [`docs/PROBLEM_AND_SOLUTION.md`](docs/PROBLEM_AND_SOLUTION.md) |
| **Paper Figures** | ✅ | [`docs/figures/`](docs/figures/) — run `python scripts/generate_paper_figures.py` |

---

## Quick Start (Judges & Reviewers)

### Option A — Demo Mode (no Splunk required)

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements-minimal.txt
pip install langchain langchain-openai openai   # for Investigation fallback

cp .env.example .env
# Set OPENAI_API_KEY only (Splunk optional)

set FINGUARD_DEMO_MODE=1          # Windows CMD
# $env:FINGUARD_DEMO_MODE="1"     # PowerShell

streamlit run app/streamlit_app.py
```

1. Sign in: Analyst `ANA-1001` / `analyst-secure-42`
2. Sidebar: enable **Demo Mode**, click **Load Synthetic Data**
3. Open **Investigation** tab → ask: *Investigate user USER_00001*
4. Open **Audit** tab → verify hash-chain integrity

### Option B — Full Path (Splunk AI)

Requires Splunk Enterprise (port **8089**) + `OPENAI_API_KEY`.

```bash
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

Click **Load & Index to Splunk**, then use **Investigation** with `splunklib.ai.Agent`.

See [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) for a 5-minute walkthrough.

---

## What We Submit

### 1. Prototype

FinGuard is a **reference architecture** for verifiable, privacy-preserving compliance agents — not an incremental AML dashboard.

| Axiom | Implementation |
|-------|----------------|
| Information architecture precedes decision quality | Unified evidence substrate (Splunk index / in-memory mock) |
| Auditability is a substrate | SHA256 hash-chain ([`core/audit_trail.py`](core/audit_trail.py)) |
| Privacy is not in tension with utility | PBKDF2 pseudonymization ([`security/anonymizer.py`](security/anonymizer.py)) |
| Bounded action space | RBAC + LLM Guard + tool registry ([`security/`](security/), [`core/splunk_ai_agent.py`](core/splunk_ai_agent.py)) |

### 2. Moonshot Paper

**Title:** *Beyond Rule Engines: A First-Principles Blueprint for AI-Native Financial Compliance*

PDF: [`FinGuard_Beyond_Rule_Engines.pdf`](FinGuard_Beyond_Rule_Engines.pdf)

Editable canonical (Section 5 updated for Splunk AI): [`docs/MOONSHOT_PAPER.md`](docs/MOONSHOT_PAPER.md)

### 3. Vision Presentation

Marp slides: [`docs/MOONSHOT_PRESENTATION.md`](docs/MOONSHOT_PRESENTATION.md)

Export to PDF (VS Code Marp extension, or CLI):

```bash
npx @marp-team/marp-cli docs/MOONSHOT_PRESENTATION.md -o docs/MOONSHOT_PRESENTATION.pdf
```

---

## Vision Statement

**English (elevator):**

> Financial compliance is not a labor crisis — it is an information-architecture crisis. Analysts spend ten minutes per alert not because they are slow, but because evidence lives in four disconnected systems with no shared semantic layer. FinGuard proposes four axioms — unified evidence, cryptographic auditability, privacy-preserving pseudonymization, and bounded agent action — composed into a reference architecture that shifts compliance from a per-institution cost toward a regulator-aligned public good.

**中文（电梯陈述）：**

> 金融合规的本质危机不是人力不足，而是信息架构断裂。分析师在每个告警上花费的十分钟，是跨四个孤立系统整合证据的认知成本。FinGuard 提出四条公理——统一证据底稿、密码学可审计、隐私假名化、有界智能体动作空间——并将其合成为可验证的参考架构，指向合规从机构成本演变为监管对齐的公共品。

---

## Pre-Submission Self-Check

- [ ] `streamlit run app/streamlit_app.py` runs with Demo Mode (no Splunk)
- [ ] Investigation tab returns a structured report with risk score and compliance basis
- [ ] Audit tab shows **intact** hash chain after investigation
- [ ] [`docs/MOONSHOT_PRESENTATION.pdf`](docs/MOONSHOT_PRESENTATION.pdf) exported (or submit `.md` if platform allows)
- [ ] Paper Section 5 matches [`core/splunk_ai_agent.py`](core/splunk_ai_agent.py) (see [`docs/MOONSHOT_PAPER.md`](docs/MOONSHOT_PAPER.md))
- [ ] Can answer Moonshot four questions: misunderstood problem / first principles / why now / civilizational impact

---

## Related Documentation

| Doc | Purpose |
|-----|---------|
| [`README.md`](README.md) | Full setup, architecture, dependencies |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Splunk / AI data-flow diagrams |
| [`SUBMISSION.md`](SUBMISSION.md) | Splunk Agentic Ops Hackathon submission |
| [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) | Live demo script |
| [`docs/PROBLEM_AND_SOLUTION.md`](docs/PROBLEM_AND_SOLUTION.md) | Clear problem & solution explanation |

*Synthetic data only — no real customer information.*
