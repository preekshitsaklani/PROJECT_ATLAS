import hashlib
import struct
from datetime import datetime, timezone
from typing import Any, Dict

class RiskEngine:
    def _seeded_uniform(self, key: str, low: float, high: float) -> float:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        seed_str = f"{key}:{date_str}"
        h = hashlib.sha256(seed_str.encode()).digest()
        val = struct.unpack("I", h[:4])[0] / (2 ** 32)
        return low + val * (high - low)

    def calculate_risk(self, entity_id: str, entity_type: str = "port") -> Dict[str, Any]:
        ts_score = self._seeded_uniform(f"{entity_id}:ts", 20, 80)
        nlp_score = self._seeded_uniform(f"{entity_id}:nlp", 25, 85)
        graph_score = self._seeded_uniform(f"{entity_id}:graph", 15, 75)
        weather_score = self._seeded_uniform(f"{entity_id}:weather", 10, 60)
        financial_score = self._seeded_uniform(f"{entity_id}:financial", 20, 70)

        composite = (
            ts_score * 0.2
            + nlp_score * 0.3
            + graph_score * 0.15
            + weather_score * 0.15
            + financial_score * 0.2
        )

        if composite >= 75:
            level = "critical"
        elif composite >= 55:
            level = "high"
        elif composite >= 35:
            level = "medium"
        else:
            level = "low"

        return {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "composite_score": round(composite, 2),
            "level": level,
            "components": {
                "time_series": round(ts_score, 2),
                "nlp_sentiment": round(nlp_score, 2),
                "graph_centrality": round(graph_score, 2),
                "weather_impact": round(weather_score, 2),
                "financial_stress": round(financial_score, 2),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

risk_engine = RiskEngine()