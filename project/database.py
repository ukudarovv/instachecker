"""Database configuration and models."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from typing import Optional

# Global base for all models
Base = declarative_base()


def get_engine(db_url: str):
    """
    Create SQLAlchemy engine.
    
    Args:
        db_url: Database connection URL
        
    Returns:
        SQLAlchemy engine instance
    """
    return create_engine(
        db_url,
        echo=False,
        future=True
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
