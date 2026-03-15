from fastapi import APIRouter, Query
from typing import Optional, List
from dataclasses import asdict
from app.services.scraper import osint_scraper
from app.services.llm_analyzer import llm_analyzer
from app.services.rag_store import rag_store
from app.services.nim_client import nim_client
from app.schemas import SearchRequest

router = APIRouter(prefix="/intelligence", tags=["Intelligence"])


@router.get("/feed")
async def get_feed(
    limit: int = Query(50, ge=1, le=200),
    category: Optional[str] = None,
    credibility: Optional[str] = None,
    min_risk: float = Query(0, ge=0, le=100),
    force_refresh: bool = False,
):
    items = await osint_scraper.get_latest_intelligence(
        limit=limit * 3,
        force=force_refresh,
        category=category,
    )

    if credibility:
        items = [i for i in items if i.get("credibility", "").lower() == credibility.lower()]
    if min_risk > 0:
        items = [i for i in items if i.get("risk_score", 0) >= min_risk]

    return {
        "items": items[:limit],
        "total": len(items),
        "cached": not force_refresh,
    }


@router.get("/analyze")
async def analyze_intelligence(
    entity: str = Query("global", description="Entity to analyze"),
    use_llm: bool = True,
    force: bool = False,
):
    items = await osint_scraper.get_latest_intelligence(limit=30, force=force)

    if use_llm:
        analysis = await llm_analyzer.analyze_intelligence(items, entity)
    else:
        analysis = asdict(llm_analyzer._fallback_analysis(items, entity))

    return analysis


@router.post("/search")
async def search_intelligence(request: SearchRequest):
    results = rag_store.search(
        query=request.query,
        n_results=request.limit,
        category=request.category,
    )
    return {"results": results, "total": len(results)}


@router.get("/sources")
async def list_sources():
    return {"sources": osint_scraper.get_sources()}


@router.get("/categories")
async def list_categories():
    return {
        "categories": [
            "maritime", "weather", "sanctions", "conflict", "economics",
            "labor", "piracy", "news", "humanitarian", "energy", "regulatory",
        ]
    }


@router.get("/status")
async def system_status():
    return {
        "scraper": "operational",
        "rag_store": rag_store.get_stats(),
        "llm": {
            "nim_available": nim_client.available(),
            "nim_model": nim_client.model,
        },
    }


@router.post("/refresh")
async def refresh_intelligence():
    items = await osint_scraper.scrape_all(force=True)
    return {"status": "refreshed", "items_count": len(items)}