"""
Global Auto Checker Manager.
Manages individual auto checkers for all users.
Each user gets their own independent scheduler with custom interval.
"""
import asyncio
from typing import Dict, Optional
from datetime import datetime
from sqlalchemy.orm import sessionmaker

try:
    from ..models import User
    from .user_auto_checker import UserAutoChecker
    from ..utils.encryptor import OptionalFernet
except ImportError:
    from models import User
    from cron.user_auto_checker import UserAutoChecker
    from utils.encryptor import OptionalFernet


class AutoCheckerManager:
    """
    Global manager for all user auto checkers.
    Maintains one UserAutoChecker instance per active user.
    """
    
    _instance: Optional['AutoCheckerManager'] = None
    
    def __init__(self, session_factory: sessionmaker, bot=None, fernet: Optional[OptionalFernet] = None):
        """
        Initialize the global auto checker manager.
        
        Args:
            session_factory: SQLAlchemy session factory
            bot: Optional TelegramBot instance
            fernet: Optional Fernet encryptor
        """
        self.session_factory = session_factory
        self.bot = bot
        self.fernet = fernet or OptionalFernet()
        
        # Dictionary of user_id -> UserAutoChecker
        self.user_checkers: Dict[int, UserAutoChecker] = {}
        
        print("[AUTO-CHECKER-MANAGER] 🚀 Initialized global auto checker manager")
    
    @classmethod
    def get_instance(cls) -> Optional['AutoCheckerManager']:
        """Get the singleton instance of the manager."""
        return cls._instance
    
    @classmethod
    def initialize(cls, session_factory: sessionmaker, bot=None, fernet: Optional[OptionalFernet] = None) -> 'AutoCheckerManager':
        """
        Initialize the singleton instance.
        
        Args:
            session_factory: SQLAlchemy session factory
            bot: Optional TelegramBot instance
            fernet: Optional Fernet encryptor
        
        Returns:
            AutoCheckerManager instance
        """
        if cls._instance is None:
            cls._instance = cls(session_factory, bot, fernet)
        return cls._instance
    
    def start_all(self, run_immediately: bool = False):
        """
        Start auto checkers for all active users.
        
        Args:
            run_immediately: Run initial check immediately for all users
        """
        print("\n" + "="*80)
        print("[AUTO-CHECKER-MANAGER] 🚀 Starting auto checkers for all active users...")
        print("="*80 + "\n")
        
        with self.session_factory() as session:
            # Get all active users
            users = session.query(User).filter(
                User.is_active == True,
                User.auto_check_enabled == True
            ).all()
            
            if not users:
                print("[AUTO-CHECKER-MANAGER] ⚠️ No active users with auto-check enabled")
                return
            
            print(f"[AUTO-CHECKER-MANAGER] 📋 Found {len(users)} active users")
            
            for user in users:
                try:
                    self.start_user_checker(
                        user_id=user.id,
                        interval_minutes=user.auto_check_interval,
                        run_immediately=run_immediately
                    )
                    print(f"[AUTO-CHECKER-MANAGER] ✅ Started checker for user {user.id} (@{user.username}) - interval: {user.auto_check_interval} min")
                except Exception as e:
                    print(f"[AUTO-CHECKER-MANAGER] ❌ Failed to start checker for user {user.id}: {e}")
        
        print("\n" + "="*80)
        print(f"[AUTO-CHECKER-MANAGER] ✅ Started {len(self.user_checkers)} auto checkers")
        print("="*80 + "\n")
    
    def start_user_checker(self, user_id: int, interval_minutes: int, run_immediately: bool = False):
        """
        Start auto checker for a specific user.
        
        Args:
            user_id: User ID
            interval_minutes: Check interval in minutes
            run_immediately: Run initial check immediately
        """
        # Stop existing checker if any
        if user_id in self.user_checkers:
            print(f"[AUTO-CHECKER-MANAGER] 🔄 Stopping existing checker for user {user_id}")
            self.stop_user_checker(user_id)
        
        # Create and start new checker
        checker = UserAutoChecker(
            user_id=user_id,
            session_factory=self.session_factory,
            bot=self.bot,
            fernet=self.fernet
        )
        
        checker.start(interval_minutes=interval_minutes, run_immediately=run_immediately)
        self.user_checkers[user_id] = checker
        
        print(f"[AUTO-CHECKER-MANAGER] ✅ User {user_id} checker started (interval: {interval_minutes} min)")
    
    def stop_user_checker(self, user_id: int):
        """
        Stop auto checker for a specific user.
        
        Args:
            user_id: User ID
        """
        if user_id not in self.user_checkers:
            print(f"[AUTO-CHECKER-MANAGER] ⚠️ No checker running for user {user_id}")
            return
        
        checker = self.user_checkers[user_id]
        checker.stop()
        del self.user_checkers[user_id]
        
        print(f"[AUTO-CHECKER-MANAGER] ✅ User {user_id} checker stopped")
    
    def update_user_interval(self, user_id: int, new_interval_minutes: int):
        """
        Update the check interval for a specific user.
        
        Args:
            user_id: User ID
            new_interval_minutes: New interval in minutes
        """
        if user_id not in self.user_checkers:
            print(f"[AUTO-CHECKER-MANAGER] ⚠️ No checker running for user {user_id}, starting new one")
            self.start_user_checker(user_id, new_interval_minutes)
            return
        
        checker = self.user_checkers[user_id]
        checker.update_interval(new_interval_minutes)
        
        print(f"[AUTO-CHECKER-MANAGER] ✅ Updated interval for user {user_id} to {new_interval_minutes} min")
    
    def enable_user_checker(self, user_id: int, interval_minutes: int):
        """
        Enable auto checker for a user.
        
        Args:
            user_id: User ID
            interval_minutes: Check interval in minutes
        """
        # Update database
        with self.session_factory() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                user.auto_check_enabled = True
                user.auto_check_interval = interval_minutes
                session.commit()
        
        # Start checker
        self.start_user_checker(user_id, interval_minutes, run_immediately=False)
        print(f"[AUTO-CHECKER-MANAGER] ✅ Enabled auto-check for user {user_id}")
    
    def disable_user_checker(self, user_id: int):
        """
        Disable auto checker for a user.
        
        Args:
            user_id: User ID
        """
        # Update database
        with self.session_factory() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                user.auto_check_enabled = False
                session.commit()
        
        # Stop checker
        self.stop_user_checker(user_id)
        print(f"[AUTO-CHECKER-MANAGER] ✅ Disabled auto-check for user {user_id}")
    
    def stop_all(self):
        """Stop all user auto checkers."""
        print("\n" + "="*80)
        print("[AUTO-CHECKER-MANAGER] 🛑 Stopping all auto checkers...")
        print("="*80 + "\n")
        
        user_ids = list(self.user_checkers.keys())
        for user_id in user_ids:
            try:
                self.stop_user_checker(user_id)
            except Exception as e:
                print(f"[AUTO-CHECKER-MANAGER] ❌ Error stopping checker for user {user_id}: {e}")
        
        print(f"[AUTO-CHECKER-MANAGER] ✅ Stopped all auto checkers")
    
    def get_all_stats(self) -> dict:
        """Get statistics for all user checkers."""
        stats = {
            "total_checkers": len(self.user_checkers),
            "checkers": []
        }
        
        for user_id, checker in self.user_checkers.items():
            checker_stats = checker.get_stats()
            
            # Get user info
            with self.session_factory() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if user:
                    checker_stats["username"] = user.username
                    checker_stats["interval_minutes"] = user.auto_check_interval
            
            stats["checkers"].append(checker_stats)
        
        return stats
    
    def print_status(self):
        """Print status of all user checkers."""
        print("\n" + "="*80)
        print("[AUTO-CHECKER-MANAGER] 📊 AUTO CHECKER STATUS")
        print("="*80)
        
        if not self.user_checkers:
            print("⚠️ No active checkers")
            print("="*80 + "\n")
            return
        
        stats = self.get_all_stats()
        
        print(f"\n📋 Total checkers: {stats['total_checkers']}\n")
        
        for checker_stat in stats["checkers"]:
            user_id = checker_stat["user_id"]
            username = checker_stat.get("username", "Unknown")
            interval = checker_stat.get("interval_minutes", "?")
            is_running = "✅" if checker_stat["is_running"] else "❌"
            is_checking = "🔄" if checker_stat["is_checking"] else "⏸️"
            last_check = checker_stat["last_check_time"]
            total_checks = checker_stat["total_checks"]
            total_found = checker_stat["total_found"]
            
            print(f"👤 User {user_id} (@{username})")
            print(f"   Status: {is_running} Running {is_checking}")
            print(f"   Interval: {interval} minutes")
            print(f"   Last check: {last_check if last_check else 'Never'}")
            print(f"   Total checks: {total_checks}")
            print(f"   Total found: {total_found}")
            print()
        
        print("="*80 + "\n")
    
    async def trigger_user_check(self, user_id: int):
        """
        Manually trigger a check for a specific user.
        
        Args:
            user_id: User ID
        """
        if user_id not in self.user_checkers:
            print(f"[AUTO-CHECKER-MANAGER] ⚠️ No checker for user {user_id}")
            return
        
        checker = self.user_checkers[user_id]
        print(f"[AUTO-CHECKER-MANAGER] 🔄 Manually triggering check for user {user_id}")
        await checker.check_user_accounts()


# Global function to get the manager instance
def get_auto_checker_manager() -> Optional[AutoCheckerManager]:
    """Get the global auto checker manager instance."""
    return AutoCheckerManager.get_instance()

