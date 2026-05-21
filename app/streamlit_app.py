"""
FinGuard Compliance Copilot - Main Streamlit Application
AI-powered compliance investigation tool with financial-grade security.
"""

import os
import sys
import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from security import Anonymizer, RBAC, LLMGuard
from core import AuditTrail, SplunkTools, ComplianceRAG, InvestigationAgent
from ui import render_dashboard, render_fund_flow, render_timeline
from data.generate import generate_synthetic_data

# ============================================================================
# Page Configuration
# ============================================================================

st.set_page_config(
    page_title="FinGuard Compliance Copilot",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark theme CSS
st.markdown("""
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
    
    .stCard {
        background-color: var(--card-bg);
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #30363d;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    
    .risk-score {
        font-size: 2rem;
        font-weight: bold;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
    
    .risk-low { background-color: #0d6d3d; color: #26d07c; }
    .risk-medium { background-color: #6d4d00; color: #d09d30; }
    .risk-high { background-color: #6d0d0d; color: #ff6b6b; }
    .risk-critical { background-color: #8d0d0d; color: #ff3333; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# Session State Initialization
# ============================================================================

def initialize_session():
    """Initialize all session state variables."""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'audit_trail' not in st.session_state:
        st.session_state.audit_trail = AuditTrail(
            log_file=".audit_chain.json"
        )
    
    if 'role' not in st.session_state:
        st.session_state.role = 'analyst'
    
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    
    if 'users_df' not in st.session_state:
        st.session_state.users_df = None
    
    if 'transactions_df' not in st.session_state:
        st.session_state.transactions_df = None
    
    if 'devices_df' not in st.session_state:
        st.session_state.devices_df = None
    
    if 'security_components' not in st.session_state:
        st.session_state.security_components = {
            'anonymizer': Anonymizer(),
            'rbac': RBAC(),
            'llm_guard': LLMGuard()
        }


# ============================================================================
# Sidebar Configuration
# ============================================================================

def render_sidebar():
    """Render configuration sidebar."""
    st.sidebar.markdown("## ⚙️ Configuration")
    
    # Role Selector
    st.sidebar.markdown("### User Role")
    new_role = st.sidebar.radio(
        "Select your role:",
        options=['analyst', 'auditor', 'admin'],
        captions=[
            'Limited: amount, timestamp, risk_score',
            'Extended: includes device, location',
            'Full: all data fields'
        ],
        index=['analyst', 'auditor', 'admin'].index(st.session_state.role)
    )
    
    if new_role != st.session_state.role:
        st.session_state.role = new_role
        st.session_state.messages = []  # Clear chat on role change
        st.rerun()
    
    # Data Management
    st.sidebar.markdown("### Data Management")
    
    if st.sidebar.button("🔄 Load Synthetic Data", use_container_width=True):
        with st.spinner("Generating synthetic data..."):
            try:
                users_df, txns_df, devices_df = generate_synthetic_data(
                    n_users=10,
                    n_transactions=500,
                    seed=42
                )
                
                st.session_state.users_df = users_df
                st.session_state.transactions_df = txns_df
                st.session_state.devices_df = devices_df
                st.session_state.data_loaded = True
                
                st.sidebar.success("✓ Data loaded successfully!")
            except Exception as e:
                st.sidebar.error(f"Error loading data: {e}")
    
    # Security Info
    st.sidebar.markdown("### 🔒 Security")
    
    visible_fields = RBAC.get_visible_fields(st.session_state.role)
    st.sidebar.info(
        f"**Visible Fields ({len(visible_fields)}):**\n" +
        ", ".join(visible_fields[:5]) +
        ("..." if len(visible_fields) > 5 else "")
    )


# ============================================================================
# Main Application
# ============================================================================

def render_header():
    """Render application header."""
    st.markdown("# 🛡️ FinGuard Compliance Copilot")
    st.markdown(
        "AI-powered compliance investigation tool for rapid suspicious transaction review. "
        "**⏱️ From 10 minutes to 10 seconds**"
    )
    
    # Status indicator
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if st.session_state.data_loaded:
            st.success("✓ Data Loaded")
        else:
            st.warning("⚠️ Load data first →")
    
    with col2:
        status = st.session_state.audit_trail.verify_integrity()
        if status['status'] == 'intact':
            st.markdown("🟢 **Audit Trail Intact**")
        else:
            st.markdown("🔴 **Audit Trail Issue**")
    
    with col3:
        st.markdown(f"**Role:** {st.session_state.role.capitalize()}")


def render_dashboards():
    """Render data visualization dashboards."""
    st.markdown("## 📊 Risk Overview")
    
    if st.session_state.data_loaded and st.session_state.transactions_df is not None:
        # Dashboard
        render_dashboard(st.session_state.transactions_df)
        
        # Fund flow and timeline
        col1, col2 = st.columns(2)
        
        with col1:
            render_fund_flow(st.session_state.transactions_df)
        
        with col2:
            render_timeline()
    else:
        st.info("📊 Load synthetic data to view dashboards")


def render_investigation_interface():
    """Render AI investigation interface."""
    st.markdown("## 🔍 Investigation Assistant")
    
    if not st.session_state.data_loaded:
        st.warning("Please load synthetic data first to use the investigation assistant.")
        return
    
    # Initialize components
    anonymizer = st.session_state.security_components['anonymizer']
    rbac = st.session_state.security_components['rbac']
    llm_guard = st.session_state.security_components['llm_guard']
    
    # Create tools
    splunk_tools = SplunkTools(
        audit_trail=st.session_state.audit_trail,
        anonymizer=anonymizer,
        rbac=rbac,
        role=st.session_state.role
    )
    
    # Load data into tools
    splunk_tools.load_mock_data(
        users_df=st.session_state.users_df,
        transactions_df=st.session_state.transactions_df,
        devices_df=st.session_state.devices_df
    )
    
    # Initialize RAG and Agent
    try:
        rag_tools = ComplianceRAG(laws_dir="data/compliance_laws")
        agent = InvestigationAgent(splunk_tools, rag_tools, llm_guard)
    except Exception as e:
        st.error(f"Failed to initialize investigation agent: {e}")
        return
    
    # Chat interface
    if len(st.session_state.messages) == 0:
        st.info(
            "💡 **Example queries:**\n"
            "- Investigate user U_00001\n"
            "- Review high-risk transactions\n"
            "- Check for suspicious patterns"
        )
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message['role']):
            st.markdown(message['content'])
    
    # Input handling
    if user_input := st.chat_input("Ask me to investigate suspicious transactions..."):
        # Add user message to history
        st.session_state.messages.append({
            'role': 'user',
            'content': user_input
        })
        
        with st.chat_message('user'):
            st.markdown(user_input)
        
        # Process investigation
        with st.spinner("🔍 Investigating..."):
            try:
                result = agent.investigate(user_input)
                
                with st.chat_message('assistant'):
                    if result['success']:
                        # Display report
                        st.markdown(result['report'])
                        
                        # Reasoning expander
                        with st.expander("📋 Investigation Steps"):
                            for step in result['reasoning']:
                                st.text(step)
                        
                        # Evidence traceability
                        with st.expander("🔗 Evidence Traceability"):
                            st.info("Evidence linked to compliance regulations and source data queries")
                            audit_summary = st.session_state.audit_trail.get_summary()
                            st.json(audit_summary)
                    else:
                        st.error(f"Investigation failed: {result.get('error', 'Unknown error')}")
                        return
                
                # Add assistant response to history
                st.session_state.messages.append({
                    'role': 'assistant',
                    'content': result['report']
                })
            
            except Exception as e:
                st.error(f"Error during investigation: {str(e)}")


def render_audit_information():
    """Render audit trail and compliance information."""
    st.markdown("## 📋 Audit & Compliance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Audit Chain Status")
        summary = st.session_state.audit_trail.get_summary()
        
        st.metric("Total Entries", summary['total_count'])
        
        status_icon = "🟢" if summary['integrity_status'] == 'intact' else "🔴"
        st.markdown(f"{status_icon} **Status:** {summary['integrity_status'].upper()}")
        
        if 'last_entry' in summary:
            st.info(
                f"**Last Action:** {summary['last_entry']['action']}\n"
                f"**Role:** {summary['last_entry']['role']}\n"
                f"**Time:** {summary['last_entry']['timestamp']}"
            )
    
    with col2:
        st.subheader("Compliance Notice")
        st.markdown(
            """
            ⚠️ **Important**
            
            - All investigations are pseudonymized with PBKDF2
            - Access is controlled by role-based permissions
            - All queries are logged in tamper-proof audit trail
            - LLM output sanitized to prevent misuse
            
            **Data:** Synthetic only - no real user information
            """
        )


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Main application entry point."""
    # Initialize
    initialize_session()
    
    # Sidebar
    render_sidebar()
    
    # Header
    render_header()
    
    # Tabs for different sections
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🔍 Investigation", "📋 Audit"])
    
    with tab1:
        render_dashboards()
    
    with tab2:
        render_investigation_interface()
    
    with tab3:
        render_audit_information()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "**FinGuard Compliance Copilot** | "
        "Security Track - Splunk Agentic Ops Hackathon | "
        "⏱️ 10 seconds compliance review"
    )


if __name__ == '__main__':
    main()
