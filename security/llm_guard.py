"""
LLM Security Guard module.
Prevents prompt injection, filters inappropriate output, and enforces compliance disclaimers.
"""

import re
from typing import Tuple


class LLMGuard:
    """
    Security layer for LLM input/output protection.
    - Validates user input for prompt injection and PII leakage
    - Sanitizes LLM output and adds compliance disclaimer
    - Enforces input length limits
    """
    
    MAX_INPUT_LENGTH = 500
    
    # Patterns indicating prompt injection attempts
    DANGEROUS_PATTERNS = [
        r"ignore\s+(your\s+)?instructions?",
        r"forget\s+(your\s+)?system\s+prompt",
        r"disregard.*previous.*instructions?",
        r"you\s+are\s+now",
        r"pretend\s+you\s+are",
        r"act\s+as\s+if",
        r"system\s+prompt",
        r"jailbreak",
        r"\[\[\[.*\]\]\]",  # Triple brackets
        r"<system>.*</system>",
        r"admin\s+override",
    ]
    
    # Patterns indicating forbidden output
    FORBIDDEN_PATTERNS = [
        r"i\s+am\s+certain|i\s+am\s+sure|definitely|absolutely\s+certain",
        r"suspect.*is.*guilty",
        r"must\s+be\s+arrested",
        r"immediately\s+freeze",
        r"ban\s+this\s+(account|user)",
    ]
    
    # PII detection patterns
    PII_PATTERNS = {
        "phone": r"1[3-9]\d{9}",  # Chinese phone
        "id_card": r"\d{18}|\d{17}[xX]",  # ID card
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "credit_card": r"\d{13,19}",
    }
    
    DISCLAIMER = (
        "\n\n⚠️ **AI-Generated Analysis Disclaimer**\n"
        "This analysis is for reference only. Final compliance decisions require "
        "**licensed compliance analyst approval**. This tool cannot make legal judgments "
        "or authorize enforcement actions."
    )
    
    @staticmethod
    def validate_input(user_input: str) -> Tuple[bool, str]:
        """
        Validate user input for prompt injection and policy violations.
        
        Args:
            user_input: User's input text
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            if not user_input or not isinstance(user_input, str):
                return False, "Input cannot be empty"
            
            # Length check
            if len(user_input) > LLMGuard.MAX_INPUT_LENGTH:
                return False, f"Input exceeds {LLMGuard.MAX_INPUT_LENGTH} character limit"
            
            # Dangerous pattern check
            user_input_lower = user_input.lower()
            for pattern in LLMGuard.DANGEROUS_PATTERNS:
                if re.search(pattern, user_input_lower, re.IGNORECASE):
                    return False, "Input contains suspicious patterns. Prompt injection detected."
            
            # PII leak check
            if LLMGuard.check_pii_leak(user_input):
                return False, "Input contains potential PII. Please anonymize user IDs."
            
            return True, "Input validated"
        
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def sanitize_output(text: str) -> str:
        """
        Sanitize LLM output by filtering forbidden patterns and adding disclaimer.
        
        Args:
            text: Original LLM output
            
        Returns:
            Sanitized output with disclaimer
        """
        try:
            if not text or not isinstance(text, str):
                return ""
            
            sanitized = text
            
            # Filter forbidden patterns
            for pattern in LLMGuard.FORBIDDEN_PATTERNS:
                # Replace with less conclusive language
                sanitized = re.sub(
                    pattern,
                    "[REQUIRES HUMAN REVIEW]",
                    sanitized,
                    flags=re.IGNORECASE
                )
            
            # Mask PII in output
            for pii_type, pattern in LLMGuard.PII_PATTERNS.items():
                sanitized = re.sub(pattern, f"[{pii_type.upper()}]", sanitized)
            
            # Add disclaimer
            sanitized = sanitized + LLMGuard.DISCLAIMER
            
            return sanitized
        
        except Exception as e:
            return f"Output processing error: {str(e)}"
    
    @staticmethod
    def check_pii_leak(text: str) -> bool:
        """
        Check if text contains PII that should not be exposed.
        
        Args:
            text: Text to check
            
        Returns:
            True if PII patterns detected, False otherwise
        """
        try:
            text_lower = text.lower()
            
            # Check for explicit PII mentions
            pii_keywords = ["phone", "id", "card", "ssn", "passport", "account number"]
            
            for keyword in pii_keywords:
                if keyword in text_lower:
                    return True
            
            # Check patterns
            for pattern in LLMGuard.PII_PATTERNS.values():
                if re.search(pattern, text):
                    return True
            
            return False
        
        except Exception as e:
            # On error, assume safety risk
            return True
