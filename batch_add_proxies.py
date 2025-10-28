"""
📥 Batch Proxy Import Script

Quickly import your list of proxies from DeepSeek's format:
ip:port:username:password

Usage:
    python batch_add_proxies.py --user-id 123 --file proxies.txt
    python batch_add_proxies.py --user-id 123 --inline "ip:port:user:pass"
"""

import argparse
import asyncio
import sys
import os

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from project.database import get_session_factory
from project.services.proxy_manager import ProxyManager
from project.services.proxy_health_checker import check_user_proxies_health


def main():
    parser = argparse.ArgumentParser(description='Batch import proxies')
    parser.add_argument('--user-id', type=int, required=True, help='User ID to assign proxies to')
    parser.add_argument('--file', type=str, help='File with proxy list')
    parser.add_argument('--inline', type=str, help='Inline proxy list (newline separated)')
    parser.add_argument('--test', action='store_true', help='Test proxies after import')
    parser.add_argument('--scheme', type=str, default='http', choices=['http', 'https', 'socks5'], 
                       help='Proxy scheme (default: http)')
    
    args = parser.parse_args()
    
    # Get proxy list
    if args.file:
        print(f"📁 Reading proxies from file: {args.file}")
        with open(args.file, 'r') as f:
            proxy_list = f.read()
    elif args.inline:
        print(f"📝 Using inline proxy list")
        proxy_list = args.inline
    else:
        print("❌ Error: Must provide either --file or --inline")
        sys.exit(1)
    
    # Import proxies
    print(f"\n📥 Importing proxies for user {args.user_id}...")
    print("=" * 60)
    
    SessionLocal = get_session_factory()
    
    with SessionLocal() as session:
        manager = ProxyManager(session)
        stats = manager.batch_add_proxies(proxy_list, args.user_id)
    
    print("\n" + "=" * 60)
    print("📊 Import Summary:")
    print(f"   ✅ Added: {stats['added']}")
    print(f"   ⏭️  Skipped (duplicates): {stats['skipped']}")
    print(f"   ❌ Errors: {stats['errors']}")
    print("=" * 60)
    
    # Test proxies if requested
    if args.test and stats['added'] > 0:
        print(f"\n🧪 Testing imported proxies...")
        print("=" * 60)
        
        result = asyncio.run(check_user_proxies_health(args.user_id))
        
        print(f"\n📊 Test Results:")
        print(f"   ✅ Healthy: {result['healthy']}/{result['total']}")
        print(f"   ❌ Unhealthy: {result['unhealthy']}/{result['total']}")
        print("=" * 60)
    
    print(f"\n✅ Done!")


if __name__ == '__main__':
    main()





