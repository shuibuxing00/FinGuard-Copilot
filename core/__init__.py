"""
Core module for compliance investigation tool.
Provides Splunk AI agent, Splunk tools, RAG, and audit trail.
"""

from .audit_trail import AuditTrail
from .splunk_tools import SplunkTools
from .splunk_ai_agent import SplunkInvestigationAgent

__all__ = [
    "InvestigationAgent",
    "SplunkInvestigationAgent",
    "SplunkTools",
    "ComplianceRAG",
    "AuditTrail",
]


def __getattr__(name: str):
    """Lazy-load heavy optional dependencies (ChromaDB, LangChain)."""
    if name == "ComplianceRAG":
        from .rag_tools import ComplianceRAG

        return ComplianceRAG
    if name == "InvestigationAgent":
        from .agent import InvestigationAgent

        return InvestigationAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
