import os
import logging
from typing import Any, Dict, List, Optional
import aiohttp
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
logger = logging.getLogger(__name__)

UCDP_BASE_URL = "https://ucdpapi.pcr.uu.se/api"

class UCDPService:
    def __init__(self):
        self.token = os.getenv("UCDP_API_TOKEN", "")
        self.base_url = UCDP_BASE_URL

    def _headers(self) -> Dict[str, str]:
        return {
            "x-ucdp-access-token": self.token,
            "Accept": "application/json",
        }

    async def _fetch(
        self,
        resource: str,
        version: str,
        pagesize: int = 100,
        page: int = 0,
        params: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/{resource}/{version}"
        query = {"pagesize": str(pagesize), "page": str(page)}
        if params:
            query.update(params)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, headers=self._headers(), params=query, timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 401:
                        logger.error("UCDP API: 401 Unauthorized — check token")
                        return {"error": "Unauthorized", "Result": []}
                    if resp.status != 200:
                        logger.error(f"UCDP API error: HTTP {resp.status}")
                        return {"error": f"HTTP {resp.status}", "Result": []}
                    return await resp.json()
        except Exception as e:
            logger.error(f"UCDP fetch error: {e}")
            return {"error": str(e), "Result": []}

    async def get_ged_events(
        self,
        pagesize: int = 100,
        page: int = 0,
        country: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        type_of_violence: Optional[str] = None,
    ) -> Dict[str, Any]:
        params = {}
        if country:
            params["Country"] = country
        if start_date:
            params["StartDate"] = start_date
        if end_date:
            params["EndDate"] = end_date
        if type_of_violence:
            params["TypeOfViolence"] = type_of_violence
        return await self._fetch("gedevents", "25.1", pagesize, page, params)

    async def get_candidate_events(
        self, pagesize: int = 100, page: int = 0, **params
    ) -> Dict[str, Any]:
        return await self._fetch("gedevents", "26.0.1", pagesize, page, params or None)

    async def get_conflicts(
        self, pagesize: int = 100, page: int = 0,
        country: Optional[str] = None,
        year: Optional[str] = None,
    ) -> Dict[str, Any]:
        params = {}
        if country:
            params["Country"] = country
        if year:
            params["Year"] = year
        return await self._fetch("ucdpprioconflict", "25.1", pagesize, page, params or None)

    async def get_battle_deaths(
        self, pagesize: int = 100, page: int = 0, **params
    ) -> Dict[str, Any]:
        return await self._fetch("battledeaths", "25.1", pagesize, page, params or None)

    async def get_nonstate_conflicts(
        self, pagesize: int = 100, page: int = 0, **params
    ) -> Dict[str, Any]:
        return await self._fetch("nonstate", "25.1", pagesize, page, params or None)

    async def get_onesided_violence(
        self, pagesize: int = 100, page: int = 0, **params
    ) -> Dict[str, Any]:
        return await self._fetch("onesided", "25.1", pagesize, page, params or None)

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "base_url": self.base_url,
            "authenticated": bool(self.token),
            "quota": "5,000 requests/day",
            "datasets": {
                "gedevents": {"version": "25.1", "description": "UCDP GED - Georeferenced Event Dataset"},
                "gedevents_candidate": {"version": "26.0.1", "description": "Near real-time candidate events"},
                "ucdpprioconflict": {"version": "25.1", "description": "UCDP/PRIO Armed Conflict Dataset"},
                "battledeaths": {"version": "25.1", "description": "Battle Related Deaths Dataset"},
                "nonstate": {"version": "25.1", "description": "Non-State Conflict Dataset"},
                "onesided": {"version": "25.1", "description": "One-Sided Violence Dataset"},
            },
        }

ucdp_service = UCDPService()