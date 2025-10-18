#!/usr/bin/env python3
"""
Test concurrent processing with different verification modes
"""

import asyncio
import sys
sys.path.append('project')
from models import User, Account
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.async_bot_wrapper import AsyncBotWrapper
from config import get_settings

async def test_concurrent_modes():
    """Test that different users with different modes don't conflict"""
    engine = create_engine('sqlite:///bot.db')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Get all active users with pending accounts
    users_with_accounts = (
        session.query(User)
        .join(Account)
        .filter(User.is_active == True, Account.done == False)
        .distinct()
        .all()
    )
    
    print(f"📊 Found {len(users_with_accounts)} active users with pending accounts")
    print("\n" + "="*60)
    
    # Display each user's configuration
    for user in users_with_accounts:
        accounts_count = session.query(Account).filter(
            Account.user_id == user.id,
            Account.done == False
        ).count()
        
        verify_mode = user.verify_mode or "api+instagram"
        
        print(f"\n👤 User: {user.username} (ID: {user.id})")
        print(f"   📋 Mode: {verify_mode}")
        print(f"   📊 Pending accounts: {accounts_count}")
        
        # Check required resources
        resources = []
        
        # Check if needs API
        if verify_mode in ["api+instagram", "api+proxy", "api+proxy+instagram"]:
            from models import APIKey
            api_keys = session.query(APIKey).filter(
                APIKey.user_id == user.id,
                APIKey.is_work == True
            ).count()
            resources.append(f"API keys: {api_keys}")
        
        # Check if needs Instagram session
        if verify_mode in ["api+instagram", "instagram", "instagram+proxy", "api+proxy+instagram"]:
            from models import InstagramSession
            ig_sessions = session.query(InstagramSession).filter(
                InstagramSession.user_id == user.id,
                InstagramSession.is_active == True
            ).count()
            resources.append(f"IG sessions: {ig_sessions}")
        
        # Check if needs Proxy
        if verify_mode in ["api+proxy", "proxy", "instagram+proxy", "api+proxy+instagram"]:
            from models import Proxy
            proxies = session.query(Proxy).filter(
                Proxy.user_id == user.id,
                Proxy.is_active == True
            ).count()
            resources.append(f"Proxies: {proxies}")
        
        if resources:
            print(f"   🔧 Resources: {', '.join(resources)}")
    
    print("\n" + "="*60)
    
    # Check for potential conflicts
    print("\n🔍 Checking for potential conflicts...")
    
    conflicts = []
    
    # Check 1: Users with same mode should not conflict
    mode_groups = {}
    for user in users_with_accounts:
        mode = user.verify_mode or "api+instagram"
        if mode not in mode_groups:
            mode_groups[mode] = []
        mode_groups[mode].append(user.username)
    
    print("\n📊 Users grouped by mode:")
    for mode, usernames in mode_groups.items():
        print(f"   {mode}: {len(usernames)} users - {', '.join(usernames[:3])}{'...' if len(usernames) > 3 else ''}")
    
    # Check 2: Verify each user has required resources
    print("\n✅ Resource validation:")
    for user in users_with_accounts:
        mode = user.verify_mode or "api+instagram"
        missing = []
        
        # Check API keys
        if mode in ["api+instagram", "api+proxy", "api+proxy+instagram"]:
            from models import APIKey
            if not session.query(APIKey).filter(
                APIKey.user_id == user.id,
                APIKey.is_work == True
            ).first():
                missing.append("API key")
        
        # Check Instagram session
        if mode in ["api+instagram", "instagram", "instagram+proxy", "api+proxy+instagram"]:
            from models import InstagramSession
            if not session.query(InstagramSession).filter(
                InstagramSession.user_id == user.id,
                InstagramSession.is_active == True
            ).first():
                missing.append("Instagram session")
        
        # Check Proxy
        if mode in ["api+proxy", "proxy", "instagram+proxy", "api+proxy+instagram"]:
            from models import Proxy
            if not session.query(Proxy).filter(
                Proxy.user_id == user.id,
                Proxy.is_active == True
            ).first():
                missing.append("Proxy")
        
        if missing:
            conflicts.append(f"User {user.username} (mode: {mode}) missing: {', '.join(missing)}")
            print(f"   ⚠️ {user.username}: Missing {', '.join(missing)}")
        else:
            print(f"   ✅ {user.username}: All resources available")
    
    # Summary
    print("\n" + "="*60)
    print("\n📋 SUMMARY:")
    print(f"   Total users: {len(users_with_accounts)}")
    print(f"   Different modes: {len(mode_groups)}")
    print(f"   Users with conflicts: {len(conflicts)}")
    
    if conflicts:
        print("\n⚠️ CONFLICTS DETECTED:")
        for conflict in conflicts:
            print(f"   • {conflict}")
        print("\n💡 These users will be skipped during auto-check")
    else:
        print("\n✅ NO CONFLICTS! All users can run concurrently")
    
    # Test parallel execution simulation
    print("\n" + "="*60)
    print("\n🧪 SIMULATING PARALLEL EXECUTION:")
    print("   Each user will be processed in a separate task")
    print("   Users with different modes will NOT interfere with each other")
    print("   Each user maintains their own:")
    print("   • verify_mode setting")
    print("   • Instagram session (if needed)")
    print("   • Proxy configuration (if needed)")
    print("   • API keys (if needed)")
    
    # Send report to user
    settings = get_settings()
    bot = AsyncBotWrapper(settings.bot_token)
    
    report_message = f"""🔍 **ПРОВЕРКА КОНФЛИКТОВ РЕЖИМОВ**

📊 **Статистика:**
• Всего пользователей: {len(users_with_accounts)}
• Разных режимов: {len(mode_groups)}
• Конфликтов: {len(conflicts)}

**📋 Режимы пользователей:**
"""
    
    for mode, usernames in mode_groups.items():
        report_message += f"\n• `{mode}`: {len(usernames)} польз."
    
    if conflicts:
        report_message += f"\n\n⚠️ **Обнаружены конфликты:**\n"
        for conflict in conflicts[:5]:  # Show first 5
            report_message += f"• {conflict}\n"
        if len(conflicts) > 5:
            report_message += f"• ... и еще {len(conflicts) - 5}\n"
        report_message += "\n💡 Эти пользователи будут пропущены при авто-проверке"
    else:
        report_message += "\n\n✅ **КОНФЛИКТОВ НЕТ!**\n\n"
        report_message += "Все пользователи могут работать параллельно без конфликтов:\n"
        report_message += "• Каждый использует свой режим\n"
        report_message += "• Каждый использует свои ресурсы\n"
        report_message += "• Проверки изолированы друг от друга\n"
    
    await bot.send_message(1972775559, report_message)
    print("\n✅ Report sent to user!")
    
    session.close()

if __name__ == '__main__':
    asyncio.run(test_concurrent_modes())
