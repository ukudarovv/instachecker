"""Final Instagram login via Playwright - based on successful test."""

import time
from typing import Optional, List, Dict, Any
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential

LOGIN_URL = "https://www.instagram.com/accounts/login/"


def _proxy_kwargs_from_url(proxy_url: Optional[str]):
    """Convert proxy URL to Playwright proxy kwargs."""
    if not proxy_url:
        return None
    from urllib.parse import urlparse
    u = urlparse(proxy_url)
    auth = {}
    if u.username and u.password:
        auth["username"] = u.username
        auth["password"] = u.password
    return {"server": f"{u.scheme}://{u.hostname}:{u.port}", **auth}


@retry(
    stop=stop_after_attempt(2), 
    wait=wait_exponential(multiplier=3, min=3, max=15),
    reraise=True
)
async def playwright_login_and_get_cookies(
    ig_username: str,
    ig_password: str,
    headless: bool,
    login_timeout_ms: int,
    twofa_timeout_ms: int,
    proxy_url: Optional[str] = None,
    user_agent: Optional[str] = None,
    bot=None,
    chat_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Final login via Chromium - based on successful test algorithm.
    Returns list of cookies (dicts).
    """
    proxy_kwargs = _proxy_kwargs_from_url(proxy_url)
    
    # Use custom user agent or default realistic one
    if not user_agent:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless, 
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=user_agent,
            proxy=proxy_kwargs
        )
        
        page = await context.new_page()
        try:
            print(f"🌐 Navigating to Instagram login page...")
            await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(5000)
            
            # Отправляем скриншот страницы логина
            if bot and chat_id:
                try:
                    screenshot_path = f"screenshots/ig_login_{ig_username}_{int(time.time())}.png"
                    await page.screenshot(path=screenshot_path)
                    await bot.send_photo(
                        chat_id,
                        screenshot_path,
                        f"🌐 Страница входа в Instagram для @{ig_username}"
                    )
                    import os
                    os.remove(screenshot_path)
                    print(f"📸 Login page screenshot sent to user")
                except Exception as e:
                    print(f"⚠️ Failed to send login screenshot: {e}")
            
            print(f"🔐 Logging in as @{ig_username}...")
            
            # Получаем все input элементы
            inputs = await page.query_selector_all("input")
            print(f"📋 Found {len(inputs)} input elements")
            
            if len(inputs) < 2:
                print(f"❌ Not enough input elements found")
                await page.screenshot(path="login_error.png")
                print(f"📸 Screenshot saved as login_error.png")
                raise Exception("Instagram login page not loaded correctly. Please use cookies import method.")
            
            # Первый input - username, второй - password
            username_input = inputs[0]
            password_input = inputs[1]
            
            print("✅ Found input fields")
            
            # Очищаем поля и вводим данные медленно
            await username_input.click()
            await page.wait_for_timeout(1000)
            await username_input.fill("")  # Очищаем
            await page.wait_for_timeout(500)
            await username_input.type(ig_username, delay=150)  # Медленный ввод
            await page.wait_for_timeout(1000)
            print("✅ Username entered")
            
            await password_input.click()
            await page.wait_for_timeout(1000)
            await password_input.fill("")  # Очищаем
            await page.wait_for_timeout(500)
            await password_input.type(ig_password, delay=150)  # Медленный ввод
            await page.wait_for_timeout(2000)
            print("✅ Password entered")
            
            print("🖱️ Clicking login button...")
            
            # Ищем кнопку входа
            submit_button = await page.query_selector('button[type="submit"]')
            if submit_button:
                await submit_button.click()
                print("✅ Login button clicked")
            else:
                print("❌ Login button not found")
                raise Exception("Login button not found. Please use cookies import method.")
            
            print("⏳ Waiting for response...")
            
            # Ждем с терпением и проверяем изменения
            for i in range(10):  # Ждем до 10 секунд
                await page.wait_for_timeout(1000)
                current_url = page.url
                print(f"  {i+1}/10: URL = {current_url}")
                
                # Если URL изменился, значит что-то происходит
                if "/accounts/login" not in current_url:
                    print("✅ URL changed - redirect happening")
                    break
            
            # Финальная проверка
            current_url = page.url
            print(f"🔍 Final URL: {current_url}")
            
            # Проверяем, не остались ли мы на странице входа
            if "/accounts/login" in current_url:
                print("❌ Login failed - still on login page")
                
                # Ищем сообщение об ошибке
                try:
                    error_element = await page.locator('[role="alert"]').first
                    if await error_element.count() > 0:
                        error_text = await error_element.text_content()
                        print(f"❌ Login failed: {error_text}")
                        raise Exception(f"Login failed: {error_text}")
                except:
                    pass
                raise Exception("Login failed - credentials may be incorrect")
            
            # Проверяем на 2FA
            if "two_factor" in current_url:
                print("🔐 Two-factor authentication required")
                
                # Отправляем скриншот страницы 2FA
                if bot and chat_id:
                    try:
                        screenshot_path = f"screenshots/ig_2fa_{ig_username}_{int(time.time())}.png"
                        await page.screenshot(path=screenshot_path)
                        await bot.send_photo(
                            chat_id,
                            screenshot_path,
                            f"🔐 Требуется двухфакторная аутентификация для @{ig_username}\n\n"
                            f"📱 Введите код из приложения аутентификатора или SMS:"
                        )
                        import os
                        os.remove(screenshot_path)
                        print(f"📸 2FA screenshot sent to user")
                    except Exception as e:
                        print(f"⚠️ Failed to send 2FA screenshot: {e}")
                
                # Ждем ввода кода от пользователя
                if bot and chat_id:
                    # Сохраняем состояние для ожидания 2FA кода
                    bot.fsm_states[chat_id] = {
                        "state": "waiting_2fa_code",
                        "ig_username": ig_username,
                        "page": page,
                        "context": context,
                        "browser": browser
                    }
                    
                    # Отправляем сообщение с инструкцией
                    await bot.send_message(
                        chat_id,
                        "⏳ Ожидаю ввода кода 2FA...\n\n"
                        "📱 Введите 6-значный код из приложения аутентификатора или SMS"
                    )
                    
                    # Возвращаем специальный результат для ожидания 2FA
                    return {"status": "waiting_2fa", "message": "2FA code required"}
                else:
                    raise Exception("2FA required - bot not available for interactive input")
            
            # Проверяем на вызов безопасности
            if "/challenge/" in current_url:
                print("🛡️ Instagram security challenge detected")
                print("❌ Cannot proceed with security challenge automatically")
                print("💡 Please login manually in browser first, then export cookies")
                raise Exception("Security challenge required - cannot automate")
            
            print("✅ Login successful!")
            
            # Убираем всплывающие окна
            try:
                not_now_buttons = await page.query_selector_all('button:has-text("Not Now")')
                for button in not_now_buttons:
                    try:
                        await button.click()
                        await page.wait_for_timeout(1000)
                        print("💾 Dismissed popup")
                    except:
                        pass
            except:
                pass
            
            # Ждем полной загрузки главной страницы
            print("🏠 Navigating to home page...")
            await page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(3000)
            
            # Получаем cookies
            print("🍪 Getting cookies...")
            cookies = await context.cookies()
            
            # Проверяем наличие sessionid
            has_sessionid = any(c.get('name') == 'sessionid' for c in cookies)
            print(f"🍪 Retrieved {len(cookies)} cookies, sessionid present: {has_sessionid}")
            
            if not has_sessionid:
                print("⚠️ Warning: sessionid cookie not found in response")
            
            return cookies
        finally:
            await context.close()
            await browser.close()
