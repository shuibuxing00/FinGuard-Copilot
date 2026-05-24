"""
Identity verification for role-based access.
Prevents arbitrary role switching without employee ID and passcode validation.
"""

import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

from .rbac import RBAC


def _hash_credential(value: str) -> str:
    """Hash a credential with a fixed application salt (demo / synthetic data only)."""
    salt = b"finguard-compliance-copilot-v1"
    return hashlib.pbkdf2_hmac(
        "sha256",
        value.strip().encode("utf-8"),
        salt,
        100_000,
    ).hex()


# Demo credentials — synthetic environment only; replace with SSO/LDAP in production.
_ROLE_CREDENTIALS: Dict[str, Dict[str, str]] = {
    "analyst": {
        "employee_id": "ANA-1001",
        "passcode_hash": _hash_credential("analyst-secure-42"),
    },
    "auditor": {
        "employee_id": "AUD-2002",
        "passcode_hash": _hash_credential("auditor-secure-88"),
    },
    "admin": {
        "employee_id": "ADM-3003",
        "passcode_hash": _hash_credential("admin-secure-99"),
    },
}

SESSION_DURATION_MINUTES = 30
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


class IdentityAuth:
    """
    Verifies employee identity before granting a compliance role.
    """

    SESSION_DURATION_MINUTES = SESSION_DURATION_MINUTES
    MAX_FAILED_ATTEMPTS = MAX_FAILED_ATTEMPTS
    LOCKOUT_MINUTES = LOCKOUT_MINUTES

    @staticmethod
    def get_role_catalog() -> Dict[str, dict]:
        """Public role metadata for UI (no secrets)."""
        catalog = {}
        for role in RBAC.VALID_ROLES:
            meta = RBAC.get_role_metadata(role)
            cred = _ROLE_CREDENTIALS.get(role, {})
            catalog[role] = {
                **meta,
                "demo_employee_id": cred.get("employee_id", ""),
            }
        return catalog

    @staticmethod
    def verify(
        role: str,
        employee_id: str,
        passcode: str,
    ) -> Tuple[bool, str]:
        """
        Validate employee ID and passcode for the requested role.

        Returns:
            (success, message)
        """
        if not RBAC.validate_role(role):
            return False, "Invalid role selected."

        employee_id = (employee_id or "").strip().upper()
        passcode = passcode or ""

        if not employee_id:
            return False, "Employee ID is required."
        if not passcode:
            return False, "Passcode is required."
        if len(passcode) < 8:
            return False, "Passcode must be at least 8 characters."

        expected = _ROLE_CREDENTIALS.get(role)
        if not expected:
            return False, "Role configuration error."

        if employee_id != expected["employee_id"]:
            return False, "Employee ID does not match this role."

        submitted_hash = _hash_credential(passcode)
        if not hmac.compare_digest(submitted_hash, expected["passcode_hash"]):
            return False, "Invalid passcode for this role."

        return True, "Identity verified successfully."

    @staticmethod
    def session_expires_at(from_time: Optional[datetime] = None) -> datetime:
        base = from_time or datetime.utcnow()
        return base + timedelta(minutes=SESSION_DURATION_MINUTES)

    @staticmethod
    def is_session_valid(expires_at: Optional[datetime]) -> bool:
        if expires_at is None:
            return False
        return datetime.utcnow() < expires_at

    @staticmethod
    def lockout_remaining(lockout_until: Optional[datetime]) -> int:
        """Seconds remaining in lockout, or 0 if not locked."""
        if lockout_until is None:
            return 0
        delta = (lockout_until - datetime.utcnow()).total_seconds()
        return max(0, int(delta))
