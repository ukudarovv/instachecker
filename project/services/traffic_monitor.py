"""
Traffic monitoring utility for proxy requests.
Tracks data usage for each proxy request.
"""

import asyncio
import time
from typing import Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json
import os


@dataclass
class TrafficStats:
    """Statistics for a single request."""
    proxy_ip: str
    url: str
    request_size: int = 0
    response_size: int = 0
    total_size: int = 0
    duration_ms: float = 0.0
    timestamp: datetime = None
    success: bool = False
    status_code: int = 0
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        self.total_size = self.request_size + self.response_size


class TrafficMonitor:
    """Monitor traffic usage for proxy requests."""
    
    def __init__(self, log_file: str = "traffic_log.json"):
        self.log_file = log_file
        self.stats: Dict[str, TrafficStats] = {}
        self.total_traffic = 0
        self.proxy_traffic = {}
        
    def start_request(self, request_id: str, proxy_ip: str, url: str) -> None:
        """Start monitoring a request."""
        self.stats[request_id] = TrafficStats(
            proxy_ip=proxy_ip,
            url=url,
            timestamp=datetime.now()
        )
        print(f"[TRAFFIC-MONITOR] 🚀 Начинаем мониторинг трафика для {proxy_ip}")
    
    def end_request(self, request_id: str, success: bool, status_code: int, 
                   request_size: int = 0, response_size: int = 0, 
                   duration_ms: float = 0.0) -> TrafficStats:
        """End monitoring a request and return stats."""
        if request_id not in self.stats:
            return None
            
        stats = self.stats[request_id]
        stats.success = success
        stats.status_code = status_code
        stats.request_size = request_size
        stats.response_size = response_size
        stats.duration_ms = duration_ms
        stats.total_size = request_size + response_size
        
        # Update totals
        self.total_traffic += stats.total_size
        
        # Update proxy-specific totals
        if stats.proxy_ip not in self.proxy_traffic:
            self.proxy_traffic[stats.proxy_ip] = {
                'total_requests': 0,
                'total_traffic': 0,
                'successful_requests': 0,
                'failed_requests': 0
            }
        
        proxy_stats = self.proxy_traffic[stats.proxy_ip]
        proxy_stats['total_requests'] += 1
        proxy_stats['total_traffic'] += stats.total_size
        
        if success:
            proxy_stats['successful_requests'] += 1
        else:
            proxy_stats['failed_requests'] += 1
        
        # Log the request
        self._log_request(stats)
        
        # Remove from active stats
        del self.stats[request_id]
        
        return stats
    
    def _log_request(self, stats: TrafficStats) -> None:
        """Log request statistics."""
        print(f"[TRAFFIC-MONITOR] 📊 Запрос завершен:")
        print(f"  🌐 Прокси: {stats.proxy_ip}")
        print(f"  📡 URL: {stats.url}")
        print(f"  📤 Исходящий трафик: {self._format_bytes(stats.request_size)}")
        print(f"  📥 Входящий трафик: {self._format_bytes(stats.response_size)}")
        print(f"  📊 Общий трафик: {self._format_bytes(stats.total_size)}")
        print(f"  ⏱️ Время: {stats.duration_ms:.2f}ms")
        print(f"  ✅ Успех: {'Да' if stats.success else 'Нет'}")
        print(f"  🔢 Статус: {stats.status_code}")
        
        # Log to file
        self._save_to_file(stats)
    
    def _format_bytes(self, bytes_count: int) -> str:
        """Format bytes in human readable format."""
        if bytes_count < 1024:
            return f"{bytes_count} B"
        elif bytes_count < 1024 * 1024:
            return f"{bytes_count / 1024:.2f} KB"
        else:
            return f"{bytes_count / (1024 * 1024):.2f} MB"
    
    def _save_to_file(self, stats: TrafficStats) -> None:
        """Save statistics to log file."""
        try:
            log_entry = {
                'timestamp': stats.timestamp.isoformat(),
                'proxy_ip': stats.proxy_ip,
                'url': stats.url,
                'request_size': stats.request_size,
                'response_size': stats.response_size,
                'total_size': stats.total_size,
                'duration_ms': stats.duration_ms,
                'success': stats.success,
                'status_code': stats.status_code
            }
            
            # Append to log file
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"[TRAFFIC-MONITOR] ❌ Ошибка записи в лог: {e}")
    
    def get_proxy_stats(self, proxy_ip: str) -> Dict[str, Any]:
        """Get statistics for a specific proxy."""
        if proxy_ip not in self.proxy_traffic:
            return {
                'total_requests': 0,
                'total_traffic': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'success_rate': 0.0,
                'average_traffic_per_request': 0
            }
        
        stats = self.proxy_traffic[proxy_ip]
        success_rate = (stats['successful_requests'] / stats['total_requests'] * 100) if stats['total_requests'] > 0 else 0
        avg_traffic = stats['total_traffic'] / stats['total_requests'] if stats['total_requests'] > 0 else 0
        
        return {
            **stats,
            'success_rate': round(success_rate, 2),
            'average_traffic_per_request': round(avg_traffic, 2)
        }
    
    def get_total_stats(self) -> Dict[str, Any]:
        """Get total traffic statistics."""
        total_requests = sum(stats['total_requests'] for stats in self.proxy_traffic.values())
        total_successful = sum(stats['successful_requests'] for stats in self.proxy_traffic.values())
        success_rate = (total_successful / total_requests * 100) if total_requests > 0 else 0
        
        # Вычисляем среднее время запроса
        completed_requests = [stats for stats in self.stats.values() if hasattr(stats, 'duration_ms') and stats.duration_ms > 0]
        average_duration_ms = sum(s.duration_ms for s in completed_requests) / len(completed_requests) if completed_requests else 0
        
        return {
            'total_traffic': self.total_traffic,
            'total_requests': total_requests,
            'successful_requests': total_successful,
            'failed_requests': total_requests - total_successful,
            'success_rate': round(success_rate, 2),
            'average_traffic_per_request': round(self.total_traffic / total_requests, 2) if total_requests > 0 else 0,
            'average_duration_ms': round(average_duration_ms, 2),
            'proxies_used': len(self.proxy_traffic)
        }
    
    def print_summary(self) -> None:
        """Print traffic summary."""
        total_stats = self.get_total_stats()
        
        print(f"\n[TRAFFIC-MONITOR] 📊 СВОДКА ТРАФИКА:")
        print(f"  📊 Общий трафик: {self._format_bytes(total_stats['total_traffic'])}")
        print(f"  🔢 Всего запросов: {total_stats['total_requests']}")
        print(f"  ✅ Успешных: {total_stats['successful_requests']}")
        print(f"  ❌ Неудачных: {total_stats['failed_requests']}")
        print(f"  📈 Успешность: {total_stats['success_rate']}%")
        print(f"  ⏱️  Среднее время запроса: {total_stats['average_duration_ms']:.0f}ms")
        print(f"  📊 Средний трафик на запрос: {self._format_bytes(total_stats['average_traffic_per_request'])}")
        print(f"  🌐 Прокси использовано: {total_stats['proxies_used']}")
        
        print(f"\n[TRAFFIC-MONITOR] 📊 ПО ПРОКСИ:")
        for proxy_ip, stats in self.proxy_traffic.items():
            proxy_stats = self.get_proxy_stats(proxy_ip)
            print(f"  🌐 {proxy_ip}:")
            print(f"    📊 Трафик: {self._format_bytes(stats['total_traffic'])}")
            print(f"    🔢 Запросов: {stats['total_requests']}")
            print(f"    ✅ Успешность: {proxy_stats['success_rate']}%")


# Global traffic monitor instance
traffic_monitor = TrafficMonitor()


def get_traffic_monitor() -> TrafficMonitor:
    """Get the global traffic monitor instance."""
    return traffic_monitor
