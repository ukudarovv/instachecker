import asyncio
from typing import Any

class ThreadSafeBotProxy:
    """
    Обёртка над ботом для вызовов из другого потока/ивент-лупа.
    Любой async-метод (send_message, send_photo, ...) переносится на основной луп.
    """
    def __init__(self, bot, main_loop: asyncio.AbstractEventLoop):
        self._bot = bot
        self._loop = main_loop

    async def _call(self, coro):
        # run_coroutine_threadsafe -> concurrent.futures.Future
        fut = asyncio.run_coroutine_threadsafe(coro, self._loop)
        # делаем await в ТЕКУЩЕМ (потоковом) лупе
        return await asyncio.wrap_future(fut)

    async def send_message(self, *args: Any, **kwargs: Any):
        return await self._call(self._bot.send_message(*args, **kwargs))

    async def send_photo(self, *args: Any, **kwargs: Any):
        return await self._call(self._bot.send_photo(*args, **kwargs))

    async def send_document(self, *args: Any, **kwargs: Any):
        return await self._call(self._bot.send_document(*args, **kwargs))

    # при необходимости добавляйте другие методы бота таким же образом
