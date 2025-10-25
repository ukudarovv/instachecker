"""
🏥 Proxy Health Checker - Automatic background monitoring

Periodically checks all active proxies and:
- Deactivates dead proxies
- Applies cooldown to failing proxies  
- Reactivates proxies after cooldown
- Tracks health metrics
"""

import asyncio
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

try:
    from ..models import Proxy
    from ..database import get_session_factory
    from .proxy_manager import ProxyManager
except ImportError:
    from models import Proxy
    from database import get_session_factory
    from services.proxy_manager import ProxyManager


class ProxyHealthChecker:
    """
    Automatic proxy health monitoring and management
    
    Features:
    - Periodic health checks (configurable interval)
    - Automatic deactivation of dead proxies
    - Cooldown management
    - Health metrics tracking
    """
    
    def __init__(
        self, 
        check_interval_seconds: int = 300,  # 5 minutes
        failure_threshold: int = 3,
        cooldown_duration_minutes: int = 15
    ):
        """
        Initialize ProxyHealthChecker
        
        Args:
            check_interval_seconds: Interval between health checks
            failure_threshold: Number of failures before deactivation
            cooldown_duration_minutes: Duration of cooldown period
        """
        self.check_interval = check_interval_seconds
        self.failure_threshold = failure_threshold
        self.cooldown_duration = timedelta(minutes=cooldown_duration_minutes)
        self.is_running = False
        self.health_history = []
        
        print(f"[PROXY-HEALTH] 🏥 Initialized (interval: {check_interval_seconds}s, threshold: {failure_threshold})")
    
    async def check_single_proxy(self, proxy: Proxy, session: Session) -> Dict:
        """
        Check health of single proxy
        
        Args:
            proxy: Proxy object to check
            session: DB session
            
        Returns:
            Health check result dict
        """
        manager = ProxyManager(session)
        
        result = {
            'proxy_id': proxy.id,
            'host': proxy.host,
            'healthy': False,
            'response_time': None,
            'error': None,
            'checked_at': datetime.now()
        }
        
        try:
            start_time = asyncio.get_event_loop().time()
            
            # Test connection
            is_working = await manager.test_proxy_connection(proxy)
            
            response_time = asyncio.get_event_loop().time() - start_time
            
            result['healthy'] = is_working
            result['response_time'] = round(response_time, 2)
            
            if is_working:
                manager.mark_success(proxy.id)
                print(f"[PROXY-HEALTH] ✅ {proxy.host} healthy ({response_time:.2f}s)")
            else:
                manager.mark_failure(proxy.id, apply_cooldown=True)
                result['error'] = 'connection_failed'
                print(f"[PROXY-HEALTH] ❌ {proxy.host} unhealthy")
        
        except Exception as e:
            result['error'] = str(e)
            manager.mark_failure(proxy.id, apply_cooldown=True)
            print(f"[PROXY-HEALTH] ❌ {proxy.host} error: {e}")
        
        return result
    
    async def check_all_proxies(self, session: Session) -> Dict:
        """
        Check health of all active proxies
        
        Args:
            session: DB session
            
        Returns:
            Check summary dict
        """
        print(f"[PROXY-HEALTH] 🔍 Starting health check...")
        
        # Get all proxies (including those in cooldown - we want to track everything)
        proxies = session.query(Proxy).all()
        
        if not proxies:
            print(f"[PROXY-HEALTH] ℹ️ No proxies to check")
            return {'total': 0, 'checked': 0, 'healthy': 0, 'unhealthy': 0}
        
        summary = {
            'total': len(proxies),
            'checked': 0,
            'healthy': 0,
            'unhealthy': 0,
            'skipped_cooldown': 0,
            'skipped_inactive': 0,
            'deactivated': 0,
            'started_at': datetime.now(),
            'results': []
        }
        
        for proxy in proxies:
            # Skip inactive proxies
            if not proxy.is_active:
                summary['skipped_inactive'] += 1
                continue
            
            # Skip proxies in cooldown (let them rest)
            if proxy.cooldown_until and proxy.cooldown_until > datetime.now():
                summary['skipped_cooldown'] += 1
                print(f"[PROXY-HEALTH] ⏸️ {proxy.host} in cooldown until {proxy.cooldown_until}")
                continue
            
            # Check proxy
            result = await self.check_single_proxy(proxy, session)
            summary['results'].append(result)
            summary['checked'] += 1
            
            if result['healthy']:
                summary['healthy'] += 1
            else:
                summary['unhealthy'] += 1
                
                # Check if should be deactivated
                if proxy.fail_streak >= self.failure_threshold:
                    summary['deactivated'] += 1
            
            # Small delay between checks to avoid overwhelming
            await asyncio.sleep(0.5)
        
        summary['completed_at'] = datetime.now()
        summary['duration_seconds'] = (summary['completed_at'] - summary['started_at']).total_seconds()
        
        # Save to history
        self.health_history.append(summary)
        
        # Keep only last 100 checks in memory
        if len(self.health_history) > 100:
            self.health_history = self.health_history[-100:]
        
        print(f"[PROXY-HEALTH] 📊 Check complete:")
        print(f"[PROXY-HEALTH]   ✅ Healthy: {summary['healthy']}")
        print(f"[PROXY-HEALTH]   ❌ Unhealthy: {summary['unhealthy']}")
        print(f"[PROXY-HEALTH]   🚫 Deactivated: {summary['deactivated']}")
        print(f"[PROXY-HEALTH]   ⏸️ In cooldown: {summary['skipped_cooldown']}")
        print(f"[PROXY-HEALTH]   ⏱️ Duration: {summary['duration_seconds']:.1f}s")
        
        return summary
    
    async def release_expired_cooldowns(self, session: Session) -> int:
        """
        Release proxies from expired cooldowns
        
        Args:
            session: DB session
            
        Returns:
            Number of proxies released
        """
        count = session.query(Proxy).filter(
            Proxy.cooldown_until != None,
            Proxy.cooldown_until <= datetime.now()
        ).update({
            'cooldown_until': None
        })
        
        session.commit()
        
        if count > 0:
            print(f"[PROXY-HEALTH] 🔓 Released {count} proxies from cooldown")
        
        return count
    
    async def auto_reactivate_recovered_proxies(self, session: Session) -> int:
        """
        Reactivate proxies that were inactive but might have recovered
        
        This is an optional feature - automatically tries to reactivate
        proxies that were deactivated but might work again
        
        Args:
            session: DB session
            
        Returns:
            Number of proxies reactivated
        """
        # Get inactive proxies that were deactivated more than 1 hour ago
        one_hour_ago = datetime.now() - timedelta(hours=1)
        
        inactive_proxies = session.query(Proxy).filter(
            Proxy.is_active == False,
            Proxy.last_checked < one_hour_ago
        ).all()
        
        if not inactive_proxies:
            return 0
        
        print(f"[PROXY-HEALTH] 🔄 Attempting to reactivate {len(inactive_proxies)} inactive proxies...")
        
        reactivated = 0
        
        for proxy in inactive_proxies:
            manager = ProxyManager(session)
            
            # Test if proxy works now
            is_working = await manager.test_proxy_connection(proxy)
            
            if is_working:
                proxy.is_active = True
                proxy.fail_streak = 0
                proxy.cooldown_until = None
                reactivated += 1
                print(f"[PROXY-HEALTH] ♻️ Reactivated {proxy.host}")
            
            await asyncio.sleep(0.5)
        
        session.commit()
        
        if reactivated > 0:
            print(f"[PROXY-HEALTH] ✅ Reactivated {reactivated}/{len(inactive_proxies)} proxies")
        
        return reactivated
    
    async def periodic_check_loop(self):
        """
        Main periodic check loop
        
        Runs continuously in background, performing health checks
        at specified intervals
        """
        print(f"[PROXY-HEALTH] 🚀 Starting periodic health checks (every {self.check_interval}s)")
        self.is_running = True
        
        SessionLocal = get_session_factory()
        
        iteration = 0
        
        while self.is_running:
            iteration += 1
            print(f"\n[PROXY-HEALTH] 🔄 Health check iteration #{iteration}")
            
            try:
                with SessionLocal() as session:
                    # Release expired cooldowns
                    await self.release_expired_cooldowns(session)
                    
                    # Check all proxies
                    summary = await self.check_all_proxies(session)
                    
                    # Every 10 iterations, try to reactivate recovered proxies
                    if iteration % 10 == 0:
                        await self.auto_reactivate_recovered_proxies(session)
            
            except Exception as e:
                print(f"[PROXY-HEALTH] ❌ Error in health check: {e}")
                import traceback
                traceback.print_exc()
            
            # Wait for next iteration
            print(f"[PROXY-HEALTH] 😴 Sleeping for {self.check_interval}s...")
            await asyncio.sleep(self.check_interval)
    
    def stop(self):
        """Stop the periodic check loop"""
        print(f"[PROXY-HEALTH] 🛑 Stopping health checker...")
        self.is_running = False
    
    def get_health_summary(self) -> Dict:
        """
        Get summary of health check history
        
        Returns:
            Health summary dict
        """
        if not self.health_history:
            return {
                'total_checks': 0,
                'avg_healthy_rate': 0,
                'total_proxies_checked': 0
            }
        
        total_checks = len(self.health_history)
        total_healthy = sum(h['healthy'] for h in self.health_history)
        total_checked = sum(h['checked'] for h in self.health_history)
        
        avg_healthy_rate = (total_healthy / total_checked * 100) if total_checked > 0 else 0
        
        return {
            'total_checks': total_checks,
            'total_proxies_checked': total_checked,
            'total_healthy': total_healthy,
            'avg_healthy_rate': round(avg_healthy_rate, 2),
            'last_check': self.health_history[-1] if self.health_history else None
        }


# ========================================================================
# GLOBAL INSTANCE & CONVENIENCE FUNCTIONS
# ========================================================================

_health_checker_instance: Optional[ProxyHealthChecker] = None


def get_health_checker() -> ProxyHealthChecker:
    """Get global ProxyHealthChecker instance"""
    global _health_checker_instance
    
    if _health_checker_instance is None:
        _health_checker_instance = ProxyHealthChecker(
            check_interval_seconds=300,  # 5 minutes
            failure_threshold=3,
            cooldown_duration_minutes=15
        )
    
    return _health_checker_instance


async def start_proxy_health_checker():
    """
    Start proxy health checker in background
    
    Usage:
        asyncio.create_task(start_proxy_health_checker())
    """
    checker = get_health_checker()
    await checker.periodic_check_loop()


def stop_proxy_health_checker():
    """Stop proxy health checker"""
    checker = get_health_checker()
    checker.stop()


# ========================================================================
# MANUAL CHECK FUNCTIONS
# ========================================================================

async def manual_health_check() -> Dict:
    """
    Perform manual health check on all proxies
    
    Returns:
        Check summary dict
    """
    print(f"[PROXY-HEALTH] 🔧 Manual health check triggered")
    
    SessionLocal = get_session_factory()
    
    with SessionLocal() as session:
        checker = ProxyHealthChecker()
        summary = await checker.check_all_proxies(session)
        return summary


async def check_user_proxies_health(user_id: int) -> Dict:
    """
    Check health of specific user's proxies
    
    Args:
        user_id: User ID
        
    Returns:
        Check summary dict
    """
    print(f"[PROXY-HEALTH] 🔧 Checking proxies for user {user_id}")
    
    SessionLocal = get_session_factory()
    
    with SessionLocal() as session:
        proxies = session.query(Proxy).filter(
            Proxy.user_id == user_id,
            Proxy.is_active == True
        ).all()
        
        if not proxies:
            return {
                'user_id': user_id,
                'total': 0,
                'message': 'No active proxies found'
            }
        
        checker = ProxyHealthChecker()
        
        results = []
        healthy_count = 0
        
        for proxy in proxies:
            result = await checker.check_single_proxy(proxy, session)
            results.append(result)
            
            if result['healthy']:
                healthy_count += 1
            
            await asyncio.sleep(0.5)
        
        return {
            'user_id': user_id,
            'total': len(proxies),
            'healthy': healthy_count,
            'unhealthy': len(proxies) - healthy_count,
            'results': results
        }




