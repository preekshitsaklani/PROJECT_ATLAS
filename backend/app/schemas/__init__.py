from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    email: str
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class IntelligenceItemResponse(BaseModel):
    id: str
    title: str
    summary: str
    source: str
    source_url: str
    category: str
    credibility: str
    published: str
    risk_score: float
    keywords: List[str] = []
    entities: List[str] = []
    authority_level: str = ""
    jurisdiction: str = ""
    corroborated_by: List[str] = []


class SearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    min_credibility: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)


class AnalysisResponse(BaseModel):
    risk_level: str
    risk_score: float
    summary: str
    thinking_trace: Optional[str] = None
    recommendations: List[str] = []
    chokepoints: List[dict] = []
    event_type: str = "general"
    provider: str = "rule_based"
    timestamp: str = ""


class DashboardStats(BaseModel):
    global_risk_index: float
    active_disruptions: int
    monitored_sources: int
    supply_chain_health: float
    ports_monitored: int


class RiskTrendPoint(BaseModel):
    date: str
    score: float
    level: str


class AlertResponse(BaseModel):
    id: str
    title: str
    description: str
    severity: str
    category: str
    source: str
    timestamp: str


class PortResponse(BaseModel):
    id: str
    name: str
    country: str
    latitude: float
    longitude: float
    risk_level: str
    status: str