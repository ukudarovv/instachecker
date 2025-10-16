"""Test screenshot sending when account is already active."""

import asyncio
import sys
import os
from datetime import date, timedelta

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from project.config import get_settings
from project.database import get_session_factory, get_engine
from project.models import User, Account
from project.services.hybrid_checker import check_account_hybrid
from project.services.ig_sessions import get_priority_valid_session
from project.utils.encryptor import OptionalFernet
from project.utils.async_bot_wrapper import AsyncBotWrapper


async def test_screenshot_on_active_account():
    """Test screenshot sending when account is already active."""
    settings = get_settings()
    engine = get_engine(settings.db_url)
    SessionLocal = get_session_factory(engine)
    fernet = OptionalFernet(settings.encryption_key)
    
    # Create async bot wrapper
    bot = AsyncBotWrapper(settings.bot_token)
    
    with SessionLocal() as session:
        # Get admin user
        admin = session.query(User).filter(
            User.role.in_(['admin', 'superuser']),
            User.is_active == True
        ).first()
        
        if not admin:
            print("[TEST] ❌ Admin user not found!")
            return
        
        print(f"[TEST] Found admin: ID={admin.id}, username={admin.username}")
        
        # Get user's Instagram session
        ig_session = get_priority_valid_session(session, admin.id, fernet)
        
        if not ig_session:
            print("[TEST] ❌ No valid Instagram session found for admin!")
            return
        
        print(f"[TEST] Found Instagram session: ID={ig_session.id}")
        
        # Test username
        test_username = "hava101012"
        print(f"[TEST] Testing with username: @{test_username}")
        
        print("\n[TEST] Performing hybrid check...")
        
        try:
            # Perform hybrid check
            result = await check_account_hybrid(
                session=session,
                user_id=admin.id,
                username=test_username,
                ig_session=ig_session,
                fernet=fernet
            )
            
            print(f"[TEST] Check result: {result}")
            
            # Simulate the logic from bot.py
            if result.get("exists") is True:
                print(f"[TEST] ✅ Account @{test_username} is active!")
                
                # Send success message
                success_message = f"✅ <a href='https://www.instagram.com/{test_username}/'>@{test_username}</a> уже активен!"
                print(f"[TEST] Sending message: {success_message}")
                
                # Check if screenshot is available
                if result.get("screenshot_path"):
                    screenshot_path = result["screenshot_path"]
                    print(f"[TEST] 📸 Screenshot available: {screenshot_path}")
                    
                    import os
                    if os.path.exists(screenshot_path):
                        print(f"[TEST] 📸 Screenshot file exists, size: {os.path.getsize(screenshot_path)} bytes")
                        
                        # Send screenshot
                        try:
                            print(f"[TEST] 📸 Sending screenshot to user {admin.id}...")
                            success = await bot.send_photo(
                                admin.id,
                                screenshot_path,
                                f'📸 <a href="https://www.instagram.com/{test_username}/">@{test_username}</a>'
                            )
                            
                            if success:
                                print(f"[TEST] ✅ Screenshot sent successfully!")
                                # Delete screenshot after sending
                                os.remove(screenshot_path)
                                print(f"[TEST] 🗑 Screenshot deleted: {screenshot_path}")
                            else:
                                print(f"[TEST] ⚠️ Screenshot send returned False")
                        except Exception as e:
                            print(f"[TEST] ❌ Failed to send photo: {e}")
                            import traceback
                            traceback.print_exc()
                    else:
                        print(f"[TEST] ⚠️ Screenshot file NOT found: {screenshot_path}")
                else:
                    print(f"[TEST] ⚠️ No screenshot path in result")
                    
            elif result.get("exists") is False:
                print(f"[TEST] ❌ Account @{test_username} not found")
            else:
                print(f"[TEST] ❓ Account @{test_username} check failed: {result.get('error', 'unknown')}")
                
        except Exception as e:
            print(f"[TEST] ❌ Error during check: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("=" * 80)
    print("ТЕСТ ОТПРАВКИ СКРИНШОТА ПРИ ДОБАВЛЕНИИ АКТИВНОГО АККАУНТА")
    print("=" * 80)
    print()
    
    asyncio.run(test_screenshot_on_active_account())
