# Smart Price — Current Project Structure

> Updated: 2026-03-18

## Architecture

```
smart-price/
├── backend/                    # FastAPI Backend (Python 3.11)
│   ├── app/
│   │   ├── agents/             # AI Agents
│   │   │   ├── __init__.py
│   │   │   ├── base_agent.py   # Base agent (Anthropic SDK, tool_use + streaming)
│   │   │   ├── shopping_agent.py # ЕГОРУШКА — main shopping AI assistant
│   │   │   └── tools/
│   │   │       └── __init__.py
│   │   ├── api/v1/
│   │   │   ├── deps.py         # FastAPI dependencies
│   │   │   ├── router.py       # API router (all endpoints registered)
│   │   │   └── endpoints/
│   │   │       ├── chat.py     # POST /chat — AI chat with SSE
│   │   │       ├── compare.py  # POST /ai/compare — AI comparison
│   │   │       ├── health.py   # GET /health — health checks
│   │   │       ├── parsers.py  # GET /parsers — marketplace list
│   │   │       ├── products.py # CRUD /products
│   │   │       ├── search.py   # GET /search — DB search
│   │   │       └── search_stream.py # GET /live-search/stream — live SSE
│   │   ├── core/
│   │   │   ├── config.py       # Re-export from app.config
│   │   │   └── exceptions.py   # Exception hierarchy
│   │   ├── db/
│   │   │   ├── base.py         # SQLAlchemy Base + Mixins
│   │   │   ├── session.py      # Async session factory
│   │   │   └── models/         # 9 ORM models (Mapped style)
│   │   │       ├── alert.py        # PriceAlert, SearchHistory
│   │   │       ├── category.py     # Category (hierarchical)
│   │   │       ├── chat.py         # ChatSession, ChatMessage ← NEW
│   │   │       ├── marketplace.py  # Marketplace
│   │   │       ├── price_history.py # PriceHistory
│   │   │       ├── product.py      # Product (GIN index)
│   │   │       ├── product_match.py # ProductMatch
│   │   │       ├── scraping_job.py # ScrapingJob ← NEW
│   │   │       └── user.py         # User
│   │   ├── ml/                 # ML components (partial)
│   │   ├── schemas/
│   │   │   ├── product.py      # Pydantic schemas
│   │   │   └── search.py       # Search schemas
│   │   ├── scrapers/
│   │   │   ├── __init__.py     # Lazy imports registry
│   │   │   ├── manager.py      # ScrapingManager (parallel search)
│   │   │   ├── onliner.py      # Onliner BY (httpx, API-based)
│   │   │   ├── yandex_market.py # Yandex Market (HTML parsing)
│   │   │   ├── wildberries.py  # Wildberries (API-based)
│   │   │   ├── ozon.py         # Ozon (browser-based)
│   │   │   ├── base.py         # Base scraper classes
│   │   │   ├── antidetect.py   # Anti-detection middleware
│   │   │   └── utils.py        # Scraping utilities
│   │   ├── services/
│   │   │   ├── analytics_service.py # Scraping job tracking ← NEW
│   │   │   ├── product_service.py   # Product CRUD
│   │   │   └── search_service.py    # Search logic
│   │   ├── config.py           # Main config (pydantic-settings)
│   │   └── main.py             # FastAPI app factory
│   ├── alembic/                # Database migrations
│   ├── scripts/
│   │   ├── run_dev.py          # Local dev server
│   │   └── seed_data.py        # Test data seeder
│   ├── tests/                  # Pytest suite (34 tests)
│   │   ├── conftest.py         # SQLite fixtures with JSONB compat
│   │   ├── test_config.py      # Settings tests
│   │   ├── test_api/           # API endpoint tests
│   │   ├── test_models/        # ORM model tests
│   │   └── test_scrapers/      # Scraper tests
│   ├── pyproject.toml          # Project config & deps
│   └── Dockerfile              # Multi-stage build
├── frontend/                   # Next.js 14 Frontend
│   ├── src/app/                # App Router pages
│   │   ├── page.tsx            # Home — search with SSE streaming
│   │   ├── chat/page.tsx       # AI chat (ЕГОРУШКА)
│   │   ├── compare/page.tsx    # Product comparison ← NEW
│   │   ├── about/page.tsx      # About page
│   │   ├── docs/page.tsx       # Documentation
│   │   └── layout.tsx          # Root layout (Header + Footer)
│   ├── src/components/         # React components
│   │   ├── layout/Header.tsx   # Navigation header
│   │   ├── layout/Footer.tsx   # Footer
│   │   ├── product/ProductCard.tsx # Product card
│   │   └── search/FilterPanel.tsx  # Search filters
│   ├── src/lib/                # API client & utilities
│   └── src/types/              # TypeScript interfaces
├── docker/                     # Docker Compose stack
├── docs/                       # Documentation
├── AUDIT_LOG.md                # Audit and progress log
└── README.md                   # Project overview
```

## API Endpoints (19 routes)

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/health | Health check |
| GET | /api/v1/health/ready | Readiness probe |
| GET | /api/v1/health/live | Liveness probe |
| GET | /api/v1/parsers | List marketplace parsers |
| GET | /api/v1/live-search/stream | SSE live marketplace search |
| GET | /api/v1/search | Database product search |
| GET | /api/v1/search/suggest | Autocomplete suggestions |
| POST | /api/v1/chat | AI chat (ЕГОРУШКА) with SSE |
| POST | /api/v1/ai/compare | AI product comparison |
| GET | /api/v1/products | List products |
| POST | /api/v1/products | Create product |
| POST | /api/v1/products/upsert | Create or update product |
| GET | /api/v1/products/{id} | Get product |
| PUT | /api/v1/products/{id} | Update product |
| DELETE | /api/v1/products/{id} | Delete product |
| GET | /api/v1/products/{id}/history | Price history |

## Database Models (11)

| Model | Table | Description |
|-------|-------|-------------|
| Product | products | Products with prices, marketplace references |
| Marketplace | marketplaces | Marketplace configurations |
| Category | categories | Hierarchical product categories |
| PriceHistory | price_histories | Price tracking over time |
| ProductMatch | product_matches | Cross-marketplace product matching |
| User | users | User accounts |
| PriceAlert | price_alerts | User price alerts |
| SearchHistory | search_histories | Search query tracking |
| ChatSession | chat_sessions | AI chat sessions |
| ChatMessage | chat_messages | Individual chat messages |
| ScrapingJob | scraping_jobs | Scraping task tracking |

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy 2.0 (async), PostgreSQL, Redis, Celery, Anthropic SDK
- **Frontend:** Next.js 14, TypeScript strict, Tailwind CSS, SSE streaming
- **AI:** Claude Haiku (tool_use for search), SSE streaming responses
- **Scraping:** httpx (Onliner API), HTML regex (Yandex), Scrapling (WB/Ozon)
- **Infrastructure:** Docker Compose, Qdrant, ClickHouse, Nginx
- **Testing:** pytest + pytest-asyncio, 34 tests, SQLite in-memory
