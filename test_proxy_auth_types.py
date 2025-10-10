#!/usr/bin/env python3
"""Test different proxy authentication methods."""

import asyncio
import base64
from aiohttp import ClientSession, ClientTimeout, BasicAuth
from aiohttp_socks import ProxyConnector, ProxyType


async def test_method_1_basic_auth_in_connector():
    """Method 1: Standard auth in ProxyConnector."""
    print("\n" + "="*60)
    print("Method 1: Standard ProxyConnector with username/password")
    print("="*60)
    
    connector = ProxyConnector(
        proxy_type=ProxyType.HTTP,
        host="213.209.130.121",
        port=50100,
        username="RriFXeBz",
        password="CpuhKzJlX0",
        rdns=True
    )
    
    timeout = ClientTimeout(total=10)
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        async with ClientSession(connector=connector, timeout=timeout, headers=headers) as sess:
            async with sess.get("http://httpbin.org/ip") as resp:
                print(f"✅ Status: {resp.status}")
                if resp.status == 200:
                    text = await resp.text()
                    print(f"✅ SUCCESS! Response: {text[:100]}")
                    return True
    except Exception as e:
        print(f"❌ Error: {e}")
    return False


async def test_method_2_from_url():
    """Method 2: Using from_url()."""
    print("\n" + "="*60)
    print("Method 2: ProxyConnector.from_url()")
    print("="*60)
    
    proxy_url = "http://RriFXeBz:CpuhKzJlX0@213.209.130.121:50100"
    
    connector = ProxyConnector.from_url(proxy_url)
    timeout = ClientTimeout(total=10)
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        async with ClientSession(connector=connector, timeout=timeout, headers=headers) as sess:
            async with sess.get("http://httpbin.org/ip") as resp:
                print(f"✅ Status: {resp.status}")
                if resp.status == 200:
                    text = await resp.text()
                    print(f"✅ SUCCESS! Response: {text[:100]}")
                    return True
    except Exception as e:
        print(f"❌ Error: {e}")
    return False


async def test_method_3_url_encoded_password():
    """Method 3: URL-encoded credentials."""
    print("\n" + "="*60)
    print("Method 3: URL-encoded credentials")
    print("="*60)
    
    from urllib.parse import quote
    
    username = quote("RriFXeBz")
    password = quote("CpuhKzJlX0")
    
    print(f"Original: RriFXeBz:CpuhKzJlX0")
    print(f"Encoded:  {username}:{password}")
    
    proxy_url = f"http://{username}:{password}@213.209.130.121:50100"
    
    connector = ProxyConnector.from_url(proxy_url)
    timeout = ClientTimeout(total=10)
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        async with ClientSession(connector=connector, timeout=timeout, headers=headers) as sess:
            async with sess.get("http://httpbin.org/ip") as resp:
                print(f"✅ Status: {resp.status}")
                if resp.status == 200:
                    text = await resp.text()
                    print(f"✅ SUCCESS! Response: {text[:100]}")
                    return True
    except Exception as e:
        print(f"❌ Error: {e}")
    return False


async def test_method_4_socks5_protocol():
    """Method 4: Try SOCKS5 instead of HTTP."""
    print("\n" + "="*60)
    print("Method 4: SOCKS5 protocol instead of HTTP")
    print("="*60)
    
    connector = ProxyConnector(
        proxy_type=ProxyType.SOCKS5,
        host="213.209.130.121",
        port=50100,
        username="RriFXeBz",
        password="CpuhKzJlX0",
        rdns=True
    )
    
    timeout = ClientTimeout(total=10)
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        async with ClientSession(connector=connector, timeout=timeout, headers=headers) as sess:
            async with sess.get("http://httpbin.org/ip") as resp:
                print(f"✅ Status: {resp.status}")
                if resp.status == 200:
                    text = await resp.text()
                    print(f"✅ SUCCESS! Response: {text[:100]}")
                    return True
    except Exception as e:
        print(f"❌ Error: {e}")
    return False


async def test_method_5_different_ports():
    """Method 5: Try different standard proxy ports."""
    print("\n" + "="*60)
    print("Method 5: Try different ports")
    print("="*60)
    
    ports = [50100, 8080, 3128, 80, 8888]
    
    for port in ports:
        print(f"\n🔍 Testing port {port}...")
        
        connector = ProxyConnector(
            proxy_type=ProxyType.HTTP,
            host="213.209.130.121",
            port=port,
            username="RriFXeBz",
            password="CpuhKzJlX0",
            rdns=True
        )
        
        timeout = ClientTimeout(total=5)
        headers = {"User-Agent": "Mozilla/5.0"}
        
        try:
            async with ClientSession(connector=connector, timeout=timeout, headers=headers) as sess:
                async with sess.get("http://httpbin.org/ip") as resp:
                    print(f"   ✅ Port {port}: Status {resp.status}")
                    if resp.status == 200:
                        text = await resp.text()
                        print(f"   ✅ SUCCESS on port {port}! Response: {text[:100]}")
                        return True
        except asyncio.TimeoutError:
            print(f"   ⏱️ Port {port}: Timeout")
        except Exception as e:
            print(f"   ❌ Port {port}: {type(e).__name__}")
    
    return False


async def test_method_6_no_rdns():
    """Method 6: Disable RDNS."""
    print("\n" + "="*60)
    print("Method 6: Disable RDNS (remote DNS)")
    print("="*60)
    
    connector = ProxyConnector(
        proxy_type=ProxyType.HTTP,
        host="213.209.130.121",
        port=50100,
        username="RriFXeBz",
        password="CpuhKzJlX0",
        rdns=False  # Changed to False
    )
    
    timeout = ClientTimeout(total=10)
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        async with ClientSession(connector=connector, timeout=timeout, headers=headers) as sess:
            async with sess.get("http://httpbin.org/ip") as resp:
                print(f"✅ Status: {resp.status}")
                if resp.status == 200:
                    text = await resp.text()
                    print(f"✅ SUCCESS! Response: {text[:100]}")
                    return True
    except Exception as e:
        print(f"❌ Error: {e}")
    return False


async def test_method_7_case_variations():
    """Method 7: Try different case variations of credentials."""
    print("\n" + "="*60)
    print("Method 7: Case variations")
    print("="*60)
    
    variations = [
        ("RriFXeBz", "CpuhKzJlX0"),  # Original
        ("rrifxebz", "cpuhkzjlx0"),  # Lowercase
        ("RRIFXEBZ", "CPUHKZJLX0"),  # Uppercase
    ]
    
    for i, (user, pwd) in enumerate(variations, 1):
        print(f"\n🔍 Variation {i}: {user}:{pwd}")
        
        connector = ProxyConnector(
            proxy_type=ProxyType.HTTP,
            host="213.209.130.121",
            port=50100,
            username=user,
            password=pwd,
            rdns=True
        )
        
        timeout = ClientTimeout(total=5)
        headers = {"User-Agent": "Mozilla/5.0"}
        
        try:
            async with ClientSession(connector=connector, timeout=timeout, headers=headers) as sess:
                async with sess.get("http://httpbin.org/ip") as resp:
                    print(f"   ✅ Status: {resp.status}")
                    if resp.status == 200:
                        text = await resp.text()
                        print(f"   ✅ SUCCESS with {user}:{pwd}!")
                        print(f"   Response: {text[:100]}")
                        return True
        except Exception as e:
            print(f"   ❌ Error: {type(e).__name__}")
    
    return False


async def test_method_8_reversed_credentials():
    """Method 8: Maybe credentials are reversed?"""
    print("\n" + "="*60)
    print("Method 8: Reversed credentials (password:username)")
    print("="*60)
    
    connector = ProxyConnector(
        proxy_type=ProxyType.HTTP,
        host="213.209.130.121",
        port=50100,
        username="CpuhKzJlX0",  # Swapped
        password="RriFXeBz",    # Swapped
        rdns=True
    )
    
    timeout = ClientTimeout(total=10)
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        async with ClientSession(connector=connector, timeout=timeout, headers=headers) as sess:
            async with sess.get("http://httpbin.org/ip") as resp:
                print(f"✅ Status: {resp.status}")
                if resp.status == 200:
                    text = await resp.text()
                    print(f"✅ SUCCESS with reversed creds! Response: {text[:100]}")
                    return True
    except Exception as e:
        print(f"❌ Error: {e}")
    return False


async def main():
    """Run all authentication tests."""
    print("🔐 TESTING DIFFERENT PROXY AUTHENTICATION METHODS")
    print("Proxy: 213.209.130.121:50100")
    print("Credentials: RriFXeBz:CpuhKzJlX0")
    
    tests = [
        ("Standard auth", test_method_1_basic_auth_in_connector),
        ("from_url()", test_method_2_from_url),
        ("URL-encoded", test_method_3_url_encoded_password),
        ("SOCKS5 protocol", test_method_4_socks5_protocol),
        ("Different ports", test_method_5_different_ports),
        ("No RDNS", test_method_6_no_rdns),
        ("Case variations", test_method_7_case_variations),
        ("Reversed creds", test_method_8_reversed_credentials),
    ]
    
    results = {}
    
    for name, test_func in tests:
        try:
            result = await test_func()
            results[name] = result
            if result:
                print(f"\n🎉 FOUND WORKING METHOD: {name}")
                break  # Stop on first success
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    working = [name for name, result in results.items() if result]
    failed = [name for name, result in results.items() if not result]
    
    if working:
        print(f"\n✅ WORKING METHODS ({len(working)}):")
        for name in working:
            print(f"   ✅ {name}")
    
    if failed:
        print(f"\n❌ FAILED METHODS ({len(failed)}):")
        for name in failed:
            print(f"   ❌ {name}")
    
    if not working:
        print("\n⚠️ NO WORKING METHOD FOUND")
        print("\n💡 RECOMMENDATIONS:")
        print("   1. Contact your proxy provider")
        print("   2. Verify credentials in provider dashboard")
        print("   3. Check if your IP is whitelisted")
        print("   4. Try a different proxy")
    else:
        print(f"\n🎉 Use the working method in production!")


if __name__ == "__main__":
    asyncio.run(main())
