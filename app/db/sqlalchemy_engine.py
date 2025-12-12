from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import Settings

""" 
SQLAlchemy engine and session setup for the application.
Provides:
- engine: SQLAlchemy engine instance.
- SessionLocal: Session factory for creating DB sessions.
- Base: Declarative base class for ORM models.

Why? 
Centralizes DB connection setup and ORM base for consistent use across the app.
Important for managing DB connections and sessions properly and avoiding leaks/SQL injection.
"""

settings = Settings()

engine = create_engine(
    settings.DATABASE_URL,
    future=True,           # future allows use of 2.0 style
    echo=False             # set True if you want SQL logging
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False, # prevent automatic commits
    autoflush=False, # prevent automatic flushes to DB
)

Base = declarative_base()
