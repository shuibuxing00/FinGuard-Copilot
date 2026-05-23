"""
Identity verification panel for secure role assignment.
"""

from datetime import datetime

import streamlit as st

from security import IdentityAuth, RBAC


def _inject_auth_styles() -> None:
    st.markdown(
        """
        <style>
        .role-card {
            border-radius: 10px;
            padding: 0.75rem 1rem;
            margin-bottom: 0.5rem;
            border: 1px solid #30363d;
            background: #161b22;
        }
        .role-card-active {
            border-color: #58a6ff;
            box-shadow: 0 0 0 1px #58a6ff;
        }
        .perm-tier-core { color: #58a6ff; font-size: 0.75rem; }
        .perm-tier-operational { color: #d29922; font-size: 0.75rem; }
        .perm-tier-restricted { color: #f85149; font-size: 0.75rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_auth_gate() -> bool:
    """
    Render login or active session UI in the sidebar.

    Returns:
        True if the user has a valid authenticated session.
    """
    _inject_auth_styles()

    if st.session_state.get("authenticated") and IdentityAuth.is_session_valid(
        st.session_state.get("auth_expires_at")
    ):
        _render_active_session()
        return True

    if st.session_state.get("authenticated"):
        st.session_state.authenticated = False
        st.session_state.employee_id = None
        st.sidebar.warning("Session expired. Please sign in again.")

    return _render_login_form()


def _render_active_session() -> None:
    role = st.session_state.role
    meta = RBAC.get_role_metadata(role)
    employee_id = st.session_state.get("employee_id", "—")
    expires = st.session_state.get("auth_expires_at")
    remaining = ""
    if expires:
        secs = max(0, int((expires - datetime.utcnow()).total_seconds()))
        remaining = f"{secs // 60}m {secs % 60}s"

    st.sidebar.markdown("### Signed In")
    st.sidebar.markdown(
        f"""
        <div class="role-card role-card-active" style="border-left: 4px solid {meta.get('color', '#58a6ff')};">
            <strong>{meta.get('label', role.title())}</strong>
            <span style="background:{meta.get('color')};color:#0e1117;padding:2px 6px;border-radius:4px;font-size:0.7rem;margin-left:6px;">{meta.get('badge')}</span>
            <br><span style="font-size:0.85rem;color:#8b949e;">ID: {employee_id}</span>
            <br><span style="font-size:0.8rem;color:#8b949e;">Session: {remaining} remaining</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    visible = len(RBAC.get_visible_fields(role))
    denied = len(RBAC.get_denied_fields(role))
    st.sidebar.metric("Visible Fields", visible, f"-{denied} restricted")

    if st.sidebar.button("Sign Out", use_container_width=True, type="primary"):
        _clear_auth_session()
        st.rerun()


def _clear_auth_session() -> None:
    st.session_state.authenticated = False
    st.session_state.employee_id = None
    st.session_state.auth_expires_at = None
    st.session_state.role = "analyst"
    st.session_state.messages = []
    st.session_state.failed_attempts = 0
    st.session_state.lockout_until = None


def _render_login_form() -> bool:
    st.sidebar.markdown("### Identity Verification")
    st.sidebar.caption(
        "Roles require employee ID and passcode. "
        "Arbitrary role switching is not permitted."
    )

    lockout_until = st.session_state.get("lockout_until")
    remaining = IdentityAuth.lockout_remaining(lockout_until)
    if remaining > 0:
        st.sidebar.error(
            f"Too many failed attempts. Try again in {remaining // 60}m {remaining % 60}s."
        )
        return False

    catalog = IdentityAuth.get_role_catalog()
    role_options = list(catalog.keys())
    role_labels = [f"{catalog[r]['label']} ({catalog[r]['badge']})" for r in role_options]

    selected_idx = st.sidebar.selectbox(
        "Request access level",
        range(len(role_options)),
        format_func=lambda i: role_labels[i],
        key="auth_role_select",
    )
    selected_role = role_options[selected_idx]
    meta = catalog[selected_role]

    st.sidebar.markdown(
        f"""
        <div class="role-card" style="border-left: 4px solid {meta['color']};">
            <strong>{meta['label']}</strong> — Level {meta['level']}<br>
            <span style="font-size:0.8rem;color:#8b949e;">{meta['description']}</span><br>
            <span style="font-size:0.75rem;color:#6e7681;">{meta['field_count']} data fields · Demo ID hint below</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    employee_id = st.sidebar.text_input(
        "Employee ID",
        placeholder=meta.get("demo_employee_id", "e.g. ANA-1001"),
        key="auth_employee_id",
    ).strip()

    passcode = st.sidebar.text_input(
        "Passcode",
        type="password",
        placeholder="Minimum 8 characters",
        key="auth_passcode",
    )

    with st.sidebar.expander("Demo credentials (synthetic environment)"):
        st.markdown(
            "| Role | Employee ID | Passcode |\n"
            "|------|-------------|----------|\n"
            "| Analyst | `ANA-1001` | `analyst-secure-42` |\n"
            "| Auditor | `AUD-2002` | `auditor-secure-88` |\n"
            "| Admin | `ADM-3003` | `admin-secure-99` |\n"
        )

    if st.sidebar.button("Verify & Sign In", use_container_width=True, type="primary"):
        ok, msg = IdentityAuth.verify(selected_role, employee_id, passcode)
        if ok:
            st.session_state.authenticated = True
            st.session_state.role = selected_role
            st.session_state.employee_id = employee_id.upper()
            st.session_state.auth_expires_at = IdentityAuth.session_expires_at()
            st.session_state.failed_attempts = 0
            st.session_state.lockout_until = None
            st.session_state.messages = []
            st.sidebar.success(msg)
            st.rerun()
        else:
            attempts = st.session_state.get("failed_attempts", 0) + 1
            st.session_state.failed_attempts = attempts
            if attempts >= IdentityAuth.MAX_FAILED_ATTEMPTS:
                from datetime import timedelta
                st.session_state.lockout_until = (
                    datetime.utcnow() + timedelta(minutes=IdentityAuth.LOCKOUT_MINUTES)
                )
                st.session_state.failed_attempts = 0
            st.sidebar.error(msg)

    st.sidebar.info("Sign in to access dashboards, exports, and investigations.")
    return False


def render_permission_summary(role: str) -> None:
    """Render a compact permission breakdown for the main area."""
    meta = RBAC.get_role_metadata(role)
    visible = RBAC.get_visible_fields(role)
    denied = RBAC.get_denied_fields(role)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div style="padding:1rem;border-radius:8px;border-left:4px solid {meta['color']};background:#161b22;">
                <div style="font-size:0.75rem;color:#8b949e;">ACTIVE ROLE</div>
                <div style="font-size:1.1rem;font-weight:600;">{meta['label']}</div>
                <div style="font-size:0.8rem;color:#6e7681;">{meta['badge']} · Level {meta['level']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.metric("Fields Granted", len(visible))
    with c3:
        st.metric("Fields Restricted", len(denied))
    with c4:
        tiers = {"core": 0, "operational": 0, "restricted": 0}
        for f in visible:
            tiers[RBAC.FIELD_TIERS.get(f, "core")] = tiers.get(
                RBAC.FIELD_TIERS.get(f, "core"), 0
            ) + 1
        st.metric("PII Fields", tiers.get("restricted", 0))
