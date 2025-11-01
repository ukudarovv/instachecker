"""
Auto-check traffic statistics tracker.
Tracks traffic consumption per check, separated by active/inactive accounts.
"""

from dataclasses import dataclass, field
from typing import Dict, List
from datetime import datetime


@dataclass
class CheckTrafficStats:
    """Statistics for a single account check."""
    username: str
    is_active: bool  # True if account found/active, False if not found
    traffic_bytes: int = 0
    duration_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    error: bool = False


class AutoCheckTrafficStats:
    """
    Collects and aggregates traffic statistics for auto-check runs.
    Separates stats for active and inactive accounts.
    """
    
    def __init__(self):
        self.checks: List[CheckTrafficStats] = []
        self.start_time: datetime = datetime.now()
        self.end_time: datetime = None
        
    def add_check(self, username: str, is_active: bool, traffic_bytes: int = 0, 
                  duration_ms: float = 0.0, error: bool = False):
        """Add a check result."""
        self.checks.append(CheckTrafficStats(
            username=username,
            is_active=is_active,
            traffic_bytes=traffic_bytes,
            duration_ms=duration_ms,
            timestamp=datetime.now(),
            error=error
        ))
    
    def finalize(self):
        """Mark the check run as complete."""
        self.end_time = datetime.now()
    
    def get_summary(self) -> Dict:
        """
        Get summary statistics.
        
        Returns:
            Dict with statistics including:
            - total_checks: Total number of checks
            - active_accounts: Number of active accounts found
            - inactive_accounts: Number of inactive accounts
            - errors: Number of errors
            - total_traffic: Total traffic in bytes
            - active_traffic: Traffic for active accounts
            - inactive_traffic: Traffic for inactive accounts
            - avg_traffic_active: Average traffic per active account
            - avg_traffic_inactive: Average traffic per inactive account
            - avg_traffic_per_check: Average traffic per check
            - total_duration_sec: Total duration in seconds
        """
        if not self.checks:
            return {
                'total_checks': 0,
                'active_accounts': 0,
                'inactive_accounts': 0,
                'errors': 0,
                'total_traffic': 0,
                'active_traffic': 0,
                'inactive_traffic': 0,
                'avg_traffic_active': 0,
                'avg_traffic_inactive': 0,
                'avg_traffic_per_check': 0,
                'total_duration_sec': 0
            }
        
        active_checks = [c for c in self.checks if c.is_active and not c.error]
        inactive_checks = [c for c in self.checks if not c.is_active and not c.error]
        error_checks = [c for c in self.checks if c.error]
        
        total_traffic = sum(c.traffic_bytes for c in self.checks)
        active_traffic = sum(c.traffic_bytes for c in active_checks)
        inactive_traffic = sum(c.traffic_bytes for c in inactive_checks)
        
        duration_sec = (self.end_time - self.start_time).total_seconds() if self.end_time else 0
        
        return {
            'total_checks': len(self.checks),
            'active_accounts': len(active_checks),
            'inactive_accounts': len(inactive_checks),
            'errors': len(error_checks),
            'total_traffic': total_traffic,
            'active_traffic': active_traffic,
            'inactive_traffic': inactive_traffic,
            'avg_traffic_active': active_traffic / len(active_checks) if active_checks else 0,
            'avg_traffic_inactive': inactive_traffic / len(inactive_checks) if inactive_checks else 0,
            'avg_traffic_per_check': total_traffic / len(self.checks) if self.checks else 0,
            'total_duration_sec': duration_sec
        }
    
    def format_bytes(self, bytes_count: int) -> str:
        """Format bytes in human readable format."""
        if bytes_count < 1024:
            return f"{bytes_count} B"
        elif bytes_count < 1024 * 1024:
            return f"{bytes_count / 1024:.2f} KB"
        else:
            return f"{bytes_count / (1024 * 1024):.2f} MB"
    
    def get_report(self) -> str:
        """
        Generate a formatted report.
        
        Returns:
            String with formatted statistics report
        """
        stats = self.get_summary()
        
        report = "📊 <b>ОТЧЕТ ПО ТРАФИКУ АВТОПРОВЕРКИ</b>\n\n"
        
        # General stats
        report += f"📋 <b>Общая статистика:</b>\n"
        report += f"  • Всего проверок: {stats['total_checks']}\n"
        report += f"  • Активных аккаунтов: {stats['active_accounts']}\n"
        report += f"  • Неактивных аккаунтов: {stats['inactive_accounts']}\n"
        report += f"  • Ошибок: {stats['errors']}\n"
        report += f"  • Длительность: {stats['total_duration_sec']:.1f} сек\n\n"
        
        # Traffic stats
        report += f"📊 <b>Статистика трафика:</b>\n"
        report += f"  • Общий трафик: <b>{self.format_bytes(stats['total_traffic'])}</b>\n"
        report += f"  • Средний трафик на проверку: <b>{self.format_bytes(int(stats['avg_traffic_per_check']))}</b>\n\n"
        
        # Active accounts traffic
        if stats['active_accounts'] > 0:
            report += f"✅ <b>Активные аккаунты:</b>\n"
            report += f"  • Количество: {stats['active_accounts']}\n"
            report += f"  • Общий трафик: <b>{self.format_bytes(stats['active_traffic'])}</b>\n"
            report += f"  • Средний трафик: <b>{self.format_bytes(int(stats['avg_traffic_active']))}</b>\n\n"
        
        # Inactive accounts traffic
        if stats['inactive_accounts'] > 0:
            report += f"❌ <b>Неактивные аккаунты:</b>\n"
            report += f"  • Количество: {stats['inactive_accounts']}\n"
            report += f"  • Общий трафик: <b>{self.format_bytes(stats['inactive_traffic'])}</b>\n"
            report += f"  • Средний трафик: <b>{self.format_bytes(int(stats['avg_traffic_inactive']))}</b>\n\n"
        
        # Timestamp
        report += f"⏰ Время: {self.start_time.strftime('%d.%m.%Y %H:%M:%S')}"
        
        return report

