"""
Universal Playwright Checker - проверенный метод создания скриншотов.
Использует мобильную эмуляцию для обхода защиты Instagram.
"""

import asyncio
import os
import random
from typing import Optional, Dict, Tuple
from datetime import datetime
from urllib.parse import urlparse

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
except ImportError:
    async_playwright = None
    PlaywrightTimeoutError = Exception


# Мобильные устройства для эмуляции
MOBILE_DEVICES = {
    "iPhone 12": {"width": 390, "height": 844},
    "iPhone 13 Pro": {"width": 390, "height": 844},
    "Samsung Galaxy S21": {"width": 360, "height": 800},
    "Pixel 6": {"width": 412, "height": 915}
}

# Мобильные User-Agents
MOBILE_USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 12; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Mobile Safari/537.36"
]


async def close_instagram_modals_aggressive(page):
    """🔥 Агрессивное удаление модальных окон и затемнения."""
    print("[PLAYWRIGHT] 🎯 Закрытие модальных окон и удаление затемнения...")
    
    try:
        # Ждем появления модальных окон
        await page.wait_for_timeout(3000)
        
        # СУПЕР АГРЕССИВНОЕ удаление затемнения и модалок
        js_code = """
        (() => {
            console.log('🔥 Начало удаления модальных окон и затемнения');
            let removedCount = 0;
            
            // 🔥 ШАГ 1: Удаляем все элементы с высоким z-index
            document.querySelectorAll('*').forEach(element => {
                const style = window.getComputedStyle(element);
                const zIndex = parseInt(style.zIndex) || 0;
                
                if (zIndex > 50) {
                    element.remove();
                    removedCount++;
                }
            });
            
            // 🔥 ШАГ 2: Удаляем все fixed и absolute элементы
            document.querySelectorAll('*').forEach(element => {
                const style = window.getComputedStyle(element);
                
                if (style.position === 'fixed' || 
                    (style.position === 'absolute' && parseInt(style.zIndex) > 0)) {
                    element.remove();
                    removedCount++;
                }
            });
            
            // 🔥 ШАГ 3: Удаляем по role
            document.querySelectorAll('[role="dialog"], [role="presentation"]').forEach(el => {
                el.remove();
                removedCount++;
            });
            
            // 🔥 ШАГ 4: Удаляем элементы с темным фоном
            document.querySelectorAll('*').forEach(element => {
                const style = window.getComputedStyle(element);
                const bg = style.backgroundColor;
                
                if (bg.includes('rgba(0, 0, 0') || bg.includes('rgb(0, 0, 0)')) {
                    if (parseInt(style.zIndex) > 0 || style.position === 'fixed') {
                        element.remove();
                        removedCount++;
                    }
                }
            });
            
            // 🔥 ШАГ 5: Восстанавливаем body и html
            if (document.body) {
                document.body.style.overflow = 'auto';
                document.body.style.filter = 'none';
                document.body.style.opacity = '1';
                document.body.style.backgroundColor = '';
                document.body.classList.remove('modal-open', 'overflow-hidden');
            }
            
            if (document.documentElement) {
                document.documentElement.style.overflow = 'auto';
                document.documentElement.style.filter = 'none';
                document.documentElement.style.opacity = '1';
            }
            
            // 🔥 ШАГ 6: Добавляем CSS для гарантии
            const style = document.createElement('style');
            style.id = 'remove-dimming-overlay';
            style.textContent = `
                body, html {
                    filter: none !important;
                    opacity: 1 !important;
                    overflow: visible !important;
                }
                [style*="position: fixed"],
                [style*="z-index"] {
                    filter: none !important;
                }
            `;
            document.head.appendChild(style);
            
            console.log('✅ Удалено элементов:', removedCount);
            console.log('✅ Затемнение и модальные окна убраны');
        })();
        """
        
        await page.evaluate(js_code)
        print("[PLAYWRIGHT] ✅ JavaScript удаление выполнено")
        
        # Метод 2: Клик по кнопкам закрытия
        close_selectors = [
            "button[aria-label='Close']",
            "svg[aria-label='Close']",
            "button[aria-label='Закрыть']",
            "svg[aria-label='Закрыть']"
        ]
        
        for selector in close_selectors:
            try:
                close_button = await page.query_selector(selector)
                if close_button:
                    await close_button.click()
                    print(f"[PLAYWRIGHT] ✅ Клик по: {selector}")
                    await page.wait_for_timeout(500)
            except Exception:
                pass
        
        # Метод 3: Escape клавиша
        try:
            await page.keyboard.press('Escape')
            await page.keyboard.press('Escape')
            await page.keyboard.press('Escape')
            print("[PLAYWRIGHT] ⌨️ Escape нажат")
        except Exception:
            pass
        
        # Финальная пауза
        await page.wait_for_timeout(1000)
        
        print("[PLAYWRIGHT] ✅ Модальные окна и затемнение обработаны")
        
    except Exception as e:
        print(f"[PLAYWRIGHT] ⚠️ Ошибка закрытия модальных окон: {e}")


async def check_instagram_account_universal(
    username: str,
    proxy_url: Optional[str] = None,
    screenshot_path: Optional[str] = None,
    headless: bool = True,
    timeout: int = 90,
    mobile_emulation: bool = True
) -> Tuple[bool, str, Optional[str], Optional[Dict]]:
    """
    Проверка Instagram аккаунта через Playwright с настраиваемой эмуляцией.
    Проверенный метод - работает стабильно.
    
    Args:
        username: Instagram username
        proxy_url: Proxy URL  
        screenshot_path: Path for screenshot
        headless: Headless mode
        timeout: Timeout in seconds
        mobile_emulation: If True, use mobile emulation; if False, use desktop
        
    Returns:
        Tuple of (success, message, screenshot_path, profile_data)
    """
    if not async_playwright:
        return False, "❌ Playwright не установлен", None, None
    
    # Парсим прокси
    proxy_config = None
    if proxy_url:
        try:
            parsed = urlparse(proxy_url)
            proxy_config = {
                "server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
            }
            if parsed.username:
                proxy_config["username"] = parsed.username
                proxy_config["password"] = parsed.password
            print(f"[PLAYWRIGHT] 🌐 Прокси: {proxy_config['server']}")
        except Exception as e:
            print(f"[PLAYWRIGHT] ⚠️ Ошибка парсинга прокси: {e}")
    
    try:
        async with async_playwright() as p:
            # Запускаем Firefox (установлен в .venv)
            try:
                browser = await p.firefox.launch(
                    headless=headless,
                    proxy=proxy_config
                )
                print(f"[PLAYWRIGHT] ✅ Firefox запущен с прокси")
            except Exception as proxy_error:
                print(f"[PLAYWRIGHT] ⚠️ Ошибка с прокси: {proxy_error}")
                print(f"[PLAYWRIGHT] 🔄 Пробуем без прокси...")
                browser = await p.firefox.launch(headless=headless)
                proxy_config = None  # Отключаем прокси
                print(f"[PLAYWRIGHT] ✅ Firefox запущен без прокси")
            
            # Настройка эмуляции (мобильная или desktop)
            if mobile_emulation:
                # Мобильная эмуляция
                device_name = random.choice(list(MOBILE_DEVICES.keys()))
                device = MOBILE_DEVICES[device_name]
                user_agent = random.choice(MOBILE_USER_AGENTS)
                
                print(f"[PLAYWRIGHT] 📱 Эмуляция: {device_name}")
                print(f"[PLAYWRIGHT] 🌐 User-Agent: {user_agent[:60]}...")
                
                # Создаем контекст с мобильными настройками
                context = await browser.new_context(
                    viewport={"width": device["width"], "height": device["height"]},
                    user_agent=user_agent,
                    locale='en-US',
                    timezone_id='America/New_York'
                )
            else:
                # Desktop режим
                desktop_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                
                print(f"[PLAYWRIGHT] 🖥️ Режим: Desktop")
                print(f"[PLAYWRIGHT] 🌐 User-Agent: {desktop_user_agent[:60]}...")
                
                # Создаем контекст с desktop настройками
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent=desktop_user_agent,
                    locale='en-US',
                    timezone_id='America/New_York'
                )
            
            page = await context.new_page()
            
            # Скрываем признаки автоматизации
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            """)
            
            # Устанавливаем таймаут
            page.set_default_timeout(timeout * 1000)
            
            # Переходим на профиль
            url = f"https://www.instagram.com/{username}/"
            print(f"[PLAYWRIGHT] 📡 Переход на: {url}")
            
            # Проверяем доступность прокси
            if proxy_url:
                print(f"[PLAYWRIGHT] 🔍 Проверяю доступность прокси...")
                try:
                    test_response = await page.goto("https://httpbin.org/ip", timeout=15000)
                    if test_response and test_response.status == 200:
                        print(f"[PLAYWRIGHT] ✅ Прокси доступен")
                    else:
                        print(f"[PLAYWRIGHT] ⚠️ Прокси может быть недоступен")
                except Exception as proxy_test_error:
                    print(f"[PLAYWRIGHT] ⚠️ Проблема с прокси: {proxy_test_error}")
            
            try:
                print(f"[PLAYWRIGHT] ⏱️ Timeout установлен: {timeout} секунд")
                # Используем более быстрый подход - ждем только DOM
                try:
                    response = await page.goto(url, wait_until='domcontentloaded', timeout=timeout * 1000)
                    status_code = response.status
                    print(f"[PLAYWRIGHT] 📊 HTTP Status: {status_code}")
                except Exception as goto_error:
                    print(f"[PLAYWRIGHT] ⚠️ Ошибка перехода: {goto_error}")
                    # Пробуем еще раз с более коротким timeout
                    try:
                        response = await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                        status_code = response.status
                        print(f"[PLAYWRIGHT] 📊 HTTP Status (retry): {status_code}")
                    except Exception as retry_error:
                        print(f"[PLAYWRIGHT] ❌ Критическая ошибка: {retry_error}")
                        await browser.close()
                        return False, f"❌ Ошибка: {retry_error}", None, None
                
                # Ждем загрузки контента - более агрессивно
                print(f"[PLAYWRIGHT] ⏳ Ждем загрузки контента...")
                
                # Ждем появления основных элементов Instagram
                try:
                    # Ждем аватар или имя пользователя
                    await page.wait_for_selector('img[alt*="Фото профиля"], img[alt*="Profile picture"], h1, h2', timeout=15000)
                    print(f"[PLAYWRIGHT] ✅ Основные элементы найдены")
                except:
                    print(f"[PLAYWRIGHT] ⚠️ Основные элементы не найдены")
                
                # Ждем загрузки изображений - более агрессивно
                print(f"[PLAYWRIGHT] 🖼️ Ждем загрузки изображений...")
                await page.wait_for_timeout(8000)
                
                # Ждем загрузки аватара профиля специально
                try:
                    # Ищем аватар по разным селекторам
                    avatar_selectors = [
                        'img[alt*="Фото профиля"]',
                        'img[alt*="Profile picture"]',
                        'img[alt*="profile"]',
                        'img[alt*="avatar"]',
                        'img[src*="profile"]',
                        'img[src*="avatar"]',
                        'img[class*="profile"]',
                        'img[class*="avatar"]'
                    ]
                    
                    avatar_found = False
                    for selector in avatar_selectors:
                        try:
                            await page.wait_for_selector(selector, timeout=5000)
                            print(f"[PLAYWRIGHT] ✅ Аватар найден: {selector}")
                            avatar_found = True
                            break
                        except:
                            continue
                    
                    if avatar_found:
                        # Ждем полной загрузки аватара
                        await page.wait_for_function("""
                            () => {
                                const selectors = [
                                    'img[alt*="Фото профиля"]',
                                    'img[alt*="Profile picture"]',
                                    'img[alt*="profile"]',
                                    'img[alt*="avatar"]',
                                    'img[src*="profile"]',
                                    'img[src*="avatar"]',
                                    'img[class*="profile"]',
                                    'img[class*="avatar"]'
                                ];
                                
                                for (const selector of selectors) {
                                    const img = document.querySelector(selector);
                                    if (img && img.complete && img.naturalWidth > 0) {
                                        return true;
                                    }
                                }
                                return false;
                            }
                        """, timeout=15000)
                        print(f"[PLAYWRIGHT] ✅ Аватар полностью загружен")
                    else:
                        print(f"[PLAYWRIGHT] ⚠️ Аватар не найден")
                        
                except Exception as avatar_error:
                    print(f"[PLAYWRIGHT] ⚠️ Проблема с аватаром: {avatar_error}")
                
                # Ждем загрузки любых изображений на странице
                try:
                    await page.wait_for_selector('img', timeout=10000)
                    print(f"[PLAYWRIGHT] ✅ Изображения найдены")
                    
                    # Ждем полной загрузки всех изображений
                    await page.wait_for_function("""
                        () => {
                            const images = document.querySelectorAll('img');
                            let loadedCount = 0;
                            images.forEach(img => {
                                if (img.complete && img.naturalWidth > 0) {
                                    loadedCount++;
                                }
                            });
                            return loadedCount > 0;
                        }
                    """, timeout=15000)
                    print(f"[PLAYWRIGHT] ✅ Изображения загружены")
                except:
                    print(f"[PLAYWRIGHT] ⚠️ Изображения не загрузились")
                
                # Дополнительное ожидание для полной загрузки всех элементов
                await page.wait_for_timeout(5000)
                
                # Закрываем модальные окна
                await close_instagram_modals_aggressive(page)
                
                # Проверяем, что контент действительно загрузился
                try:
                    # Проверяем наличие видимого контента
                    visible_elements = await page.evaluate("""
                        () => {
                            const elements = document.querySelectorAll('img, h1, h2, div[role="main"]');
                            let visibleCount = 0;
                            elements.forEach(el => {
                                const rect = el.getBoundingClientRect();
                                if (rect.width > 0 && rect.height > 0) {
                                    visibleCount++;
                                }
                            });
                            return visibleCount;
                        }
                    """)
                    print(f"[PLAYWRIGHT] 👁️ Видимых элементов: {visible_elements}")
                    
                    if visible_elements < 3:
                        print(f"[PLAYWRIGHT] ⚠️ Мало видимого контента, ждем еще...")
                        await page.wait_for_timeout(5000)
                except:
                    print(f"[PLAYWRIGHT] ⚠️ Не удалось проверить видимость контента")
                
                # Получаем информацию
                page_title = await page.title()
                content = await page.content()
                current_url = page.url
                
                print(f"[PLAYWRIGHT] 📄 Title: {page_title}")
                print(f"[PLAYWRIGHT] 🔗 URL: {current_url}")
                
                # Проверяем статус
                profile_data = {}
                
                if status_code == 404:
                    message = "❌ Профиль не найден (404)"
                    await browser.close()
                    return False, message, None, None
                
                elif status_code == 403:
                    message = "🚫 Доступ запрещен (403)"
                    await browser.close()
                    return False, message, None, None
                
                elif "Sorry, this page isn't available" in content:
                    message = "❌ Страница недоступна"
                    await browser.close()
                    return False, message, None, None
                
                # Профиль доступен - делаем скриншот
                if screenshot_path:
                    try:
                        # Создаем папку
                        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                        
                        # Делаем полный скриншот страницы профиля БЕЗ обрезки
                        print(f"[PLAYWRIGHT] 📸 Создание полного скриншота профиля...")
                        await page.screenshot(path=screenshot_path, full_page=False)
                        
                        if os.path.exists(screenshot_path):
                            size = os.path.getsize(screenshot_path) / 1024
                            print(f"[PLAYWRIGHT] ✅ Скриншот профиля создан: {size:.1f} KB")
                            profile_data['screenshot'] = screenshot_path
                        else:
                            print(f"[PLAYWRIGHT] ❌ Скриншот не создан")
                            screenshot_path = None
                        
                    except Exception as e:
                        print(f"[PLAYWRIGHT] ⚠️ Ошибка скриншота: {e}")
                        screenshot_path = None
                
                # Закрываем браузер
                await browser.close()
                
                # Получаем meta description
                try:
                    meta_desc = page_title
                    if meta_desc:
                        profile_data['description'] = meta_desc
                except:
                    pass
                
                message = f"✅ Профиль доступен"
                if page_title:
                    message += f"\n📄 {page_title}"
                
                return True, message, screenshot_path, profile_data
                
            except PlaywrightTimeoutError as e:
                print(f"[PLAYWRIGHT] ⏱️ Timeout ошибка: {e}")
                await browser.close()
                return False, f"⏱️ Timeout - страница не загрузилась за {timeout} секунд", None, None
            
    except Exception as e:
        return False, f"❌ Ошибка: {str(e)[:100]}", None, None


async def batch_check_accounts_universal(
    accounts: list,
    proxy_url: Optional[str] = None,
    screenshots_dir: str = "screenshots",
    headless: bool = True
) -> Dict[str, Dict]:
    """Массовая проверка аккаунтов."""
    results = {}
    
    for account in accounts:
        if hasattr(account, 'account'):
            username = account.account
        else:
            username = str(account)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(screenshots_dir, f"{username}_{timestamp}.png")
        
        print(f"\n[PLAYWRIGHT] 🔍 Проверка @{username}...")
        
        success, message, screenshot, profile_data = await check_instagram_account_universal(
            username=username,
            proxy_url=proxy_url,
            screenshot_path=screenshot_path,
            headless=headless
        )
        
        results[username] = {
            'success': success,
            'message': message,
            'screenshot': screenshot,
            'profile_data': profile_data,
            'checked_at': datetime.now().isoformat()
        }
        
        # Пауза между проверками
        await asyncio.sleep(random.uniform(3, 6))
    
    return results
