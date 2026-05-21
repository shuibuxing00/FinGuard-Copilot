"""
UI module for compliance investigation dashboard.
Provides dashboard, fund flow, and timeline visualizations.
"""

from .dashboard import render_dashboard
from .fund_flow import render_fund_flow
from .timeline import render_timeline

__all__ = ["render_dashboard", "render_fund_flow", "render_timeline"]
