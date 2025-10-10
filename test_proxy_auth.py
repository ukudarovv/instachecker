#!/usr/bin/env python3
"""Test proxy authentication."""

import sys
import os
import asyncio
from urllib.parse import urlparse
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


async def test_proxy_url_parsing():
    """Test how we parse proxy URLs."""
    print("🔍 Testing proxy URL parsing...\n")
    
    # Test URL from logs
    proxy_url = "http://RriFXeBz:CpuhKzJlX0@213.209.130.121:50100"
    
    parsed = urlparse(proxy_url)
    
    print(f"Original URL: {proxy_url}")
    print(f"Scheme: {parsed.scheme}")
    print(f"Hostname: {parsed.hostname}")
    print(f"Port: {parsed.port}")
    print(f"Username: {parsed.username}")
    print(f"Password: {parsed.password}")
    
    if parsed.username and parsed.password:
        print(f"✅ Auth detected: {parsed.username}:{parsed.password}")
    else:
        print("❌ No auth detected")
    
    return parsed


async def test_proxy_connector_creation():
    """Test ProxyConnector creation with auth."""
    print("\n🔍 Testing ProxyConnector creation...\n")
    
    from aiohttp_socks import ProxyConnector, ProxyType
    
    # Real proxy from logs
    proxy_url = "http://RriFXeBz:CpuhKzJlX0@213.209.130.121:50100"
    parsed = urlparse(proxy_url)
    
    print(f"Creating connector with:")
    print(f"  proxy_type: HTTP")
    print(f"  host: {parsed.hostname}")
    print(f"  port: {parsed.port}")
    print(f"  username: {parsed.username}")
    print(f"  password: {parsed.password}")
    
    try:
        connector = ProxyConnector(
            proxy_type=ProxyType.HTTP,
            host=parsed.hostname,
            port=parsed.port,
            username=parsed.username,
            password=parsed.password,
            rdns=True
        )
        print("✅ Connector created successfully")
        print(f"   Connector: {connector}")
        print(f"   Proxy type: {connector._proxy_type}")
        print(f"   Proxy host: {connector._proxy_host}")
        print(f"   Proxy port: {connector._proxy_port}")
        print(f"   Has username: {connector._proxy_username is not None}")
        print(f"   Has password: {connector._proxy_password is not None}")
        return connector
    except Exception as e:
        print(f"❌ Failed to create connector: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_actual_connection():
    """Test actual connection through proxy."""
    print("\n🔍 Testing actual connection through proxy...\n")
    
    from aiohttp import ClientSession, ClientTimeout
    from aiohttp_socks import ProxyConnector, ProxyType
    
    # Real proxy from logs
    proxy_url = "http://RriFXeBz:CpuhKzJlX0@213.209.130.121:50100"
    parsed = urlparse(proxy_url)
    
    connector = ProxyConnector(
        proxy_type=ProxyType.HTTP,
        host=parsed.hostname,
        port=parsed.port,
        username=parsed.username,
        password=parsed.password,
        rdns=True
    )
    
    timeout = ClientTimeout(total=10)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit Safari/537.36"}
    
    test_urls = [
        "http://httpbin.org/ip",  # Should return your proxy IP
        "https://www.instagram.com/",
    ]
    
    for url in test_urls:
        print(f"\n📡 Testing: {url}")
        try:
            async with ClientSession(connector=connector, timeout=timeout, headers=headers) as sess:
                async with sess.get(url, allow_redirects=True) as resp:
                    print(f"   Status: {resp.status}")
                    if resp.status == 200:
                        text = await resp.text()
                        print(f"   ✅ Success! Got {len(text)} chars")
                        if 'httpbin' in url:
                            print(f"   Response preview: {text[:200]}")
                    elif resp.status == 407:
                        print(f"   ❌ 407 Proxy Authentication Required")
                    else:
                        print(f"   ⚠️ Unexpected status: {resp.status}")
        except Exception as e:
            print(f"   ❌ Error: {type(e).__name__}: {e}")


async def test_alternative_auth_format():
    """Test alternative way to pass proxy auth."""
    print("\n🔍 Testing alternative auth format (BasicAuth)...\n")
    
    from aiohttp import ClientSession, ClientTimeout, BasicAuth
    from aiohttp_socks import ProxyConnector, ProxyType
    
    proxy_url = "http://RriFXeBz:CpuhKzJlX0@213.209.130.121:50100"
    parsed = urlparse(proxy_url)
    
    # Try with explicit BasicAuth
    connector = ProxyConnector(
        proxy_type=ProxyType.HTTP,
        host=parsed.hostname,
        port=parsed.port,
        username=parsed.username,
        password=parsed.password,
        rdns=True
    )
    
    timeout = ClientTimeout(total=10)
    headers = {"User-Agent": "Mozilla/5.0"}
    
    print(f"Trying connection with BasicAuth in connector...")
    
    try:
        async with ClientSession(connector=connector, timeout=timeout, headers=headers) as sess:
            async with sess.get("http://httpbin.org/ip", allow_redirects=True) as resp:
                print(f"   Status: {resp.status}")
                if resp.status == 200:
                    text = await resp.text()
                    print(f"   ✅ Success! {text[:100]}")
                else:
                    print(f"   ❌ Failed with status {resp.status}")
    except Exception as e:
        print(f"   ❌ Error: {e}")


async def test_proxy_from_utils():
    """Test proxy creation using our actual code."""
    print("\n🔍 Testing with our actual proxy_utils code...\n")
    
    from project.services.proxy_utils import parse_proxy_url
    
    proxy_url = "http://RriFXeBz:CpuhKzJlX0@213.209.130.121:50100"
    
    parsed = parse_proxy_url(proxy_url)
    print(f"Parsed by our code: {parsed}")
    
    if parsed:
        print("✅ Our parser works correctly")
        print(f"   scheme: {parsed['scheme']}")
        print(f"   host: {parsed['host']}")
        print(f"   user: {parsed.get('user', 'None')}")
        print(f"   pass: {parsed.get('pass', 'None')}")
    else:
        print("❌ Our parser failed")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("🧪 PROXY AUTHENTICATION TEST")
    print("=" * 60)
    
    # Test 1: URL parsing
    await test_proxy_url_parsing()
    
    # Test 2: Connector creation
    await test_proxy_connector_creation()
    
    # Test 3: Our parser
    await test_proxy_from_utils()
    
    # Test 4: Actual connection
    await test_actual_connection()
    
    # Test 5: Alternative auth format
    await test_alternative_auth_format()
    
    print("\n" + "=" * 60)
    print("✅ All tests completed")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
