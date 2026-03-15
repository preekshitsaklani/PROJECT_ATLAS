import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, Text
from app.db.base_class import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)


class RiskScore(Base):
    __tablename__ = "risk_scores"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_id = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    level = Column(String, nullable=False)
    factors = Column(Text, default="{}")
    timestamp = Column(DateTime, default=utcnow)


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(Text)
    severity = Column(String, nullable=False)
    category = Column(String)
    source = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)


class Port(Base):
    __tablename__ = "ports"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    risk_level = Column(String, default="low")
    status = Column(String, default="operational")


class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    country = Column(String)
    risk_score = Column(Float, default=0.0)
    tier = Column(Integer, default=1)