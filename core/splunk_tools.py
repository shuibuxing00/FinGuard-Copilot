"""
Splunk Tools module.
Provides Splunk data interface with optional real Splunk SDK support.
Supports real Splunk searches via `splunklib`, with fallback to mock pandas-based data.
"""

import hashlib
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
from security.rbac import RBAC
from security.anonymizer import Anonymizer
from core.audit_trail import AuditTrail

try:
    import splunklib.client as splunk_client
    import splunklib.results as splunk_results
    ResultsReader = splunk_results.JSONResultsReader
    SPLUNK_SDK_AVAILABLE = True
except ImportError:
    SPLUNK_SDK_AVAILABLE = False


class SplunkTools:
    """
    Splunk data interface with optional real Splunk SDK integration,
    audit logging, and RBAC filtering.
    """
    
    def __init__(
        self,
        audit_trail: AuditTrail,
        anonymizer: Anonymizer,
        rbac: RBAC,
        role: str,
        force_mock: bool = False,
    ):
        """
        Initialize Splunk tools with security context.
        
        Args:
            audit_trail: AuditTrail instance for logging
            anonymizer: Anonymizer for pseudonymization
            rbac: RBAC instance for access control
            role: Current user role
            force_mock: If True, use in-memory mock data only (Demo Mode)
        """
        self.audit_trail = audit_trail
        self.anonymizer = anonymizer
        self.rbac = rbac
        self.role = role

        self.splunk_service = None
        self.splunk_connected = False
        self.splunk_config = self._load_splunk_config()
        if force_mock:
            self.splunk_config["use_real"] = False
        self.user_search_template = self.splunk_config["user_search"]
        self.txn_search_template = self.splunk_config["txn_search"]
        self.device_search_template = self.splunk_config["device_search"]

        if self.splunk_config["use_real"] and SPLUNK_SDK_AVAILABLE:
            self._connect_to_splunk()

        self.users_df: Optional[pd.DataFrame] = None
        self.transactions_df: Optional[pd.DataFrame] = None
        self.devices_df: Optional[pd.DataFrame] = None

    def _resolve_user_key(self, user_id: str) -> str:
        """Map display ID (USER_00001) or raw ID to stored user_id (pseudonym)."""
        if not user_id:
            return user_id
        if self.users_df is not None:
            if "user_id" in self.users_df.columns:
                direct = self.users_df[self.users_df["user_id"] == user_id]
                if not direct.empty:
                    return user_id
            if "display_user_id" in self.users_df.columns:
                match = self.users_df[
                    self.users_df["display_user_id"].str.upper() == user_id.upper()
                ]
                if not match.empty:
                    return match.iloc[0]["user_id"]
        if user_id.upper().startswith("USER_"):
            return self.anonymizer.pseudonymize(user_id)
        return user_id
    
    def _load_splunk_config(self) -> Dict[str, Any]:
        """
        Load Splunk connection configuration from environment variables.
        """
        return {
            "host": os.getenv("SPLUNK_HOST", "localhost"),
            "port": int(os.getenv("SPLUNK_PORT", "8089")),
            "username": os.getenv("SPLUNK_USERNAME", "admin"),
            "password": os.getenv("SPLUNK_PASSWORD", ""),
            "index": os.getenv("SPLUNK_INDEX", "main"),
            "use_real": os.getenv("SPLUNK_USE_REAL", "true").lower() in ("1", "true", "yes"),
            "timeout": int(os.getenv("SPLUNK_SEARCH_TIMEOUT", "60")),
            "user_search": os.getenv(
                "SPLUNK_USER_SEARCH",
                'search index={index} user_id="{user_id}" | table user_id name email risk_score account_status role'
            ),
            "txn_search": os.getenv(
                "SPLUNK_TXN_SEARCH",
                'search index={index} user_id="{user_id}" | table user_id amount timestamp transaction_type anomaly_type | sort - timestamp | head 20'
            ),
            "device_search": os.getenv(
                "SPLUNK_DEVICE_SEARCH",
                'search index={index} user_id="{user_id}" | table user_id device_ip device_type timestamp location | sort - timestamp | head 20'
            ),
        }

    def _connect_to_splunk(self) -> None:
        """
        Initialize a connection to Splunk using the SDK.
        """
        if not SPLUNK_SDK_AVAILABLE:
            print("Splunk SDK not installed; real Splunk integration disabled.")
            return

        try:
            self.splunk_service = splunk_client.connect(
                host=self.splunk_config["host"],
                port=self.splunk_config["port"],
                username=self.splunk_config["username"],
                password=self.splunk_config["password"],
                scheme="https",
                verify=False,
            )
            self.splunk_connected = True
        except Exception as e:
            print(f"Failed to connect to Splunk: {e}")
            self.splunk_connected = False

    def _run_splunk_search(
        self,
        search: str,
        earliest_time: str = "-24h",
        latest_time: str = "now",
    ) -> List[Dict[str, Any]]:
        """
        Execute a Splunk search job and return JSON results.
        """
        if not self.splunk_connected or self.splunk_service is None:
            return []

        try:
            job = self.splunk_service.jobs.create(
                search,
                exec_mode="blocking",
                earliest_time=earliest_time,
                latest_time=latest_time,
                timeout=self.splunk_config["timeout"],
            )
            results_reader = ResultsReader(
                job.results(output_mode="json")
            )
            results = [dict(item) for item in results_reader if isinstance(item, dict)]
            job.cancel()
            return results
        except Exception as e:
            print(f"Splunk search failed: {e}")
            return []

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
            if self.splunk_connected:
                search = self.user_search_template.format(
                    index=self.splunk_config["index"],
                    user_id=user_id,
                )
                results = self._run_splunk_search(search)
                if results:
                    result = results[0]
                else:
                    result = {"error": f"No Splunk profile found for {user_id}"}
            elif self.users_df is None:
                return {"error": "No mock data loaded"}
            else:
                pseudonym = self._resolve_user_key(user_id)
                user_rows = self.users_df[self.users_df["user_id"] == pseudonym]
                if user_rows.empty:
                    result = {"error": f"User {pseudonym} not found"}
                else:
                    result = user_rows.iloc[0].to_dict()

            # Audit and filter
            return self._audit_and_filter(
                action="get_user_profile",
                user_id=user_id,
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
            if self.splunk_connected:
                search = self.txn_search_template.format(
                    index=self.splunk_config["index"],
                    user_id=user_id,
                )
                results = self._run_splunk_search(search)
            elif self.transactions_df is None:
                return []
            else:
                pseudonym = self._resolve_user_key(user_id)
                user_txns = self.transactions_df[
                    self.transactions_df["user_id"] == pseudonym
                ]
                if "timestamp" in user_txns.columns:
                    user_txns = user_txns.sort_values("timestamp", ascending=False)
                    user_txns = user_txns.head(20)
                results = user_txns.to_dict("records")

            # Audit and filter
            return self._audit_and_filter(
                action="get_recent_transactions",
                user_id=user_id,
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
            if self.splunk_connected:
                search = self.device_search_template.format(
                    index=self.splunk_config["index"],
                    user_id=user_id,
                )
                results = self._run_splunk_search(search)
            elif self.devices_df is None:
                return []
            else:
                pseudonym = self._resolve_user_key(user_id)
                user_devices = self.devices_df[
                    self.devices_df["user_id"] == pseudonym
                ]
                results = user_devices.to_dict("records")

            # Audit and filter
            return self._audit_and_filter(
                action="get_device_history",
                user_id=user_id,
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
