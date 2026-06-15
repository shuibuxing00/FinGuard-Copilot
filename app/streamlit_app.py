"""
FinGuard Compliance Copilot - Main Streamlit Application
AI-powered compliance investigation tool with financial-grade security.
"""

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Load environment before other imports that read os.environ
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from security import Anonymizer, RBAC, LLMGuard, IdentityAuth
from core.audit_trail import AuditTrail
from core.splunk_ai_agent import SplunkInvestigationAgent
from core.splunk_connection import connect_splunk, get_splunk_status, load_splunk_config
from data.splunk_ingest import add_display_user_ids, ingest_from_session
from ui import (
    render_dashboard,
    render_fund_flow,
    render_timeline,
    render_auth_gate,
    render_permission_summary,
    render_data_output,
)
from data.generate import generate_synthetic_data

# ============================================================================
# Page Configuration
# ============================================================================

st.set_page_config(
    page_title="FinGuard Compliance Copilot",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    :root {
        --primary-color: #0d47a1;
        --text-color: #e6edf3;
        --bg-color: #0e1117;
        --card-bg: #161b22;
    }

    .main {
        background-color: var(--bg-color);
        color: var(--text-color);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }

    div[data-testid="stMetricValue"] {
        font-size: 1.4rem;
    }

    .auth-wall {
        text-align: center;
        padding: 4rem 2rem;
        background: linear-gradient(180deg, #161b22 0%, #0e1117 100%);
        border-radius: 16px;
        border: 1px solid #30363d;
        margin: 2rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================================
# Session State Initialization
# ============================================================================


def initialize_session():
    """Initialize all session state variables."""
    defaults = {
        "messages": [],
        "audit_trail": AuditTrail(log_file=".audit_chain.json"),
        "role": "analyst",
        "data_loaded": False,
        "users_df": None,
        "transactions_df": None,
        "devices_df": None,
        "authenticated": False,
        "employee_id": None,
        "auth_expires_at": None,
        "failed_attempts": 0,
        "lockout_until": None,
        "security_components": {
            "anonymizer": Anonymizer(),
            "rbac": RBAC(),
            "llm_guard": LLMGuard(),
        },
        "splunk_connected": False,
        "splunk_status": {},
        "splunk_ingest_result": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ============================================================================
# Sidebar
# ============================================================================


def render_sidebar():
    """Render configuration sidebar (data load + identity gate)."""
    st.sidebar.markdown("## Configuration")

    is_authenticated = render_auth_gate()

    st.sidebar.markdown("### Data Management")
    if not is_authenticated:
        st.sidebar.caption("Sign in to load and export compliance data.")

    load_disabled = not is_authenticated
    if st.sidebar.button(
        "Load & Index to Splunk",
        use_container_width=True,
        disabled=load_disabled,
        help="Generate synthetic data and index into Splunk for real SPL queries",
    ):
        with st.spinner("Generating data and indexing to Splunk..."):
            try:
                users_df, txns_df, devices_df = generate_synthetic_data(
                    n_users=10,
                    n_transactions=500,
                    seed=42,
                )
                users_df, txns_df, devices_df = add_display_user_ids(
                    users_df, txns_df, devices_df,
                )
                st.session_state.users_df = users_df
                st.session_state.transactions_df = txns_df
                st.session_state.devices_df = devices_df
                st.session_state.data_loaded = True

                ingest_result = ingest_from_session(users_df, txns_df, devices_df)
                st.session_state.splunk_ingest_result = ingest_result

                try:
                    service = connect_splunk()
                    st.session_state.splunk_connected = True
                    st.session_state.splunk_status = get_splunk_status(service)
                except Exception as conn_err:
                    st.session_state.splunk_connected = False
                    st.sidebar.warning(f"Splunk connection issue: {conn_err}")

                st.session_state.audit_trail.add_entry(
                    action="load_and_index_splunk",
                    user_id=st.session_state.employee_id or "anonymous",
                    query="n_users=10,n_transactions=500,splunk_index",
                    result_hash="splunk_indexed_batch",
                    role=st.session_state.role,
                )

                if ingest_result.get("success"):
                    counts = ingest_result.get("counts", {})
                    st.sidebar.success(
                        f"Indexed to Splunk: {counts.get('users', 0)} users, "
                        f"{counts.get('transactions', 0)} txns, "
                        f"{counts.get('devices', 0)} devices"
                    )
                else:
                    st.sidebar.error(
                        f"Splunk ingest failed: {ingest_result.get('error', 'unknown')}"
                    )
            except Exception as e:
                st.sidebar.error(f"Error loading data: {e}")

    if is_authenticated:
        st.sidebar.markdown("### Splunk AI Status")
        if st.session_state.splunk_connected:
            ver = st.session_state.splunk_status.get("version", "connected")
            st.sidebar.success(f"Splunk connected (v{ver})")
            cfg = load_splunk_config()
            st.sidebar.caption(
                f"Index: `{cfg['index']}` · SDK AI: `splunklib.ai`"
            )
        else:
            st.sidebar.warning("Splunk not connected — check .env credentials")

    if is_authenticated and st.session_state.data_loaded:
        st.sidebar.markdown("### Access Summary")
        visible = RBAC.get_visible_fields(st.session_state.role)
        st.sidebar.success(
            f"**{len(visible)}** fields visible · "
            f"**{len(RBAC.get_denied_fields(st.session_state.role))}** restricted"
        )

    return is_authenticated


# ============================================================================
# Main Application
# ============================================================================


def render_header(is_authenticated: bool):
    """Render application header."""
    st.markdown("# FinGuard Compliance Copilot")
    st.markdown(
        "AI-powered compliance investigation for suspicious transaction review. "
        "**From 10 minutes to 10 seconds** — with verified identity and field-level RBAC."
    )

    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        if st.session_state.data_loaded:
            if st.session_state.splunk_connected:
                st.success("Data Loaded · Splunk Indexed")
            else:
                st.warning("Data Loaded · Splunk Pending")
        else:
            st.warning("Load & index data from the sidebar")

    with col2:
        status = st.session_state.audit_trail.verify_integrity()
        if status["status"] == "intact":
            st.markdown("**Audit Trail** · Intact")
        else:
            st.markdown("**Audit Trail** · Issue Detected")

    with col3:
        if is_authenticated:
            meta = RBAC.get_role_metadata(st.session_state.role)
            st.markdown(
                f"**Session** · {meta['badge']} {st.session_state.role.title()}"
            )
        else:
            st.markdown("**Session** · Locked")

    with col4:
        if is_authenticated and st.session_state.auth_expires_at:
            secs = max(
                0,
                int(
                    (
                        st.session_state.auth_expires_at - datetime.utcnow()
                    ).total_seconds()
                ),
            )
            st.markdown(f"**Expires** · {secs // 60}m")


def render_auth_wall():
    """Block main content until identity is verified."""
    st.markdown(
        """
        <div class="auth-wall">
            <h2>Identity Verification Required</h2>
            <p style="color:#8b949e;max-width:520px;margin:1rem auto;">
                This workspace enforces role-based access control with verified credentials.
                Use the sidebar to sign in with your employee ID and passcode.
                Roles cannot be switched without re-authentication.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    catalog = IdentityAuth.get_role_catalog()
    cols = st.columns(3)
    for col, (role, meta) in zip(cols, catalog.items()):
        with col:
            st.markdown(
                f"""
                **{meta['label']}** `{meta['badge']}`

                {meta['description']}

                - **{meta['field_count']}** data fields
                - Demo ID: `{meta['demo_employee_id']}`
                """
            )


def render_dashboards():
    """Render data visualization dashboards."""
    render_permission_summary(st.session_state.role)
    st.markdown("## Risk Overview")

    if st.session_state.data_loaded and st.session_state.transactions_df is not None:
        render_dashboard(st.session_state.transactions_df)
        col1, col2 = st.columns(2)
        with col1:
            render_fund_flow(st.session_state.transactions_df)
        with col2:
            render_timeline()
    else:
        st.info("Load synthetic data to view dashboards.")


def render_investigation_interface():
    """Render Splunk AI investigation interface."""
    st.markdown("## Investigation Assistant (Splunk AI)")

    if not st.session_state.data_loaded:
        st.warning("Load & index data to Splunk first to use the investigation assistant.")
        return

    if not st.session_state.splunk_connected:
        st.error(
            "Splunk Enterprise is required for this tab. "
            "Configure `.env` (port **8089**) and click **Load & Index to Splunk** again. "
            "Investigation uses **splunklib.ai.Agent** against real indexed data — not mock output."
        )
        return

    llm_guard = st.session_state.security_components["llm_guard"]

    try:
        agent = SplunkInvestigationAgent(llm_guard=llm_guard)
    except Exception as e:
        st.error(f"Failed to initialize Splunk AI agent: {e}")
        return

    meta = RBAC.get_role_metadata(st.session_state.role)
    splunk_ver = st.session_state.splunk_status.get("version", "connected")
    st.success(
        f"Splunk AI active · splunklib.ai Agent · Splunk v{splunk_ver} · "
        f"Role: {meta['label']} ({st.session_state.employee_id})"
    )
    st.caption(
        "Investigation calls Splunk SDK AI tools (`generate_spl`, `run_splunk_query`, profile/txn/device) "
        "against indexed Splunk data. Remote MCP tools used when Splunk MCP Server is installed."
    )

    if len(st.session_state.messages) == 0:
        st.info(
            "**Example queries:**\n"
            "- Investigate user USER_00001\n"
            "- Review high-risk transactions in Splunk\n"
            "- Check device anomalies for USER_00003"
        )

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_input := st.chat_input("Ask me to investigate suspicious transactions..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.spinner("Splunk AI investigating..."):
            try:
                result = agent.investigate(user_input)
                with st.chat_message("assistant"):
                    if result["success"]:
                        st.markdown(result["report"])
                        with st.expander("Splunk AI Investigation Steps"):
                            for step in result["reasoning"]:
                                st.text(step)
                        with st.expander("Splunk AI Capabilities Used"):
                            st.json(result.get("splunk_ai", {}))
                        with st.expander("Evidence Traceability"):
                            st.info(
                                "Evidence linked to compliance regulations and source data queries."
                            )
                            st.json(st.session_state.audit_trail.get_summary())
                    else:
                        st.error(
                            f"Investigation failed: {result.get('error', 'Unknown error')}"
                        )
                        return

                st.session_state.messages.append(
                    {"role": "assistant", "content": result["report"]}
                )
            except Exception as e:
                st.error(f"Error during investigation: {str(e)}")


def render_audit_information():
    """Render audit trail and compliance information."""
    st.markdown("## Audit & Compliance")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Audit Chain Status")
        summary = st.session_state.audit_trail.get_summary()
        st.metric("Total Entries", summary["total_count"])
        status_icon = "OK" if summary["integrity_status"] == "intact" else "ALERT"
        st.markdown(f"**Status:** {status_icon} — {summary['integrity_status'].upper()}")
        if "last_entry" in summary:
            st.info(
                f"**Last Action:** {summary['last_entry']['action']}\n\n"
                f"**Role:** {summary['last_entry']['role']}\n\n"
                f"**Time:** {summary['last_entry']['timestamp']}"
            )

    with col2:
        st.subheader("Compliance Notice")
        st.markdown(
            """
            **Important**

            - All investigations are pseudonymized with PBKDF2
            - Access requires verified employee identity per role
            - Role elevation requires separate auditor/admin credentials
            - All queries are logged in a tamper-proof audit trail
            - LLM output is sanitized to prevent misuse

            **Data:** Synthetic only — no real user information
            """
        )


def main():
    """Main application entry point."""
    initialize_session()
    is_authenticated = render_sidebar()
    render_header(is_authenticated)

    if not is_authenticated:
        render_auth_wall()
        st.markdown("---")
        st.markdown(
            "**FinGuard Compliance Copilot** | Security Track | "
            "Identity-verified compliance review"
        )
        return

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Dashboard", "Data Output", "Investigation", "Audit"]
    )

    with tab1:
        render_dashboards()

    with tab2:
        render_data_output(
            role=st.session_state.role,
            users_df=st.session_state.users_df,
            transactions_df=st.session_state.transactions_df,
            devices_df=st.session_state.devices_df,
        )

    with tab3:
        render_investigation_interface()

    with tab4:
        render_audit_information()

    st.markdown("---")
    st.markdown(
        "**FinGuard Compliance Copilot** | "
        "Splunk Agentic Ops Hackathon | "
        f"Signed in as {st.session_state.employee_id} ({st.session_state.role})"
    )


if __name__ == "__main__":
    main()
