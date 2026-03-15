<div align="center">

# 🌐 ATLAS

### Advanced Threat & Logistics Analysis System

**Real-time geopolitical risk intelligence for global supply chains**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React_18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![NVIDIA NIM](https://img.shields.io/badge/NVIDIA_NIM-GLM--5-76B900?style=for-the-badge&logo=nvidia&logoColor=white)](https://build.nvidia.com)
[![Neo4j](https://img.shields.io/badge/Neo4j-4581C3?style=for-the-badge&logo=neo4j&logoColor=white)](https://neo4j.com)
[![Pinecone](https://img.shields.io/badge/Pinecone-000000?style=for-the-badge&logo=pinecone&logoColor=white)](https://pinecone.io)

---

*ATLAS continuously monitors 30+ OSINT sources, analyzes geopolitical events using AI-powered reasoning (NVIDIA GLM-5), and visualizes risk across 6 critical maritime chokepoints — giving supply chain teams the intelligence to predict disruptions before they happen.*

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Screenshots](#-screenshots)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [API Reference](#-api-reference)
- [OSINT Sources](#-osint-sources)
- [Database Schema](#-database-schema)
- [Project Structure](#-project-structure)
- [How It Works](#-how-it-works)
- [API Rate Limits](#-api-rate-limits)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

ATLAS is a full-stack web application that provides **real-time geopolitical risk intelligence** for global supply chains. It scrapes data from **30+ trusted OSINT sources**, runs **AI-powered analysis** using NVIDIA NIM (GLM-5), and visualizes risk across **6 critical maritime chokepoints**:

| Chokepoint | Region | Global Trade Impact |
|---|---|---|
| 🔴 **Suez Canal** | Egypt | 12-15% of global trade |
| 🟠 **Panama Canal** | Central America | 5% of global trade |
| 🟡 **Strait of Hormuz** | Persian Gulf | 20% of world oil |
| 🔵 **Strait of Malacca** | Southeast Asia | 25% of global trade |
| 🟣 **Bosphorus Strait** | Turkey | Key grain corridor |
| 🔴 **Bab el-Mandeb** | Yemen/Djibouti | Gateway to Suez |

### Who Is This For?

- **Supply chain analysts** tracking disruption risks
- **Maritime logistics companies** planning vessel routes
- **Risk management teams** needing early warning systems
- **Geopolitical researchers** studying conflict impacts on trade
- **Insurance underwriters** assessing maritime risk premiums

---

## ✨ Key Features

### 🕵️ OSINT Intelligence Scraping
- **30+ verified sources** across 5 credibility tiers (UN agencies → Government → Academic → Industry → News)
- Real-time RSS feed parsing, authenticated API access, and structured data ingestion
- **Cross-source corroboration detection** — flags when multiple sources report the same event
- Keyword-based **risk scoring** (0-100) using threat pattern matching

### 🤖 AI-Powered Risk Analysis
- **Primary LLM**: NVIDIA NIM GLM-5 with chain-of-thought reasoning
- **Fallback chain**: GLM-5 → Ollama (local) → Rule-based engine
- Streaming responses with **thinking trace** visibility
- Automated **chokepoint impact assessment** and **alternative route recommendations**

### 📊 RAG (Retrieval-Augmented Generation)
- **In-memory TF-IDF** vector store for instant search
- **Pinecone** cloud vector database for persistent semantic search (384-dim embeddings via `all-MiniLM-L6-v2`)
- **Credibility-weighted** search ranking — UN sources rank higher than news

### 🕸️ Knowledge Graph
- **Neo4j** graph database mapping relationships between:
  - `(:Source)-[:PROVIDER_OF]->(:IntelligenceItem)-[:IMPACTS]->(:Chokepoint)`
- All **6 chokepoints** initialized as permanent nodes
- Enables causal reasoning and event chain tracking

### 🗺️ Interactive Dashboard
- **Dark-themed** responsive UI with glassmorphism effects
- **Live world map** (Leaflet) with port risk markers, chokepoint indicators, and trade route overlays
- **Risk severity trend** charts (Recharts)
- **Category-filtered** intelligence feed with real-time updates
- **Semantic search** across all ingested intelligence

---

## 🏗 Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                        ATLAS FRONTEND                          │
│              React 18 + TypeScript + Vite + Leaflet            │
│                                                                │
│  ┌──────────┐       ┌──────────┐       ┌───────────────────┐  │
│  │Dashboard │       │ RiskMap  │       │ RiskIntelligence  │  │
│  └──────────┘       └──────────┘       └───────────────────┘  │
└─────────────────────┬──────────────────────────────────────────┘
                      │  HTTP (localhost:5173 → localhost:8000)
┌─────────────────────▼──────────────────────────────────────────┐
│                        ATLAS BACKEND                           │
│                Python 3.10+ / FastAPI / Uvicorn                │
│                                                                │
│  ┌─────────────── API Layer ──────────────────────────┐        │
│  │  /api/v1/intelligence/*  (OSINT Feed + Analysis)   │        │
│  │  /api/v1/risk/*          (Risk Dashboard Stats)    │        │
│  │  /api/v1/auth/*          (JWT Authentication)      │        │
│  │  /api/v1/ucdp/*          (UCDP Conflict Data)      │        │
│  └────────────────────────────────────────────────────┘        │
│                                                                │
│  ┌─────────────── Service Layer ──────────────────────┐        │
│  │  scraper.py        → 30+ source OSINT scraper      │        │
│  │  llm_analyzer.py   → AI risk analysis (NIM+fallback│        │
│  │  nim_client.py     → NVIDIA NIM GLM-5 client       │        │
│  │  rag_store.py      → In-memory TF-IDF vector store │        │
│  │  pinecone_store.py → Pinecone vector DB            │        │
│  │  graph_store.py    → Neo4j graph DB                │        │
│  │  risk_engine.py    → Multi-modal risk fusion       │        │
│  │  ucdp_service.py   → UCDP conflict API client      │        │
│  └────────────────────────────────────────────────────┘        │
│                                                                │
│  ┌─────────────── Data Layer ─────────────────────────┐        │
│  │  SQLite (aiosqlite)  → Users, alerts, ports        │        │
│  │  Pinecone (cloud)    → Vector embeddings for RAG   │        │
│  │  Neo4j (local)       → Causal relationship graph   │        │
│  └────────────────────────────────────────────────────┘        │
└────────────────────────────────────────────────────────────────┘
                      │
        ┌─────────────┼──────────────────┐
        ▼             ▼                  ▼
  ┌─────────┐   ┌──────────┐   ┌──────────────┐
  │ RSS/API │   │ UCDP API │   │ NewsData.io  │
  │  Feeds  │   │  (auth)  │   │  GDELT API   │
  │  (20+)  │   │          │   │  + others    │
  └─────────┘   └──────────┘   └──────────────┘
```

---

## 🛠 Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | React 18 + TypeScript | UI framework |
| **Frontend Bundler** | Vite | Fast dev server and bundler |
| **Frontend Charts** | Recharts | Risk severity trend charts |
| **Frontend Map** | Leaflet + react-leaflet | Interactive world map |
| **Frontend Icons** | Lucide React | Icon library |
| **Backend Framework** | FastAPI | Async REST API |
| **Backend Server** | Uvicorn | ASGI server |
| **LLM (Primary)** | NVIDIA NIM GLM-5 (`z-ai/glm5`) | AI geopolitical risk analysis with chain-of-thought reasoning |
| **LLM Client** | OpenAI Python SDK | OpenAI-compatible client for NIM |
| **Embeddings** | Sentence Transformers (`all-MiniLM-L6-v2`) | Local text embeddings for Pinecone (384-dim) |
| **Vector DB** | Pinecone | Semantic search over intelligence documents |
| **Graph DB** | Neo4j | Causal relationship mapping |
| **Relational DB** | SQLite + aiosqlite | User accounts, alerts, port data |
| **Authentication** | JWT (PyJWT) + OAuth2 | Token-based user authentication |
| **HTTP Client** | aiohttp | Async HTTP for scraping |
| **RSS Parser** | feedparser | Parse RSS/Atom feeds |
| **HTML Parser** | BeautifulSoup4 | Extract text from HTML pages |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** with `venv`
- **Node.js 18+** with `npm`
- **Neo4j Desktop** (running locally on `bolt://localhost:7687`)
- API keys (see [Configuration](#-configuration))

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/ATLAS.git
cd ATLAS
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your actual API keys
nano .env   # or use your preferred editor
```

Minimum required keys for basic functionality:

- `NVIDIA_API_KEY` — For AI analysis (get at [build.nvidia.com](https://build.nvidia.com))
- `UCDP_API_TOKEN` — For conflict data (request from mert.yilmaz@pcr.uu.se)
- `NEWSDATA_IO_KEY` — For news aggregation (get at [newsdata.io](https://newsdata.io))

Optional but recommended:

- `PINECONE_API_KEY` — For persistent vector search
- `NEO4J_PASSWORD` — For knowledge graph (requires Neo4j Desktop)

### 3. Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Frontend Setup

```bash
cd ../frontend
npm install
```

### 5. Neo4j Setup

Open Neo4j Desktop → Create a local DBMS → Set password (same as in `.env`) → Start

### 6. Run the Application

**Terminal 1 — Backend:**

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Frontend:**

```bash
cd frontend
npm run dev
```

### 7. Open in Browser

| Service | URL |
|---|---|
| 🖥️ Dashboard | http://localhost:5173 |
| 📖 API Docs (Swagger) | http://localhost:8000/docs |
| ❤️ Health Check | http://localhost:8000/health |

---

## ⚙️ Configuration

### Required API Keys

| API | How to Get | Free Tier Limit |
|---|---|---|
| NVIDIA NIM | [build.nvidia.com](https://build.nvidia.com) | 1,000 requests/day |
| UCDP | Email mert.yilmaz@pcr.uu.se | 5,000 requests/day |
| NewsData.io | [newsdata.io](https://newsdata.io) | 200 credits/day (2,000 articles) |
| NewsAPI | [newsapi.org](https://newsapi.org) | 100 requests/day |

### Optional API Keys

| API | How to Get | Free Tier Limit |
|---|---|---|
| Pinecone | [pinecone.io](https://pinecone.io) | 1 index, 100K vectors |
| OpenWeatherMap | [openweathermap.org](https://openweathermap.org) | 2,000 calls/day |
| StormGlass | [stormglass.io](https://stormglass.io) | 5 calls/day |
| AISStream | [aisstream.io](https://aisstream.io) | WebSocket streaming |
| ACLED | [acleddata.com](https://acleddata.com) | Per-plan |
| Marinesia | [marinesia.com](https://marinesia.com) | 1 req/30 min |

### Neo4j Setup

1. Download Neo4j Desktop
2. Create a new project → Add Local DBMS
3. Set password (put this in `.env` as `NEO4J_PASSWORD`)
4. Start the DBMS
5. Default bolt URL: `bolt://localhost:7687`

---

## 📡 API Reference

### Intelligence Endpoints (`/api/v1/intelligence/`)

| Method | Path | Description |
|---|---|---|
| GET | `/feed` | Get latest OSINT intelligence feed |
| GET | `/analyze` | AI-powered geopolitical risk analysis |
| POST | `/search` | Semantic search across intelligence |
| GET | `/sources` | List all configured sources |
| GET | `/categories` | List available categories |
| GET | `/status` | System health status |
| POST | `/refresh` | Force re-scrape all sources |

### Risk Endpoints (`/api/v1/risk/`)

| Method | Path | Description |
|---|---|---|
| GET | `/dashboard` | Dashboard statistics |
| GET | `/scores` | Risk scores for all entities |
| GET | `/scores/{id}` | Risk score for specific entity |
| GET | `/alerts` | Active alerts |
| GET | `/trend` | Risk severity trend (7 days) |
| GET | `/ports` | Monitored ports with risk levels |

### UCDP Conflict Endpoints (`/api/v1/ucdp/`)

| Method | Path | Description |
|---|---|---|
| GET | `/events` | UCDP GED Events (v25.1) |
| GET | `/events/candidate` | Near real-time events (v26.0.1) |
| GET | `/conflicts` | Armed Conflict Dataset |
| GET | `/battle-deaths` | Battle Related Deaths |
| GET | `/nonstate` | Non-State Conflicts |
| GET | `/onesided` | One-Sided Violence |
| GET | `/meta` | API metadata |

### Authentication (`/api/v1/auth/`)

| Method | Path | Description |
|---|---|---|
| POST | `/register` | Register new user |
| POST | `/login` | OAuth2 token login |
| GET | `/me` | Get current user |

---

## 📰 OSINT Sources

Sources are organized into 5 credibility tiers:

### Tier 1 — UN Agencies (Highest Credibility)
- IMO Maritime Safety Committee
- OCHA ReliefWeb
- UN News Centre
- World Food Programme (WFP)

### Tier 2 — Government Sources
- NOAA / National Weather Service
- EU External Action Service (EEAS)

### Tier 3 — Academic / Research
- UCDP (Uppsala Conflict Data Program) — Authenticated API
- GDELT (Global Database of Events, Language, and Tone)
- International Crisis Group — CrisisWatch

### Tier 4 — Industry Sources
- gCaptain Maritime News
- The Maritime Executive
- Reuters (Wire Service)

### Tier 5 — Verified News
- BBC World News
- Al Jazeera
- AP News
- NewsData.io (Aggregator)

---

## 🗄️ Database Schema

### SQLite (Relational)

```
Users        → id, email, username, hashed_password, is_active, created_at
RiskScores   → id, entity_id, entity_type, score, level, factors, timestamp
Alerts       → id, title, description, severity, category, source, is_active
Ports        → id, name, country, latitude, longitude, risk_level, status
Suppliers    → id, name, country, risk_score, tier
```

### Neo4j (Graph)

```cypher
(:Source {name})-[:PROVIDER_OF]->(:IntelligenceItem {id, title, source, published, category, risk_score})
(:IntelligenceItem)-[:IMPACTS]->(:Chokepoint {name})
```

### Pinecone (Vector)

```
Index: project-atlas (384 dimensions, cosine metric)
Metadata: title, source, category, credibility, risk_score, published
```

---

## 📁 Project Structure

```
ATLAS/
├── .env.example              # Environment template (copy to .env)
├── .gitignore                # Git ignore rules
├── README.md                 # This file
├── backend/
│   ├── requirements.txt      # Python dependencies
│   └── app/
│       ├── main.py           # FastAPI entry point + lifespan
│       ├── api/
│       │   ├── __init__.py   # Router exports
│       │   ├── auth.py       # JWT authentication
│       │   ├── intelligence.py # OSINT feed + AI analysis
│       │   ├── risk.py       # Dashboard stats + risk scores
│       │   └── ucdp.py       # UCDP conflict data
│       ├── core/
│       │   ├── config.py     # Settings from environment
│       │   └── security.py   # Password hashing + JWT
│       ├── db/
│       │   ├── base_class.py # SQLAlchemy declarative base
│       │   └── session.py    # Async engine + session factory
│       ├── models/
│       │   └── models.py     # ORM models (User, Port, Alert, etc.)
│       ├── schemas/
│       │   └── __init__.py   # Pydantic request/response schemas
│       └── services/
│           ├── scraper.py        # 30+ source OSINT scraper
│           ├── llm_analyzer.py   # AI risk analysis (NIM + fallback)
│           ├── nim_client.py     # NVIDIA NIM GLM-5 streaming client
│           ├── rag_store.py      # In-memory TF-IDF vector store
│           ├── pinecone_store.py # Pinecone vector DB integration
│           ├── graph_store.py    # Neo4j graph DB integration
│           ├── risk_engine.py    # Multi-modal risk fusion engine
│           └── ucdp_service.py   # UCDP REST API client
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    └── src/
        ├── main.tsx          # React entry point
        ├── App.tsx           # Layout with sidebar navigation
        ├── index.css         # Global dark theme styles
        └── components/
            ├── Dashboard.tsx         # Overview with AI analysis
            ├── RiskMap.tsx           # Interactive Leaflet map
            └── RiskIntelligence.tsx  # Deep-dive risk analysis
```

---

## 🔄 How It Works

### Data Flow

```
1. User opens Dashboard (localhost:5173)
        │
2. Frontend calls GET /api/v1/intelligence/feed
        │
3. Backend → scraper.scrape_all()
        │
        ├── asyncio.gather() → 30+ concurrent HTTP requests
        │     ├── RSS feeds (IMO, UN, BBC, Al Jazeera, etc.)
        │     ├── UCDP authenticated API (conflict data)
        │     ├── GDELT API (global events)
        │     ├── NewsData.io API (breaking news)
        │     └── Simulated strategic alerts (6 chokepoints)
        │
        ├── Cross-source corroboration detection
        ├── Risk score computation (keyword-based, 0-100)
        ├── Upsert to Pinecone (vector embeddings)
        ├── Upsert to Neo4j (knowledge graph)
        └── Add to in-memory RAG store
        │
4. Frontend calls GET /api/v1/intelligence/analyze
        │
5. Backend → llm_analyzer.analyze_situation()
        │
        ├── Try NVIDIA NIM GLM-5 (15s timeout, streaming)
        ├── Try Ollama fallback (local LLM)
        └── Rule-based fallback (chokepoint + event taxonomy)
        │
6. Dashboard renders:
        ├── Risk cards (Global Risk Index, Disruptions, Sources)
        ├── AI Analysis panel with recommendations
        ├── Chokepoint status table with alternatives
        ├── Risk severity trend chart (7-day)
        └── Categorized OSINT feed with filtering
```

### LLM Fallback Chain

```
NVIDIA NIM GLM-5 (Primary)
    │ timeout/error
    ▼
Ollama Local LLM (Fallback)
    │ unavailable
    ▼
Rule-Based Engine (Always Available)
    ├── Keyword-based event classification
    ├── Chokepoint detection from text
    ├── Event taxonomy (11 event types)
    └── Deterministic risk scoring
```

---

## ⏱ API Rate Limits

| API | Daily Limit | Strategy |
|---|---|---|
| NVIDIA NIM | ~1,000 req | Cache analysis for 5 min |
| UCDP | 5,000 req | Fetch max 20 events per scrape |
| NewsData.io | 200 credits (2,000 articles) | Fetch 10 per scrape |
| OpenWeatherMap | 2,000 calls (use 1,500 max) | Cache weather data |
| StormGlass | 5 calls/day | Only for critical chokepoints |
| NewsAPI | 100 req/day | Supplementary source |
| Marinesia | 1 req/30 min | Scheduled polling |
| GDELT | Reasonable use | Fetch 15 per scrape |
| RSS Feeds | Unlimited | 10-minute cache TTL |

---

## 🔧 Troubleshooting

### Backend won't start

```bash
# Check Python version
python3 --version  # Need 3.10+

# Reinstall dependencies
cd backend
pip install -r requirements.txt
```

### UCDP returns 401 Unauthorized

```bash
# Verify token is loaded
python3 -c "from dotenv import load_dotenv, find_dotenv; load_dotenv(find_dotenv()); import os; print(os.getenv('UCDP_API_TOKEN'))"
```

### Neo4j connection failed

- Ensure Neo4j Desktop is running
- Check the DBMS is started (green play button)
- Verify password matches `.env`

### Pinecone upsert fails

- Check API key is valid
- Verify index exists with dimension `384`
- Check the host URL matches your Pinecone dashboard

### Frontend shows no data

- Wait 10-15 seconds for initial scrape
- Check browser console for CORS errors
- Verify backend is running on port `8000`

### LLM analysis returns rule-based only

- Check `NVIDIA_API_KEY` is set correctly
- The NIM API has a 15-second timeout — slow networks may trigger fallback
- Install Ollama locally as a backup:
  ```bash
  curl -fsSL https://ollama.com/install.sh | sh && ollama pull llama3.2
  ```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
