#!/usr/bin/env python3
"""
Быстрый тест проверки прокси
"""

import asyncio
import aiohttp
from sqlalchemy.orm import Session
from project.database import get_engine, get_session_factory, init_db
from project.models import Proxy


async def test_proxy():
    """Проверяем первый активный прокси"""
    
    print("=" * 80)
    print("🔍 ТЕСТ ПРОКСИ")
    print("=" * 80)
    print()
    
    # Инициализация БД
    db_url = "sqlite:///bot.db"
    engine = get_engine(db_url)
    init_db(engine)
    session_factory = get_session_factory(engine)
    
    with session_factory() as session:
        # Получаем первый активный прокси
        proxy = session.query(Proxy).filter(
            Proxy.is_active == True
        ).first()
        
        if not proxy:
            print("❌ Нет активных прокси в БД!")
            return
        
        # Формируем proxy_url (host уже содержит ip:port)
        if proxy.username and proxy.password:
            proxy_url = f"{proxy.scheme}://{proxy.username}:{proxy.password}@{proxy.host}"
        else:
            proxy_url = f"{proxy.scheme}://{proxy.host}"
        
        print(f"📋 Тестируемый прокси:")
        print(f"   Scheme: {proxy.scheme}")
        print(f"   Host: {proxy.host}")
        print(f"   Username: {proxy.username if proxy.username else 'None'}")
        print()
        
        # Тест 1: Проверка через httpbin.org
        print("🔄 Тест 1: Проверка через httpbin.org...")
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    "http://httpbin.org/ip",
                    proxy=proxy_url
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        ip = data.get("origin", "Unknown")
                        print(f"✅ Прокси работает! IP: {ip}")
                    else:
                        print(f"⚠️ Статус: {response.status}")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        print()
        
        # Тест 2: Проверка доступа к Instagram
        print("🔄 Тест 2: Проверка доступа к Instagram...")
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            headers = {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 203.0.0.29.118"
            }
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    "https://www.instagram.com/",
                    proxy=proxy_url,
                    headers=headers,
                    allow_redirects=True
                ) as response:
                    print(f"   Статус: {response.status}")
                    print(f"   URL: {response.url}")
                    
                    if response.status == 200:
                        print(f"✅ Доступ к Instagram через прокси работает!")
                    elif response.status == 302 or response.status == 301:
                        print(f"⚠️ Редирект на: {response.headers.get('Location', 'Unknown')}")
                    else:
                        print(f"⚠️ Необычный статус: {response.status}")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        print()
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_proxy())

