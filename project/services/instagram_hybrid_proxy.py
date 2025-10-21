"""
🔥 Гибридная система проверки Instagram с прокси
API проверка через прокси + Firefox скриншоты без прокси
"""

import asyncio
import aiohttp
import time
import random
import os
from typing import Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By


class InstagramHybridProxyChecker:
    """Гибридная система проверки Instagram: API с прокси + Firefox без прокси"""
    
    def __init__(self):
        self.mobile_user_agents = [
            'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 12; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36'
        ]
    
    async def check_via_api_with_proxy(self, username: str, proxy: str) -> dict:
        """✅ Проверка через API с прокси и аутентификацией"""
        print(f"[API-PROXY] 🔍 Проверка @{username} через API с прокси...")
        
        headers = {
            'User-Agent': random.choice(self.mobile_user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
        urls_to_try = [
            f'https://www.instagram.com/{username}/?__a=1&__d=dis',
            f'https://i.instagram.com/api/v1/users/web_profile_info/?username={username}',
            f'https://www.instagram.com/{username}/',
        ]
        
        for url in urls_to_try:
            try:
                print(f"[API-PROXY] 🌐 Запрос: {url[:60]}...")
                
                timeout = aiohttp.ClientTimeout(total=30)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url, headers=headers, proxy=proxy) as response:
                        status = response.status
                        print(f"[API-PROXY] 📊 Статус: {status}")
                        
                        if status == 200:
                            text = await response.text()
                            text_lower = text.lower()
                            
                            # Проверяем на 404
                            if 'страница не найдена' in text_lower or 'sorry, this page' in text_lower or 'not found' in text_lower:
                                print(f"[API-PROXY] ❌ Профиль @{username} не найден (404)")
                                return {"exists": False, "method": "api_proxy", "status_code": status}
                            
                            # Проверяем наличие username в тексте
                            if username.lower() in text_lower:
                                print(f"[API-PROXY] ✅ Профиль @{username} найден через API с прокси")
                                return {"exists": True, "method": "api_proxy", "status_code": status}
                        
                        elif status == 404:
                            print(f"[API-PROXY] ❌ Профиль @{username} не найден (404)")
                            return {"exists": False, "method": "api_proxy", "status_code": status}
                        
                        elif status in [200, 201]:
                            print(f"[API-PROXY] ✅ Профиль @{username} найден (статус {status})")
                            return {"exists": True, "method": "api_proxy", "status_code": status}
                            
            except Exception as e:
                print(f"[API-PROXY] ⚠️ Ошибка с {url[:60]}...: {e}")
                continue
        
        print(f"[API-PROXY] ⚠️ Все API эндпоинты не сработали")
        return {"exists": None, "error": "api_failed", "method": "api_proxy"}
    
    async def take_screenshot_with_playwright(self, username: str, screenshot_path: str, headless: bool = True, proxy: str = None) -> bool:
        """✅ Создание скриншота через Playwright (РЕКОМЕНДУЕТСЯ)"""
        print(f"[PLAYWRIGHT-SCREENSHOT] 📸 Создание скриншота для @{username}...")
        if proxy:
            print(f"[PLAYWRIGHT-SCREENSHOT] 🔗 С прокси (нативная поддержка)")
        else:
            print(f"[PLAYWRIGHT-SCREENSHOT] 🔗 Без прокси")
        
        try:
            from project.services.instagram_playwright import InstagramPlaywrightChecker
            
            checker = InstagramPlaywrightChecker()
            result = await checker.check_profile_existence(
                username=username,
                screenshot_path=screenshot_path,
                headless=headless,
                proxy=proxy
            )
            
            if result.get("screenshot_path") and os.path.exists(result["screenshot_path"]):
                file_size = os.path.getsize(result["screenshot_path"])
                print(f"[PLAYWRIGHT-SCREENSHOT] ✅ Скриншот создан: {file_size} байт")
                return True
            else:
                print(f"[PLAYWRIGHT-SCREENSHOT] ❌ Скриншот не создан")
                return False
                
        except ImportError:
            print(f"[PLAYWRIGHT-SCREENSHOT] ⚠️ Playwright не установлен, используем Firefox fallback")
            print(f"[PLAYWRIGHT-SCREENSHOT] 💡 Установите: pip install playwright && playwright install chromium")
            return self.take_screenshot_with_firefox(username, screenshot_path, headless, proxy)
        except Exception as e:
            print(f"[PLAYWRIGHT-SCREENSHOT] ❌ Ошибка Playwright: {e}")
            print(f"[PLAYWRIGHT-SCREENSHOT] 🔄 Переход на Firefox fallback")
            return self.take_screenshot_with_firefox(username, screenshot_path, headless, proxy)
    
    def take_screenshot_with_firefox(self, username: str, screenshot_path: str, headless: bool = True, proxy: str = None) -> bool:
        """✅ Создание скриншота через Firefox с поддержкой прокси"""
        print(f"[FIREFOX-SCREENSHOT] 📸 Создание скриншота для @{username}...")
        if proxy:
            print(f"[FIREFOX-SCREENSHOT] 🔗 С прокси: {proxy.split('@')[0].split(':')[0]}:***@{proxy.split('@')[1] if '@' in proxy else proxy}")
        else:
            print(f"[FIREFOX-SCREENSHOT] 🔗 Без прокси")
        
        driver = None
        try:
            options = FirefoxOptions()
            
            # Мобильная эмуляция
            mobile_user_agent = random.choice(self.mobile_user_agents)
            options.set_preference("general.useragent.override", mobile_user_agent)
            
            # Настройки для обхода блокировок
            options.set_preference("dom.webdriver.enabled", False)
            options.set_preference("useAutomationExtension", False)
            
            # Размер окна
            options.add_argument("--width=390")
            options.add_argument("--height=844")
            
            if headless:
                options.add_argument("--headless")
            
            # 🔥 ПОДДЕРЖКА ПРОКСИ ЧЕРЕЗ SELENIUM WIRE
            if proxy:
                try:
                    from seleniumwire import webdriver as seleniumwire_webdriver
                    print(f"[FIREFOX-SCREENSHOT] 🔧 Инициализация Firefox с прокси через Selenium Wire...")
                    
                    # Настройка прокси для Selenium Wire
                    seleniumwire_options = {
                        'proxy': {
                            'http': proxy,
                            'https': proxy,
                            'no_proxy': 'localhost,127.0.0.1'
                        }
                    }
                    
                    driver = seleniumwire_webdriver.Firefox(
                        options=options,
                        seleniumwire_options=seleniumwire_options
                    )
                    print(f"[FIREFOX-SCREENSHOT] ✅ Firefox с прокси инициализирован")
                    
                except ImportError:
                    print(f"[FIREFOX-SCREENSHOT] ⚠️ Selenium Wire не установлен, используем Firefox без прокси")
                    print(f"[FIREFOX-SCREENSHOT] 💡 Установите: pip install selenium-wire")
                    driver = webdriver.Firefox(options=options)
                except Exception as e:
                    print(f"[FIREFOX-SCREENSHOT] ⚠️ Ошибка Selenium Wire: {e}, используем Firefox без прокси")
                    driver = webdriver.Firefox(options=options)
            else:
                print(f"[FIREFOX-SCREENSHOT] 🔧 Инициализация Firefox без прокси...")
                driver = webdriver.Firefox(options=options)
            
            driver.set_window_size(390, 844)
            
            # Переходим на страницу профиля
            url = f'https://www.instagram.com/{username}/'
            print(f"[FIREFOX-SCREENSHOT] 🌐 Переход на: {url}")
            driver.get(url)
            time.sleep(5)
            
            # 🔥 Агрессивное закрытие модальных окон
            self.close_instagram_modals_aggressive(driver)
            
            # Делаем скриншот
            print(f"[FIREFOX-SCREENSHOT] 📸 Сохранение скриншота: {screenshot_path}")
            driver.save_screenshot(screenshot_path)
            
            if os.path.exists(screenshot_path):
                size = os.path.getsize(screenshot_path)
                print(f"[FIREFOX-SCREENSHOT] ✅ Скриншот сохранен: {screenshot_path} ({size} байт)")
                return True
            else:
                print(f"[FIREFOX-SCREENSHOT] ❌ Скриншот не найден: {screenshot_path}")
                return False
                
        except Exception as e:
            print(f"[FIREFOX-SCREENSHOT] ❌ Ошибка при создании скриншота: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            if driver:
                try:
                    driver.quit()
                    print(f"[FIREFOX-SCREENSHOT] 🔒 Firefox драйвер закрыт")
                except:
                    pass
    
    def close_instagram_modals_aggressive(self, driver):
        """🔥 Агрессивное закрытие модальных окон Instagram"""
        print("[FIREFOX-SCREENSHOT] 🎯 Закрытие модальных окон...")
        
        # Метод 1: JavaScript принудительное удаление ВСЕХ элементов
        try:
            js_code = """
            // 🔥 УДАЛЯЕМ ВСЕ МОДАЛЬНЫЕ ОКНА И OVERLAY
            var allElements = document.querySelectorAll('*');
            for (var i = 0; i < allElements.length; i++) {
                var element = allElements[i];
                var className = element.className || '';
                var style = element.style || {};
                
                // Проверяем на модальные окна и overlay
                if (className.includes('x7r02ix') || 
                    className.includes('x1vjfegm') || 
                    className.includes('_abcm') ||
                    className.includes('modal') ||
                    className.includes('overlay') ||
                    className.includes('backdrop') ||
                    element.getAttribute('role') === 'dialog' ||
                    style.position === 'fixed' ||
                    style.zIndex > 1000) {
                    
                    element.style.display = 'none !important';
                    element.style.visibility = 'hidden !important';
                    element.style.opacity = '0 !important';
                    element.style.pointerEvents = 'none !important';
                    element.remove();
                }
            }
            
            // 🔥 УДАЛЯЕМ ВСЕ ЭЛЕМЕНТЫ С ВЫСОКИМ Z-INDEX
            var highZElements = document.querySelectorAll('[style*="z-index"]');
            for (var i = 0; i < highZElements.length; i++) {
                var zIndex = parseInt(highZElements[i].style.zIndex) || 0;
                if (zIndex > 100) {
                    highZElements[i].style.display = 'none !important';
                    highZElements[i].remove();
                }
            }
            
            // 🔥 УДАЛЯЕМ ВСЕ FIXED ПОЗИЦИОНИРОВАННЫЕ ЭЛЕМЕНТЫ
            var fixedElements = document.querySelectorAll('[style*="position: fixed"]');
            for (var i = 0; i < fixedElements.length; i++) {
                fixedElements[i].style.display = 'none !important';
                fixedElements[i].remove();
            }
            
            // 🔥 ВОССТАНАВЛИВАЕМ BODY И HTML
            document.body.classList.remove('modal-open', 'overflow-hidden');
            document.body.style.overflow = 'auto !important';
            document.body.style.position = 'static !important';
            document.body.style.background = 'transparent !important';
            document.documentElement.style.overflow = 'auto !important';
            document.documentElement.style.background = 'transparent !important';
            
            // 🔥 УДАЛЯЕМ ВСЕ OVERLAY КЛАССЫ
            var bodyClasses = document.body.className;
            var newClasses = bodyClasses.replace(/modal-open|overflow-hidden|backdrop|overlay/g, '');
            document.body.className = newClasses.trim();
            
            // 🔥 ПРИНУДИТЕЛЬНО ОЧИЩАЕМ СТИЛИ
            document.body.removeAttribute('style');
            document.documentElement.removeAttribute('style');
            
            // 🔥 ВОССТАНАВЛИВАЕМ СКРОЛЛИНГ
            document.body.style.overflow = 'auto';
            document.documentElement.style.overflow = 'auto';
            """
            driver.execute_script(js_code)
            print("[FIREFOX-SCREENSHOT] 🧹 JavaScript агрессивное удаление ВСЕХ модальных элементов")
            time.sleep(3)  # Больше времени для обработки
        except Exception as e:
            print(f"[FIREFOX-SCREENSHOT] ⚠️ JavaScript удаление не удалось: {e}")
        
        # Метод 2: Клик по кнопкам закрытия
        modal_selectors = [
            "button[aria-label='Close']",
            "svg[aria-label='Close']",
            "button[aria-label='Закрыть']",
            "svg[aria-label='Закрыть']",
            "//button[contains(text(), 'Not Now')]",
            "//button[contains(text(), 'Close')]",
            "//button[contains(text(), 'Закрыть')]",
            "//button[contains(text(), 'Не сейчас')]",
        ]
        
        for selector in modal_selectors:
            try:
                if selector.startswith('//'):
                    elements = driver.find_elements(By.XPATH, selector)
                else:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                for element in elements:
                    try:
                        if element.is_displayed():
                            element.click()
                            print(f"[FIREFOX-SCREENSHOT] ✅ Модальное окно закрыто: {selector}")
                            time.sleep(1)
                            return True
                    except:
                        continue
            except:
                continue
        
        print("[FIREFOX-SCREENSHOT] ✅ Модальные окна обработаны")
        return True
    
    async def hybrid_check(self, username: str, proxy: str = None, screenshot_path: str = None, headless: bool = True) -> dict:
        """🔥 Гибридная проверка: API с прокси + Firefox без прокси"""
        print(f"[HYBRID-PROXY] 🚀 Запуск гибридной проверки @{username}")
        print(f"[HYBRID-PROXY] 🔗 Прокси для API: {'Да' if proxy else 'Нет'}")
        print(f"[HYBRID-PROXY] 📸 Скриншот: {'Да' if screenshot_path else 'Нет'}")
        
        # Шаг 1: Проверка через API с прокси
        api_result = {"exists": None, "error": "not_checked"}
        if proxy:
            api_result = await self.check_via_api_with_proxy(username, proxy)
        else:
            print("[HYBRID-PROXY] ⚠️ Прокси не указан, пропускаем API проверку")
        
        # Шаг 2: Создание скриншота через Playwright (с автоматическим fallback на Firefox)
        screenshot_success = False
        if screenshot_path:
            screenshot_success = await self.take_screenshot_with_playwright(username, screenshot_path, headless, proxy)
        
        # Комбинируем результаты
        result = {
            "username": username,
            "exists": api_result.get("exists"),
            "checked_via": "hybrid_proxy_system",
            "api_method": api_result.get("method"),
            "api_status_code": api_result.get("status_code"),
            "screenshot_created": screenshot_success,
            "screenshot_path": screenshot_path if screenshot_success else None,
            "proxy_used": bool(proxy),
            "error": api_result.get("error")
        }
        
        print(f"[HYBRID-PROXY] 📊 Результат гибридной проверки:")
        print(f"[HYBRID-PROXY]   ✅ Профиль существует: {result['exists']}")
        print(f"[HYBRID-PROXY]   📸 Скриншот создан: {result['screenshot_created']}")
        print(f"[HYBRID-PROXY]   🔗 Прокси использован: {result['proxy_used']}")
        
        return result


async def check_account_with_hybrid_proxy(
    username: str,
    screenshot_path: Optional[str] = None,
    headless: bool = True,
    max_retries: int = 2,
    proxy: Optional[str] = None
) -> Dict[str, Any]:
    """
    🔥 ГИБРИДНАЯ ПРОВЕРКА С ПРОКСИ
    
    Использует:
    - API проверку через прокси с аутентификацией (для определения существования)
    - Firefox без прокси (для создания скриншотов)
    
    Args:
        username: Instagram username
        screenshot_path: Путь для сохранения скриншота
        headless: Запускать Firefox в headless режиме
        max_retries: Максимальное количество попыток
        proxy: Прокси в формате "http://user:pass@host:port" (для API)
    
    Returns:
        dict: Результат проверки
    """
    
    print(f"[HYBRID-PROXY-CHECK] 🚀 Запуск гибридной проверки с прокси для @{username}")
    print(f"[HYBRID-PROXY-CHECK] 🎯 Максимум попыток: {max_retries}")
    
    checker = InstagramHybridProxyChecker()
    
    for attempt in range(max_retries):
        print(f"[HYBRID-PROXY-CHECK] 🔄 Попытка {attempt + 1}/{max_retries}")
        
        try:
            result = await checker.hybrid_check(
                username=username,
                proxy=proxy,  # 🔥 Прокси используется ТОЛЬКО для API
                screenshot_path=screenshot_path,
                headless=headless
            )
            
            if result["exists"] is not None:
                print(f"[HYBRID-PROXY-CHECK] ✅ Проверка завершена успешно")
                return {
                    "username": username,
                    "exists": result["exists"],
                    "is_private": None,
                    "full_name": None,
                    "followers": None,
                    "following": None,
                    "posts": None,
                    "error": result.get("error"),
                    "checked_via": result["checked_via"],
                    "screenshot_path": result["screenshot_path"],
                    "proxy_used": result["proxy_used"],
                    "api_method": result.get("api_method"),
                    "api_status_code": result.get("api_status_code"),
                    "screenshot_created": result["screenshot_created"]
                }
            else:
                print(f"[HYBRID-PROXY-CHECK] ⚠️ Не удалось определить статус профиля @{username}")
                if attempt < max_retries - 1:
                    delay = random.uniform(5, 10)
                    print(f"[HYBRID-PROXY-CHECK] ⏳ Ожидание {delay:.1f}с перед следующей попыткой...")
                    await asyncio.sleep(delay)
                    continue
                
        except Exception as e:
            print(f"[HYBRID-PROXY-CHECK] ❌ Ошибка в попытке {attempt + 1}: {e}")
            import traceback
            traceback.print_exc()
            if attempt < max_retries - 1:
                delay = random.uniform(5, 10)
                print(f"[HYBRID-PROXY-CHECK] ⏳ Ожидание {delay:.1f}с перед следующей попыткой...")
                await asyncio.sleep(delay)
                continue
    
    # Все попытки не удались
    print(f"[HYBRID-PROXY-CHECK] ❌ Все попытки гибридной проверки не удались")
    return {
        "username": username,
        "exists": None,
        "is_private": None,
        "full_name": None,
        "followers": None,
        "following": None,
        "posts": None,
        "error": "Все попытки гибридной проверки с прокси не удались",
        "checked_via": "hybrid_proxy_system",
        "screenshot_path": None,
        "proxy_used": bool(proxy),
        "screenshot_created": False
    }

