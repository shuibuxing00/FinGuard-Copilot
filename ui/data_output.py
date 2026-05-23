"""
Data output and export panel with RBAC-enforced visibility.
"""

import json
from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st

from security import RBAC


def render_data_output(
    role: str,
    users_df: Optional[pd.DataFrame],
    transactions_df: Optional[pd.DataFrame],
    devices_df: Optional[pd.DataFrame],
) -> None:
    """Render the data output workspace with role-filtered views and exports."""
    st.markdown("## Data Output Center")
    st.caption(
        "All tables and downloads respect your verified role. "
        "Restricted columns are removed — not merely hidden."
    )

    if users_df is None or transactions_df is None:
        st.warning("Load synthetic data from the sidebar to use the Data Output Center.")
        return

    _render_output_metrics(role, users_df, transactions_df, devices_df)
    st.markdown("---")
    _render_permission_matrix(role)
    st.markdown("---")
    _render_dataset_tabs(role, users_df, transactions_df, devices_df)
    st.markdown("---")
    _render_export_panel(role, users_df, transactions_df, devices_df)


def _render_output_metrics(
    role: str,
    users_df: pd.DataFrame,
    transactions_df: pd.DataFrame,
    devices_df: Optional[pd.DataFrame],
) -> None:
    st.markdown("### Dataset Overview")
    high_risk = 0
    if "risk_score" in transactions_df.columns:
        high_risk = int((transactions_df["risk_score"] > 70).sum())
    anomalies = 0
    if "anomaly_type" in transactions_df.columns:
        anomalies = int((transactions_df["anomaly_type"].astype(str).str.len() > 0).sum())
    total_vol = float(transactions_df["amount"].sum()) if "amount" in transactions_df.columns else 0
    n_devices = len(devices_df) if devices_df is not None else 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Users", len(users_df))
    c2.metric("Transactions", len(transactions_df))
    c3.metric("Devices", n_devices)
    c4.metric("High Risk (70+)", high_risk)
    c5.metric("Flagged Anomalies", anomalies)
    c6.metric("Total Volume", f"${total_vol:,.0f}")

    meta = RBAC.get_role_metadata(role)
    st.info(
        f"**{meta['label']}** can export **{len(RBAC.get_visible_fields(role))}** of "
        f"**{len(RBAC.ALL_FIELDS)}** tracked field types. "
        f"Elevated access requires re-authentication with auditor or admin credentials."
    )


def _render_permission_matrix(role: str) -> None:
    st.markdown("### Field Access Matrix")
    rows = RBAC.get_field_access_matrix()
    matrix_df = pd.DataFrame(rows)
    matrix_df["analyst"] = matrix_df["analyst"].map({True: "✓", False: "—"})
    matrix_df["auditor"] = matrix_df["auditor"].map({True: "✓", False: "—"})
    matrix_df["admin"] = matrix_df["admin"].map({True: "✓", False: "—"})

    def _highlight_role(row):
        styles = [""] * len(row)
        col_idx = {"analyst": 2, "auditor": 3, "admin": 4}.get(role)
        if col_idx is not None:
            styles[col_idx] = "background-color: #1f3d5c; font-weight: 600;"
        tier = row.get("tier", "")
        if tier == "restricted":
            styles[1] = "color: #f85149;"
        elif tier == "operational":
            styles[1] = "color: #d29922;"
        else:
            styles[1] = "color: #58a6ff;"
        return styles

    styled = matrix_df.style.apply(_highlight_role, axis=1)
    st.dataframe(styled, use_container_width=True, hide_index=True)

    denied = RBAC.get_denied_fields(role)
    if denied:
        with st.expander(f"Restricted for your role ({len(denied)} fields)", expanded=False):
            st.code(", ".join(denied))


def _render_dataset_tabs(
    role: str,
    users_df: pd.DataFrame,
    transactions_df: pd.DataFrame,
    devices_df: Optional[pd.DataFrame],
) -> None:
    st.markdown("### Role-Filtered Data Preview")

    tab_txn, tab_users, tab_devices, tab_merged = st.tabs(
        ["Transactions", "Users", "Devices", "Investigation View"]
    )

    with tab_txn:
        filtered = _enrich_transactions(transactions_df, devices_df)
        visible = RBAC.filter_dataframe(filtered, role)
        st.markdown(f"**{len(visible)}** rows · **{len(visible.columns)}** columns visible")
        if visible.empty:
            st.warning("No transaction columns available at your access level.")
        else:
            st.dataframe(visible.head(100), use_container_width=True, height=320)
            if "risk_score" in visible.columns:
                st.bar_chart(visible["risk_score"].value_counts(bins=10).sort_index())

    with tab_users:
        visible = RBAC.filter_dataframe(users_df, role)
        st.markdown(f"**{len(visible)}** user records (PII redacted by policy)")
        st.dataframe(visible, use_container_width=True, height=280)

    with tab_devices:
        if devices_df is None or devices_df.empty:
            st.info("No device records in the current dataset.")
        else:
            visible = RBAC.filter_dataframe(devices_df, role)
            st.markdown(f"**{len(visible)}** device records")
            st.dataframe(visible.head(50), use_container_width=True, height=280)

    with tab_merged:
        merged = _build_investigation_view(role, users_df, transactions_df, devices_df)
        st.markdown(
            "Consolidated high-risk slice for compliance review "
            f"({len(merged)} rows at your clearance level)"
        )
        if merged.empty:
            st.info("No high-risk records match the current filters.")
        else:
            st.dataframe(merged.head(50), use_container_width=True, height=360)


def _enrich_transactions(
    transactions_df: pd.DataFrame,
    devices_df: Optional[pd.DataFrame],
) -> pd.DataFrame:
    """Attach device/location and transaction hash for RBAC-aware export."""
    df = transactions_df.copy()
    if "transaction_id" in df.columns and "transaction_hash" not in df.columns:
        import hashlib
        df["transaction_hash"] = df["transaction_id"].apply(
            lambda x: hashlib.sha256(str(x).encode()).hexdigest()[:16]
        )
    if devices_df is not None and not devices_df.empty:
        dev = devices_df.groupby("user_id").first().reset_index()
        merge_cols = [c for c in ["user_id", "device_id", "location", "device_type", "ip_address"] if c in dev.columns]
        if merge_cols:
            df = df.merge(dev[merge_cols], on="user_id", how="left", suffixes=("", "_dev"))
    return df


def _build_investigation_view(
    role: str,
    users_df: pd.DataFrame,
    transactions_df: pd.DataFrame,
    devices_df: Optional[pd.DataFrame],
) -> pd.DataFrame:
    enriched = _enrich_transactions(transactions_df, devices_df)
    if "risk_score" in enriched.columns:
        slice_df = enriched[enriched["risk_score"] >= 50].copy()
    else:
        slice_df = enriched.head(100).copy()
    if users_df is not None and not users_df.empty:
        user_cols = [c for c in users_df.columns if c != "user_id"]
        slice_df = slice_df.merge(users_df, on="user_id", how="left", suffixes=("", "_usr"))
    return RBAC.filter_dataframe(slice_df, role)


def _render_export_panel(
    role: str,
    users_df: pd.DataFrame,
    transactions_df: pd.DataFrame,
    devices_df: Optional[pd.DataFrame],
) -> None:
    st.markdown("### Secure Export")
    st.caption("Downloads contain only fields your verified role may access.")

    enriched_txn = _enrich_transactions(transactions_df, devices_df)
    export_sets = {
        "transactions_rbac.csv": RBAC.filter_dataframe(enriched_txn, role),
        "users_rbac.csv": RBAC.filter_dataframe(users_df, role),
        "investigation_high_risk.csv": _build_investigation_view(
            role, users_df, transactions_df, devices_df
        ),
    }
    if devices_df is not None:
        export_sets["devices_rbac.csv"] = RBAC.filter_dataframe(devices_df, role)

    manifest = {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "role": role,
        "role_label": RBAC.get_role_metadata(role).get("label"),
        "visible_fields": RBAC.get_visible_fields(role),
        "denied_fields": RBAC.get_denied_fields(role),
        "record_counts": {k: len(v) for k, v in export_sets.items()},
    }

    col_a, col_b = st.columns(2)
    with col_a:
        for filename, df in export_sets.items():
            if df is not None and not df.empty:
                st.download_button(
                    label=f"Download {filename}",
                    data=df.to_csv(index=False),
                    file_name=filename,
                    mime="text/csv",
                    use_container_width=True,
                )
            else:
                st.button(f"{filename} (empty)", disabled=True, use_container_width=True)

    with col_b:
        st.download_button(
            label="Download export manifest (JSON)",
            data=json.dumps(manifest, indent=2),
            file_name="export_manifest.json",
            mime="application/json",
            use_container_width=True,
        )
        st.json(manifest)
