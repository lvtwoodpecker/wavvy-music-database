from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import Settings

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
