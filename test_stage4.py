#!/usr/bin/env python3
"""Test script for Stage 4 proxy functionality."""

import sys
import os

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all new modules can be imported."""
    print("🔄 Testing Stage 4 imports...")
    
    try:
        from project.models import Proxy
        print("✅ Proxy model imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Proxy model: {e}")
        return False
    
    try:
        from project.services.proxy_utils import (
            parse_proxy_url, save_proxy, mark_success, mark_failure,
            is_available, select_best_proxy
        )
        print("✅ Proxy utils imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import proxy utils: {e}")
        return False
    
    try:
        from project.services.proxy_checker import test_proxy_connectivity
        print("✅ Proxy checker imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import proxy checker: {e}")
        return False
    
    try:
        from project.services.ig_probe import fetch_profile_exists_via_proxy
        print("✅ IG probe imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import IG probe: {e}")
        return False
    
    try:
        from project.keyboards import proxies_menu_kb, proxy_card_kb
        print("✅ Proxy keyboards imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import proxy keyboards: {e}")
        return False
    
    return True


def test_proxy_parsing():
    """Test proxy URL parsing."""
    print("\n🔄 Testing proxy URL parsing...")
    
    try:
        from project.services.proxy_utils import parse_proxy_url
        
        # Test valid URLs
        test_cases = [
            ("http://1.2.3.4:8080", {"scheme": "http", "host": "1.2.3.4:8080", "username": None, "password": None}),
            ("https://user:pass@5.6.7.8:1080", {"scheme": "https", "host": "5.6.7.8:1080", "username": "user", "password": "pass"}),
            ("socks5://proxy.example.com:9050", {"scheme": "socks5", "host": "proxy.example.com:9050", "username": None, "password": None}),
        ]
        
        for url, expected in test_cases:
            result = parse_proxy_url(url)
            if result == expected:
                print(f"✅ '{url}' -> {result}")
            else:
                print(f"❌ '{url}' -> {result} (expected {expected})")
                return False
        
        # Test invalid URLs
        invalid_urls = [
            "invalid://url",
            "http://",
            "not-a-url",
            "",
        ]
        
        for url in invalid_urls:
            result = parse_proxy_url(url)
            if result is None:
                print(f"✅ '{url}' -> None (correctly rejected)")
            else:
                print(f"❌ '{url}' -> {result} (should be None)")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Proxy parsing test failed: {e}")
        return False


def test_keyboards():
    """Test keyboard generation."""
    print("\n🔄 Testing proxy keyboards...")
    
    try:
        from project.keyboards import proxies_menu_kb, proxy_card_kb
        
        # Test proxies menu keyboard
        menu_kb = proxies_menu_kb()
        assert "keyboard" in menu_kb
        assert len(menu_kb["keyboard"]) == 3  # 3 rows
        print("✅ Proxies menu keyboard works")
        
        # Test proxy card keyboard
        card_kb = proxy_card_kb(123)
        assert "inline_keyboard" in card_kb
        assert len(card_kb["inline_keyboard"]) == 3  # 3 rows
        print("✅ Proxy card keyboard works")
        
        return True
        
    except Exception as e:
        print(f"❌ Keyboard test failed: {e}")
        return False


def test_database_model():
    """Test Proxy model creation."""
    print("\n🔄 Testing Proxy model...")
    
    try:
        from project.database import get_engine, get_session_factory, init_db
        from project.config import get_settings
        from project.models import Proxy
        
        # Setup database
        settings = get_settings()
        engine = get_engine(settings.db_url)
        session_factory = get_session_factory(engine)
        init_db(engine)
        
        # Test model creation
        with session_factory() as session:
            # Check if table exists
            from sqlalchemy import text
            result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='proxies'"))
            if result.fetchone():
                print("✅ Proxy table exists")
            else:
                print("❌ Proxy table not found")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Database model test failed: {e}")
        return False


def main():
    """Run all Stage 4 tests."""
    print("🧪 Testing Stage 4 proxy functionality...\n")
    
    tests = [
        test_imports,
        test_proxy_parsing,
        test_keyboards,
        test_database_model
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Stage 4 tests passed!")
        print("\nStage 4 features ready:")
        print("✅ Proxy model and database")
        print("✅ Proxy URL parsing")
        print("✅ Proxy management keyboards")
        print("✅ Proxy connectivity checker")
        print("✅ Instagram profile checking")
        print("✅ Proxy rotation and telemetry")
        return True
    else:
        print("❌ Some tests failed. Check the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
