import asyncio
import aiohttp
import json
from typing import Any, Dict, Optional


class AsyncBotWrapper:
    """
    Асинхронная обертка для нашего TelegramBot для совместимости с ThreadSafeBotProxy.
    """
    def __init__(self, bot_token: str):
        self.token = bot_token
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
    
    async def send_message(
        self, 
        chat_id: int, 
        text: str, 
        reply_markup: Optional[Dict] = None,
        parse_mode: str = "HTML"
    ) -> bool:
        """Send message to chat."""
        url = f"{self.api_url}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, timeout=10) as response:
                    result = await response.json()
                    if not result.get("ok", False):
                        print(f"Telegram API error: {result.get('description', 'Unknown error')}")
                        print(f"Error code: {result.get('error_code', 'N/A')}")
                        return False
                    return True
        except Exception as e:
            print(f"Error sending message: {e}")
            # Try to send without HTML parsing if that's the issue
            try:
                data.pop("parse_mode", None)
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=data, timeout=10) as response:
                        result = await response.json()
                        if not result.get("ok", False):
                            print(f"Telegram API error (retry): {result.get('description', 'Unknown error')}")
                            return False
                        return True
            except Exception as e2:
                print(f"Error sending message (retry): {e2}")
                return False
    
    async def send_photo(
        self, 
        chat_id: int, 
        photo_path: str, 
        caption: Optional[str] = None,
        parse_mode: str = "HTML"
    ) -> bool:
        """Send photo to chat."""
        url = f"{self.api_url}/sendPhoto"
        
        try:
            from aiohttp import FormData
            
            form_data = FormData()
            form_data.add_field('chat_id', str(chat_id))
            
            if caption:
                form_data.add_field('caption', caption)
                form_data.add_field('parse_mode', parse_mode)
            
            with open(photo_path, 'rb') as photo:
                form_data.add_field('photo', photo, filename='screenshot.png', content_type='image/png')
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, data=form_data, timeout=30) as response:
                        response.raise_for_status()
                        result = await response.json()
                        return result.get("ok", False)
        except Exception as e:
            print(f"Error sending photo: {e}")
            return False
    
    async def send_document(
        self, 
        chat_id: int, 
        document_path: str, 
        caption: Optional[str] = None,
        parse_mode: str = "HTML"
    ) -> bool:
        """Send document to chat."""
        url = f"{self.api_url}/sendDocument"
        
        try:
            from aiohttp import FormData
            
            form_data = FormData()
            form_data.add_field('chat_id', str(chat_id))
            
            if caption:
                form_data.add_field('caption', caption)
                form_data.add_field('parse_mode', parse_mode)
            
            with open(document_path, 'rb') as document:
                form_data.add_field('document', document, filename='document.pdf', content_type='application/pdf')
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, data=form_data, timeout=30) as response:
                        response.raise_for_status()
                        result = await response.json()
                        return result.get("ok", False)
        except Exception as e:
            print(f"Error sending document: {e}")
            return False
