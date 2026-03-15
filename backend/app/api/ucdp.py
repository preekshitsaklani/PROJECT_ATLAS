from fastapi import APIRouter, Query
from typing import Optional
from app.services.ucdp_service import ucdp_service

router = APIRouter(prefix="/ucdp", tags=["UCDP Conflict Data"])

@router.get("/events")
async def get_events(
    pagesize: int = Query(100, ge=1, le=1000),
    page: int = Query(0, ge=0),
    country: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    type_of_violence: Optional[str] = None,
):
    return await ucdp_service.get_ged_events(
        pagesize=pagesize, page=page,
        country=country, start_date=start_date,
        end_date=end_date, type_of_violence=type_of_violence,
    )


@router.get("/events/candidate")
async def get_candidate_events(
    pagesize: int = Query(100, ge=1, le=1000),
    page: int = Query(0, ge=0),
):
    return await ucdp_service.get_candidate_events(pagesize=pagesize, page=page)


@router.get("/conflicts")
async def get_conflicts(
    pagesize: int = Query(100, ge=1, le=1000),
    page: int = Query(0, ge=0),
    country: Optional[str] = None,
    year: Optional[str] = None,
):
    return await ucdp_service.get_conflicts(
        pagesize=pagesize, page=page,
        country=country, year=year,
    )


@router.get("/battle-deaths")
async def get_battle_deaths(
    pagesize: int = Query(100, ge=1, le=1000),
    page: int = Query(0, ge=0),
):
    return await ucdp_service.get_battle_deaths(pagesize=pagesize, page=page)


@router.get("/nonstate")
async def get_nonstate(
    pagesize: int = Query(100, ge=1, le=1000),
    page: int = Query(0, ge=0),
):
    return await ucdp_service.get_nonstate_conflicts(pagesize=pagesize, page=page)


@router.get("/onesided")
async def get_onesided(
    pagesize: int = Query(100, ge=1, le=1000),
    page: int = Query(0, ge=0),
):
    return await ucdp_service.get_onesided_violence(pagesize=pagesize, page=page)


@router.get("/meta")
async def get_metadata():
    return ucdp_service.get_metadata()