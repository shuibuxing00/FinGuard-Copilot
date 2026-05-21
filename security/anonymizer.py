"""
Pseudonymization module using PBKDF2-HMAC-SHA256.
Provides irreversible one-way hashing for personally identifiable information.
"""

import hashlib
import binascii
from typing import Optional


class Anonymizer:
    """
    Anonymizes user IDs and sensitive data using PBKDF2-HMAC-SHA256.
    """
    
    # Fixed salt for consistent pseudonymization
    SALT = b"FinGuardAML2024"
    ITERATIONS = 100000
    
    @staticmethod
    def pseudonymize(raw_id: str) -> str:
        """
        Convert raw ID to irreversible pseudonymized form using PBKDF2.
        
        Args:
            raw_id: Original user ID or sensitive identifier
            
        Returns:
            16-character hexadecimal pseudonymized ID
        """
        try:
            if not raw_id or not isinstance(raw_id, str):
                raise ValueError("raw_id must be a non-empty string")
            
            # PBKDF2-HMAC-SHA256 with 100k iterations
            hashed = hashlib.pbkdf2_hmac(
                'sha256',
                raw_id.encode('utf-8'),
                Anonymizer.SALT,
                Anonymizer.ITERATIONS,
                dklen=8  # 8 bytes = 16 hex chars
            )
            
            # Convert to hex and take first 16 chars
            hex_str = binascii.hexlify(hashed).decode('utf-8')
            return hex_str[:16]
        
        except Exception as e:
            raise RuntimeError(f"Pseudonymization failed for ID: {str(e)}")
    
    @staticmethod
    def is_pseudonymized(value: str) -> bool:
        """
        Check if a value appears to be already pseudonymized.
        
        Args:
            value: String to check
            
        Returns:
            True if value matches pseudonymized format (16 hex chars)
        """
        if not isinstance(value, str):
            return False
        
        # Check if it's 16 hex characters
        if len(value) == 16:
            try:
                int(value, 16)  # Try to parse as hex
                return True
            except ValueError:
                return False
        
        return False
