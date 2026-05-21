"""
Splunk Tools module.
Provides mock data interface simulating Splunk queries with RBAC filtering.
"""

import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
from security.rbac import RBAC
from security.anonymizer import Anonymizer
from core.audit_trail import AuditTrail


class SplunkTools:
    """
    Simulates Splunk data interface with audit logging and RBAC enforcement.
    All queries are logged to audit trail and results filtered by role.
    """
    
    def __init__(
        self,
        audit_trail: AuditTrail,
        anonymizer: Anonymizer,
        rbac: RBAC,
        role: str
    ):
        """
        Initialize Splunk tools with security context.
        
        Args:
            audit_trail: AuditTrail instance for logging
            anonymizer: Anonymizer for pseudonymization
            rbac: RBAC instance for access control
            role: Current user role
        """
        self.audit_trail = audit_trail
        self.anonymizer = anonymizer
        self.rbac = rbac
        self.role = role
        
        self.users_df: Optional[pd.DataFrame] = None
        self.transactions_df: Optional[pd.DataFrame] = None
        self.devices_df: Optional[pd.DataFrame] = None
    
    def load_mock_data(
        self,
        users_df: pd.DataFrame,
        transactions_df: pd.DataFrame,
        devices_df: pd.DataFrame
    ) -> None:
        """
        Load mock data into memory (simulates Splunk).
        
        Args:
            users_df: Users dataframe with columns: user_id, name, email, etc.
            transactions_df: Transactions dataframe
            devices_df: Devices dataframe
        """
        self.users_df = users_df.copy()
        self.transactions_df = transactions_df.copy()
        self.devices_df = devices_df.copy()
    
    def _compute_result_hash(self, result: Any) -> str:
        """
        Compute SHA256 hash of query result.
        
        Args:
            result: Query result (list, dict, or dataframe)
            
        Returns:
            64-character hex hash
        """
        try:
            import json
            
            if isinstance(result, pd.DataFrame):
                result_str = result.to_json()
            elif isinstance(result, (list, dict)):
                result_str = json.dumps(result, sort_keys=True, default=str)
            else:
                result_str = str(result)
            
            return hashlib.sha256(result_str.encode('utf-8')).hexdigest()
        
        except Exception:
            return hashlib.sha256(b"error").hexdigest()
    
    def _audit_and_filter(
        self,
        action: str,
        user_id: str,
        query: str,
        result: Any
    ) -> Any:
        """
        Log query to audit trail and filter result by RBAC.
        
        Args:
            action: Type of query action
            user_id: User performing query
            query: Query description
            result: Query result to filter
            
        Returns:
            RBAC-filtered result
        """
        try:
            # Compute result hash before filtering
            result_hash = self._compute_result_hash(result)
            
            # Log to audit trail
            self.audit_trail.add_entry(
                action=action,
                user_id=user_id,
                query=query,
                result_hash=result_hash,
                role=self.role
            )
            
            # Apply RBAC filtering
            if isinstance(result, list) and all(isinstance(r, dict) for r in result):
                # Filter each record
                filtered = [self.rbac.filter_record(r, self.role) for r in result]
                return filtered
            elif isinstance(result, dict):
                return self.rbac.filter_record(result, self.role)
            else:
                return result
        
        except Exception as e:
            print(f"Audit/filter error: {e}")
            return result if isinstance(result, list) else {}
    
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Get user profile with audit logging and RBAC filtering.
        
        Args:
            user_id: User ID to query
            
        Returns:
            User profile dictionary (RBAC filtered)
        """
        try:
            if self.users_df is None:
                return {"error": "No mock data loaded"}
            
            # Query
            pseudonym = self.anonymizer.pseudonymize(user_id)
            user_rows = self.users_df[self.users_df['user_id'] == pseudonym]
            
            if user_rows.empty:
                result = {"error": f"User {pseudonym} not found"}
            else:
                result = user_rows.iloc[0].to_dict()
            
            # Audit and filter
            return self._audit_and_filter(
                action="get_user_profile",
                user_id=pseudonym,
                query=f"user_id={user_id}",
                result=result
            )
        
        except Exception as e:
            return {"error": f"Query failed: {str(e)}"}
    
    def get_recent_transactions(
        self,
        user_id: str,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get recent transactions for a user.
        
        Args:
            user_id: User ID to query
            hours: Hours lookback window
            
        Returns:
            List of transactions (RBAC filtered)
        """
        try:
            if self.transactions_df is None:
                return []
            
            # Query
            pseudonym = self.anonymizer.pseudonymize(user_id)
            user_txns = self.transactions_df[
                self.transactions_df['user_id'] == pseudonym
            ]
            
            # Filter by time
            if 'timestamp' in user_txns.columns:
                user_txns = user_txns.sort_values('timestamp', ascending=False)
                user_txns = user_txns.head(20)  # Limit to 20 recent
            
            results = user_txns.to_dict('records')
            
            # Audit and filter
            return self._audit_and_filter(
                action="get_recent_transactions",
                user_id=pseudonym,
                query=f"user_id={user_id}, hours={hours}",
                result=results
            )
        
        except Exception as e:
            return [{"error": f"Query failed: {str(e)}"}]
    
    def get_device_history(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get device history for a user.
        
        Args:
            user_id: User ID to query
            
        Returns:
            List of device records (RBAC filtered)
        """
        try:
            if self.devices_df is None:
                return []
            
            # Query
            pseudonym = self.anonymizer.pseudonymize(user_id)
            user_devices = self.devices_df[
                self.devices_df['user_id'] == pseudonym
            ]
            
            results = user_devices.to_dict('records')
            
            # Audit and filter
            return self._audit_and_filter(
                action="get_device_history",
                user_id=pseudonym,
                query=f"user_id={user_id}",
                result=results
            )
        
        except Exception as e:
            return [{"error": f"Query failed: {str(e)}"}]
    
    def search_transactions(
        self,
        criteria: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Search transactions by criteria (amount, anomaly type, etc.).
        
        Args:
            criteria: Search criteria dictionary
            
        Returns:
            List of matching transactions (RBAC filtered)
        """
        try:
            if self.transactions_df is None:
                return []
            
            results_df = self.transactions_df.copy()
            
            # Apply filters
            for key, value in criteria.items():
                if key in results_df.columns:
                    if isinstance(value, (list, tuple)):
                        results_df = results_df[results_df[key].isin(value)]
                    else:
                        results_df = results_df[results_df[key] == value]
            
            results = results_df.to_dict('records')
            
            # Audit and filter
            return self._audit_and_filter(
                action="search_transactions",
                user_id="system",
                query=f"criteria={criteria}",
                result=results
            )
        
        except Exception as e:
            return [{"error": f"Search failed: {str(e)}"}]
