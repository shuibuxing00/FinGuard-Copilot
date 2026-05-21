"""
Tamper-Proof Audit Trail module.
Implements hash chain logging with integrity verification.
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from pathlib import Path


class AuditTrail:
    """
    Maintains cryptographic hash chain of all investigative actions.
    Detects any tampering with log records.
    """
    
    def __init__(self, log_file: str = "audit_chain.json"):
        """
        Initialize audit trail with persistence to file.
        
        Args:
            log_file: Path to audit log JSON file
        """
        self.log_file = Path(log_file)
        self.entries: list = []
        self.previous_hash: str = "0" * 64  # Genesis block
        
        # Load existing logs if available
        self._load_logs()
    
    def _load_logs(self) -> None:
        """Load existing audit logs from file."""
        try:
            if self.log_file.exists():
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.entries = data.get("entries", [])
                    if self.entries:
                        self.previous_hash = self.entries[-1]["hash"]
        except Exception as e:
            print(f"Warning: Could not load audit logs: {e}")
    
    def add_entry(
        self,
        action: str,
        user_id: str,
        query: str,
        result_hash: str,
        role: str
    ) -> str:
        """
        Add entry to audit chain and persist to disk.
        
        Args:
            action: Type of action (investigate, query, etc.)
            user_id: Pseudonymized user ID performing action
            query: Query or investigation parameters
            result_hash: SHA256 hash of results
            role: User role (analyst, auditor, admin)
            
        Returns:
            Hash of new entry
        """
        try:
            timestamp = datetime.utcnow().isoformat() + "Z"
            
            # Create entry
            entry = {
                "timestamp": timestamp,
                "action": action,
                "user_id": user_id,
                "role": role,
                "query": query,
                "result_hash": result_hash,
                "previous_hash": self.previous_hash
            }
            
            # Compute entry hash (deterministic)
            entry_hash = self._compute_hash(entry)
            entry["hash"] = entry_hash
            
            # Add to chain
            self.entries.append(entry)
            self.previous_hash = entry_hash
            
            # Persist to file
            self._save_logs()
            
            return entry_hash
        
        except Exception as e:
            raise RuntimeError(f"Failed to add audit entry: {str(e)}")
    
    def _compute_hash(self, entry: Dict[str, Any]) -> str:
        """
        Compute SHA256 hash of entry (excluding hash field itself).
        
        Args:
            entry: Entry dictionary
            
        Returns:
            64-character hex hash
        """
        # Exclude hash field from computation
        hashable = {k: v for k, v in entry.items() if k != "hash"}
        
        # Deterministic JSON serialization
        entry_str = json.dumps(hashable, sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(entry_str.encode('utf-8')).hexdigest()
    
    def _save_logs(self) -> None:
        """Persist audit logs to disk."""
        try:
            data = {
                "entries": self.entries,
                "total_count": len(self.entries),
                "last_updated": datetime.utcnow().isoformat() + "Z"
            }
            
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=True)
        
        except Exception as e:
            print(f"Warning: Could not save audit logs: {e}")
    
    def verify_integrity(self) -> Dict[str, Any]:
        """
        Verify integrity of audit chain by checking hash continuity.
        
        Returns:
            Dictionary with status and details
        """
        try:
            if not self.entries:
                return {
                    "status": "intact",
                    "message": "No entries to verify",
                    "count": 0
                }
            
            current_hash = "0" * 64  # Genesis
            broken_at: Optional[int] = None
            
            # Verify each entry
            for i, entry in enumerate(self.entries):
                stored_hash = entry.get("hash")
                stored_previous = entry.get("previous_hash")
                
                # Check previous hash link
                if stored_previous != current_hash:
                    broken_at = i
                    break
                
                # Verify current entry hash
                computed_hash = self._compute_hash(entry)
                if computed_hash != stored_hash:
                    broken_at = i
                    break
                
                current_hash = stored_hash
            
            if broken_at is not None:
                return {
                    "status": "broken",
                    "message": f"Chain integrity broken at entry {broken_at}",
                    "count": len(self.entries),
                    "broken_at": broken_at
                }
            
            return {
                "status": "intact",
                "message": "Audit chain integrity verified",
                "count": len(self.entries)
            }
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"Verification error: {str(e)}"
            }
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of audit trail status.
        
        Returns:
            Dictionary with count, status, and last entry info
        """
        try:
            integrity = self.verify_integrity()
            
            summary = {
                "total_count": len(self.entries),
                "integrity_status": integrity["status"],
                "integrity_message": integrity.get("message", "")
            }
            
            if self.entries:
                last_entry = self.entries[-1]
                summary["last_entry"] = {
                    "timestamp": last_entry.get("timestamp"),
                    "action": last_entry.get("action"),
                    "user_id": last_entry.get("user_id"),
                    "role": last_entry.get("role")
                }
            
            return summary
        
        except Exception as e:
            return {
                "total_count": 0,
                "integrity_status": "error",
                "error": str(e)
            }
