from fastapi import APIRouter
from datetime import datetime, timedelta, timezone
from typing import List
from app.services.risk_engine import risk_engine

router = APIRouter(prefix="/risk", tags=["Risk"])

MONITORED_PORTS = [
    {"id": "singapore", "name": "Port of Singapore", "country": "Singapore", "lat": 1.2644, "lon": 103.8222},
    {"id": "shanghai", "name": "Port of Shanghai", "country": "China", "lat": 31.3622, "lon": 121.5068},
    {"id": "rotterdam", "name": "Port of Rotterdam", "country": "Netherlands", "lat": 51.9036, "lon": 4.4939},
    {"id": "los_angeles", "name": "Port of Los Angeles", "country": "USA", "lat": 33.7361, "lon": -118.2642},
    {"id": "dubai", "name": "Port of Jebel Ali", "country": "UAE", "lat": 25.0086, "lon": 55.0583},
    {"id": "hamburg", "name": "Port of Hamburg", "country": "Germany", "lat": 53.5461, "lon": 9.9664},
    {"id": "busan", "name": "Port of Busan", "country": "South Korea", "lat": 35.0963, "lon": 129.0405},
    {"id": "mumbai", "name": "Port of Mumbai (JNPT)", "country": "India", "lat": 18.9498, "lon": 72.9512},
]


@router.get("/dashboard")
async def dashboard_stats():
    scores = [risk_engine.calculate_risk(p["id"], "port") for p in MONITORED_PORTS]
    avg_risk = sum(s["composite_score"] for s in scores) / len(scores)
    disruptions = sum(1 for s in scores if s["level"] in ("high", "critical"))

    return {
        "global_risk_index": round(avg_risk, 1),
        "active_disruptions": disruptions,
        "monitored_sources": 30,
        "supply_chain_health": round(100 - avg_risk, 1),
        "ports_monitored": len(MONITORED_PORTS),
    }


@router.get("/scores")
async def risk_scores():
    return {
        "scores": [
            {**risk_engine.calculate_risk(p["id"], "port"), "name": p["name"], "country": p["country"]}
            for p in MONITORED_PORTS
        ]
    }


@router.get("/scores/{entity_id}")
async def risk_score_by_entity(entity_id: str):
    return risk_engine.calculate_risk(entity_id, "port")


@router.get("/alerts")
async def active_alerts():
    from app.services.scraper import osint_scraper
    items = await osint_scraper.get_latest_intelligence(limit=100)
    high_risk = [
        {
            "id": i.get("id", ""),
            "title": i.get("title", ""),
            "description": i.get("summary", ""),
            "severity": "critical" if i.get("risk_score", 0) >= 80 else "warning" if i.get("risk_score", 0) >= 60 else "info",
            "category": i.get("category", ""),
            "source": i.get("source", ""),
            "timestamp": i.get("published", ""),
        }
        for i in items if i.get("risk_score", 0) >= 50
    ]
    return {"alerts": high_risk[:20]}


@router.get("/trend")
async def risk_trend():
    trend = []
    now = datetime.now(timezone.utc)
    for i in range(7, -1, -1):
        date = now - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        score = risk_engine._seeded_uniform(f"trend:{date_str}", 30, 75)
        level = "critical" if score >= 75 else "high" if score >= 55 else "medium" if score >= 35 else "low"
        trend.append({
            "date": date_str,
            "score": round(score, 1),
            "level": level,
        })
    return {"trend": trend}


@router.get("/ports")
async def monitored_ports():
    ports = []
    for p in MONITORED_PORTS:
        risk = risk_engine.calculate_risk(p["id"], "port")
        ports.append({
            "id": p["id"],
            "name": p["name"],
            "country": p["country"],
            "latitude": p["lat"],
            "longitude": p["lon"],
            "risk_level": risk["level"],
            "risk_score": risk["composite_score"],
            "status": "disrupted" if risk["level"] in ("high", "critical") else "operational",
        })
    return {"ports": ports}