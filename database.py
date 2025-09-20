from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
import sqlite3
from config import config

engine = create_engine(config.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class URLMapping(Base):
    __tablename__ = "url_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    shortcode = Column(String(50), unique=True, index=True, nullable=False)
    original_url = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=False)
    click_count = Column(Integer, default=0)

class ClickLog(Base):
    __tablename__ = "click_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    shortcode = Column(String(50), index=True, nullable=False)
    clicked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    referrer = Column(String(500))
    user_agent = Column(String(500))
    ip_address = Column(String(45))
    location = Column(String(100))  # Coarse-grained geographical location

def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()