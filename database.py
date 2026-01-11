"""
Database models and session management for time tracking
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, String, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

Base = declarative_base()

# Database file path
DB_PATH = os.environ.get("DB_PATH", "time_tracking.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class CheckIn(Base):
    """Model for storing check-in records"""
    __tablename__ = "checkins"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    status = Column(String, nullable=False)  # working, break, away
    timestamp = Column(DateTime, default=datetime.now, nullable=False, index=True)
    
    def __repr__(self):
        return f"<CheckIn(user_id={self.user_id}, status={self.status}, timestamp={self.timestamp})>"


class DailyReport(Base):
    """Model for storing daily report summaries"""
    __tablename__ = "daily_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, index=True)
    user_id = Column(String, index=True, nullable=False)
    total_hours = Column(Integer, default=0)
    working_count = Column(Integer, default=0)
    break_count = Column(Integer, default=0)
    away_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<DailyReport(date={self.date}, user_id={self.user_id}, total_hours={self.total_hours})>"


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def get_db_session() -> Session:
    """Get database session"""
    return SessionLocal()

