"""
Role-Based Access Control (RBAC) module.
Implements principle of least privilege for compliance investigation.
"""

from typing import List, Dict, Set


class RBAC:
    """
    Role-based access control with three tiers: analyst, auditor, admin.
    Enforces field-level access restrictions based on role.
    """
    
    # Field visibility per role
    ROLE_PERMISSIONS: Dict[str, Set[str]] = {
        "analyst": {
            "user_id", "amount", "timestamp", "risk_score", "anomaly_type"
        },
        "auditor": {
            "user_id", "amount", "timestamp", "risk_score", "anomaly_type",
            "device_id", "location", "transaction_hash", "status"
        },
        "admin": {
            "user_id", "amount", "timestamp", "risk_score", "anomaly_type",
            "device_id", "location", "transaction_hash", "status",
            "email", "phone", "account_number", "metadata"
        }
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
