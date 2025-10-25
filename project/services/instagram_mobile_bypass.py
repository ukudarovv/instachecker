"""Продвинутая система обхода Instagram с мобильной эмуляцией и человеческим поведением."""

import time
import random
import json
import os
from typing import Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import undetected_chromedriver as uc


class InstagramMobileBypass:
    """Продвинутый класс для обхода блокировок Instagram с фиксированным desktop устройством."""
    
    def __init__(self):
        self.driver = None
        self.wait = None
        
        # Фиксированное desktop устройство для стабильности
        self.desktop_device = {
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "width": 1920,
            "height": 1080,
            "pixelRatio": 1.0
        }
        
        # Конфигурации различных мобильных устройств (оставляем для совместимости)
        self.mobile_devices = {
            "iphone_12": {
                "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
                "width": 390,
                "height": 844,
                "pixelRatio": 3.0
            },
            "samsung_galaxy_s21": {
                "userAgent": "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
                "width": 360,
                "height": 800,
                "pixelRatio": 3.0
            },
            "iphone_x": {
                "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
                "width": 375,
                "height": 812,
                "pixelRatio": 3.0
            },
            "pixel_7": {
                "userAgent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
                "width": 393,
                "height": 851,
                "pixelRatio": 2.75
            }
        }
    
    def get_desktop_device(self) -> dict:
        """Получить фиксированное desktop устройство с обработкой ошибок."""
        try:
            print(f"[DEVICE] 🖥️ Используем фиксированное desktop устройство")
            return self.desktop_device
        except Exception as e:
            print(f"[DEVICE] ❌ Ошибка получения desktop устройства: {e}")
            # Fallback на базовое устройство
            return {
                "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "width": 1920,
                "height": 1080,
                "pixelRatio": 1.0
            }
    
    def validate_proxy_format(self, proxy: str) -> dict:
        """Валидация и парсинг прокси для исправления ERR_UNSUPPORTED_PROXIES"""
        print(f"[PROXY] 🔍 Валидация прокси: {proxy}")
        
        try:
            # Убираем пробелы
            proxy = proxy.strip()
            
            # Проверяем различные форматы прокси
            if proxy.startswith('http://'):
                return {"type": "http", "url": proxy, "valid": True}
            elif proxy.startswith('https://'):
                return {"type": "https", "url": proxy, "valid": True}
            elif proxy.startswith('socks5://'):
                return {"type": "socks5", "url": proxy, "valid": True}
            elif ':' in proxy and not proxy.startswith(('http', 'socks5')):
                # Формат ip:port или user:pass@ip:port
                if '@' in proxy:
                    # user:pass@ip:port
                    auth_part, server_part = proxy.split('@', 1)
                    if ':' in auth_part:
                        username, password = auth_part.split(':', 1)
                        return {
                            "type": "http", 
                            "url": f"http://{proxy}",
                            "auth": {"username": username, "password": password},
                            "valid": True
                        }
                else:
                    # ip:port
                    return {"type": "http", "url": f"http://{proxy}", "valid": True}
            
            return {"valid": False, "error": "Неверный формат прокси"}
            
        except Exception as e:
            return {"valid": False, "error": str(e)}

    def create_mobile_driver_fixed(self, headless: bool = True, proxy: Optional[str] = None) -> bool:
        """Исправленная версия создания драйвера с фиксированным desktop устройством"""
        
        # Получаем фиксированное desktop устройство
        device = self.get_desktop_device()
        device_name = "desktop_windows"
        
        print(f"[DRIVER] 🖥️ Создание драйвера с фиксированным desktop устройством: {device_name}")
        
        try:
            # Используем undetected_chromedriver для исправления ERR_UNSUPPORTED_PROXIES
            options = uc.ChromeOptions()
            
            # Desktop настройки (без мобильной эмуляции)
            options.add_argument(f"--user-agent={device['userAgent']}")
            options.add_argument(f"--window-size={device['width']},{device['height']}")
            
            # Базовые настройки для обхода блокировок
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-features=VizDisplayCompositor')
            options.add_argument('--disable-background-timer-throttling')
            options.add_argument('--disable-backgrounding-occluded-windows')
            options.add_argument('--disable-renderer-backgrounding')
            options.add_argument('--disable-ipc-flooding-protection')
            
            # Скрытие автоматизации (упрощенная версия)
            options.add_experimental_option('useAutomationExtension', False)
            
            # Дополнительные настройки
            options.add_argument('--disable-web-security')
            options.add_argument('--allow-running-insecure-content')
            options.add_argument('--disable-notifications')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-software-rasterizer')
            
            # Headless режим (лучше отключить для обхода защиты)
            if headless:
                options.add_argument('--headless=new')  # Новый формат headless
            else:
                # В видимом режиме настраиваем размер окна
                options.add_argument(f'--window-size={device["width"]},{device["height"]}')
            
            # НАСТРОЙКА ПРОКСИ - КЛЮЧЕВОЙ МОМЕНТ
            if proxy:
                proxy_info = self.validate_proxy_format(proxy)
                
                if proxy_info["valid"]:
                    print(f"[PROXY] ✅ Используем прокси: {proxy_info['url']}")
                    
                    # Правильная настройка прокси через аргумент
                    options.add_argument(f'--proxy-server={proxy_info["url"]}')
                    
                    # Дополнительные настройки для прокси
                    options.add_argument('--ignore-certificate-errors')
                    options.add_argument('--ignore-ssl-errors')
                    options.add_argument('--disable-web-security')
                    options.add_argument('--allow-running-insecure-content')
                    
                    # Для прокси с аутентификацией
                    if 'auth' in proxy_info:
                        auth = proxy_info['auth']
                        print(f"[PROXY] 🔐 Прокси с аутентификацией: {auth['username']}:***")
                else:
                    print(f"[PROXY] ❌ Ошибка прокси: {proxy_info['error']}")
                    print("[PROXY] 🚫 Продолжаем без прокси")
            else:
                print("[PROXY] ℹ️ Работаем без прокси")
            
            # Инициализация undetected_chromedriver
            print("[DRIVER] 🔧 Инициализация undetected_chromedriver...")
            
            self.driver = uc.Chrome(
                options=options,
                headless=headless,
                use_subprocess=False,  # Важно для стабильности
                version_main=None      # Автовыбор версии Chrome
            )
            
            # Дополнительные настройки после инициализации
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            
            # Установка таймаутов
            self.driver.set_page_load_timeout(45)
            self.driver.implicitly_wait(15)
            
            print("[DRIVER] ✅ Драйвер успешно создан")
            return True
            
        except Exception as e:
            print(f"[DRIVER] ❌ Ошибка создания драйвера: {e}")
            
            # Попытка создать драйвер без прокси
            if proxy:
                print("[DRIVER] 🔄 Попытка создать драйвер без прокси...")
                return self.create_mobile_driver_fixed(headless, None)
            
            return False

    def create_firefox_driver(self, headless: bool = True, proxy: Optional[str] = None) -> bool:
        """Создание Firefox драйвера с фиксированным desktop устройством."""
        
        # Получаем фиксированное desktop устройство
        device = self.get_desktop_device()
        device_name = "desktop_windows"
        
        # Firefox использует свой User-Agent
        device["userAgent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
        
        print(f"[FIREFOX] 🖥️ Создание Firefox драйвера с фиксированным desktop устройством: {device_name}")
        
        try:
            # Настройки Firefox
            options = FirefoxOptions()
            
            # Мобильная эмуляция через User-Agent
            mobile_user_agent = device["userAgent"]
            options.set_preference("general.useragent.override", mobile_user_agent)
            
            # Настройки для обхода блокировок
            options.set_preference("dom.webdriver.enabled", False)
            options.set_preference("useAutomationExtension", False)
            options.set_preference("dom.webnotifications.enabled", False)
            options.set_preference("media.volume_scale", "0.0")
            options.set_preference("dom.push.enabled", False)
            
            # Настройки для прокси
            if proxy:
                proxy_info = self.validate_proxy_format(proxy)
                
                if proxy_info["valid"]:
                    print(f"[FIREFOX] 🔗 Настройка прокси: {proxy_info['url']}")
                    
                    # Парсим прокси правильно
                    proxy_url = proxy_info["url"]
                    
                    # Убираем протокол
                    if "://" in proxy_url:
                        proxy_url = proxy_url.split("://")[1]
                    
                    # Парсим host:port (игнорируем username:password)
                    if '@' in proxy_url:
                        # Формат: username:password@host:port
                        auth_part, server_part = proxy_url.split('@', 1)
                        proxy_host, proxy_port = server_part.split(':', 1)
                    elif ':' in proxy_url:
                        # Формат: host:port
                        proxy_host, proxy_port = proxy_url.split(':', 1)
                    else:
                        print(f"[FIREFOX] ❌ Неправильный формат прокси: {proxy}")
                        proxy_host = None
                        proxy_port = None
                    
                    if proxy_host and proxy_port:
                        
                        # Настройка прокси в Firefox
                        options.set_preference("network.proxy.type", 1)  # Ручная настройка прокси
                        options.set_preference("network.proxy.http", proxy_host)
                        options.set_preference("network.proxy.http_port", int(proxy_port))
                        options.set_preference("network.proxy.ssl", proxy_host)
                        options.set_preference("network.proxy.ssl_port", int(proxy_port))
                        options.set_preference("network.proxy.ftp", proxy_host)
                        options.set_preference("network.proxy.ftp_port", int(proxy_port))
                        options.set_preference("network.proxy.socks", proxy_host)
                        options.set_preference("network.proxy.socks_port", int(proxy_port))
                        options.set_preference("network.proxy.socks_version", 5)
                        options.set_preference("network.proxy.socks_remote_dns", True)
                        
                        # Для прокси с аутентификацией
                        if 'auth' in proxy_info:
                            auth = proxy_info['auth']
                            print(f"[FIREFOX] 🔐 Прокси с аутентификацией: {auth['username']}:***")
                            # Firefox не поддерживает аутентификацию прокси напрямую
                            # Нужно использовать расширения или другие методы
                else:
                    print(f"[FIREFOX] ❌ Ошибка прокси: {proxy_info['error']}")
                    print("[FIREFOX] 🚫 Продолжаем без прокси")
            else:
                print("[FIREFOX] ℹ️ Работаем без прокси")
            
            # Headless режим с GPU поддержкой для скриншотов
            if headless:
                options.add_argument('--headless=new')  # Новый headless режим
                options.add_argument('--disable-gpu-sandbox')  # GPU поддержка
                options.add_argument('--enable-gpu')  # Включаем GPU
                options.add_argument('--no-sandbox')  # Отключаем sandbox для GPU
                options.add_argument('--disable-dev-shm-usage')  # Память для GPU
            
            # Размер окна для мобильной эмуляции
            options.add_argument(f'--width={device["width"]}')
            options.add_argument(f'--height={device["height"]}')
            
            # Дополнительные настройки
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            
            # Инициализация Firefox драйвера
            print("[FIREFOX] 🔧 Инициализация Firefox...")
            
            self.driver = webdriver.Firefox(options=options)
            
            # Установка размера окна для мобильной эмуляции
            self.driver.set_window_size(device["width"], device["height"])
            
            # Скрытие WebDriver признаков
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            
            # Установка таймаутов
            self.driver.set_page_load_timeout(45)
            self.driver.implicitly_wait(15)
            
            print("[FIREFOX] ✅ Firefox драйвер успешно создан")
            return True
            
        except Exception as e:
            print(f"[FIREFOX] ❌ Ошибка создания Firefox драйвера: {e}")
            import traceback
            traceback.print_exc()
            
            # Попытка создать драйвер без прокси (только если прокси был указан)
            if proxy:
                print("[FIREFOX] 🔄 Попытка создать Firefox драйвер без прокси...")
                return self.create_firefox_driver(headless, None)
            
            return False
    
    def create_firefox_driver_no_fallback(self, headless: bool = True, proxy: Optional[str] = None) -> bool:
        """Создание Firefox драйвера БЕЗ fallback с фиксированным desktop устройством."""
        
        # Получаем фиксированное desktop устройство
        device = self.get_desktop_device()
        device_name = "desktop_windows"
        
        # Firefox использует свой User-Agent
        device["userAgent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
        
        print(f"[FIREFOX-PROXY] 🖥️ Создание Firefox драйвера с фиксированным desktop устройством: {device_name}")
        
        try:
            # Настройки Firefox
            options = FirefoxOptions()
            
            # Мобильная эмуляция через User-Agent
            mobile_user_agent = device["userAgent"]
            options.set_preference("general.useragent.override", mobile_user_agent)
            
            # Настройки для обхода блокировок
            options.set_preference("dom.webdriver.enabled", False)
            options.set_preference("useAutomationExtension", False)
            options.set_preference("dom.webnotifications.enabled", False)
            options.set_preference("media.volume_scale", "0.0")
            options.set_preference("dom.push.enabled", False)
            
            # ОБЯЗАТЕЛЬНАЯ НАСТРОЙКА ПРОКСИ
            if not proxy:
                print("[FIREFOX-PROXY] ❌ Прокси не указан - это обязательно для этого режима")
                return False
            
            proxy_info = self.validate_proxy_format(proxy)
            
            if not proxy_info["valid"]:
                print(f"[FIREFOX-PROXY] ❌ Неправильный формат прокси: {proxy_info['error']}")
                return False
            
            print(f"[FIREFOX-PROXY] 🔗 Настройка прокси: {proxy_info['url']}")
            
            # Парсим прокси правильно
            proxy_url = proxy_info["url"]
            
            # Убираем протокол
            if "://" in proxy_url:
                proxy_url = proxy_url.split("://")[1]
            
            # Парсим host:port (извлекаем username:password если есть)
            if '@' in proxy_url:
                # Формат: username:password@host:port
                auth_part, server_part = proxy_url.split('@', 1)
                username, password = auth_part.split(':', 1)
                proxy_host, proxy_port = server_part.split(':', 1)
                print(f"[FIREFOX-PROXY] 🔐 Прокси с аутентификацией: {username}:***@{proxy_host}:{proxy_port}")
            elif ':' in proxy_url:
                # Формат: host:port
                proxy_host, proxy_port = proxy_url.split(':', 1)
                print(f"[FIREFOX-PROXY] ℹ️ Прокси без аутентификации: {proxy_host}:{proxy_port}")
            else:
                print(f"[FIREFOX-PROXY] ❌ Неправильный формат прокси: {proxy}")
                return False
            
            # Настройка прокси в Firefox
            options.set_preference("network.proxy.type", 1)  # Ручная настройка прокси
            options.set_preference("network.proxy.http", proxy_host)
            options.set_preference("network.proxy.http_port", int(proxy_port))
            options.set_preference("network.proxy.ssl", proxy_host)
            options.set_preference("network.proxy.ssl_port", int(proxy_port))
            options.set_preference("network.proxy.ftp", proxy_host)
            options.set_preference("network.proxy.ftp_port", int(proxy_port))
            options.set_preference("network.proxy.socks", proxy_host)
            options.set_preference("network.proxy.socks_port", int(proxy_port))
            options.set_preference("network.proxy.socks_version", 5)
            options.set_preference("network.proxy.socks_remote_dns", True)
            
            # Headless режим с GPU поддержкой для скриншотов
            if headless:
                options.add_argument('--headless=new')  # Новый headless режим
                options.add_argument('--disable-gpu-sandbox')  # GPU поддержка
                options.add_argument('--enable-gpu')  # Включаем GPU
                options.add_argument('--no-sandbox')  # Отключаем sandbox для GPU
                options.add_argument('--disable-dev-shm-usage')  # Память для GPU
            
            # Размер окна для мобильной эмуляции
            options.add_argument(f'--width={device["width"]}')
            options.add_argument(f'--height={device["height"]}')
            
            # Дополнительные настройки
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            
            # Инициализация Firefox драйвера
            print("[FIREFOX-PROXY] 🔧 Инициализация Firefox...")
            
            self.driver = webdriver.Firefox(options=options)
            
            # Установка размера окна для мобильной эмуляции
            self.driver.set_window_size(device["width"], device["height"])
            
            # Скрытие WebDriver признаков
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            
            # Установка таймаутов
            self.driver.set_page_load_timeout(45)
            self.driver.implicitly_wait(15)
            
            print("[FIREFOX-PROXY] ✅ Firefox драйвер с прокси успешно создан")
            return True
            
        except Exception as e:
            print(f"[FIREFOX-PROXY] ❌ Ошибка создания Firefox драйвера с прокси: {e}")
            import traceback
            traceback.print_exc()
            
            # НЕТ FALLBACK - возвращаем False
            print("[FIREFOX-PROXY] ⚠️ FALLBACK НЕ ИСПОЛЬЗУЕТСЯ")
            return False

    def create_mobile_driver(self, headless: bool = True, proxy: Optional[str] = None) -> bool:
        """Создание Chrome драйвера с фиксированным desktop устройством."""
        
        # Получаем фиксированное desktop устройство
        device = self.get_desktop_device()
        device_name = "desktop_windows"
        
        print(f"[MOBILE-BYPASS] 🖥️ Используем фиксированное desktop устройство: {device_name}")
        
        try:
            # Опции Chrome для desktop
            options = Options()
            
            # Desktop настройки (без мобильной эмуляции)
            options.add_argument(f"--user-agent={device['userAgent']}")
            options.add_argument(f"--window-size={device['width']},{device['height']}")
            
            # Базовые настройки
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-features=VizDisplayCompositor')
            options.add_argument('--disable-background-timer-throttling')
            options.add_argument('--disable-backgrounding-occluded-windows')
            options.add_argument('--disable-renderer-backgrounding')
            
            # Скрытие автоматизации (упрощенная версия)
            options.add_experimental_option('useAutomationExtension', False)
            
            # Дополнительные настройки для мобильного вида
            options.add_argument('--disable-web-security')
            options.add_argument('--allow-running-insecure-content')
            options.add_argument('--disable-notifications')
            options.add_argument('--disable-popup-blocking')
            
            # Headless режим с GPU поддержкой для скриншотов
            if headless:
                options.add_argument('--headless=new')  # Новый headless режим
                options.add_argument('--disable-gpu-sandbox')  # GPU поддержка
                options.add_argument('--enable-gpu')  # Включаем GPU
                options.add_argument('--no-sandbox')  # Отключаем sandbox для GPU
                options.add_argument('--disable-dev-shm-usage')  # Память для GPU
                options.add_argument('--disable-gpu')
            
            # Настройка прокси если указан
            if proxy:
                print(f"[MOBILE-BYPASS] 🔗 Используем прокси: {proxy}")
                
                # Парсим прокси для правильной настройки
                if proxy.startswith('http://') or proxy.startswith('https://'):
                    # HTTP/HTTPS прокси
                    options.add_argument(f'--proxy-server={proxy}')
                elif proxy.startswith('socks5://'):
                    # SOCKS5 прокси
                    options.add_argument(f'--proxy-server={proxy}')
                else:
                    # Если формат не указан, добавляем http://
                    options.add_argument(f'--proxy-server=http://{proxy}')
                
                # Дополнительные настройки для прокси
                options.add_argument('--proxy-bypass-list=<-loopback>')
                options.add_argument('--disable-proxy-certificate-handler')
                options.add_argument('--disable-web-security')
                options.add_argument('--allow-running-insecure-content')
                options.add_argument('--ignore-certificate-errors')
                options.add_argument('--ignore-ssl-errors')
                options.add_argument('--ignore-certificate-errors-spki-list')
                options.add_argument('--disable-extensions')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                
                # Настройки для аутентификации прокси
                if '@' in proxy:
                    # Прокси с аутентификацией
                    options.add_argument('--proxy-auth=*')
                    options.add_argument('--disable-background-timer-throttling')
                    options.add_argument('--disable-backgrounding-occluded-windows')
                    options.add_argument('--disable-renderer-backgrounding')
            
            # Инициализация драйвера
            self.driver = webdriver.Chrome(options=options)
            
            # Дополнительная настройка прокси через DevTools Protocol
            if proxy:
                try:
                    # Настройка прокси через DevTools Protocol
                    self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                        "userAgent": self.rotate_user_agent()
                    })
                    
                    # Настройка прокси
                    if '@' in proxy:
                        # Прокси с аутентификацией
                        proxy_parts = proxy.split('@')
                        if len(proxy_parts) == 2:
                            auth_part = proxy_parts[0].split('://')[-1]
                            if ':' in auth_part:
                                username, password = auth_part.split(':', 1)
                                proxy_url = proxy_parts[1]
                                
                                # Настройка аутентификации прокси
                                self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                                    "userAgent": self.rotate_user_agent()
                                })
                                
                                print(f"[MOBILE-BYPASS] 🔐 Настроена аутентификация прокси: {username}:***")
                    
                except Exception as e:
                    print(f"[MOBILE-BYPASS] ⚠️ Ошибка настройки прокси через DevTools: {e}")
            
            # Скрытие WebDriver признаков
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
            
            # Установка таймаутов
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            self.wait = WebDriverWait(self.driver, 15)
            
            print(f"[MOBILE-BYPASS] ✅ Драйвер создан с эмуляцией {device_name}")
            return True
            
        except Exception as e:
            print(f"[MOBILE-BYPASS] ❌ Ошибка создания драйвера: {e}")
            return False
    
    def human_like_behavior(self, duration: int = 5) -> None:
        """Эмуляция человеческого поведения."""
        print(f"[MOBILE-BYPASS] 🧠 Эмуляция человеческого поведения ({duration}с)...")
        
        start_time = time.time()
        
        try:
            body = self.driver.find_element(By.TAG_NAME, 'body')
        except:
            print("[MOBILE-BYPASS] ⚠️ Не удалось найти body элемент")
            return
        
        while time.time() - start_time < duration:
            try:
                # Случайный скроллинг
                scroll_height = self.driver.execute_script("return document.body.scrollHeight")
                if scroll_height > 0:
                    random_scroll = random.randint(100, min(500, scroll_height))
                    self.driver.execute_script(f"window.scrollTo(0, {random_scroll})")
                
                # Случайные клики
                if random.random() > 0.7:
                    try:
                        body.click()
                    except:
                        pass
                
                # Случайные тапы (для мобильного)
                if random.random() > 0.8:
                    self.driver.execute_script("""
                        var tapEvent = new TouchEvent('touchstart', {
                            touches: [new Touch({identifier: 1, target: document.body, clientX: 100, clientY: 200})],
                            bubbles: true
                        });
                        document.body.dispatchEvent(tapEvent);
                    """)
                
                # Случайная задержка
                time.sleep(random.uniform(0.5, 2))
                
            except Exception as e:
                print(f"[MOBILE-BYPASS] ⚠️ Ошибка в human_like_behavior: {e}")
                break
    
    def accept_cookies_if_present(self) -> bool:
        """Принятие куки если появляется окно."""
        try:
            # Различные селекторы для кнопок принятия куки
            cookie_selectors = [
                "button[data-testid='cookie-banner-accept']",
                "button:contains('Accept')",
                "button:contains('Allow')", 
                "button:contains('Принять')",
                "//button[contains(text(), 'Accept')]",
                "//button[contains(text(), 'Allow')]",
                "//button[contains(text(), 'Принять')]"
            ]
            
            for selector in cookie_selectors:
                try:
                    if selector.startswith('//'):
                        button = self.driver.find_element(By.XPATH, selector)
                    else:
                        button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if button.is_displayed():
                        button.click()
                        print("[MOBILE-BYPASS] 🍪 Куки приняты")
                        time.sleep(2)
                        return True
                except:
                    continue
                    
        except Exception as e:
            print(f"[MOBILE-BYPASS] ⚠️ Ошибка при принятии куки: {e}")
        
        return False
    
    def close_instagram_modal(self) -> bool:
        """Закрытие модального окна Instagram (приложение/логин)."""
        try:
            print("[MOBILE-BYPASS] 🔍 Поиск модального окна Instagram...")
            
            # Сначала проверим, есть ли модальное окно
            page_source = self.driver.page_source.lower()
            if 'смотрите профиль полностью' in page_source or 'view profile completely' in page_source:
                print("[MOBILE-BYPASS] 🎯 Обнаружено модальное окно Instagram")
            else:
                print("[MOBILE-BYPASS] ✅ Модальное окно не обнаружено")
                return True
            
            # Точные селекторы для закрытия модального окна Instagram
            modal_selectors = [
                # Точный селектор для кнопки закрытия Instagram
                "div[role='button'][tabindex='0'] svg[aria-label='Закрыть']",
                "div[role='button'] svg[aria-label='Закрыть']",
                "svg[aria-label='Закрыть']",
                "//svg[@aria-label='Закрыть']",
                "//div[@role='button']//svg[@aria-label='Закрыть']",
                # Родительские элементы кнопки закрытия
                "//div[@role='button' and .//svg[@aria-label='Закрыть']]",
                "//div[contains(@class, 'x1i10hfl') and .//svg[@aria-label='Закрыть']]",
                # Альтернативные селекторы
                "button[aria-label='Close']",
                "button[aria-label='Закрыть']",
                "//button[contains(@aria-label, 'Close')]",
                "//button[contains(@aria-label, 'Закрыть')]",
                # Кнопки "Открыть приложение"
                "//button[contains(text(), 'Открыть приложение')]",
                "//button[contains(text(), 'Open app')]",
                "//button[contains(text(), 'Открыть Instagram')]",
                # Кнопки регистрации/логина
                "//button[contains(text(), 'Зарегистрироваться')]",
                "//button[contains(text(), 'Register')]",
                "//a[contains(text(), 'Зарегистрироваться в Instagram')]",
                # Общие селекторы модальных окон
                "[role='dialog'] button",
                ".modal button",
                "[data-testid='modal'] button",
                # Более специфичные селекторы
                "div[role='dialog'] button",
                "div[class*='modal'] button",
                "div[class*='Modal'] button"
            ]
            
            modal_closed = False
            
            for selector in modal_selectors:
                try:
                    if selector.startswith('//'):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        try:
                            if element.is_displayed() and element.is_enabled():
                                # Проверяем, что это действительно кнопка закрытия
                                text = element.text.lower()
                                aria_label = element.get_attribute('aria-label') or ''
                                tag_name = element.tag_name.lower()
                                
                                # Специальная обработка для SVG элементов
                                if tag_name == 'svg' and 'закрыть' in aria_label.lower():
                                    # Для SVG элементов кликаем на родительский элемент
                                    try:
                                        parent = element.find_element(By.XPATH, "..")
                                        if parent.is_displayed() and parent.is_enabled():
                                            parent.click()
                                            print(f"[MOBILE-BYPASS] ✅ Модальное окно закрыто через SVG (селектор: {selector})")
                                            time.sleep(3)
                                            modal_closed = True
                                            break
                                    except:
                                        # Если не удалось кликнуть на родителя, пробуем сам SVG
                                        element.click()
                                        print(f"[MOBILE-BYPASS] ✅ Модальное окно закрыто через SVG напрямую (селектор: {selector})")
                                        time.sleep(3)
                                        modal_closed = True
                                        break
                                elif any(keyword in text or keyword in aria_label.lower() for keyword in 
                                      ['close', 'закрыть', '×', '✕', 'открыть приложение', 'open app', 'открыть instagram', 'зарегистрироваться', 'register']):
                                    element.click()
                                    print(f"[MOBILE-BYPASS] ✅ Модальное окно закрыто (селектор: {selector})")
                                    time.sleep(3)
                                    modal_closed = True
                                    break
                        except Exception as e:
                            continue
                    
                    if modal_closed:
                        break
                            
                except Exception as e:
                    continue
            
            # АГРЕССИВНЫЕ МЕТОДЫ ЗАКРЫТИЯ МОДАЛЬНОГО ОКНА
            if not modal_closed:
                print("[MOBILE-BYPASS] 🔥 АГРЕССИВНОЕ ЗАКРЫТИЕ МОДАЛЬНОГО ОКНА...")
                
                # Метод 1: JavaScript принудительное удаление всех модальных окон
                try:
                    js_code = """
                    // Удаляем все модальные окна принудительно
                    var modals = document.querySelectorAll('[class*="x7r02ix"], [class*="x1vjfegm"], [class*="_abcm"], [class*="x1i10hfl"]');
                    for (var i = 0; i < modals.length; i++) {
                        modals[i].style.display = 'none !important';
                        modals[i].style.visibility = 'hidden !important';
                        modals[i].style.opacity = '0 !important';
                        modals[i].remove();
                    }
                    
                    // Удаляем все overlay элементы
                    var overlays = document.querySelectorAll('[class*="x7r02ix"]');
                    for (var i = 0; i < overlays.length; i++) {
                        overlays[i].style.display = 'none !important';
                        overlays[i].remove();
                    }
                    
                    // Удаляем body классы модального окна
                    document.body.classList.remove('modal-open');
                    document.body.style.overflow = 'auto !important';
                    document.body.style.position = 'static !important';
                    
                    // Удаляем все элементы с классом модального окна
                    var allElements = document.querySelectorAll('*');
                    for (var i = 0; i < allElements.length; i++) {
                        if (allElements[i].className && allElements[i].className.includes('x7r02ix')) {
                            allElements[i].style.display = 'none !important';
                            allElements[i].remove();
                        }
                    }
                    """
                    self.driver.execute_script(js_code)
                    print("[MOBILE-BYPASS] 🧹 JavaScript принудительное удаление модальных окон")
                    time.sleep(2)
                    modal_closed = True
                except Exception as js_error:
                    print(f"[MOBILE-BYPASS] ⚠️ JavaScript удаление не удалось: {js_error}")
                
                # Метод 2: Множественные Escape
                if not modal_closed:
                    try:
                        from selenium.webdriver.common.keys import Keys
                        for _ in range(5):
                            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                            time.sleep(0.5)
                        print("[MOBILE-BYPASS] ⌨️ Множественные Escape")
                        modal_closed = True
                    except Exception as escape_error:
                        print(f"[MOBILE-BYPASS] ⚠️ Множественные Escape не сработали: {escape_error}")
                
                # Метод 3: Клики в разные углы экрана
                if not modal_closed:
                    try:
                        from selenium.webdriver.common.action_chains import ActionChains
                        actions = ActionChains(self.driver)
                        
                        # Клики в углы экрана
                        corners = [(10, 10), (10, 100), (100, 10), (100, 100)]
                        for x, y in corners:
                            try:
                                actions.move_by_offset(x, y).click().perform()
                                time.sleep(0.5)
                            except:
                                continue
                        print("[MOBILE-BYPASS] 🖱️ Клики в углы экрана")
                        modal_closed = True
                    except Exception as corner_error:
                        print(f"[MOBILE-BYPASS] ⚠️ Клики в углы не удались: {corner_error}")
                
                # Метод 4: Принудительное обновление страницы
                if not modal_closed:
                    try:
                        self.driver.refresh()
                        print("[MOBILE-BYPASS] 🔄 Принудительное обновление страницы")
                        time.sleep(3)
                        modal_closed = True
                    except Exception as refresh_error:
                        print(f"[MOBILE-BYPASS] ⚠️ Обновление страницы не удалось: {refresh_error}")
                
                # Метод 5: Переход на другую страницу и обратно
                if not modal_closed:
                    try:
                        current_url = self.driver.current_url
                        self.driver.get("https://www.instagram.com/")
                        time.sleep(2)
                        self.driver.get(current_url)
                        print("[MOBILE-BYPASS] 🔄 Переход на главную и обратно")
                        time.sleep(3)
                        modal_closed = True
                    except Exception as nav_error:
                        print(f"[MOBILE-BYPASS] ⚠️ Навигация не удалась: {nav_error}")
            
            # Проверяем результат
            if modal_closed:
                # Дополнительная проверка - есть ли еще модальное окно
                time.sleep(1)
                page_source_after = self.driver.page_source.lower()
                if 'смотрите профиль полностью' not in page_source_after and 'view profile completely' not in page_source_after:
                    print("[MOBILE-BYPASS] ✅ Модальное окно успешно закрыто")
                    return True
                else:
                    print("[MOBILE-BYPASS] ⚠️ Модальное окно все еще присутствует")
                    return False
            else:
                print("[MOBILE-BYPASS] ❌ Не удалось закрыть модальное окно")
                return False
                    
        except Exception as e:
            print(f"[MOBILE-BYPASS] ❌ Ошибка при закрытии модального окна: {e}")
            return False
    
    def prepare_session(self) -> bool:
        """Подготовка сессии перед проверкой профиля."""
        print("[MOBILE-BYPASS] 🔧 Подготовка сессии...")
        
        try:
            # Посещение главной страницы Instagram
            self.driver.get('https://www.instagram.com/')
            time.sleep(random.uniform(3, 6))
            
            # Принятие куки
            self.accept_cookies_if_present()
            
            # Эмуляция человеческого поведения
            self.human_like_behavior(random.randint(5, 8))
            
            # Проверка что мы не перенаправлены на логин
            current_url = self.driver.current_url
            if 'accounts/login' in current_url:
                print("[MOBILE-BYPASS] ⚠️ Обнаружено перенаправление на логин, пытаемся обойти...")
                # Пробуем вернуться назад
                self.driver.back()
                time.sleep(2)
            
            print("[MOBILE-BYPASS] ✅ Сессия подготовлена успешно")
            return True
            
        except Exception as e:
            print(f"[MOBILE-BYPASS] ❌ Ошибка подготовки сессии: {e}")
            return False
    
    def handle_login_redirect(self, username: str) -> Optional[bool]:
        """Обработка перенаправления на логин."""
        print("[MOBILE-BYPASS] 🔄 Обработка перенаправления на логин...")
        
        try:
            # Пробуем альтернативные URL
            alternative_urls = [
                f'https://www.instagram.com/{username}/?__a=1',
                f'https://www.instagram.com/{username}/channel/',
                f'https://www.instagram.com/explore/people/?search={username}'
            ]
            
            for url in alternative_urls:
                try:
                    print(f"[MOBILE-BYPASS] 🔗 Пробуем альтернативный URL: {url}")
                    self.driver.get(url)
                    time.sleep(3)
                    
                    current_url = self.driver.current_url
                    if 'accounts/login' not in current_url:
                        page_source = self.driver.page_source.lower()
                        if username.lower() in page_source:
                            print(f"[MOBILE-BYPASS] ✅ Профиль найден через альтернативный URL")
                            return True
                        elif '404' in page_source:
                            print(f"[MOBILE-BYPASS] ❌ Профиль не найден (404)")
                            return False
                            
                except Exception as e:
                    print(f"[MOBILE-BYPASS] ⚠️ Ошибка с альтернативным URL {url}: {e}")
                    continue
            
            # Если все альтернативные URL ведут на логин, вероятно профиль существует но требуется авторизация
            print("[MOBILE-BYPASS] ✅ Все запросы перенаправляются на логин - профиль вероятно существует")
            return True
            
        except Exception as e:
            print(f"[MOBILE-BYPASS] ❌ Ошибка обработки редиректа: {e}")
            return None
    
    def additional_checks(self, username: str) -> bool:
        """Дополнительные проверки существования профиля."""
        try:
            print("[MOBILE-BYPASS] 🔍 Дополнительные проверки...")
            
            # Проверка мета-тегов
            meta_tags = self.driver.find_elements(By.TAG_NAME, 'meta')
            for meta in meta_tags:
                content = meta.get_attribute('content') or ''
                if username.lower() in content.lower():
                    print("[MOBILE-BYPASS] ✅ Найден в мета-тегах")
                    return True
            
            # Проверка JSON-LD данных
            scripts = self.driver.find_elements(By.TAG_NAME, 'script')
            for script in scripts:
                script_type = script.get_attribute('type') or ''
                if 'application/ld+json' in script_type:
                    script_content = script.get_attribute('innerHTML') or ''
                    if username.lower() in script_content.lower():
                        print("[MOBILE-BYPASS] ✅ Найден в JSON-LD данных")
                        return True
            
            # Проверка заголовка страницы
            title = self.driver.title.lower()
            if username.lower() in title and 'instagram' in title:
                print("[MOBILE-BYPASS] ✅ Найден в заголовке страницы")
                return True
            
            print("[MOBILE-BYPASS] ❌ Профиль не найден после дополнительных проверок")
            return False
            
        except Exception as e:
            print(f"[MOBILE-BYPASS] ❌ Ошибка дополнительных проверок: {e}")
            return False
    
    def check_profile_existence(self, username: str, screenshot_path: Optional[str] = None, proxy: Optional[str] = None) -> Dict[str, Any]:
        """Основная функция проверки существования профиля."""
        print(f"[MOBILE-BYPASS] 🔍 Проверка профиля: @{username}")
        
        # Используем Firefox драйвер для лучшей работы с прокси
        if not self.create_firefox_driver(proxy=proxy):
            return {
                "exists": None,
                "screenshot_path": None,
                "error": "driver_creation_failed"
            }
        
        try:
            # Подготовка сессии
            if not self.prepare_session():
                return None
            
            # Посещение профиля
            profile_url = f'https://www.instagram.com/{username}/'
            print(f"[MOBILE-BYPASS] 🌐 Переход на: {profile_url}")
            
            self.driver.get(profile_url)
            time.sleep(random.uniform(4, 7))
            
            # Эмуляция поведения на странице профиля
            self.human_like_behavior(random.randint(3, 5))
            
            # Закрытие модального окна если появилось
            self.close_instagram_modal()
            
            # Дополнительная задержка после закрытия модального окна
            time.sleep(random.uniform(2, 4))
            
            # Создание скриншота если нужно
            if screenshot_path:
                try:
                    self.driver.save_screenshot(screenshot_path)
                    print(f"[MOBILE-BYPASS] 📸 Скриншот сохранен: {screenshot_path}")
                except Exception as e:
                    print(f"[MOBILE-BYPASS] ⚠️ Ошибка создания скриншота: {e}")
            
            # Анализ результата
            current_url = self.driver.current_url
            page_source = self.driver.page_source.lower()
            
            print(f"[MOBILE-BYPASS] 🔗 Текущий URL: {current_url}")
            
            # Проверка различных сценариев
            if 'accounts/login' in current_url:
                print("[MOBILE-BYPASS] 🔄 Перенаправление на страницу логина")
                login_result = self.handle_login_redirect(username)
                return {
                    "exists": login_result,
                    "screenshot_path": screenshot_path if screenshot_path and os.path.exists(screenshot_path) else None,
                    "error": None if login_result is not None else "login_redirect_failed"
                }
            
            elif '404' in page_source or 'not found' in page_source:
                print("[MOBILE-BYPASS] ❌ Профиль не найден (404)")
                return {
                    "exists": False,
                    "screenshot_path": screenshot_path if screenshot_path and os.path.exists(screenshot_path) else None,
                    "error": None
                }
            
            elif username.lower() in page_source:
                print("[MOBILE-BYPASS] ✅ Профиль существует")
                return {
                    "exists": True,
                    "screenshot_path": screenshot_path if screenshot_path and os.path.exists(screenshot_path) else None,
                    "error": None
                }
            
            else:
                # Дополнительные проверки
                additional_result = self.additional_checks(username)
                return {
                    "exists": additional_result,
                    "screenshot_path": screenshot_path if screenshot_path and os.path.exists(screenshot_path) else None,
                    "error": None if additional_result is not None else "additional_checks_failed"
                }
                
        except TimeoutException:
            print("[MOBILE-BYPASS] ⏰ Таймаут при загрузке страницы")
            return {
                "exists": None,
                "screenshot_path": screenshot_path if screenshot_path and os.path.exists(screenshot_path) else None,
                "error": "timeout"
            }
        except Exception as e:
            print(f"[MOBILE-BYPASS] ❌ Общая ошибка при проверке: {e}")
            return {
                "exists": None,
                "screenshot_path": screenshot_path if screenshot_path and os.path.exists(screenshot_path) else None,
                "error": str(e)
            }
        finally:
            if self.driver:
                self.driver.quit()
    
    def rotate_user_agent(self) -> str:
        """Ротация User-Agent для каждого запроса."""
        user_agents = [
            # iOS devices
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPad; CPU OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
            # Android devices
            "Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        ]
        return random.choice(user_agents)


async def check_account_with_mobile_bypass(
    username: str,
    screenshot_path: Optional[str] = None,
    headless: bool = True,
    max_retries: int = 2,
    proxy: Optional[str] = None
) -> Dict[str, Any]:
    """
    Проверка аккаунта Instagram с использованием продвинутой мобильной эмуляции.
    
    Args:
        username: Имя пользователя Instagram
        screenshot_path: Путь для сохранения скриншота
        headless: Запуск в headless режиме
        max_retries: Максимальное количество попыток
        proxy: Прокси для обхода блокировок (опционально)
        
    Returns:
        Dict с результатом проверки
    """
    print(f"[MOBILE-BYPASS] 🚀 Запуск мобильной проверки @{username}")
    print(f"[MOBILE-BYPASS] 🎯 Максимум попыток: {max_retries}")
    
    bypass = InstagramMobileBypass()
    
    for attempt in range(max_retries):
        print(f"[MOBILE-BYPASS] 🔄 Попытка {attempt + 1}/{max_retries}")
        
        try:
            result = bypass.check_profile_existence(username, screenshot_path, proxy)
            
            if result.get("exists") is True:
                print(f"[MOBILE-BYPASS] ✅ Профиль @{username} НАЙДЕН через мобильную эмуляцию")
                return {
                    "username": username,
                    "exists": True,
                    "is_private": None,
                    "full_name": None,
                    "followers": None,
                    "following": None,
                    "posts": None,
                    "error": result.get("error"),
                    "checked_via": "mobile_bypass_emulation",
                    "screenshot_path": result.get("screenshot_path"),
                    "mobile_device_used": "random"
                }
            elif result.get("exists") is False:
                print(f"[MOBILE-BYPASS] ❌ Профиль @{username} НЕ НАЙДЕН")
                return {
                    "username": username,
                    "exists": False,
                    "is_private": None,
                    "full_name": None,
                    "followers": None,
                    "following": None,
                    "posts": None,
                    "error": result.get("error"),
                    "checked_via": "mobile_bypass_emulation",
                    "screenshot_path": result.get("screenshot_path")
                }
            else:
                print(f"[MOBILE-BYPASS] ⚠️ Не удалось определить статус профиля @{username}")
                if attempt < max_retries - 1:
                    delay = random.uniform(5, 10)
                    print(f"[MOBILE-BYPASS] ⏳ Ожидание {delay:.1f}с перед следующей попыткой...")
                    time.sleep(delay)
                    continue
                
        except Exception as e:
            print(f"[MOBILE-BYPASS] ❌ Ошибка в попытке {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                delay = random.uniform(5, 10)
                print(f"[MOBILE-BYPASS] ⏳ Ожидание {delay:.1f}с перед следующей попыткой...")
                time.sleep(delay)
                continue
    
    # Все попытки не удались
    return {
        "username": username,
        "exists": None,
        "is_private": None,
        "full_name": None,
        "followers": None,
        "following": None,
        "posts": None,
        "error": "Все попытки мобильной эмуляции не удались",
        "checked_via": "mobile_bypass_emulation",
        "screenshot_path": None
    }
