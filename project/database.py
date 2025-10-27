"""Database configuration and models."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from typing import Optional

# Global base for all models
Base = declarative_base()


def get_engine(db_url: str, max_connections: int = None):
    """
    Create SQLAlchemy engine with adaptive connection pool for parallel processing.
    
    Args:
        db_url: Database connection URL
        max_connections: Maximum total connections (auto-calculated if None)
        
    Returns:
        SQLAlchemy engine instance
    """
    # Автоматический расчет максимальных соединений
    if max_connections is None:
        # Базовое количество: 50 соединений
        # + 20 соединений на каждые 10 пользователей
        # + 10 соединений на каждые 100 аккаунтов
        import os
        try:
            # Пытаемся получить количество пользователей из переменной окружения
            users_count = int(os.getenv('ESTIMATED_USERS', '10'))
            accounts_count = int(os.getenv('ESTIMATED_ACCOUNTS', '100'))
        except (ValueError, TypeError):
            users_count = 10
            accounts_count = 100
        
        # Формула: 50 + (пользователи/10)*20 + (аккаунты/100)*10
        max_connections = 50 + (users_count // 10) * 20 + (accounts_count // 100) * 10
        # Ограничиваем максимум 500 соединениями
        max_connections = min(max_connections, 500)
    
    # Распределяем между pool_size и max_overflow (70% основной пул, 30% overflow)
    pool_size = int(max_connections * 0.7)
    max_overflow = max_connections - pool_size
    
    print(f"[DATABASE] 🔧 Adaptive pool: {pool_size} + {max_overflow} = {max_connections} total connections")
    
    return create_engine(
        db_url,
        echo=False,
        future=True,
        # Адаптивный пул соединений
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=120,  # 2 минуты timeout
        pool_pre_ping=True,  # Проверяем соединение перед использованием
        pool_recycle=1800,  # Переиспользуем соединения каждые 30 минут
        # Дополнительные настройки для стабильности
        connect_args={
            "check_same_thread": False,  # Для SQLite
            "timeout": 30,  # Timeout для SQLite
        } if "sqlite" in db_url else {}
    )


def get_session_factory(engine):
    """
    Create session factory.
    
    Args:
        engine: SQLAlchemy engine
        
    Returns:
        Session factory
    """
    return sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True
    )


def init_db(engine) -> None:
    """
    Initialize database tables.
    
    Args:
        engine: SQLAlchemy engine
    """
    # Import models to ensure they are registered
    try:
        from .models import User, Account, APIKey
    except ImportError:
        # If relative import fails, try absolute import
        from models import User, Account, APIKey
    
    # Create all tables
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    """Initialize database when run as script."""
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Get database URL
    db_url = os.getenv("DB_URL", "sqlite:///bot.db")
    
    # Create engine and initialize database
    engine = get_engine(db_url)
    init_db(engine)
    
    print("DB ready")
