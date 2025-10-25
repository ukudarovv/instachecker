"""
🔗 Advanced Proxy Manager with Database Integration

Combines the best features from:
- Existing DB-backed Proxy model (persistent, multi-user)
- DeepSeek's ProxyManager (convenient interface)
- Additional smart features (adaptive selection, health tracking)
"""

import asyncio
import random
import time
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

try:
    from ..models import Proxy
    from ..database import get_session_factory
except ImportError:
    from models import Proxy
    from database import get_session_factory


class ProxyManager:
    """
    Advanced Proxy Manager with DB integration
    
    Features:
    - Smart proxy selection (adaptive, priority-based, random)
    - Automatic rotation and fallback
    - Health tracking and cooldown
    - Batch import from lists
    - Real-time statistics
    """
    
    def __init__(self, session: Optional[Session] = None):
        """
        Initialize ProxyManager
        
        Args:
            session: SQLAlchemy session (optional, will create if not provided)
        """
        self.session = session
        self.should_close_session = False
        
        if not self.session:
            SessionLocal = get_session_factory()
            self.session = SessionLocal()
            self.should_close_session = True
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.should_close_session and self.session:
            self.session.close()
    
    # ========================================================================
    # PROXY SELECTION (Smart Strategies)
    # ========================================================================
    
    def get_best_proxy(
        self, 
        user_id: int, 
        strategy: str = 'adaptive',
        exclude_ids: Optional[List[int]] = None
    ) -> Optional[Proxy]:
        """
        Get the best proxy for user based on strategy
        
        Args:
            user_id: User ID
            strategy: Selection strategy ('adaptive', 'priority', 'random', 'least_used')
            exclude_ids: List of proxy IDs to exclude
            
        Returns:
            Best proxy object or None
        """
        print(f"[PROXY-MANAGER] 🎯 Selecting proxy for user {user_id} (strategy: {strategy})")
        
        # Base query: active proxies for this user, not in cooldown
        query = self.session.query(Proxy).filter(
            Proxy.user_id == user_id,
            Proxy.is_active == True,
            (Proxy.cooldown_until == None) | (Proxy.cooldown_until < datetime.now())
        )
        
        # Exclude specified proxies
        if exclude_ids:
            query = query.filter(~Proxy.id.in_(exclude_ids))
        
        proxies = query.all()
        
        if not proxies:
            print(f"[PROXY-MANAGER] ⚠️ No available proxies for user {user_id}")
            return None
        
        # Apply strategy
        if strategy == 'adaptive':
            return self._select_adaptive(proxies)
        elif strategy == 'priority':
            return self._select_priority(proxies)
        elif strategy == 'random':
            return random.choice(proxies)
        elif strategy == 'least_used':
            return min(proxies, key=lambda p: p.used_count)
        else:
            return self._select_adaptive(proxies)
    
    def _select_adaptive(self, proxies: List[Proxy]) -> Proxy:
        """
        Adaptive selection based on success rate and usage
        
        Algorithm:
        - Calculate score for each proxy
        - Score = (success_rate * 0.7) + (inverse_usage * 0.2) + (priority_score * 0.1)
        - Select best score with some randomness (epsilon-greedy)
        """
        scored_proxies = []
        
        for proxy in proxies:
            # Success rate (0-1)
            total_uses = proxy.used_count
            if total_uses == 0:
                success_rate = 0.5  # Neutral for new proxies
            else:
                success_rate = proxy.success_count / total_uses
            
            # Inverse usage (prefer less used) (0-1)
            max_usage = max(p.used_count for p in proxies) if proxies else 1
            inverse_usage = 1 - (proxy.used_count / (max_usage + 1))
            
            # Priority score (0-1) - lower priority number = higher score
            priority_score = 1 - ((proxy.priority - 1) / 9)  # priority 1-10 -> score 1-0
            
            # Combined score
            score = (success_rate * 0.7) + (inverse_usage * 0.2) + (priority_score * 0.1)
            
            scored_proxies.append((score, proxy))
        
        # Sort by score
        scored_proxies.sort(key=lambda x: x[0], reverse=True)
        
        # Epsilon-greedy selection (90% best, 10% random exploration)
        if random.random() < 0.9:
            selected = scored_proxies[0][1]
        else:
            selected = random.choice(proxies)
        
        print(f"[PROXY-MANAGER] ✅ Selected proxy {selected.host} (score: {scored_proxies[0][0]:.3f})")
        return selected
    
    def _select_priority(self, proxies: List[Proxy]) -> Proxy:
        """Select proxy with highest priority (lowest priority number)"""
        return min(proxies, key=lambda p: p.priority)
    
    def get_random_proxy(self, user_id: int, exclude_ids: Optional[List[int]] = None) -> Optional[Proxy]:
        """Get random active proxy (convenience method)"""
        return self.get_best_proxy(user_id, strategy='random', exclude_ids=exclude_ids)
    
    # ========================================================================
    # PROXY ROTATION & FALLBACK
    # ========================================================================
    
    async def get_proxy_with_fallback(
        self, 
        user_id: int, 
        max_attempts: int = 3,
        test_url: str = "https://httpbin.org/ip"
    ) -> Optional[Proxy]:
        """
        Get working proxy with automatic fallback
        
        Args:
            user_id: User ID
            max_attempts: Maximum number of proxies to try
            test_url: URL to test proxy connection
            
        Returns:
            Working proxy or None
        """
        print(f"[PROXY-MANAGER] 🔄 Getting proxy with fallback (max {max_attempts} attempts)")
        
        exclude_ids = []
        
        for attempt in range(max_attempts):
            proxy = self.get_best_proxy(user_id, strategy='adaptive', exclude_ids=exclude_ids)
            
            if not proxy:
                print(f"[PROXY-MANAGER] ❌ No more proxies available")
                return None
            
            # Test proxy
            print(f"[PROXY-MANAGER] 🧪 Testing proxy {proxy.host} (attempt {attempt + 1}/{max_attempts})")
            
            is_working = await self.test_proxy_connection(proxy, test_url)
            
            if is_working:
                print(f"[PROXY-MANAGER] ✅ Proxy {proxy.host} is working!")
                return proxy
            else:
                print(f"[PROXY-MANAGER] ❌ Proxy {proxy.host} failed, trying next...")
                exclude_ids.append(proxy.id)
                self.mark_failure(proxy.id, apply_cooldown=True)
        
        print(f"[PROXY-MANAGER] ❌ All {max_attempts} proxies failed")
        return None
    
    # ========================================================================
    # HEALTH TRACKING
    # ========================================================================
    
    async def test_proxy_connection(
        self, 
        proxy: Proxy, 
        test_url: str = "https://httpbin.org/ip",
        timeout: int = 15
    ) -> bool:
        """
        Test if proxy is working
        
        Args:
            proxy: Proxy object to test
            test_url: URL to test against
            timeout: Request timeout in seconds
            
        Returns:
            True if proxy works, False otherwise
        """
        proxy_url = self.build_proxy_url(proxy)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    test_url,
                    proxy=proxy_url,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    if response.status == 200:
                        # Verify IP changed
                        data = await response.json()
                        origin_ip = data.get('origin', '')
                        
                        # Extract host from proxy
                        proxy_host = proxy.host.split(':')[0] if ':' in proxy.host else proxy.host
                        
                        if proxy_host in origin_ip:
                            print(f"[PROXY-MANAGER] ✅ Proxy {proxy.host} - IP verified: {origin_ip}")
                            return True
                        else:
                            print(f"[PROXY-MANAGER] ⚠️ Proxy {proxy.host} - IP not changed (got {origin_ip})")
                            return False
                    else:
                        print(f"[PROXY-MANAGER] ❌ Proxy {proxy.host} - HTTP {response.status}")
                        return False
        
        except asyncio.TimeoutError:
            print(f"[PROXY-MANAGER] ❌ Proxy {proxy.host} - Timeout")
            return False
        except Exception as e:
            print(f"[PROXY-MANAGER] ❌ Proxy {proxy.host} - Error: {e}")
            return False
    
    def mark_success(self, proxy_id: int):
        """Mark proxy usage as successful"""
        proxy = self.session.query(Proxy).filter(Proxy.id == proxy_id).first()
        if proxy:
            proxy.used_count += 1
            proxy.success_count += 1
            proxy.fail_streak = 0
            proxy.last_checked = datetime.now()
            self.session.commit()
            print(f"[PROXY-MANAGER] ✅ Marked proxy {proxy.host} as successful")
    
    def mark_failure(self, proxy_id: int, apply_cooldown: bool = True):
        """
        Mark proxy usage as failed
        
        Args:
            proxy_id: Proxy ID
            apply_cooldown: If True, apply cooldown after threshold
        """
        proxy = self.session.query(Proxy).filter(Proxy.id == proxy_id).first()
        if proxy:
            proxy.used_count += 1
            proxy.fail_streak += 1
            proxy.last_checked = datetime.now()
            
            # Apply cooldown after 3 consecutive failures
            if apply_cooldown and proxy.fail_streak >= 3:
                cooldown_duration = timedelta(minutes=15)
                proxy.cooldown_until = datetime.now() + cooldown_duration
                print(f"[PROXY-MANAGER] ⏳ Proxy {proxy.host} in cooldown for 15 minutes")
            
            # Deactivate after 5 consecutive failures
            if proxy.fail_streak >= 5:
                proxy.is_active = False
                print(f"[PROXY-MANAGER] 🚫 Proxy {proxy.host} deactivated after 5 failures")
            
            self.session.commit()
            print(f"[PROXY-MANAGER] ❌ Marked proxy {proxy.host} as failed (streak: {proxy.fail_streak})")
    
    # ========================================================================
    # BATCH OPERATIONS
    # ========================================================================
    
    def parse_proxy_list(self, proxy_list: str, user_id: int) -> List[Dict]:
        """
        Parse proxy list from text
        
        Supported formats:
        - ip:port:username:password
        - username:password@ip:port
        - http://username:password@ip:port
        
        Args:
            proxy_list: Multi-line string with proxies
            user_id: User ID to assign proxies to
            
        Returns:
            List of parsed proxy dicts
        """
        proxies = []
        lines = proxy_list.strip().split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            try:
                proxy_data = self._parse_single_proxy(line)
                if proxy_data:
                    proxy_data['user_id'] = user_id
                    proxies.append(proxy_data)
            except Exception as e:
                print(f"[PROXY-MANAGER] ⚠️ Line {line_num} parse error: {e}")
                continue
        
        print(f"[PROXY-MANAGER] 📋 Parsed {len(proxies)} proxies from {len(lines)} lines")
        return proxies
    
    def _parse_single_proxy(self, line: str) -> Optional[Dict]:
        """Parse single proxy line"""
        # Remove protocol prefix if present
        line = line.replace('http://', '').replace('https://', '').replace('socks5://', '')
        
        # Format 1: ip:port:username:password
        if line.count(':') == 3 and '@' not in line:
            parts = line.split(':')
            return {
                'scheme': 'http',
                'host': f"{parts[0]}:{parts[1]}",
                'username': parts[2],
                'password': parts[3],
                'priority': 5
            }
        
        # Format 2: username:password@ip:port
        elif '@' in line:
            if ':' in line.split('@')[0] and ':' in line.split('@')[1]:
                auth, server = line.split('@')
                username, password = auth.split(':', 1)
                return {
                    'scheme': 'http',
                    'host': server,
                    'username': username,
                    'password': password,
                    'priority': 5
                }
        
        return None
    
    def batch_add_proxies(self, proxy_list: str, user_id: int) -> Dict[str, int]:
        """
        Add multiple proxies from list
        
        Args:
            proxy_list: Multi-line string with proxies
            user_id: User ID
            
        Returns:
            Stats dict with 'added', 'skipped', 'errors'
        """
        print(f"[PROXY-MANAGER] 📥 Batch adding proxies for user {user_id}")
        
        parsed_proxies = self.parse_proxy_list(proxy_list, user_id)
        
        stats = {'added': 0, 'skipped': 0, 'errors': 0}
        
        for proxy_data in parsed_proxies:
            try:
                # Check if proxy already exists
                existing = self.session.query(Proxy).filter(
                    Proxy.user_id == user_id,
                    Proxy.host == proxy_data['host'],
                    Proxy.scheme == proxy_data['scheme']
                ).first()
                
                if existing:
                    stats['skipped'] += 1
                    print(f"[PROXY-MANAGER] ⏭️ Proxy {proxy_data['host']} already exists")
                    continue
                
                # Add new proxy
                new_proxy = Proxy(**proxy_data)
                self.session.add(new_proxy)
                stats['added'] += 1
                print(f"[PROXY-MANAGER] ➕ Added proxy {proxy_data['host']}")
            
            except Exception as e:
                stats['errors'] += 1
                print(f"[PROXY-MANAGER] ❌ Error adding proxy: {e}")
        
        self.session.commit()
        
        print(f"[PROXY-MANAGER] 📊 Batch import complete: {stats['added']} added, {stats['skipped']} skipped, {stats['errors']} errors")
        return stats
    
    # ========================================================================
    # STATISTICS & MONITORING
    # ========================================================================
    
    def get_proxy_stats(self, user_id: int) -> Dict[str, Any]:
        """Get detailed proxy statistics for user"""
        proxies = self.session.query(Proxy).filter(Proxy.user_id == user_id).all()
        
        if not proxies:
            return {
                'total': 0,
                'active': 0,
                'inactive': 0,
                'in_cooldown': 0,
                'success_rate': 0,
                'total_uses': 0
            }
        
        active = [p for p in proxies if p.is_active]
        in_cooldown = [p for p in proxies if p.cooldown_until and p.cooldown_until > datetime.now()]
        
        total_uses = sum(p.used_count for p in proxies)
        total_successes = sum(p.success_count for p in proxies)
        
        success_rate = (total_successes / total_uses * 100) if total_uses > 0 else 0
        
        return {
            'total': len(proxies),
            'active': len(active),
            'inactive': len(proxies) - len(active),
            'in_cooldown': len(in_cooldown),
            'success_rate': round(success_rate, 2),
            'total_uses': total_uses,
            'total_successes': total_successes
        }
    
    def get_best_proxies(self, user_id: int, top_n: int = 5) -> List[Dict]:
        """Get top N best performing proxies"""
        proxies = self.session.query(Proxy).filter(
            Proxy.user_id == user_id,
            Proxy.used_count > 0
        ).all()
        
        proxy_stats = []
        
        for proxy in proxies:
            success_rate = (proxy.success_count / proxy.used_count * 100) if proxy.used_count > 0 else 0
            
            proxy_stats.append({
                'id': proxy.id,
                'host': proxy.host,
                'success_rate': round(success_rate, 2),
                'used_count': proxy.used_count,
                'success_count': proxy.success_count,
                'fail_streak': proxy.fail_streak,
                'is_active': proxy.is_active,
                'priority': proxy.priority
            })
        
        # Sort by success rate
        proxy_stats.sort(key=lambda x: x['success_rate'], reverse=True)
        
        return proxy_stats[:top_n]
    
    def get_worst_proxies(self, user_id: int, bottom_n: int = 5) -> List[Dict]:
        """Get bottom N worst performing proxies"""
        all_stats = self.get_best_proxies(user_id, top_n=999)
        return all_stats[-bottom_n:] if len(all_stats) >= bottom_n else all_stats
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def build_proxy_url(self, proxy: Proxy) -> str:
        """
        Build proxy URL for aiohttp/requests
        
        Args:
            proxy: Proxy object
            
        Returns:
            Proxy URL string
        """
        if proxy.username and proxy.password:
            return f"{proxy.scheme}://{proxy.username}:{proxy.password}@{proxy.host}"
        else:
            return f"{proxy.scheme}://{proxy.host}"
    
    def build_playwright_proxy_config(self, proxy: Proxy) -> Dict[str, str]:
        """
        Build proxy config for Playwright
        
        Args:
            proxy: Proxy object
            
        Returns:
            Playwright proxy config dict
        """
        config = {
            "server": f"{proxy.scheme}://{proxy.host}"
        }
        
        if proxy.username and proxy.password:
            config["username"] = proxy.username
            config["password"] = proxy.password
        
        return config
    
    def reset_cooldowns(self, user_id: int) -> int:
        """Reset cooldowns for all user's proxies"""
        count = self.session.query(Proxy).filter(
            Proxy.user_id == user_id,
            Proxy.cooldown_until != None
        ).update({'cooldown_until': None})
        
        self.session.commit()
        print(f"[PROXY-MANAGER] 🔄 Reset cooldowns for {count} proxies")
        return count
    
    def reactivate_all(self, user_id: int) -> int:
        """Reactivate all inactive proxies"""
        count = self.session.query(Proxy).filter(
            Proxy.user_id == user_id,
            Proxy.is_active == False
        ).update({'is_active': True, 'fail_streak': 0})
        
        self.session.commit()
        print(f"[PROXY-MANAGER] ✅ Reactivated {count} proxies")
        return count


# ========================================================================
# CONVENIENCE FUNCTIONS
# ========================================================================

def get_active_proxy_for_user(session: Session, user_id: int) -> Optional[str]:
    """
    Get active proxy URL for user (convenience function)
    
    Args:
        session: DB session
        user_id: User ID
        
    Returns:
        Proxy URL string or None
    """
    with ProxyManager(session) as manager:
        proxy = manager.get_best_proxy(user_id)
        if proxy:
            return manager.build_proxy_url(proxy)
        return None


async def test_all_user_proxies(session: Session, user_id: int) -> Dict[str, Any]:
    """
    Test all proxies for user
    
    Args:
        session: DB session
        user_id: User ID
        
    Returns:
        Test results dict
    """
    with ProxyManager(session) as manager:
        proxies = session.query(Proxy).filter(Proxy.user_id == user_id).all()
        
        print(f"[PROXY-MANAGER] 🧪 Testing {len(proxies)} proxies for user {user_id}")
        
        results = {
            'total': len(proxies),
            'working': 0,
            'failed': 0,
            'details': []
        }
        
        for proxy in proxies:
            is_working = await manager.test_proxy_connection(proxy)
            
            result_detail = {
                'id': proxy.id,
                'host': proxy.host,
                'working': is_working
            }
            
            results['details'].append(result_detail)
            
            if is_working:
                results['working'] += 1
                manager.mark_success(proxy.id)
            else:
                results['failed'] += 1
                manager.mark_failure(proxy.id, apply_cooldown=False)
            
            # Small delay between tests
            await asyncio.sleep(1)
        
        print(f"[PROXY-MANAGER] 📊 Test complete: {results['working']}/{results['total']} working")
        return results




