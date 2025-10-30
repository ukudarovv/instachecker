"""
Измерение трафика при запросах к Instagram API через прокси.
"""

import asyncio
import sys
import os
import aiohttp

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from project.database import get_engine, get_session_factory
from project.models import Proxy
from project.config import get_settings


class TrafficMeasurer:
    """Класс для измерения трафика"""
    
    def __init__(self):
        self.request_bytes = 0
        self.response_bytes = 0
        self.headers_bytes = 0
        
    def measure_headers(self, headers):
        """Измеряем размер заголовков"""
        headers_str = ""
        for key, value in headers.items():
            headers_str += f"{key}: {value}\r\n"
        self.headers_bytes = len(headers_str.encode('utf-8'))
        return self.headers_bytes
    
    def format_bytes(self, bytes_count):
        """Форматирование размера"""
        if bytes_count < 1024:
            return f"{bytes_count} B"
        elif bytes_count < 1024 * 1024:
            return f"{bytes_count / 1024:.2f} KB"
        else:
            return f"{bytes_count / (1024 * 1024):.2f} MB"


async def measure_single_request(username: str, proxy_url: str = None):
    """
    Измеряет трафик для одного запроса к Instagram API
    """
    measurer = TrafficMeasurer()
    
    url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
    
    # Заголовки
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.9",
        "accept-encoding": "gzip, deflate, br",
        "cache-control": "max-age=0",
        "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "X-ASBD-ID": "129477",
        "X-IG-WWW-Claim": "0",
        "X-IG-App-ID": "936619743392459",
        "Referer": "https://www.instagram.com/",
    }
    
    # Измеряем размер заголовков
    headers_size = measurer.measure_headers(headers)
    
    # Измеряем размер URL и метода
    request_line = f"GET {url} HTTP/1.1"
    request_line_size = len(request_line.encode('utf-8'))
    
    # Общий размер исходящего запроса
    measurer.request_bytes = request_line_size + headers_size + 4  # +4 для \r\n\r\n
    
    print(f"\n📤 ИСХОДЯЩИЙ ЗАПРОС:")
    print(f"   URL: {url}")
    print(f"   Метод + URL: {measurer.format_bytes(request_line_size)}")
    print(f"   Headers: {measurer.format_bytes(headers_size)}")
    print(f"   ВСЕГО: {measurer.format_bytes(measurer.request_bytes)}")
    
    # Делаем запрос
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=headers,
                proxy=proxy_url,
                timeout=aiohttp.ClientTimeout(total=15),
                ssl=False
            ) as response:
                # Читаем ответ
                response_data = await response.read()
                measurer.response_bytes = len(response_data)
                
                # Измеряем заголовки ответа
                response_headers_size = 0
                for key, value in response.headers.items():
                    response_headers_size += len(f"{key}: {value}\r\n".encode('utf-8'))
                
                # Статус линия
                status_line = f"HTTP/1.1 {response.status} {response.reason}"
                status_line_size = len(status_line.encode('utf-8'))
                
                print(f"\n📥 ВХОДЯЩИЙ ОТВЕТ:")
                print(f"   Статус: {response.status} {response.reason}")
                print(f"   Status Line: {measurer.format_bytes(status_line_size)}")
                print(f"   Response Headers: {measurer.format_bytes(response_headers_size)}")
                print(f"   Body (raw): {measurer.format_bytes(measurer.response_bytes)}")
                
                # Декомпрессия если gzip
                is_compressed = response.headers.get('Content-Encoding', '').lower() in ['gzip', 'br', 'deflate']
                if is_compressed:
                    print(f"   Body (compressed): ДА ({response.headers.get('Content-Encoding')})")
                else:
                    print(f"   Body (compressed): НЕТ")
                
                total_response = status_line_size + response_headers_size + measurer.response_bytes + 4
                print(f"   ВСЕГО: {measurer.format_bytes(total_response)}")
                
                # Итого
                total_traffic = measurer.request_bytes + total_response
                
                print(f"\n📊 ИТОГО ЗА ОДИН ЗАПРОС:")
                print(f"   Исходящий трафик: {measurer.format_bytes(measurer.request_bytes)}")
                print(f"   Входящий трафик: {measurer.format_bytes(total_response)}")
                print(f"   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                print(f"   ОБЩИЙ ТРАФИК: {measurer.format_bytes(total_traffic)}")
                
                # Успешность
                if response.status == 200:
                    print(f"   ✅ Запрос успешен")
                else:
                    print(f"   ⚠️ Статус: {response.status}")
                
                return {
                    'success': response.status == 200,
                    'request_bytes': measurer.request_bytes,
                    'response_bytes': total_response,
                    'total_bytes': total_traffic,
                    'status': response.status
                }
                
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        return None


async def measure_multiple_requests(usernames: list, proxy_url: str = None):
    """
    Измеряет трафик для нескольких запросов
    """
    print(f"\n{'='*60}")
    print(f"📊 ИЗМЕРЕНИЕ ТРАФИКА ДЛЯ {len(usernames)} ЗАПРОСОВ")
    print(f"{'='*60}")
    
    results = []
    
    for idx, username in enumerate(usernames, 1):
        print(f"\n[{idx}/{len(usernames)}] Запрос для @{username}")
        print(f"{'-'*60}")
        
        result = await measure_single_request(username, proxy_url)
        if result:
            results.append(result)
        
        # Задержка между запросами
        if idx < len(usernames):
            await asyncio.sleep(2)
    
    # Статистика
    if results:
        print(f"\n\n{'='*60}")
        print(f"📈 СТАТИСТИКА ПО ВСЕМ ЗАПРОСАМ")
        print(f"{'='*60}\n")
        
        total_request = sum(r['request_bytes'] for r in results)
        total_response = sum(r['response_bytes'] for r in results)
        total_all = sum(r['total_bytes'] for r in results)
        avg_total = total_all / len(results)
        
        success_count = sum(1 for r in results if r['success'])
        
        print(f"Всего запросов: {len(results)}")
        print(f"Успешных: {success_count}")
        print(f"Неудачных: {len(results) - success_count}")
        print(f"\nОбщий исходящий трафик: {TrafficMeasurer().format_bytes(total_request)}")
        print(f"Общий входящий трафик: {TrafficMeasurer().format_bytes(total_response)}")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"ВСЕГО ТРАФИКА: {TrafficMeasurer().format_bytes(total_all)}")
        print(f"\n📊 Средний трафик на 1 запрос: {TrafficMeasurer().format_bytes(avg_total)}")
        
        # Экстраполяция
        print(f"\n📈 ЭКСТРАПОЛЯЦИЯ:")
        print(f"   10 запросов = {TrafficMeasurer().format_bytes(avg_total * 10)}")
        print(f"   100 запросов = {TrafficMeasurer().format_bytes(avg_total * 100)}")
        print(f"   1000 запросов = {TrafficMeasurer().format_bytes(avg_total * 1000)}")


async def main():
    """Главная функция"""
    print("\n" + "="*60)
    print("📊 ИЗМЕРИТЕЛЬ ТРАФИКА Instagram API")
    print("="*60)
    
    # Инициализация БД для получения прокси
    try:
        settings = get_settings()
        engine = get_engine(settings.db_url)
        SessionFactory = get_session_factory(engine)
        session = SessionFactory()
        
        # Получаем прокси
        proxy = session.query(Proxy).filter(Proxy.is_active == True).first()
        
        if proxy:
            proxy_url = f"{proxy.scheme}://{proxy.username}:{proxy.password}@{proxy.host}"
            print(f"\n🔗 Используем прокси: {proxy.host}")
        else:
            proxy_url = None
            print(f"\n⚠️ Прокси не найден, используем прямое подключение")
        
        session.close()
        
    except Exception as e:
        print(f"\n⚠️ Ошибка получения прокси: {e}")
        proxy_url = None
    
    # Тестовые аккаунты
    test_usernames = ["instagram", "cristiano", "leomessi"]
    
    await measure_multiple_requests(test_usernames, proxy_url)
    
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

