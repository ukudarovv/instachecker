#!/usr/bin/env python3
"""Test SOCKS5 proxy authentication fix."""

import asyncio
import sys
import os

# Add project to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'project'))

from services.proxy_checker import test_proxy_connectivity, check_account_via_proxy
from models import Proxy

async def test_socks5_proxy():
    """Test SOCKS5 proxy with and without authentication."""
    
    print("🧪 Testing SOCKS5 proxy authentication fix...")
    
    # Test 1: SOCKS5 without auth (should work)
    print("\n1️⃣ Testing SOCKS5 without authentication:")
    proxy_no_auth = Proxy(
        id=1,
        host="127.0.0.1",
        port=1080,
        scheme="socks5",
        username=None,
        password=None,
        is_active=True
    )
    
    result1 = await test_proxy_connectivity(proxy_no_auth, timeout_ms=5000)
    print(f"   Result: {result1}")
    
    # Test 2: SOCKS5 with auth (should use without auth)
    print("\n2️⃣ Testing SOCKS5 with authentication:")
    proxy_with_auth = Proxy(
        id=2,
        host="127.0.0.1", 
        port=1080,
        scheme="socks5",
        username="testuser",
        password="testpass",
        is_active=True
    )
    
    result2 = await test_proxy_connectivity(proxy_with_auth, timeout_ms=5000)
    print(f"   Result: {result2}")
    
    # Test 3: HTTP proxy with auth (should work normally)
    print("\n3️⃣ Testing HTTP proxy with authentication:")
    proxy_http = Proxy(
        id=3,
        host="127.0.0.1",
        port=8080,
        scheme="http",
        username="testuser",
        password="testpass",
        is_active=True
    )
    
    result3 = await test_proxy_connectivity(proxy_http, timeout_ms=5000)
    print(f"   Result: {result3}")
    
    print("\n✅ SOCKS5 authentication fix test completed!")
    print("💡 Note: SOCKS5 with auth will use without auth (Playwright limitation)")
    print("💡 Tip: Use HTTP proxies with authentication for better compatibility")

if __name__ == "__main__":
    asyncio.run(test_socks5_proxy())
