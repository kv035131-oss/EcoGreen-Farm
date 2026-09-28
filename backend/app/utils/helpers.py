"""
General helper functions for EcoGreen application.
"""

from typing import Dict, Any

def format_currency(amount: float) -> str:
    """Formats float amount into currency string."""
    return f"₹{amount:,.2f}"

def api_response(status: str = 'success', message: str = '', data: Any = None, code: int = 200) -> tuple:
    """Standardized API JSON response builder."""
    payload = {'status': status}
    if message:
        payload['message'] = message
    if data is not None:
        payload['data'] = data
    return payload, code
