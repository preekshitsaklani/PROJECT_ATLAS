import os
import logging
from typing import Any, Dict, List
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
logger = logging.getLogger(__name__)

CHOKEPOINT_KEYWORDS = {
    "suez": "Suez Canal",
    "suez canal": "Suez Canal",
    "port said": "Suez Canal",
    "ismailia": "Suez Canal",
    "egypt canal": "Suez Canal",
    "panama": "Panama Canal",
    "panama canal": "Panama Canal",
    "gatun lake": "Panama Canal",
    "panama drought": "Panama Canal",
    "hormuz": "Strait of Hormuz",
    "strait of hormuz": "Strait of Hormuz",
    "persian gulf": "Strait of Hormuz",
    "iran tanker": "Strait of Hormuz",
    "oman gulf": "Strait of Hormuz",
    "malacca": "Strait of Malacca",
    "strait of malacca": "Strait of Malacca",
    "singapore strait": "Strait of Malacca",
    "southeast asia shipping": "Strait of Malacca",
    "indonesia strait": "Strait of Malacca",
    "south china sea": "Strait of Malacca",
    "bosphorus": "Bosphorus Strait",
    "bosporus": "Bosphorus Strait",
    "istanbul strait": "Bosphorus Strait",
    "turkish strait": "Bosphorus Strait",
    "dardanelles": "Bosphorus Strait",
    "black sea": "Bosphorus Strait",
    "bab el-mandeb": "Bab el-Mandeb Strait",
    "bab_el_mandeb": "Bab el-Mandeb Strait",
    "bab al-mandab": "Bab el-Mandeb Strait",
    "red sea": "Bab el-Mandeb Strait",
    "houthi": "Bab el-Mandeb Strait",
    "yemen shipping": "Bab el-Mandeb Strait",
    "aden gulf": "Bab el-Mandeb Strait",
    "gulf of aden": "Bab el-Mandeb Strait",
}

ALL_CHOKEPOINTS = [
    "Suez Canal",
    "Panama Canal",
    "Strait of Hormuz",
    "Strait of Malacca",
    "Bosphorus Strait",
    "Bab el-Mandeb Strait",
]

class GraphStore:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "")
        self._driver = None
        self._available = None
        self._initialized = False

    def _get_driver(self):
        if self._driver is None:
            try:
                from neo4j import GraphDatabase
                self._driver = GraphDatabase.driver(
                    self.uri,
                    auth=(self.user, self.password),
                )
                self._driver.verify_connectivity()
                logger.info(f"Connected to Neo4j at {self.uri}")
            except Exception as e:
                logger.error(f"Neo4j connection failed: {e}")
                self._driver = None
        return self._driver

    def available(self) -> bool:
        if self._available is not None:
            return self._available
        if not self.password:
            self._available = False
            return False
        try:
            driver = self._get_driver()
            self._available = driver is not None
        except Exception:
            self._available = False
        return self._available

    def initialize_chokepoints(self):
        if self._initialized or not self.available():
            return

        driver = self._get_driver()
        if driver is None:
            return

        try:
            with driver.session() as session:
                for cp_name in ALL_CHOKEPOINTS:
                    session.run(
                        "MERGE (c:Chokepoint {name: $name})",
                        name=cp_name,
                    )
                logger.info(f"Neo4j: initialized all {len(ALL_CHOKEPOINTS)} chokepoint nodes")
            self._initialized = True
        except Exception as e:
            logger.error(f"Neo4j chokepoint init error: {e}")

    def _detect_chokepoints(self, text: str) -> List[str]:
        text_lower = text.lower()
        found = set()
        for keyword, chokepoint_name in CHOKEPOINT_KEYWORDS.items():
            if keyword in text_lower:
                found.add(chokepoint_name)
        return list(found)

    @staticmethod
    def _create_intel_nodes_tx(tx, doc: Dict[str, Any], chokepoints: List[str]):
        tx.run(
            """
            MERGE (i:IntelligenceItem {id: $id})
            SET i.title = $title,
                i.source = $source,
                i.published = $published,
                i.category = $category,
                i.credibility = $credibility,
                i.risk_score = $risk_score
            """,
            id=doc.get("id", ""),
            title=doc.get("title", ""),
            source=doc.get("source", ""),
            published=doc.get("published", ""),
            category=doc.get("category", ""),
            credibility=doc.get("credibility", ""),
            risk_score=float(doc.get("risk_score", 0)),
        )

        source_name = doc.get("source", "Unknown")
        tx.run(
            """
            MERGE (s:Source {name: $source_name})
            MERGE (i:IntelligenceItem {id: $id})
            MERGE (s)-[:PROVIDER_OF]->(i)
            """,
            source_name=source_name,
            id=doc.get("id", ""),
        )

        for cp in chokepoints:
            tx.run(
                """
                MERGE (c:Chokepoint {name: $cp_name})
                MERGE (i:IntelligenceItem {id: $id})
                MERGE (i)-[:IMPACTS]->(c)
                """,
                cp_name=cp,
                id=doc.get("id", ""),
            )

    def add_intelligence_graph(self, documents: List[Dict[str, Any]]) -> int:
        if not self.available():
            logger.warning("Neo4j not available, skipping graph upsert")
            return 0

        self.initialize_chokepoints()

        driver = self._get_driver()
        if driver is None:
            return 0

        added = 0
        try:
            with driver.session() as session:
                for doc in documents:
                    text = f"{doc.get('title', '')} {doc.get('summary', '')}"
                    chokepoints = self._detect_chokepoints(text)
                    session.execute_write(
                        self._create_intel_nodes_tx, doc, chokepoints
                    )
                    added += 1
            logger.info(f"Neo4j: added {added} intelligence items to graph")
        except Exception as e:
            logger.error(f"Neo4j upsert error: {e}")

        return added

    def close(self):
        if self._driver:
            self._driver.close()
            self._driver = None

graph_store = GraphStore()