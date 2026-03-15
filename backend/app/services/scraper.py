import asyncio
import hashlib
import logging
import os
import re
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import aiohttp
import feedparser
from bs4 import BeautifulSoup
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
logger = logging.getLogger(__name__)

class SourceCategory(str, Enum):
    MARITIME = "maritime"
    WEATHER = "weather"
    SANCTIONS = "sanctions"
    CONFLICT = "conflict"
    ECONOMICS = "economics"
    LABOR = "labor"
    PIRACY = "piracy"
    NEWS = "news"
    HUMANITARIAN = "humanitarian"
    ENERGY = "energy"
    REGULATORY = "regulatory"


class CredibilityLevel(str, Enum):
    UN_AGENCY = "un_agency"
    GOVERNMENT = "government"
    ACADEMIC = "academic"
    INDUSTRY = "industry"
    VERIFIED = "verified"


# ─── Data Model ───────────────────────────────────────────────────
@dataclass
class IntelligenceItem:
    id: str = ""
    title: str = ""
    summary: str = ""
    source: str = ""
    source_url: str = ""
    category: str = ""
    credibility: str = ""
    published: str = ""
    risk_score: float = 0.0
    keywords: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    authority_level: str = ""
    jurisdiction: str = ""
    content_hash: str = ""
    corroborated_by: List[str] = field(default_factory=list)


# ─── Threat Patterns for Risk Scoring ─────────────────────────────
THREAT_PATTERNS = {
    "critical": {
        "keywords": [
            "blockade", "war", "military strike", "missile attack", "naval mine",
            "port closure", "canal closed", "embargo", "nuclear", "invasion",
        ],
        "score": 85,
    },
    "high": {
        "keywords": [
            "sanctions", "piracy", "hijack", "drone attack", "armed conflict",
            "terrorist", "explosion", "oil spill", "typhoon", "hurricane",
            "tsunami", "earthquake", "strike action", "port congestion",
        ],
        "score": 65,
    },
    "medium": {
        "keywords": [
            "tariff", "trade war", "dispute", "protest", "unrest", "flood",
            "storm", "delays", "disruption", "shortage", "cyber attack",
            "diplomatic tension", "ceasefire", "negotiation",
        ],
        "score": 45,
    },
    "low": {
        "keywords": [
            "regulation", "policy change", "trade agreement", "inspection",
            "weather advisory", "maintenance", "drill", "exercise",
        ],
        "score": 25,
    },
}


# ─── Source Definitions ───────────────────────────────────────────
SOURCES = [
    # Tier 1: UN Agencies
    {
        "name": "IMO Maritime Safety",
        "url": "https://www.imo.org/en/MediaCentre/Pages/WhatsNew.aspx",
        "rss_url": "https://www.imo.org/en/MediaCentre/PressBriefings/Pages/Home.aspx",
        "method": "rss",
        "category": SourceCategory.MARITIME,
        "credibility": CredibilityLevel.UN_AGENCY,
        "authority_level": "International Maritime Organization",
    },
    {
        "name": "OCHA ReliefWeb",
        "url": "https://reliefweb.int",
        "rss_url": "https://reliefweb.int/updates/rss.xml",
        "method": "rss",
        "category": SourceCategory.HUMANITARIAN,
        "credibility": CredibilityLevel.UN_AGENCY,
        "authority_level": "UN OCHA",
    },
    {
        "name": "UN News",
        "url": "https://news.un.org",
        "rss_url": "https://news.un.org/feed/subscribe/en/news/all/rss.xml",
        "method": "rss",
        "category": SourceCategory.NEWS,
        "credibility": CredibilityLevel.UN_AGENCY,
        "authority_level": "United Nations",
    },
    {
        "name": "WFP News",
        "url": "https://www.wfp.org",
        "rss_url": "https://www.wfp.org/news/rss",
        "method": "rss",
        "category": SourceCategory.HUMANITARIAN,
        "credibility": CredibilityLevel.UN_AGENCY,
        "authority_level": "World Food Programme",
    },
    # Tier 2: Government
    {
        "name": "NOAA Weather Alerts",
        "url": "https://www.weather.gov",
        "rss_url": "https://alerts.weather.gov/cap/us.php?x=0",
        "method": "rss",
        "category": SourceCategory.WEATHER,
        "credibility": CredibilityLevel.GOVERNMENT,
        "authority_level": "US Government",
    },
    {
        "name": "EU EEAS Press",
        "url": "https://www.eeas.europa.eu",
        "rss_url": "https://www.eeas.europa.eu/eeas/press-material_en?page=0&_format=rss",
        "method": "rss",
        "category": SourceCategory.SANCTIONS,
        "credibility": CredibilityLevel.GOVERNMENT,
        "authority_level": "European Union",
    },
    # Tier 3: Academic
    {
        "name": "UCDP Conflict Events",
        "url": "https://ucdpapi.pcr.uu.se/api/gedevents/25.1",
        "method": "ucdp_auth",
        "category": SourceCategory.CONFLICT,
        "credibility": CredibilityLevel.ACADEMIC,
        "authority_level": "Uppsala University",
    },
    {
        "name": "GDELT Project",
        "url": "https://api.gdeltproject.org/api/v2/doc/doc",
        "method": "gdelt",
        "category": SourceCategory.NEWS,
        "credibility": CredibilityLevel.ACADEMIC,
        "authority_level": "GDELT Project",
    },
    {
        "name": "ICG CrisisWatch",
        "url": "https://www.crisisgroup.org",
        "rss_url": "https://www.crisisgroup.org/latest-updates/rss",
        "method": "rss",
        "category": SourceCategory.CONFLICT,
        "credibility": CredibilityLevel.ACADEMIC,
        "authority_level": "International Crisis Group",
    },
    # Tier 4: Industry
    {
        "name": "gCaptain Maritime",
        "url": "https://gcaptain.com",
        "rss_url": "https://gcaptain.com/feed/",
        "method": "rss",
        "category": SourceCategory.MARITIME,
        "credibility": CredibilityLevel.INDUSTRY,
        "authority_level": "Maritime Industry",
    },
    {
        "name": "The Maritime Executive",
        "url": "https://www.maritime-executive.com",
        "rss_url": "https://www.maritime-executive.com/rss",
        "method": "rss",
        "category": SourceCategory.MARITIME,
        "credibility": CredibilityLevel.INDUSTRY,
        "authority_level": "Maritime Industry",
    },
    # Tier 5: News
    {
        "name": "BBC World News",
        "url": "https://www.bbc.com/news",
        "rss_url": "https://feeds.bbci.co.uk/news/world/rss.xml",
        "method": "rss",
        "category": SourceCategory.NEWS,
        "credibility": CredibilityLevel.VERIFIED,
        "authority_level": "Major News Outlet",
    },
    {
        "name": "Al Jazeera",
        "url": "https://www.aljazeera.com",
        "rss_url": "https://www.aljazeera.com/xml/rss/all.xml",
        "method": "rss",
        "category": SourceCategory.NEWS,
        "credibility": CredibilityLevel.VERIFIED,
        "authority_level": "Major News Outlet",
    },
    {
        "name": "AP News",
        "url": "https://apnews.com",
        "rss_url": "https://rsshub.app/apnews/topics/apf-topnews",
        "method": "rss",
        "category": SourceCategory.NEWS,
        "credibility": CredibilityLevel.VERIFIED,
        "authority_level": "Wire Service",
    },
    {
        "name": "Reuters World",
        "url": "https://www.reuters.com",
        "rss_url": "https://www.reutersagency.com/feed/",
        "method": "rss",
        "category": SourceCategory.NEWS,
        "credibility": CredibilityLevel.INDUSTRY,
        "authority_level": "Wire Service",
    },
    # API-based sources
    {
        "name": "NewsData.io",
        "url": "https://newsdata.io/api/1/news",
        "method": "newsdata",
        "category": SourceCategory.NEWS,
        "credibility": CredibilityLevel.VERIFIED,
        "authority_level": "News Aggregator",
    },
]


class OsintScraper:
    """Multi-source OSINT intelligence scraper."""

    def __init__(self):
        self._cache: List[Dict[str, Any]] = []
        self._cache_time: Optional[datetime] = None
        self.cache_ttl = timedelta(minutes=10)
        self._seen_hashes: set = set()

    def _content_hash(self, title: str, source: str) -> str:
        """Generate content hash for deduplication."""
        raw = f"{title.lower().strip()}:{source.lower().strip()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _compute_risk_score(self, item: IntelligenceItem) -> float:
        """Compute risk score (0-100) based on keyword matching."""
        text = f"{item.title} {item.summary}".lower()
        score = 10.0  # Base score

        for level, data in THREAT_PATTERNS.items():
            for kw in data["keywords"]:
                if kw in text:
                    score = max(score, data["score"])
                    break

        # Credibility boost
        cred_boost = {
            "un_agency": 10, "government": 8, "academic": 6,
            "industry": 4, "verified": 2,
        }
        score += cred_boost.get(item.credibility, 0)

        return min(score, 100.0)

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text."""
        keywords = set()
        text_lower = text.lower()
        all_keywords = []
        for data in THREAT_PATTERNS.values():
            all_keywords.extend(data["keywords"])
        for kw in all_keywords:
            if kw in text_lower:
                keywords.add(kw)
        return list(keywords)[:10]

    # ─── Fetcher Methods ──────────────────────────────────────────

    async def _fetch_rss(
        self, session: aiohttp.ClientSession, source: Dict
    ) -> List[IntelligenceItem]:
        """Parse an RSS/Atom feed."""
        items = []
        rss_url = source.get("rss_url", source.get("url"))
        try:
            async with session.get(rss_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    logger.warning(f"RSS {source['name']}: HTTP {resp.status}")
                    return items
                text = await resp.text()

            feed = feedparser.parse(text)
            for entry in feed.entries[:10]:  # Limit per source
                title = entry.get("title", "").strip()
                if not title:
                    continue

                summary = ""
                if entry.get("summary"):
                    soup = BeautifulSoup(entry.summary, "html.parser")
                    summary = soup.get_text(separator=" ", strip=True)[:500]

                pub_date = ""
                if entry.get("published_parsed"):
                    try:
                        from time import mktime
                        dt = datetime.fromtimestamp(mktime(entry.published_parsed), tz=timezone.utc)
                        pub_date = dt.isoformat()
                    except Exception:
                        pub_date = datetime.now(timezone.utc).isoformat()
                else:
                    pub_date = datetime.now(timezone.utc).isoformat()

                link = entry.get("link", source.get("url", ""))

                ch = self._content_hash(title, source["name"])
                if ch in self._seen_hashes:
                    continue
                self._seen_hashes.add(ch)

                item = IntelligenceItem(
                    id=str(uuid.uuid4()),
                    title=title,
                    summary=summary[:500],
                    source=source["name"],
                    source_url=link,
                    category=source["category"].value if isinstance(source["category"], Enum) else source["category"],
                    credibility=source["credibility"].value if isinstance(source["credibility"], Enum) else source["credibility"],
                    published=pub_date,
                    authority_level=source.get("authority_level", ""),
                    content_hash=ch,
                )
                item.keywords = self._extract_keywords(f"{title} {summary}")
                item.risk_score = self._compute_risk_score(item)
                items.append(item)

        except Exception as e:
            logger.warning(f"RSS fetch error [{source['name']}]: {e}")

        return items

    async def _fetch_ucdp_auth(
        self, session: aiohttp.ClientSession, source: Dict
    ) -> List[IntelligenceItem]:
        """Fetch from UCDP API with authenticated token."""
        items = []
        token = os.getenv("UCDP_API_TOKEN", "")
        if not token:
            logger.warning("UCDP: No API token configured")
            return items

        # Get recent conflict events (last 2 years)
        url = f"https://ucdpapi.pcr.uu.se/api/gedevents/25.1"
        params = {"pagesize": "20", "StartDate": "2023-01-01"}
        headers = {"x-ucdp-access-token": token}

        try:
            async with session.get(
                url, headers=headers, params=params,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 401:
                    logger.error("UCDP: 401 Unauthorized")
                    return items
                if resp.status != 200:
                    logger.warning(f"UCDP: HTTP {resp.status}")
                    return items
                data = await resp.json()

            for event in data.get("Result", [])[:15]:
                title = f"Conflict: {event.get('dyad_name', 'Unknown')} in {event.get('country', 'Unknown')}"
                summary = (
                    f"Type: {event.get('type_of_violence', 'N/A')} | "
                    f"Region: {event.get('region', 'N/A')} | "
                    f"Deaths (best est.): {event.get('best', 'N/A')} | "
                    f"Date: {event.get('date_start', 'N/A')} to {event.get('date_end', 'N/A')} | "
                    f"Location: {event.get('where_description', 'N/A')}"
                )

                ch = self._content_hash(title, "UCDP")
                if ch in self._seen_hashes:
                    continue
                self._seen_hashes.add(ch)

                item = IntelligenceItem(
                    id=str(uuid.uuid4()),
                    title=title,
                    summary=summary,
                    source="UCDP",
                    source_url=f"https://ucdp.uu.se/event/{event.get('id', '')}",
                    category=SourceCategory.CONFLICT.value,
                    credibility=CredibilityLevel.ACADEMIC.value,
                    published=event.get("date_end", datetime.now(timezone.utc).isoformat()),
                    risk_score=70.0,
                    keywords=["conflict", "violence", event.get("country", "").lower()],
                    authority_level="Uppsala University",
                    content_hash=ch,
                )
                item.risk_score = self._compute_risk_score(item)
                items.append(item)

        except Exception as e:
            logger.warning(f"UCDP fetch error: {e}")

        return items

    async def _fetch_gdelt(
        self, session: aiohttp.ClientSession, source: Dict
    ) -> List[IntelligenceItem]:
        """Fetch from GDELT API."""
        items = []
        url = "https://api.gdeltproject.org/api/v2/doc/doc"
        params = {
            "query": "maritime OR shipping OR port OR sanctions OR conflict",
            "mode": "ArtList",
            "maxrecords": "15",
            "format": "json",
            "timespan": "1d",
        }

        try:
            async with session.get(
                url, params=params, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status != 200:
                    return items
                data = await resp.json()

            for article in data.get("articles", [])[:10]:
                title = article.get("title", "").strip()
                if not title:
                    continue

                ch = self._content_hash(title, "GDELT")
                if ch in self._seen_hashes:
                    continue
                self._seen_hashes.add(ch)

                pub_date = article.get("seendate", "")
                if pub_date and len(pub_date) >= 8:
                    try:
                        dt = datetime.strptime(pub_date[:8], "%Y%m%d").replace(tzinfo=timezone.utc)
                        pub_date = dt.isoformat()
                    except Exception:
                        pub_date = datetime.now(timezone.utc).isoformat()

                item = IntelligenceItem(
                    id=str(uuid.uuid4()),
                    title=title,
                    summary=article.get("title", "")[:300],
                    source="GDELT",
                    source_url=article.get("url", ""),
                    category=SourceCategory.NEWS.value,
                    credibility=CredibilityLevel.ACADEMIC.value,
                    published=pub_date,
                    authority_level="GDELT Project",
                    content_hash=ch,
                )
                item.keywords = self._extract_keywords(title)
                item.risk_score = self._compute_risk_score(item)
                items.append(item)

        except Exception as e:
            logger.warning(f"GDELT fetch error: {e}")

        return items

    async def _fetch_newsdata(
        self, session: aiohttp.ClientSession, source: Dict
    ) -> List[IntelligenceItem]:
        """Fetch from NewsData.io API."""
        items = []
        api_key = os.getenv("NEWSDATA_IO_KEY", "")
        if not api_key:
            return items

        url = "https://newsdata.io/api/1/news"
        params = {
            "apikey": api_key,
            "q": "maritime OR shipping OR port disruption OR sanctions OR geopolitical",
            "language": "en",
            "size": 10,
        }

        try:
            async with session.get(
                url, params=params, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status != 200:
                    logger.warning(f"NewsData.io: HTTP {resp.status}")
                    return items
                data = await resp.json()

            for article in data.get("results", [])[:10]:
                title = article.get("title", "").strip()
                if not title:
                    continue

                ch = self._content_hash(title, "NewsData.io")
                if ch in self._seen_hashes:
                    continue
                self._seen_hashes.add(ch)

                pub_date = article.get("pubDate", datetime.now(timezone.utc).isoformat())

                item = IntelligenceItem(
                    id=str(uuid.uuid4()),
                    title=title,
                    summary=(article.get("description") or title)[:500],
                    source="NewsData.io",
                    source_url=article.get("link", ""),
                    category=SourceCategory.NEWS.value,
                    credibility=CredibilityLevel.VERIFIED.value,
                    published=pub_date,
                    authority_level="News Aggregator",
                    content_hash=ch,
                )
                item.keywords = self._extract_keywords(f"{title} {item.summary}")
                item.risk_score = self._compute_risk_score(item)
                items.append(item)

        except Exception as e:
            logger.warning(f"NewsData.io fetch error: {e}")

        return items

    async def _fetch_source(
        self, session: aiohttp.ClientSession, source: Dict
    ) -> List[IntelligenceItem]:
        """Dispatch to the correct fetcher based on source method."""
        method = source.get("method", "rss")
        try:
            if method == "rss":
                return await self._fetch_rss(session, source)
            elif method == "ucdp_auth":
                return await self._fetch_ucdp_auth(session, source)
            elif method == "gdelt":
                return await self._fetch_gdelt(session, source)
            elif method == "newsdata":
                return await self._fetch_newsdata(session, source)
            else:
                logger.warning(f"Unknown fetch method: {method}")
                return []
        except Exception as e:
            logger.error(f"Error fetching {source['name']}: {e}")
            return []

    def _get_simulated_alerts(self) -> List[IntelligenceItem]:
        """Hardcoded high-priority demo alerts covering ALL 6 chokepoints."""
        now = datetime.now(timezone.utc).isoformat()
        alerts = [
            IntelligenceItem(
                id=str(uuid.uuid4()),
                title="🔴 Red Sea Shipping Crisis — Houthi Attacks Continue",
                summary="Multiple commercial vessels targeted by Houthi drone and missile attacks in the Red Sea and Gulf of Aden. Major carriers rerouting via Cape of Good Hope, adding 10-14 days. Bab el-Mandeb Strait transit risk at maximum.",
                source="ATLAS Strategic Alert",
                source_url="https://atlas.intel/alerts/red-sea",
                category=SourceCategory.CONFLICT.value,
                credibility=CredibilityLevel.VERIFIED.value,
                published=now,
                risk_score=92.0,
                keywords=["red sea", "houthi", "missile attack", "shipping", "bab el-mandeb", "gulf of aden"],
                authority_level="ATLAS Intelligence",
            ),
            IntelligenceItem(
                id=str(uuid.uuid4()),
                title="⚠️ Panama Canal — Drought Restrictions Persist",
                summary="Water levels at Gatun Lake remain critically low. Panama Canal daily transit slots reduced from 36 to 24, causing 7-10 day delays and surcharges up to $4M per vessel.",
                source="ATLAS Strategic Alert",
                source_url="https://atlas.intel/alerts/panama",
                category=SourceCategory.MARITIME.value,
                credibility=CredibilityLevel.VERIFIED.value,
                published=now,
                risk_score=78.0,
                keywords=["panama canal", "drought", "delays", "port congestion", "panama"],
                authority_level="ATLAS Intelligence",
            ),
            IntelligenceItem(
                id=str(uuid.uuid4()),
                title="🟡 Strait of Hormuz — Elevated Tensions",
                summary="Iran-US tensions elevated following tanker seizures in the Strait of Hormuz and Persian Gulf. Naval presence increased. Insurance premiums for vessels transiting the strait up 35%.",
                source="ATLAS Strategic Alert",
                source_url="https://atlas.intel/alerts/hormuz",
                category=SourceCategory.CONFLICT.value,
                credibility=CredibilityLevel.VERIFIED.value,
                published=now,
                risk_score=72.0,
                keywords=["hormuz", "strait of hormuz", "iran", "tanker", "persian gulf", "oil"],
                authority_level="ATLAS Intelligence",
            ),
            IntelligenceItem(
                id=str(uuid.uuid4()),
                title="🔴 Suez Canal — Container Ship Grounding Disrupts Traffic",
                summary="A large container vessel has run aground in the Suez Canal near Ismailia, blocking northbound traffic. Port Said anchorage filling rapidly. Estimated 48-72 hours to refloat. Over 100 vessels queued.",
                source="ATLAS Strategic Alert",
                source_url="https://atlas.intel/alerts/suez",
                category=SourceCategory.MARITIME.value,
                credibility=CredibilityLevel.VERIFIED.value,
                published=now,
                risk_score=88.0,
                keywords=["suez canal", "grounding", "blockade", "port said", "suez", "canal closed"],
                authority_level="ATLAS Intelligence",
            ),
            IntelligenceItem(
                id=str(uuid.uuid4()),
                title="🟠 Strait of Malacca — Piracy Incidents Surge",
                summary="Armed robbery and piracy incidents in the Strait of Malacca and Singapore Strait have increased 40% this quarter. Southeast Asia shipping lanes under heightened alert. Indonesian and Malaysian navies deploying additional patrols.",
                source="ATLAS Strategic Alert",
                source_url="https://atlas.intel/alerts/malacca",
                category=SourceCategory.PIRACY.value,
                credibility=CredibilityLevel.VERIFIED.value,
                published=now,
                risk_score=68.0,
                keywords=["malacca", "strait of malacca", "piracy", "singapore strait", "southeast asia shipping", "hijack"],
                authority_level="ATLAS Intelligence",
            ),
            IntelligenceItem(
                id=str(uuid.uuid4()),
                title="🟡 Bosphorus Strait — Black Sea Grain Corridor Under Threat",
                summary="Turkey tightens Bosphorus Strait transit regulations amid Black Sea security concerns. Dardanelles and Istanbul Strait experiencing delays of 24-48 hours for bulk carriers. Turkish Strait passage requires enhanced documentation.",
                source="ATLAS Strategic Alert",
                source_url="https://atlas.intel/alerts/bosphorus",
                category=SourceCategory.REGULATORY.value,
                credibility=CredibilityLevel.GOVERNMENT.value,
                published=now,
                risk_score=62.0,
                keywords=["bosphorus", "turkish strait", "black sea", "dardanelles", "istanbul strait", "regulatory"],
                authority_level="ATLAS Intelligence",
            ),
            IntelligenceItem(
                id=str(uuid.uuid4()),
                title="🟢 EU Sanctions Update — New Russian Shipping Restrictions",
                summary="European Council adopts 14th sanctions package targeting Russian LNG transshipment and shadow fleet operations in European waters.",
                source="ATLAS Strategic Alert",
                source_url="https://atlas.intel/alerts/sanctions",
                category=SourceCategory.SANCTIONS.value,
                credibility=CredibilityLevel.GOVERNMENT.value,
                published=now,
                risk_score=65.0,
                keywords=["sanctions", "russia", "lng", "eu", "regulatory"],
                authority_level="ATLAS Intelligence",
            ),
            IntelligenceItem(
                id=str(uuid.uuid4()),
                title="🌀 Typhoon Warning — Western Pacific Shipping Lanes",
                summary="Category 4 typhoon forming east of Philippines. Expected to cross major Asia-Europe shipping lanes and South China Sea within 72 hours. Vessels advised to divert from Strait of Malacca approaches.",
                source="ATLAS Strategic Alert",
                source_url="https://atlas.intel/alerts/typhoon",
                category=SourceCategory.WEATHER.value,
                credibility=CredibilityLevel.GOVERNMENT.value,
                published=now,
                risk_score=70.0,
                keywords=["typhoon", "storm", "weather advisory", "shipping", "south china sea", "malacca"],
                authority_level="ATLAS Intelligence",
            ),
            IntelligenceItem(
                id=str(uuid.uuid4()),
                title="🟠 Hamburg Port — Docker Strike Day 3",
                summary="Dockworkers at Hamburg port continue strike action over pay dispute. Container throughput reduced by 60%. Spillover congestion at Rotterdam and Antwerp.",
                source="ATLAS Strategic Alert",
                source_url="https://atlas.intel/alerts/hamburg",
                category=SourceCategory.LABOR.value,
                credibility=CredibilityLevel.INDUSTRY.value,
                published=now,
                risk_score=58.0,
                keywords=["strike action", "port congestion", "labor", "hamburg"],
                authority_level="ATLAS Intelligence",
            ),
        ]
        return alerts

    def _detect_corroboration(self, items: List[IntelligenceItem]) -> List[IntelligenceItem]:
        """Cross-reference items by keyword overlap to detect multi-source corroboration."""
        for i, item_a in enumerate(items):
            if not item_a.keywords:
                continue
            kw_a = set(item_a.keywords)
            for j, item_b in enumerate(items):
                if i == j or item_a.source == item_b.source:
                    continue
                if not item_b.keywords:
                    continue
                kw_b = set(item_b.keywords)
                overlap = kw_a & kw_b
                if len(overlap) >= 2:
                    if item_b.source not in item_a.corroborated_by:
                        item_a.corroborated_by.append(item_b.source)
        return items

    async def scrape_all(self, force: bool = False) -> List[Dict[str, Any]]:
        """Main orchestrator. Fetches all sources concurrently."""
        # Check cache
        if not force and self._cache and self._cache_time:
            if datetime.now(timezone.utc) - self._cache_time < self.cache_ttl:
                logger.info("Returning cached intelligence")
                return self._cache

        logger.info(f"Starting OSINT scrape from {len(SOURCES)} sources...")

        all_items: List[IntelligenceItem] = []

        # Fetch all sources concurrently
        connector = aiohttp.TCPConnector(limit=10, ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [self._fetch_source(session, source) for source in SOURCES]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Scrape task error: {result}")
                    continue
                if isinstance(result, list):
                    all_items.extend(result)

        # Add simulated alerts
        all_items.extend(self._get_simulated_alerts())

        # Detect corroboration
        all_items = self._detect_corroboration(all_items)

        # Convert to dicts
        result_dicts = [asdict(item) for item in all_items]

        # Sort by published date (newest first)
        result_dicts.sort(key=lambda x: x.get("published", ""), reverse=True)

        logger.info(f"OSINT scrape complete: {len(result_dicts)} items")

        # Upsert to Pinecone and Neo4j (non-blocking)
        try:
            from app.services.pinecone_store import pinecone_store
            pinecone_store.add_documents(result_dicts)
        except Exception as e:
            logger.warning(f"Pinecone upsert skipped: {e}")

        try:
            from app.services.graph_store import graph_store
            graph_store.add_intelligence_graph(result_dicts)
        except Exception as e:
            logger.warning(f"Neo4j upsert skipped: {e}")

        # Add to in-memory RAG store
        try:
            from app.services.rag_store import rag_store
            rag_store.add_documents(result_dicts)
        except Exception as e:
            logger.warning(f"RAG store error: {e}")

        # Cache
        self._cache = result_dicts
        self._cache_time = datetime.now(timezone.utc)

        return result_dicts

    async def get_latest_intelligence(
        self,
        limit: int = 50,
        force: bool = False,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Public function called by the API layer."""
        items = await self.scrape_all(force=force)

        # Apply category filter BEFORE limiting
        if category:
            items = [i for i in items if i.get("category", "").lower() == category.lower()]

        return items[:limit]

    def get_sources(self) -> List[Dict[str, str]]:
        """Return all configured source definitions."""
        return [
            {
                "name": s["name"],
                "url": s.get("url", ""),
                "category": s["category"].value if isinstance(s["category"], Enum) else s["category"],
                "credibility": s["credibility"].value if isinstance(s["credibility"], Enum) else s["credibility"],
                "method": s.get("method", "rss"),
            }
            for s in SOURCES
        ]

osint_scraper = OsintScraper()