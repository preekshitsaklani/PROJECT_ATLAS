import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import init_db
from app.api import auth_router, intelligence_router, risk_router, ucdp_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ATLAS Intelligence System starting...")
    await init_db()
    logger.info("Database initialized")

    from app.services.nim_client import nim_client
    from app.services.pinecone_store import pinecone_store
    from app.services.graph_store import graph_store

    nim_ok = nim_client.available()
    pine_ok = pinecone_store.available()
    neo_ok = graph_store.available()

    logger.info(f"NIM GLM-5: {'Available' if nim_ok else 'Not configured'}")
    logger.info(f"Pinecone: {'Available' if pine_ok else 'Not configured'}")
    logger.info(f"Neo4j: {'Available' if neo_ok else 'Not configured'}")

    if neo_ok:
        try:
            graph_store.initialize_chokepoints()
            logger.info("Neo4j:All 6 chokepoints initialized")
        except Exception as e:
            logger.warning(f"Neo4j:Chokepoint init failed: {e}")

    logger.info("ATLAS is operational")
    yield
    logger.info("ATLAS shutting down...")
    graph_store.close()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Real-time geopolitical risk intelligence for global supply chains",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(intelligence_router, prefix=settings.API_V1_STR)
app.include_router(risk_router, prefix=settings.API_V1_STR)
app.include_router(ucdp_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    return {
        "status": "operational",
        "service": "ATLAS Intelligence System",
        "version": "1.0.0",
    }


@app.get("/")
async def root():
    return {
        "message": "ATLAS Intelligence System",
        "docs": "/docs",
        "health": "/health",
    }