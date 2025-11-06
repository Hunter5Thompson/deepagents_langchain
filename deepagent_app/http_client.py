"""
HTTP Client Factory
Creates configured httpx clients for corporate environments.
"""

from typing import Optional

import httpx


def create_http_client(
    cert_path: Optional[str] = None,
    timeout: float = 30.0
) -> httpx.Client:
    """
    Create httpx client with optional certificate verification.
    
    Args:
        cert_path: Path to certificate file for corporate proxies
        timeout: Request timeout in seconds
        
    Returns:
        Configured httpx.Client instance
    """
    verify = cert_path if cert_path else True
    
    return httpx.Client(
        http2=True,
        verify=verify,
        timeout=timeout,
        follow_redirects=True,
    )