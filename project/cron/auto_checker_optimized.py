"""Optimized automatic background checker with parallel batch processing."""

import asyncio
import os
import random
from datetime import datetime, timedelta, date
from sqlalchemy.orm import sessionmaker

try:
    from ..models import Account, User
    from ..services.main_checker import check_account_main
    from ..services.system_settings import get_global_verify_mode
    from ..services.traffic_monitor import get_traffic_monitor
    from ..services.autocheck_traffic_stats import AutoCheckTrafficStats
    from ..utils.encryptor import OptionalFernet
    from ..config import get_settings
except ImportError:
    from models import Account, User
    from services.main_checker import check_account_main
    from services.system_settings import get_global_verify_mode
    from services.traffic_monitor import get_traffic_monitor
    from services.autocheck_traffic_stats import AutoCheckTrafficStats
    from utils.encryptor import OptionalFernet
    from config import get_settings


async def send_notification_async(bot, user, acc, screenshot_path, message_text):
    """Send notification to user asynchronously without blocking."""
    try:
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                await bot.send_photo(user.id, screenshot_path, message_text)
                print(f"[AUTO-CHECK] 📸 Screenshot sent successfully!")
            except Exception as e:
                print(f"[AUTO-CHECK] ❌ Failed to send photo: {e}")
                await bot.send_message(user.id, message_text)
        else:
            await bot.send_message(user.id, message_text)
    except Exception as e:
        print(f"[AUTO-CHECK] ❌ Failed to send notification: {e}")


async def check_single_account_optimized(acc, user_id: int, user, session, traffic_monitor, bot=None):
    """
    Check a single account (optimized for parallel execution).
    
    Returns:
        Tuple: (acc, result_dict)
    """
    check_start_traffic = traffic_monitor.total_traffic
    check_start_time = datetime.now()
    
    result = {
        'success': False,
        'message': '',
        'screenshot_path': None,
        'traffic_bytes': 0,
        'duration_ms': 0,
        'error': False,
        'marked_done': False
    }
    
    try:
        # Check account
        success, message, screenshot_path = await check_account_main(
            username=acc.account,
            session=session,
            user_id=user_id
        )
        
        # Calculate metrics
        check_end_time = datetime.now()
        check_traffic = traffic_monitor.total_traffic - check_start_traffic
        check_duration_ms = (check_end_time - check_start_time).total_seconds() * 1000
        
        result.update({
            'success': success,
            'message': message,
            'screenshot_path': screenshot_path,
            'traffic_bytes': check_traffic,
            'duration_ms': check_duration_ms
        })
        
        # Mark as done if found
        if success:
            account = session.query(Account).filter(
                Account.user_id == user_id,
                Account.account == acc.account
            ).first()
            
            if account:
                account.done = True
                account.date_of_finish = date.today()
                session.commit()
                result['marked_done'] = True
                
                # Send notification asynchronously (don't wait)
                if bot:
                    # Calculate completion time
                    completed_text = "1 дней"
                    if hasattr(acc, 'from_date_time') and acc.from_date_time:
                        start_datetime = acc.from_date_time
                    elif acc.from_date:
                        start_datetime = datetime.combine(acc.from_date, datetime.min.time()) if not isinstance(acc.from_date, datetime) else acc.from_date
                    else:
                        start_datetime = None
                    
                    if start_datetime:
                        time_diff = datetime.now() - start_datetime
                        total_seconds = int(time_diff.total_seconds())
                        days = total_seconds // 86400
                        hours = (total_seconds % 86400) // 3600
                        minutes = (total_seconds % 3600) // 60
                        
                        parts = []
                        if days > 0:
                            parts.append(f"{days} {'день' if days == 1 else 'дней' if days > 4 else 'дня'}")
                        if hours > 0:
                            parts.append(f"{hours} {'час' if hours == 1 else 'часов' if hours > 4 else 'часа'}")
                        if minutes > 0 or not parts:
                            parts.append(f"{minutes} {'минута' if minutes == 1 else 'минут' if minutes > 4 else 'минуты'}")
                        completed_text = " ".join(parts)
                    
                    # Format message
                    start_date_str = acc.from_date_time.strftime("%d.%m.%Y в %H:%M") if hasattr(acc, 'from_date_time') and acc.from_date_time else (acc.from_date.strftime("%d.%m.%Y") if acc.from_date else "N/A")
                    
                    notification_text = f"""Имя пользователя: <a href="https://www.instagram.com/{acc.account}/">{acc.account}</a>
Начало работ: {start_date_str}
Заявлено: {acc.period} дней
Завершено за: {completed_text}
Конец работ: {acc.to_date.strftime("%d.%m.%Y") if acc.to_date else "N/A"}
Статус: Аккаунт разблокирован✅"""
                    
                    # Send in background
                    asyncio.create_task(send_notification_async(bot, user, acc, screenshot_path, notification_text))
            
    except Exception as e:
        print(f"[AUTO-CHECK] ❌ Error checking @{acc.account}: {str(e)}")
        check_end_time = datetime.now()
        result.update({
            'error': True,
            'message': str(e),
            'traffic_bytes': traffic_monitor.total_traffic - check_start_traffic,
            'duration_ms': (check_end_time - check_start_time).total_seconds() * 1000
        })
    
    return acc, result


async def check_user_accounts_optimized(user_id: int, user_accounts: list, SessionLocal: sessionmaker, fernet: OptionalFernet, bot=None, batch_size: int = 3):
    """
    OPTIMIZED: Check accounts with parallel batch processing.
    
    Args:
        batch_size: Number of accounts to check in parallel (default: 3)
    """
    print(f"[AUTO-CHECK-OPT] 🚀 Starting OPTIMIZED check for user {user_id} with {len(user_accounts)} accounts (batch: {batch_size})")
    
    checked = 0
    found = 0
    not_found = 0
    errors = 0
    
    traffic_stats = AutoCheckTrafficStats()
    traffic_monitor = get_traffic_monitor()
    initial_traffic = traffic_monitor.total_traffic
    
    with SessionLocal() as session:
        user = session.query(User).get(user_id)
        if not user:
            print(f"[AUTO-CHECK-OPT] ❌ User {user_id} not found")
            return {"checked": 0, "found": 0, "not_found": 0, "errors": 1}
        
        verify_mode = get_global_verify_mode(session)
        print(f"[AUTO-CHECK-OPT] 👤 User {user_id} - режим: {verify_mode}")
        
        # Process in batches
        total_batches = (len(user_accounts) + batch_size - 1) // batch_size
        
        for batch_idx in range(0, len(user_accounts), batch_size):
            batch = user_accounts[batch_idx:batch_idx + batch_size]
            batch_num = batch_idx // batch_size + 1
            
            print(f"[AUTO-CHECK-OPT] 📦 Batch {batch_num}/{total_batches}: {len(batch)} accounts in parallel...")
            
            # Create parallel tasks
            tasks = [check_single_account_optimized(acc, user_id, user, session, traffic_monitor, bot) for acc in batch]
            
            # Execute in parallel
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for item in batch_results:
                if isinstance(item, Exception):
                    print(f"[AUTO-CHECK-OPT] ❌ Exception in batch: {item}")
                    errors += 1
                    continue
                
                acc, result = item
                checked += 1
                
                # Add to traffic stats
                traffic_stats.add_check(
                    username=acc.account,
                    is_active=result['success'],
                    traffic_bytes=result['traffic_bytes'],
                    duration_ms=result['duration_ms'],
                    error=result['error']
                )
                
                if result['error']:
                    errors += 1
                elif result['success']:
                    found += 1
                    print(f"[AUTO-CHECK-OPT] ✅ @{acc.account} - FOUND")
                else:
                    not_found += 1
                    print(f"[AUTO-CHECK-OPT] ❌ @{acc.account} - NOT FOUND")
            
            # No delay between batches for maximum speed
        
        traffic_stats.finalize()
        
        print(f"[AUTO-CHECK-OPT] ✅ Complete: {checked} checked, {found} found, {not_found} not found, {errors} errors")
        print(f"[AUTO-CHECK-OPT] 📊 Traffic: {traffic_stats.format_bytes(traffic_monitor.total_traffic - initial_traffic)}")
        
        return {
            "checked": checked,
            "found": found,
            "not_found": not_found,
            "errors": errors,
            "traffic_stats": traffic_stats
        }

