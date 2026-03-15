import logging
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

CREDIBILITY_WEIGHTS = {
    "un_agency": 1.0,
    "government": 0.9,
    "academic": 0.8,
    "industry": 0.7,
    "verified": 0.6,
    "news": 0.5,
}

class RAGStore:

    def __init__(self):
        self.documents: List[Dict[str, Any]] = []
        self.doc_index: Dict[str, int] = {}  # id -> index
        self.idf: Dict[str, float] = {}
        self.tfidf_vectors: List[Dict[str, float]] = []
        self._dirty = True

    def _tokenize(self, text: str) -> List[str]:
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        tokens = text.split()
        return [t for t in tokens if len(t) > 2]

    def _rebuild_index(self):
        if not self._dirty or not self.documents:
            return

        n = len(self.documents)
        df = Counter()
        doc_tokens = []

        for doc in self.documents:
            text = f"{doc.get('title', '')} {doc.get('summary', '')} {' '.join(doc.get('keywords', []))}"
            tokens = self._tokenize(text)
            unique_tokens = set(tokens)
            for token in unique_tokens:
                df[token] += 1
            doc_tokens.append(tokens)

        self.idf = {}
        for term, count in df.items():
            self.idf[term] = math.log((n + 1) / (count + 1)) + 1

        self.tfidf_vectors = []
        for tokens in doc_tokens:
            tf = Counter(tokens)
            total = len(tokens) if tokens else 1
            vector = {}
            for term, count in tf.items():
                vector[term] = (count / total) * self.idf.get(term, 0)
            self.tfidf_vectors.append(vector)

        self._dirty = False
        logger.info(f"RAG index rebuilt: {n} documents, {len(self.idf)} terms")

    def add_documents(self, documents: List[Dict[str, Any]]):
        added = 0
        for doc in documents:
            doc_id = doc.get("id", "")
            if doc_id and doc_id not in self.doc_index:
                self.doc_index[doc_id] = len(self.documents)
                self.documents.append(doc)
                added += 1

        if added > 0:
            self._dirty = True
            logger.info(f"RAG store: added {added} documents (total: {len(self.documents)})")

    def _cosine_similarity(self, vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
        common_terms = set(vec_a.keys()) & set(vec_b.keys())
        if not common_terms:
            return 0.0

        dot = sum(vec_a[t] * vec_b[t] for t in common_terms)
        norm_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
        norm_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))

        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def search(
        self,
        query: str,
        n_results: int = 10,
        category: Optional[str] = None,
        min_risk_score: float = 0.0,
        credibility_weighted: bool = True,
    ) -> List[Dict[str, Any]]:
        self._rebuild_index()

        if not self.documents:
            return []

        query_tokens = self._tokenize(query)
        tf = Counter(query_tokens)
        total = len(query_tokens) if query_tokens else 1
        query_vec = {}
        for term, count in tf.items():
            query_vec[term] = (count / total) * self.idf.get(term, 0)

        results = []
        for i, doc in enumerate(self.documents):
            if category and doc.get("category", "").lower() != category.lower():
                continue
            if doc.get("risk_score", 0) < min_risk_score:
                continue

            similarity = self._cosine_similarity(query_vec, self.tfidf_vectors[i])

            if credibility_weighted:
                cred = doc.get("credibility", "news").lower()
                weight = CREDIBILITY_WEIGHTS.get(cred, 0.5)
                similarity *= weight

            if doc.get("corroborated_by"):
                similarity *= 1.2

            if similarity > 0:
                results.append({**doc, "_score": similarity})

        results.sort(key=lambda x: x["_score"], reverse=True)
        return results[:n_results]

    def get_recent(self, hours: int = 24, limit: int = 50) -> List[Dict[str, Any]]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent = []
        for doc in self.documents:
            pub = doc.get("published", "")
            if pub:
                try:
                    pub_dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                    if pub_dt >= cutoff:
                        recent.append(doc)
                except (ValueError, TypeError):
                    continue

        recent.sort(key=lambda x: x.get("published", ""), reverse=True)
        return recent[:limit]

    def get_by_credibility(self, credibility: str, limit: int = 50) -> List[Dict[str, Any]]:
        return [
            doc for doc in self.documents
            if doc.get("credibility", "").lower() == credibility.lower()
        ][:limit]

    def get_stats(self) -> Dict[str, Any]:
        categories = defaultdict(int)
        sources = set()
        corroborated = 0

        for doc in self.documents:
            categories[doc.get("category", "unknown")] += 1
            sources.add(doc.get("source", "unknown"))
            if doc.get("corroborated_by"):
                corroborated += 1

        return {
            "total_documents": len(self.documents),
            "categories": dict(categories),
            "unique_sources": len(sources),
            "corroborated_items": corroborated,
        }


rag_store = RAGStore()