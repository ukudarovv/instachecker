"""Configuration management."""

import os
from typing import List, Optional
from dotenv import load_dotenv


class Settings:
    """Application settings."""
    
    def __init__(self):
        """Initialize settings from environment variables."""
        # Load environment variables
        load_dotenv()
        
        self.bot_token: str = os.getenv("BOT_TOKEN", "")
        self.admin_ids: List[int] = self._parse_admin_ids(os.getenv("ADMIN_IDS", ""))
        self.db_url: str = os.getenv("DB_URL", "sqlite:///bot.db")
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.tz: str = os.getenv("TZ", "Asia/Aqtobe")
        
        # Screenshot settings
        self.screenshot_headless: bool = os.getenv("SCREENSHOT_HEADLESS", "true").lower() == "true"
        self.screenshot_timeout_ms: int = int(os.getenv("SCREENSHOT_TIMEOUT", "15000"))
        self.screenshot_wait_selector: str = os.getenv("SCREENSHOT_WAIT_SELECTOR", "header")
        self.screenshot_fallback_selector: str = os.getenv("SCREENSHOT_FALLBACK_SELECTOR", "main")
        self.screenshot_dark_theme: bool = os.getenv("SCREENSHOT_DARK_THEME", "true").lower() == "true"

        # Encryption
        self.encryption_key: str = os.getenv("ENCRYPTION_KEY", "")

        # Instagram settings
        self.ig_headless: bool = os.getenv("IG_HEADLESS", "true").lower() == "true"
        self.ig_login_timeout_ms: int = int(os.getenv("IG_LOGIN_TIMEOUT", "25000"))
        self.ig_2fa_timeout_ms: int = int(os.getenv("IG_2FA_TIMEOUT", "300000"))
        self.ig_screenshot_header_selector: str = os.getenv("IG_SCREENSHOT_HEADER_SELECTOR", "header")
        self.ig_screenshot_fallback_selector: str = os.getenv("IG_SCREENSHOT_FALLBACK_SELECTOR", "main")
        self.ig_mini_app_url: str = os.getenv("IG_MINI_APP_URL", "")  # URL for Telegram Mini App

        # RapidAPI settings
        self.rapidapi_host: str = os.getenv("RAPIDAPI_HOST", "instagram210.p.rapidapi.com")
        self.rapidapi_url: str = os.getenv("RAPIDAPI_URL", "https://instagram210.p.rapidapi.com/ig/user/profile")
        self.api_daily_limit: int = int(os.getenv("API_DAILY_LIMIT", "950"))
        self.rapidapi_timeout_seconds: int = int(os.getenv("RAPIDAPI_TIMEOUT_SECONDS", "10"))
    
    def _parse_admin_ids(self, admin_ids_str: str) -> List[int]:
        """Parse admin IDs from comma-separated string."""
        if not admin_ids_str:
            return []
        
        try:
            return [int(id_str.strip()) for id_str in admin_ids_str.split(",") if id_str.strip()]
        except ValueError:
            return []


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get application settings (singleton pattern).
    
    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
