"""
Cerebro Chaos - Database Models & ORM Setup
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, String, Text, DateTime, Integer, 
    Float, Boolean, ForeignKey, JSON, Enum as SAEnum
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from config import settings

# For MVP, use SQLite if PostgreSQL is not available
DATABASE_URL = settings.DATABASE_URL
if not DATABASE_URL or "postgresql" in DATABASE_URL:
    try:
        engine = create_engine(DATABASE_URL, echo=settings.DEBUG)
    except Exception:
        DATABASE_URL = "sqlite:///./cerebro_chaos.db"
        engine = create_engine(DATABASE_URL, echo=settings.DEBUG)
else:
    engine = create_engine(DATABASE_URL, echo=settings.DEBUG)

# Fallback to SQLite for easy setup
try:
    engine.connect()
except Exception:
    DATABASE_URL = "sqlite:///./cerebro_chaos.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=settings.DEBUG)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class AnalysisStatus(str, enum.Enum):
    PENDING = "pending"
    CLONING = "cloning"
    ANALYZING = "analyzing"
    RISK_DETECTION = "risk_detection"
    COMPLETED = "completed"
    FAILED = "failed"


class RiskSeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ChaosStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ─── Database Models ───────────────────────────────────────────

class Repository(Base):
    __tablename__ = "repositories"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    url = Column(String, nullable=False)
    name = Column(String, nullable=False)
    owner = Column(String, nullable=True)
    branch = Column(String, default="main")
    local_path = Column(String, nullable=True)
    status = Column(String, default=AnalysisStatus.PENDING.value)
    language = Column(String, nullable=True)
    file_count = Column(Integer, default=0)
    total_lines = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    services = relationship("Service", back_populates="repository", cascade="all, delete-orphan")
    risks = relationship("Risk", back_populates="repository", cascade="all, delete-orphan")
    chaos_tests = relationship("ChaosTest", back_populates="repository", cascade="all, delete-orphan")


class Service(Base):
    __tablename__ = "services"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String, ForeignKey("repositories.id"), nullable=False)
    name = Column(String, nullable=False)
    service_type = Column(String, nullable=True)  # api, database, queue, cache, external
    file_path = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    dependencies = Column(JSON, default=list)  # list of service IDs it depends on
    endpoints = Column(JSON, default=list)
    config = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    repository = relationship("Repository", back_populates="services")


class Risk(Base):
    __tablename__ = "risks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String, ForeignKey("repositories.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String, default=RiskSeverity.MEDIUM.value)
    category = Column(String, nullable=True)  # retry, timeout, fallback, spof, cascading
    file_path = Column(String, nullable=True)
    line_start = Column(Integer, nullable=True)
    line_end = Column(Integer, nullable=True)
    code_snippet = Column(Text, nullable=True)
    failure_probability = Column(Float, default=0.0)
    impact_score = Column(Float, default=0.0)
    fix_suggestion = Column(Text, nullable=True)
    fix_code = Column(Text, nullable=True)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    repository = relationship("Repository", back_populates="risks")


class ChaosTest(Base):
    __tablename__ = "chaos_tests"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String, ForeignKey("repositories.id"), nullable=False)
    risk_id = Column(String, ForeignKey("risks.id"), nullable=True)
    test_type = Column(String, nullable=False)  # latency, failure, resource, network
    target_service = Column(String, nullable=True)
    status = Column(String, default=ChaosStatus.PENDING.value)
    config = Column(JSON, default=dict)
    
    # Results
    baseline_latency = Column(Float, nullable=True)
    chaos_latency = Column(Float, nullable=True)
    error_rate_before = Column(Float, nullable=True)
    error_rate_after = Column(Float, nullable=True)
    cascading_failures = Column(JSON, default=list)
    result_summary = Column(Text, nullable=True)
    failure_probability = Column(Float, nullable=True)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    repository = relationship("Repository", back_populates="chaos_tests")


# Create tables
Base.metadata.create_all(bind=engine)
