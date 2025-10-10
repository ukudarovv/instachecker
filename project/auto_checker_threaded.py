import threading
import asyncio
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import sessionmaker

try:
    from .utils.bot_proxy import ThreadSafeBotProxy
    from .utils.async_bot_wrapper import AsyncBotWrapper
    from .cron.auto_checker import check_pending_accounts
except ImportError:
    from utils.bot_proxy import ThreadSafeBotProxy
    from utils.async_bot_wrapper import AsyncBotWrapper
    from cron.auto_checker import check_pending_accounts

class AutoCheckerThread:
    """
    Фоновый планировщик в отдельном потоке с отдельным asyncio-лупом.
    """
    def __init__(
        self,
        main_loop: asyncio.AbstractEventLoop,
        bot_token: str,
        SessionLocal: sessionmaker,
        interval_seconds: int = 300,
        run_immediately: bool = True,
    ):
        self._main_loop = main_loop
        self._bot_token = bot_token
        self._SessionLocal = SessionLocal
        self._interval = interval_seconds
        self._run_immediately = run_immediately

        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._thread_entry, name="AutoChecker", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _thread_entry(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._runner(loop))
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()

    async def _runner(self, loop):
        # Создаем асинхронную обертку для бота
        async_bot = AsyncBotWrapper(self._bot_token)
        bot_proxy = ThreadSafeBotProxy(async_bot, self._main_loop)

        # 1) первый прогон (опционально)
        if self._run_immediately and not self._stop.is_set():
            try:
                print(f"[AUTO-CHECK/T] Initial run at {datetime.now()}")
                await check_pending_accounts(self._SessionLocal, bot=bot_proxy, max_accounts=999999, notify_admin=True)
                print(f"[AUTO-CHECK/T] Initial run completed at {datetime.now()}")
            except Exception as e:
                print(f"[AUTO-CHECK/T] Initial run failed: {e}")

        # 2) далее циклически
        while not self._stop.is_set():
            try:
                await asyncio.sleep(self._interval)
                if self._stop.is_set():
                    break
                print(f"[AUTO-CHECK/T] Tick at {datetime.now()}")
                await check_pending_accounts(self._SessionLocal, bot=bot_proxy, max_accounts=999999, notify_admin=True)
                print(f"[AUTO-CHECK/T] Tick completed at {datetime.now()}")
            except Exception as e:
                print(f"[AUTO-CHECK/T] Periodic run failed: {e}")
