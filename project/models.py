"""Database models."""

from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey, func, UniqueConstraint, CheckConstraint, Text
from sqlalchemy.orm import relationship
try:
    from .database import Base
except ImportError:
    from database import Base


class User(Base):
    """User model."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, index=True)
    is_active = Column(Boolean, default=False, index=True)
    role = Column(String, default="user", nullable=False)  # 'user'|'admin'|'superuser'
    verify_mode = Column(String, default="api+instagram", nullable=False)  # 'api+instagram'|'api+proxy'|'api+proxy+instagram'|'instagram+proxy'|'instagram'|'proxy'
    auto_check_interval = Column(Integer, default=5, nullable=False)  # Индивидуальный интервал автопроверки в минутах (по умолчанию 5 минут)
    auto_check_enabled = Column(Boolean, default=True, nullable=False)  # Включена ли автопроверка для пользователя
    
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    proxies = relationship("Proxy", back_populates="user", cascade="all, delete-orphan")
    instagram_sessions = relationship("InstagramSession", back_populates="user", cascade="all, delete-orphan")


class Account(Base):
    """Account model."""
    
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    account = Column(String, index=True, nullable=False)
    from_date = Column(Date)
    from_date_time = Column(DateTime)  # Точное время добавления аккаунта
    period = Column(Integer)  # дни
    to_date = Column(Date)
    date_of_finish = Column(Date)
    done = Column(Boolean, default=False, index=True)
    
    user = relationship("User", back_populates="accounts")


class APIKey(Base):
    """API Key model."""
    
    __tablename__ = "api"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    key = Column(String, unique=True, nullable=False)
    qty_req = Column(Integer, default=0)
    ref_date = Column(DateTime, server_default=func.now())
    is_work = Column(Boolean, default=True, index=True)
    
    user = relationship("User", back_populates="api_keys")


class Proxy(Base):
    """Proxy model."""
    __tablename__ = "proxies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    scheme = Column(String, nullable=False)  # 'http' | 'https' | 'socks5'
    host = Column(String, nullable=False)  # "ip:port"
    username = Column(String)  # optional
    password = Column(String)  # optional
    is_active = Column(Boolean, default=True, index=True)
    priority = Column(Integer, default=5)  # 1 (лучше) .. 10
    used_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    fail_streak = Column(Integer, default=0)
    cooldown_until = Column(DateTime)  # если не None — прокси в кулдауне
    last_checked = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="proxies")

    __table_args__ = (
        UniqueConstraint("user_id", "scheme", "host", name="uq_proxy_user_scheme_host"),
        CheckConstraint("priority >= 1 AND priority <= 10", name="ck_proxy_priority"),
    )


class InstagramSession(Base):
    """Instagram Session model."""
    __tablename__ = "instagram_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    username = Column(String, nullable=False, index=True)   # IG username, под которым логинились
    password = Column(Text, nullable=True)                  # Encrypted IG password for re-login
    cookies = Column(Text, nullable=False)                  # JSON cookies (зашифр. или в плейнтекст, см. encryptor)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    last_used = Column(DateTime)
    expires_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="instagram_sessions")


class SystemSettings(Base):
    """System settings model."""
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String, unique=True, nullable=False, index=True)
    value = Column(String, nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ExpiryNotification(Base):
    """Expiry notification tracking model."""
    __tablename__ = "expiry_notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), index=True, nullable=False)
    notification_type = Column(String, nullable=False, index=True)  # 'expiring_soon' | 'expired'
    notification_date = Column(Date, nullable=False, index=True)  # Date when notification was sent
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "account_id", "notification_type", "notification_date", 
                        name="uq_expiry_notification"),
    )