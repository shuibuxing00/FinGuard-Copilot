"""
UI module for compliance investigation dashboard.
Provides dashboard, fund flow, and timeline visualizations.
"""

from .dashboard import render_dashboard
from .fund_flow import render_fund_flow
from .timeline import render_timeline
from .auth_panel import render_auth_gate, render_permission_summary
from .data_output import render_data_output

__all__ = [
    "render_dashboard",
    "render_fund_flow",
    "render_timeline",
    "render_auth_gate",
    "render_permission_summary",
    "render_data_output",
]
