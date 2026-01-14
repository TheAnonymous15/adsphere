"""
Database configuration for AdSphere Python System
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import os

# Database configuration - use python_shared/database/adsphere.db
DATABASE_PATH = Path(__file__).parent / "python_shared" / "database"
DATABASE_PATH.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DATABASE_PATH}/adsphere.db"

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False  # Set to True for SQL logging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database with all models"""
    from models import Base
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")


def drop_all_tables():
    """Drop all tables (for development only)"""
    from models import Base
    Base.metadata.drop_all(bind=engine)
    print("⚠️ All tables dropped")


if __name__ == "__main__":
    init_db()

