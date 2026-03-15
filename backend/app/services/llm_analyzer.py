import json
import logging
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from app.services.nim_client import nim_client

logger = logging.getLogger(__name__)

CHOKEPOINTS = {
    "suez": {
        "name": "Suez Canal",
        "region": "Middle East / North Africa",
        "daily_traffic": "50+ vessels",
        "alternatives": [
            {"route": "Cape of Good Hope", "extra_days": 10, "extra_cost_pct": 30},
        ],
    },
    "panama": {
        "name": "Panama Canal",
        "region": "Central America",
        "daily_traffic": "35-40 vessels",
        "alternatives": [
            {"route": "Strait of Magellan", "extra_days": 7, "extra_cost_pct": 25},
            {"route": "Suez Canal (for Asia-Europe)", "extra_days": 5, "extra_cost_pct": 15},
        ],
    },
    "hormuz": {
        "name": "Strait of Hormuz",
        "region": "Persian Gulf",
        "daily_traffic": "Oil tanker corridor — 20% world oil",
        "alternatives": [
            {"route": "Saudi East-West Pipeline", "extra_days": 0, "extra_cost_pct": 10},
            {"route": "UAE Habshan-Fujairah Pipeline", "extra_days": 0, "extra_cost_pct": 8},
        ],
    },
    "malacca": {
        "name": "Strait of Malacca",
        "region": "Southeast Asia",
        "daily_traffic": "60,000+ vessels/year",
        "alternatives": [
            {"route": "Lombok Strait", "extra_days": 2, "extra_cost_pct": 12},
            {"route": "Sunda Strait", "extra_days": 1, "extra_cost_pct": 8},
        ],
    },
    "bosphorus": {
        "name": "Bosphorus Strait",
        "region": "Turkey",
        "daily_traffic": "48,000 vessels/year",
        "alternatives": [
            {"route": "Overland via rail (Turkey)", "extra_days": 3, "extra_cost_pct": 20},
        ],
    },
    "bab_el_mandeb": {
        "name": "Bab el-Mandeb Strait",
        "region": "Horn of Africa / Yemen",
        "daily_traffic": "Gateway to Suez — 4.8M bbl/day",
        "alternatives": [
            {"route": "Cape of Good Hope", "extra_days": 10, "extra_cost_pct": 30},
        ],
    },
}

EVENT_TAXONOMY = {
    "blockade": {"base_duration_days": 14, "cost_impact_pct": 40, "sectors": ["shipping", "energy", "trade"]},
    "military_conflict": {"base_duration_days": 30, "cost_impact_pct": 50, "sectors": ["defense", "shipping", "energy"]},
    "piracy": {"base_duration_days": 7, "cost_impact_pct": 15, "sectors": ["shipping", "insurance"]},
    "weather_event": {"base_duration_days": 5, "cost_impact_pct": 10, "sectors": ["shipping", "agriculture"]},
    "labor_dispute": {"base_duration_days": 10, "cost_impact_pct": 20, "sectors": ["shipping", "manufacturing"]},
    "regulatory_change": {"base_duration_days": 30, "cost_impact_pct": 8, "sectors": ["trade", "compliance"]},
    "sanctions": {"base_duration_days": 180, "cost_impact_pct": 25, "sectors": ["trade", "energy", "finance"]},
    "infrastructure_failure": {"base_duration_days": 14, "cost_impact_pct": 18, "sectors": ["shipping", "logistics"]},
    "pandemic": {"base_duration_days": 90, "cost_impact_pct": 30, "sectors": ["shipping", "labor", "trade"]},
    "cyber_attack": {"base_duration_days": 7, "cost_impact_pct": 12, "sectors": ["logistics", "port_ops"]},
    "political_instability": {"base_duration_days": 60, "cost_impact_pct": 20, "sectors": ["trade", "investment"]},
}


@dataclass
class RiskAnalysis:
    risk_level: str = "medium"
    risk_score: float = 50.0
    summary: str = ""
    thinking_trace: str = ""
    recommendations: List[str] = field(default_factory=list)
    chokepoints: List[Dict[str, Any]] = field(default_factory=list)
    event_type: str = "general"
    provider: str = "rule_based"
    timestamp: str = ""


class LLMAnalyzer:
    def __init__(self):
        self._analysis_cache: Optional[Dict[str, Any]] = None
        self._cache_time: Optional[datetime] = None
        self._cache_ttl = timedelta(minutes=5)

    def _strip_markdown_json(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        return text.strip()

    async def _get_llm_response(
        self, prompt: str, system: str
    ) -> Tuple[str, str, str]:
        if nim_client.available():
            try:
                thinking, answer = await nim_client.complete(
                    system_prompt=system,
                    user_prompt=prompt,
                    temperature=0.6,
                    max_tokens=4096,
                )
                if answer.strip():
                    logger.info("LLM response from NVIDIA NIM GLM-5")
                    return thinking, answer, "nvidia_nim_glm5"
            except Exception as e:
                logger.warning(f"NIM failed: {e}")

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama3.2",
                        "prompt": f"System: {system}\n\nUser: {prompt}",
                        "stream": False,
                    },
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        answer = data.get("response", "")
                        if answer.strip():
                            logger.info("LLM response from Ollama")
                            return "", answer, "ollama"
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")

        return "", "", "fallback"

    def _detect_event_type(self, text: str) -> str:
        text_lower = text.lower()
        type_keywords = {
            "blockade": ["blockade", "canal closed", "port closure"],
            "military_conflict": ["military", "war", "attack", "missile", "armed conflict", "strike"],
            "piracy": ["piracy", "hijack", "pirates", "armed robbery"],
            "weather_event": ["typhoon", "hurricane", "storm", "tsunami", "flood", "cyclone"],
            "labor_dispute": ["strike action", "labor", "dock workers", "union"],
            "sanctions": ["sanctions", "embargo", "restriction", "ban"],
            "political_instability": ["protest", "coup", "unrest", "revolution"],
            "cyber_attack": ["cyber", "hack", "ransomware"],
        }
        for event_type, keywords in type_keywords.items():
            for kw in keywords:
                if kw in text_lower:
                    return event_type
        return "general"

    def _detect_chokepoints(self, text: str) -> List[str]:
        text_lower = text.lower()
        found = []
        keywords_map = {
            "suez": ["suez"],
            "panama": ["panama"],
            "hormuz": ["hormuz", "persian gulf"],
            "malacca": ["malacca", "singapore strait"],
            "bosphorus": ["bosphorus", "istanbul strait"],
            "bab_el_mandeb": ["bab el-mandeb", "red sea", "yemen", "houthi"],
        }
        for key, keywords in keywords_map.items():
            for kw in keywords:
                if kw in text_lower:
                    found.append(key)
                    break
        return found

    def _get_recommendations(
        self, event_type: str, chokepoint_keys: List[str], level: str
    ) -> List[str]:
        recs = []

        if event_type == "blockade":
            recs.extend([
                "IMMEDIATE: Reroute all vessels to alternative corridors",
                "Activate war risk insurance clauses",
                "Pre-position inventory at alternative ports",
            ])
        elif event_type == "military_conflict":
            recs.extend([
                "Monitor situation via military intelligence feeds",
                "Establish communication with vessels in affected areas",
                "Consider temporary suspension of transit through conflict zone",
            ])
        elif event_type == "piracy":
            recs.extend([
                "Engage armed escort services for high-value cargo",
                "Activate vessel tracking and reporting protocols",
                "Coordinate with naval coalition forces in the area",
            ])
        elif event_type == "weather_event":
            recs.extend([
                "Reroute vessels around weather system",
                "Delay departures by 48-72 hours if possible",
                "Activate severe weather protocols",
            ])
        elif event_type == "labor_dispute":
            recs.extend([
                "Divert cargo to alternative ports",
                "Engage backup logistics providers",
                "Monitor negotiation progress",
            ])
        elif event_type == "sanctions":
            recs.extend([
                "Review all contracts for sanctions compliance",
                "Engage legal counsel for sanctions risk assessment",
                "Identify alternative suppliers in non-sanctioned regions",
            ])
        else:
            recs.extend([
                "Continue monitoring situation via OSINT feeds",
                "Review contingency plans for supply chain disruption",
                "Maintain elevated awareness posture",
            ])

        for cp_key in chokepoint_keys:
            cp_data = CHOKEPOINTS.get(cp_key, {})
            for alt in cp_data.get("alternatives", []):
                recs.append(
                    f"Alternative route: {alt['route']} (+{alt['extra_days']} days, +{alt['extra_cost_pct']}% cost)"
                )

        return recs

    def _fallback_analysis(
        self, items: List[Dict[str, Any]], entity: str = "global"
    ) -> RiskAnalysis:
        all_text = " ".join(
            f"{item.get('title', '')} {item.get('summary', '')}" for item in items
        )

        event_type = self._detect_event_type(all_text)
        chokepoint_keys = self._detect_chokepoints(all_text)

        scores = [item.get("risk_score", 30) for item in items if item.get("risk_score", 0) > 0]
        avg_score = sum(scores) / len(scores) if scores else 45.0

        if avg_score >= 80:
            level = "CRITICAL"
        elif avg_score >= 60:
            level = "HIGH"
        elif avg_score >= 40:
            level = "MEDIUM"
        else:
            level = "LOW"

        chokepoint_status = []
        for cp_key, cp_data in CHOKEPOINTS.items():
            status = "elevated" if cp_key in chokepoint_keys else "normal"
            risk = avg_score + 10 if cp_key in chokepoint_keys else max(20, avg_score - 20)
            chokepoint_status.append({
                "name": cp_data["name"],
                "status": status,
                "risk_score": min(100, risk),
                "alternatives": cp_data.get("alternatives", []),
            })

        recommendations = self._get_recommendations(event_type, chokepoint_keys, level)

        active_sources = len(set(item.get("source", "") for item in items))
        high_risk = len([i for i in items if i.get("risk_score", 0) >= 70])
        summary = (
            f"ATLAS Rule-Based Analysis | Risk Level: {level} | "
            f"Analyzed {len(items)} intelligence items from {active_sources} sources. "
            f"{high_risk} high-risk items detected. "
            f"Primary event type: {event_type.replace('_', ' ').title()}. "
            f"Affected chokepoints: {', '.join(CHOKEPOINTS[k]['name'] for k in chokepoint_keys) if chokepoint_keys else 'None directly identified'}."
        )

        return RiskAnalysis(
            risk_level=level,
            risk_score=avg_score,
            summary=summary,
            thinking_trace="Rule-based analysis (LLM unavailable)",
            recommendations=recommendations,
            chokepoints=chokepoint_status,
            event_type=event_type,
            provider="rule_based",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    async def analyze_situation(
        self, items: List[Dict[str, Any]], entity: str = "global"
    ) -> RiskAnalysis:
        if self._analysis_cache and self._cache_time:
            if datetime.now(timezone.utc) - self._cache_time < self._cache_ttl:
                logger.info("Returning cached analysis")
                return RiskAnalysis(**self._analysis_cache)

        if not items:
            return self._fallback_analysis([], entity)

        briefing_items = items[:15]
        briefing = "\n".join(
            f"- [{item.get('category', 'N/A').upper()}] {item.get('title', 'N/A')} "
            f"(Source: {item.get('source', 'N/A')}, Risk: {item.get('risk_score', 0):.0f}/100)"
            for item in briefing_items
        )

        system_prompt = """You are ATLAS, an elite geopolitical risk intelligence analyst specializing in global supply chain disruption assessment. You analyze OSINT data to provide actionable strategic intelligence.

Respond ONLY with valid JSON in this exact format:
{
  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "risk_score": <float 0-100>,
  "summary": "<2-3 sentence strategic assessment>",
  "event_type": "<blockade|military_conflict|piracy|weather_event|labor_dispute|sanctions|general>",
  "recommendations": ["<actionable recommendation 1>", "<recommendation 2>", "<recommendation 3>"],
  "affected_chokepoints": ["<chokepoint name if any>"]
}"""

        user_prompt = f"""Analyze this intelligence briefing for entity: {entity}

INTELLIGENCE BRIEFING:
{briefing}

Provide your risk assessment as JSON."""

        thinking, response, provider = await self._get_llm_response(user_prompt, system_prompt)

        if provider == "fallback" or not response.strip():
            analysis = self._fallback_analysis(items, entity)
        else:
            try:
                cleaned = self._strip_markdown_json(response)
                data = json.loads(cleaned)

                all_text = " ".join(f"{i.get('title', '')} {i.get('summary', '')}" for i in items)
                cp_keys = self._detect_chokepoints(all_text)

                chokepoint_status = []
                for cp_key, cp_data in CHOKEPOINTS.items():
                    status = "elevated" if cp_key in cp_keys else "normal"
                    risk = data.get("risk_score", 50) + 10 if cp_key in cp_keys else 30
                    chokepoint_status.append({
                        "name": cp_data["name"],
                        "status": status,
                        "risk_score": min(100, risk),
                        "alternatives": cp_data.get("alternatives", []),
                    })

                analysis = RiskAnalysis(
                    risk_level=data.get("risk_level", "MEDIUM"),
                    risk_score=float(data.get("risk_score", 50)),
                    summary=data.get("summary", "Analysis completed."),
                    thinking_trace=thinking,
                    recommendations=data.get("recommendations", []),
                    chokepoints=chokepoint_status,
                    event_type=data.get("event_type", "general"),
                    provider=provider,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.warning(f"LLM JSON parse failed: {e}, falling back to rule-based")
                analysis = self._fallback_analysis(items, entity)
                analysis.thinking_trace = f"LLM responded but JSON parse failed: {thinking}"

        self._analysis_cache = asdict(analysis)
        self._cache_time = datetime.now(timezone.utc)

        return analysis

    async def classify_risk(
        self, items: List[Dict[str, Any]], entity: str = "global"
    ) -> Dict[str, Any]:
        analysis = await self.analyze_situation(items, entity)
        return asdict(analysis)

    async def analyze_intelligence(
        self, items: List[Dict[str, Any]], entity: str = "global"
    ) -> Dict[str, Any]:
        analysis = await self.analyze_situation(items, entity)
        return asdict(analysis)

llm_analyzer = LLMAnalyzer()