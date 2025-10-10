#!/usr/bin/env python3
"""Direct proxy test with different methods."""

import asyncio
from aiohttp import ClientSession, ClientTimeout
from aiohttp_socks import ProxyConnector


async def test_from_url_method():
    """Test using ProxyConnector.from_url() method."""
    print("🔍 Testing ProxyConnector.from_url() method...\n")
    
    proxy_url = "http://RriFXeBz:CpuhKzJlX0@213.209.130.121:50100"
    
    print(f"Proxy URL: {proxy_url}")
    
    try:
        connector = ProxyConnector.from_url(proxy_url)
        print(f"✅ Connector created: {connector}")
        print(f"   Proxy type: {connector._proxy_type}")
        print(f"   Proxy host: {connector._proxy_host}")
        print(f"   Proxy port: {connector._proxy_port}")
        print(f"   Has username: {connector._proxy_username is not None}")
        print(f"   Has password: {connector._proxy_password is not None}")
        
        # Try connection
        print("\n📡 Testing connection to httpbin.org...")
        timeout = ClientTimeout(total=10)
        headers = {"User-Agent": "Mozilla/5.0"}
        
        async with ClientSession(connector=connector, timeout=timeout, headers=headers) as sess:
            try:
                async with sess.get("http://httpbin.org/ip") as resp:
                    print(f"   Status: {resp.status}")
                    if resp.status == 200:
                        text = await resp.text()
                        print(f"   ✅ Success! Response: {text[:200]}")
                        return True
                    else:
                        print(f"   ❌ Failed with status {resp.status}")
                        return False
            except Exception as e:
                print(f"   ❌ Connection error: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_without_auth():
    """Test if proxy works without auth."""
    print("\n🔍 Testing proxy without auth (to check if it's open)...\n")
    
    from aiohttp_socks import ProxyType
    
    connector = ProxyConnector(
        proxy_type=ProxyType.HTTP,
        host="213.209.130.121",
        port=50100,
        rdns=True
    )
    
    print("Trying without credentials...")
    
    timeout = ClientTimeout(total=10)
    try:
        async with ClientSession(connector=connector, timeout=timeout) as sess:
            async with sess.get("http://httpbin.org/ip") as resp:
                print(f"   Status: {resp.status}")
                if resp.status == 200:
                    print("   ✅ Works without auth!")
                    return True
                else:
                    print(f"   ❌ Status {resp.status}")
                    return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


async def test_with_manual_headers():
    """Test with manual Proxy-Authorization header."""
    print("\n🔍 Testing with manual Proxy-Authorization header...\n")
    
    import base64
    from aiohttp_socks import ProxyType
    
    # Create auth header
    auth_str = f"RriFXeBz:CpuhKzJlX0"
    auth_bytes = auth_str.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    print(f"Auth header: Proxy-Authorization: Basic {auth_b64}")
    
    connector = ProxyConnector(
        proxy_type=ProxyType.HTTP,
        host="213.209.130.121",
        port=50100,
        rdns=True
    )
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Proxy-Authorization": f"Basic {auth_b64}"
    }
    
    timeout = ClientTimeout(total=10)
    try:
        async with ClientSession(connector=connector, timeout=timeout, headers=headers) as sess:
            async with sess.get("http://httpbin.org/ip") as resp:
                print(f"   Status: {resp.status}")
                if resp.status == 200:
                    text = await resp.text()
                    print(f"   ✅ Success with manual header! {text[:100]}")
                    return True
                else:
                    print(f"   ❌ Status {resp.status}")
                    return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


async def test_direct_connection():
    """Test direct connection without proxy."""
    print("\n🔍 Testing direct connection (no proxy) to verify network...\n")
    
    timeout = ClientTimeout(total=10)
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        async with ClientSession(timeout=timeout, headers=headers) as sess:
            async with sess.get("http://httpbin.org/ip") as resp:
                print(f"   Status: {resp.status}")
                if resp.status == 200:
                    text = await resp.text()
                    print(f"   ✅ Direct connection works! Your IP: {text[:200]}")
                    return True
                else:
                    print(f"   ❌ Status {resp.status}")
                    return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 70)
    print("🧪 COMPREHENSIVE PROXY TEST")
    print("=" * 70)
    
    results = {}
    
    # Test 1: Direct connection
    results['direct'] = await test_direct_connection()
    
    # Test 2: from_url method
    results['from_url'] = await test_from_url_method()
    
    # Test 3: Without auth
    results['no_auth'] = await test_without_auth()
    
    # Test 4: Manual headers
    results['manual_headers'] = await test_with_manual_headers()
    
    print("\n" + "=" * 70)
    print("📊 RESULTS:")
    print("=" * 70)
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name:20s}: {status}")
    
    print("\n💡 ANALYSIS:")
    if results['direct']:
        print("  ✅ Network connection is working")
    else:
        print("  ❌ Network issue - can't connect to internet")
    
    if results['from_url']:
        print("  ✅ Proxy works with from_url() method")
    elif results['no_auth']:
        print("  ⚠️ Proxy works WITHOUT auth - credentials might be wrong")
    elif results['manual_headers']:
        print("  ⚠️ Proxy works with manual headers only")
    else:
        print("  ❌ Proxy is not working or blocked")
    
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
