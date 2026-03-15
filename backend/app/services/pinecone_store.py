import os
import logging
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
logger = logging.getLogger(__name__)

class PineconeStore:
    def __init__(self):
        self.api_key = os.getenv("PINECONE_API_KEY", "")
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "project-atlas")
        self.host_url = os.getenv("PINECONE_HOST_URL", "")
        self._index = None
        self._embed_model = None
        self._available = None
        self._init_attempted = False

    def _get_embed_model(self):
        if self._embed_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embed_model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("Loaded embedding model: all-MiniLM-L6-v2 (384-dim)")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
        return self._embed_model

    def _get_index(self):
        if self._index is None and not self._init_attempted:
            self._init_attempted = True
            try:
                from pinecone import Pinecone
                pc = Pinecone(api_key=self.api_key)
                existing = [idx.name for idx in pc.list_indexes()]
                if self.index_name not in existing:
                    logger.info(f"Creating Pinecone index '{self.index_name}' with dim=384...")
                    from pinecone import ServerlessSpec
                    pc.create_index(
                        name=self.index_name,
                        dimension=384,
                        metric="cosine",
                        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
                    )
                    logger.info(f"Pinecone index '{self.index_name}' created")

                if self.host_url:
                    self._index = pc.Index(name=self.index_name, host=self.host_url)
                else:
                    self._index = pc.Index(name=self.index_name)

                stats = self._index.describe_index_stats()
                logger.info(
                    f"Connected to Pinecone index: {self.index_name} "
                    f"(vectors: {stats.get('total_vector_count', 0)}, dim: {stats.get('dimension', '?')})"
                )
            except Exception as e:
                logger.error(f"Pinecone connection failed: {e}")
                self._index = None
        return self._index

    def available(self) -> bool:
        if self._available is not None:
            return self._available
        if not self.api_key:
            logger.warning("Pinecone: No API key configured")
            self._available = False
            return False
        try:
            idx = self._get_index()
            self._available = idx is not None
        except Exception:
            self._available = False
        return self._available

    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        model = self._get_embed_model()
        if model is None:
            return None
        try:
            embedding = model.encode(text, show_progress_bar=False)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None

    def add_documents(self, documents: List[Dict[str, Any]]) -> int:
        if not self.available():
            logger.warning("Pinecone not available, skipping upsert")
            return 0

        index = self._get_index()
        if index is None:
            return 0

        vectors = []
        for doc in documents:
            doc_id = doc.get("id", "")
            if not doc_id:
                continue

            text = f"{doc.get('title', '')} {doc.get('summary', '')}"
            embedding = self._generate_embedding(text)
            if embedding is None:
                continue

            metadata = {
                "title": str(doc.get("title", ""))[:200],
                "source": str(doc.get("source", ""))[:100],
                "category": str(doc.get("category", "")),
                "credibility": str(doc.get("credibility", "")),
                "risk_score": float(doc.get("risk_score", 0)),
                "published": str(doc.get("published", "")),
            }

            vectors.append({
                "id": doc_id,
                "values": embedding,
                "metadata": metadata,
            })

        upserted = 0
        batch_size = 100
        try:
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i : i + batch_size]
                index.upsert(vectors=batch)
                upserted += len(batch)
            logger.info(f"Pinecone: upserted {upserted} vectors successfully")
        except Exception as e:
            logger.error(f"Pinecone upsert error: {e}")

        return upserted

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        if not self.available():
            return []

        embedding = self._generate_embedding(query)
        if embedding is None:
            return []

        index = self._get_index()
        if index is None:
            return []

        try:
            results = index.query(
                vector=embedding,
                top_k=top_k,
                include_metadata=True,
            )
            return [
                {
                    "id": match["id"],
                    "score": match["score"],
                    **match.get("metadata", {}),
                }
                for match in results.get("matches", [])
            ]
        except Exception as e:
            logger.error(f"Pinecone search error: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        if not self.available():
            return {"status": "unavailable"}
        try:
            index = self._get_index()
            if index:
                stats = index.describe_index_stats()
                return {
                    "status": "connected",
                    "total_vectors": stats.get("total_vector_count", 0),
                    "dimension": stats.get("dimension", 0),
                }
        except Exception:
            pass
        return {"status": "error"}

pinecone_store = PineconeStore()