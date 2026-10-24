"""
AI Sarthi — Database Models and Setup
SQLite with SQLAlchemy ORM, PostgreSQL-ready schema
"""
import os
import json
from datetime import datetime
from pathlib import Path
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime,
    Text, ForeignKey, UniqueConstraint, Index, Boolean
)
from sqlalchemy.orm import DeclarativeBase, relationship, Session
from sqlalchemy import event


BASE_DIR = Path(__file__).parent.parent.parent
DB_PATH = os.environ.get("SARTHI_DB_PATH", str(BASE_DIR / "data" / "ai_sarthi.db"))

# Ensure data dir exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False
)


class Base(DeclarativeBase):
    pass


class District(Base):
    __tablename__ = "districts"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    aliases_json = Column(Text, default="[]")   # JSON array
    division = Column(String(100))
    region = Column(String(100))
    population_lakh = Column(Float)
    vulnerability_index = Column(Float)

    financial_records = relationship("FinancialRecord", back_populates="district")

    @property
    def aliases(self) -> list:
        return json.loads(self.aliases_json or "[]")

    @aliases.setter
    def aliases(self, value: list):
        self.aliases_json = json.dumps(value)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "aliases": self.aliases,
            "division": self.division,
            "region": self.region,
            "population_lakh": self.population_lakh,
            "vulnerability_index": self.vulnerability_index,
        }


class FinancialRecord(Base):
    __tablename__ = "financial_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=True)
    financial_year = Column(String(10), nullable=False)   # e.g. "2022-23"
    programme = Column(String(200))
    scheme = Column(String(300))
    pool = Column(String(100))
    financial_stage = Column(String(50), nullable=False)  # PROPOSED_PIP, APPROVED_ROP, etc.
    amount_lakh = Column(Float, nullable=False)
    currency_unit = Column(String(20), default="lakh")
    scope = Column(String(50), default="DISTRICT")  # DISTRICT, STATE, DIVISION
    source_document = Column(Text)
    source_sheet = Column(String(200))
    source_row = Column(Integer)
    source_cell = Column(String(20))
    source_page = Column(Integer)
    fmr_code = Column(String(50))
    objective = Column(Text)
    verification_status = Column(String(30), default="UNVERIFIED")
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    district = relationship("District", back_populates="financial_records")

    __table_args__ = (
        Index("idx_district_year_stage", "district_id", "financial_year", "financial_stage"),
        Index("idx_financial_year", "financial_year"),
        Index("idx_stage", "financial_stage"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "district_id": self.district_id,
            "district_name": self.district.name if self.district else None,
            "financial_year": self.financial_year,
            "programme": self.programme,
            "scheme": self.scheme,
            "pool": self.pool,
            "financial_stage": self.financial_stage,
            "amount_lakh": self.amount_lakh,
            "currency_unit": self.currency_unit,
            "scope": self.scope,
            "source_document": self.source_document,
            "source_sheet": self.source_sheet,
            "source_row": self.source_row,
            "source_cell": self.source_cell,
            "fmr_code": self.fmr_code,
            "verification_status": self.verification_status,
            "notes": self.notes,
        }


class DataQualityLog(Base):
    __tablename__ = "data_quality_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    check_name = Column(String(100))
    district_name = Column(String(100))
    financial_year = Column(String(10))
    status = Column(String(10))  # PASS, WARN, FAIL, INFO
    message = Column(Text)
    source_document = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class RAGDocument(Base):
    __tablename__ = "rag_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_file = Column(String(500))
    page_or_sheet = Column(String(200))
    chunk_index = Column(Integer, default=0)
    text = Column(Text, nullable=False)
    document_type = Column(String(50))  # PDF, EXCEL, CSV
    year_range = Column(String(20))
    category = Column(String(100))
    embedding_id = Column(Integer)  # Reference to FAISS index position
    created_at = Column(DateTime, default=datetime.utcnow)


class SourceDocument(Base):
    __tablename__ = "source_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(500), unique=True)
    document_type = Column(String(50))
    year_range = Column(String(20))
    scope_description = Column(Text)
    pages_or_sheets = Column(Integer)
    ingested = Column(Boolean, default=False)
    ingested_at = Column(DateTime)
    notes = Column(Text)


def create_tables():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(engine)


def get_session() -> Session:
    """Return a new database session."""
    return Session(engine)


def get_db():
    """FastAPI dependency for database sessions."""
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()
