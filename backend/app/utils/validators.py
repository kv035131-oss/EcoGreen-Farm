"""
Validation and normalization helper functions.
"""

import re
from typing import Optional

def normalize_phone(phone_input: Optional[str]) -> Optional[str]:
    """
    Normalizes Indian & international phone numbers into E.164 format (+91XXXXXXXXXX).
    Accepts: '9876543210', '919876543210', '+919876543210', '98765-43210', '+91 98765 43210'
    Returns: '+919876543210' or None if invalid.
    """
    if not phone_input:
        return None
    
    cleaned = re.sub(r'[\s\-\(\)]', '', str(phone_input).strip())
    
    if not cleaned:
        return None
        
    if cleaned.startswith('+'):
        digits = cleaned[1:]
        if digits.isdigit() and 10 <= len(digits) <= 15:
            return cleaned
        return None
        
    if len(cleaned) == 10 and cleaned.isdigit() and cleaned[0] in '6789':
        return f"+91{cleaned}"
        
    if len(cleaned) == 12 and cleaned.isdigit() and cleaned.startswith('91'):
        return f"+{cleaned}"
        
    if cleaned.isdigit() and 10 <= len(cleaned) <= 15:
        return f"+91{cleaned[-10:]}"
        
    return None
