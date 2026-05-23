"""
Role-Based Access Control (RBAC) module.
Implements principle of least privilege for compliance investigation.
"""

from typing import Any, List, Dict, Set


class RBAC:
    """
    Role-based access control with three tiers: analyst, auditor, admin.
    Enforces field-level access restrictions based on role.
    """

    ALL_FIELDS: Set[str] = {
        "user_id", "amount", "timestamp", "risk_score", "anomaly_type",
        "transaction_id", "recipient_id", "transaction_type", "violation_flags",
        "device_id", "location", "transaction_hash", "status",
        "email", "phone", "account_number", "metadata",
        "account_type", "risk_profile", "device_type", "ip_address",
    }

    FIELD_TIERS: Dict[str, str] = {
        "user_id": "core",
        "amount": "core",
        "timestamp": "core",
        "risk_score": "core",
        "anomaly_type": "core",
        "transaction_id": "core",
        "recipient_id": "core",
        "transaction_type": "core",
        "violation_flags": "core",
        "status": "operational",
        "device_id": "operational",
        "location": "operational",
        "transaction_hash": "operational",
        "device_type": "operational",
        "ip_address": "operational",
        "account_type": "operational",
        "risk_profile": "operational",
        "email": "restricted",
        "phone": "restricted",
        "account_number": "restricted",
        "metadata": "restricted",
    }

    ROLE_METADATA: Dict[str, dict] = {
        "analyst": {
            "label": "Compliance Analyst",
            "level": 1,
            "color": "#3b82f6",
            "badge": "L1",
            "description": "Transaction screening and risk triage. Core fields only.",
        },
        "auditor": {
            "label": "Senior Auditor",
            "level": 2,
            "color": "#f59e0b",
            "badge": "L2",
            "description": "Investigation workflows with device and location context.",
        },
        "admin": {
            "label": "Compliance Administrator",
            "level": 3,
            "color": "#ef4444",
            "badge": "L3",
            "description": "Full PII and account metadata for escalated reviews.",
        },
    }

    # Field visibility per role
    ROLE_PERMISSIONS: Dict[str, Set[str]] = {
        "analyst": {
            "user_id", "amount", "timestamp", "risk_score", "anomaly_type",
            "transaction_id", "recipient_id", "transaction_type", "violation_flags",
        },
        "auditor": {
            "user_id", "amount", "timestamp", "risk_score", "anomaly_type",
            "transaction_id", "recipient_id", "transaction_type", "violation_flags",
            "device_id", "location", "transaction_hash", "status",
            "device_type", "ip_address", "account_type", "risk_profile",
        },
        "admin": {
            "user_id", "amount", "timestamp", "risk_score", "anomaly_type",
            "transaction_id", "recipient_id", "transaction_type", "violation_flags",
            "device_id", "location", "transaction_hash", "status",
            "device_type", "ip_address", "account_type", "risk_profile",
            "email", "phone", "account_number", "metadata",
        },
    }

    VALID_ROLES: Set[str] = set(ROLE_PERMISSIONS.keys())
    
    @staticmethod
    def validate_role(role: str) -> bool:
        """
        Check if a role is valid.
        
        Args:
            role: Role name to validate
            
        Returns:
            True if role is valid, False otherwise
        """
        return role in RBAC.VALID_ROLES
    
    @staticmethod
    def can_access(role: str, field: str) -> bool:
        """
        Check if a role can access a specific field.
        Implements least privilege principle.
        
        Args:
            role: User role (analyst, auditor, admin)
            field: Field name to check access for
            
        Returns:
            True if role can access field, False otherwise
        """
        if role not in RBAC.VALID_ROLES:
            return False
        
        return field in RBAC.ROLE_PERMISSIONS[role]
    
    @staticmethod
    def get_visible_fields(role: str) -> List[str]:
        """
        Get list of all fields visible to a role.
        
        Args:
            role: User role (analyst, auditor, admin)
            
        Returns:
            Sorted list of visible field names
        """
        if role not in RBAC.VALID_ROLES:
            return []
        
        return sorted(list(RBAC.ROLE_PERMISSIONS[role]))
    
    @staticmethod
    def filter_record(record: Dict, role: str) -> Dict:
        """
        Filter a record to only include fields visible to role.
        
        Args:
            record: Original record dictionary
            role: User role
            
        Returns:
            Filtered record with only permitted fields
        """
        if role not in RBAC.VALID_ROLES:
            return {}
        
        visible_fields = RBAC.get_visible_fields(role)
        return {k: v for k, v in record.items() if k in visible_fields}

    @staticmethod
    def get_role_metadata(role: str) -> dict:
        """Display metadata for a role."""
        if role not in RBAC.VALID_ROLES:
            return {}
        meta = RBAC.ROLE_METADATA[role].copy()
        meta["role"] = role
        meta["field_count"] = len(RBAC.ROLE_PERMISSIONS[role])
        return meta

    @staticmethod
    def get_denied_fields(role: str) -> List[str]:
        """Fields present in the dataset but hidden for this role."""
        if role not in RBAC.VALID_ROLES:
            return sorted(RBAC.ALL_FIELDS)
        visible = RBAC.ROLE_PERMISSIONS[role]
        return sorted(RBAC.ALL_FIELDS - visible)

    @staticmethod
    def get_field_access_matrix() -> List[dict]:
        """Permission matrix rows for UI."""
        rows = []
        for field in sorted(RBAC.ALL_FIELDS):
            tier = RBAC.FIELD_TIERS.get(field, "core")
            rows.append({
                "field": field,
                "tier": tier,
                "analyst": RBAC.can_access("analyst", field),
                "auditor": RBAC.can_access("auditor", field),
                "admin": RBAC.can_access("admin", field),
            })
        return rows

    @staticmethod
    def filter_dataframe(df: Any, role: str) -> Any:
        """Return a copy with only columns visible to the role."""
        if df is None:
            return df
        if getattr(df, "empty", False):
            return df
        if role not in RBAC.VALID_ROLES:
            return df.iloc[0:0].copy() if hasattr(df, "iloc") else df
        visible = set(RBAC.get_visible_fields(role))
        cols = [c for c in df.columns if c in visible]
        return df[cols].copy() if cols else df.iloc[0:0].copy()

    @staticmethod
    def mask_value(field: str, role: str) -> str:
        """Placeholder for redacted fields in previews."""
        if RBAC.can_access(role, field):
            return ""
        tier = RBAC.FIELD_TIERS.get(field, "restricted")
        return f"[REDACTED — {tier.upper()}]"
