#!/usr/bin/env python3
"""Debug SOCKS5 proxy authentication issue."""

import asyncio
import sys
import os

# Add project to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'project'))

from services.proxy_checker import test_proxy_connectivity
from models import Proxy

async def debug_socks5():
    """Debug SOCKS5 proxy issue."""
    
    print("🔍 Debugging SOCKS5 proxy authentication...")
    
    # Create a SOCKS5 proxy with authentication
    proxy = Proxy(
        id=1,
        user_id=1,
        host="127.0.0.1:1080",
        scheme="socks5",
        username="testuser",
        password="testpass",
        is_active=True
    )
    
    print(f"Proxy: {proxy.scheme}://{proxy.host}")
    print(f"Auth: {proxy.username}:{proxy.password}")
    
    # Test connectivity
    print("\n🧪 Testing proxy connectivity...")
    result = await test_proxy_connectivity(proxy, timeout_ms=5000)
    
    print(f"Result: {result}")
    
    if result["error"]:
        print(f"Error: {result['error']}")
        
        # Check if it's the SOCKS5 auth error
        if "socks5 proxy authentication" in result["error"].lower():
            print("❌ Still getting SOCKS5 auth error - fix not applied!")
        else:
            print("✅ SOCKS5 auth error fixed, but other error occurred")

if __name__ == "__main__":
    asyncio.run(debug_socks5())
