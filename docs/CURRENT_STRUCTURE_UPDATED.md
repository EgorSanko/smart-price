# Current Project Structure

## Полная структура проекта

```
smart-price/
│
├── backend/                          # Python Backend (FastAPI)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI application entry
│   │   ├── config.py                 # Pydantic Settings
│   │   │
│   │   ├── api/                      # API Layer
│   │   │   ├── __init__.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── router.py         # Main API router
│   │   │       ├── deps.py           # Dependency injection
│   │   │       └── endpoints/
│   │   │           ├── __init__.py
│   │   │           ├── health.py     # Health checks
│   │   │           ├── products.py   # Product CRUD
│   │   │           ├── search.py     # Search endpoints
│   │   │           ├── analytics.py  # Price analytics
│   │   │           └── chat.py       # AI chat endpoint
│   │   │
│   │   ├── core/                     # Core utilities
│   │   │   ├── __init__.py
│   │   │   ├── security.py           # JWT, password hashing
│   │   │   └── exceptions.py         # Custom exceptions
│   │   │
│   │   ├── db/                       # Database Layer
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # SQLAlchemy Base class
│   │   │   ├── session.py            # Async session factory
│   │   │   └── models/
│   │   │       ├── __init__.py       # Export all models
│   │   │       ├── marketplace.py    # Marketplace model
│   │   │       ├── category.py       # Category model
│   │   │       ├── product.py        # Product model
│   │   │       ├── price_history.py  # PriceHistory model
│   │   │       ├── product_match.py  # ProductMatch model
│   │   │       ├── user.py           # User model
│   │   │       └── alert.py          # PriceAlert, SearchHistory
│   │   │
│   │   ├── schemas/                  # Pydantic Schemas
│   │   │   ├── __init__.py           # ✅ Export all schemas
│   │   │   ├── product.py            # ✅ Product schemas
│   │   │   ├── search.py             # Search schemas
│   │   │   ├── user.py               # User schemas
│   │   │   └── analytics.py          # Analytics schemas
│   │   │
│   │   ├── services/                 # Business Logic
│   │   │   ├── __init__.py
│   │   │   ├── product_service.py    # Product CRUD operations
│   │   │   ├── search_service.py     # Search logic
│   │   │   └── analytics_service.py  # Price analytics
│   │   │
│   │   ├── scrapers/                 # Marketplace Scrapers
│   │   │   ├── __init__.py           # ✅ Factory & exports
│   │   │   ├── base.py               # ✅ BaseScraper, PlaywrightScraper
│   │   │   ├── ozon.py               # ✅ Ozon scraper
│   │   │   ├── wildberries.py        # ✅ Wildberries scraper
│   │   │   └── yandex_market.py      # Yandex.Market scraper
│   │   │
│   │   ├── ml/                       # ML Components
│   │   │   ├── __init__.py
│   │   │   ├── embeddings/
│   │   │   │   ├── __init__.py
│   │   │   │   └── encoder.py        # Text/Image embeddings
│   │   │   ├── matching/
│   │   │   │   ├── __init__.py
│   │   │   │   └── matcher.py        # Product matching
│   │   │   ├── forecasting/
│   │   │   │   ├── __init__.py
│   │   │   │   └── predictor.py      # Price forecasting
│   │   │   └── anomaly/
│   │   │       ├── __init__.py
│   │   │       └── detector.py       # Anomaly detection
│   │   │
│   │   └── agents/                   # AI Agents
│   │       ├── __init__.py
│   │       ├── shopping_agent.py     # Main shopping assistant
│   │       └── tools/
│   │           ├── __init__.py
│   │           ├── search_tool.py
│   │           ├── compare_tool.py
│   │           └── analyze_tool.py
│   │
│   ├── tests/                        # Tests
│   │   ├── __init__.py
│   │   ├── conftest.py               # Pytest fixtures
│   │   ├── test_api/
│   │   │   ├── __init__.py
│   │   │   ├── test_health.py
│   │   │   └── test_products.py
│   │   └── test_scrapers/            # ✅ Scraper tests
│   │       ├── __init__.py           # ✅
│   │       ├── conftest.py           # ✅ Scraper test fixtures
│   │       ├── test_base.py          # ✅ Base scraper tests
│   │       └── test_wildberries.py   # ✅ WB scraper tests
│   │
│   ├── alembic/                      # Database Migrations
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── 001_initial.py
│   │
│   ├── alembic.ini
│   ├── pyproject.toml                # Dependencies (Poetry)
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/                         # Next.js Frontend
│   └── ...
│
├── docker/                           # Docker Configuration
│   └── ...
│
├── docs/                             # Documentation
│   └── ...
│
└── README.md
```

---

## Статус реализации

### Sprint 1-2: Foundation ✅

| Компонент | Статус | Файл |
|-----------|--------|------|
| pyproject.toml | ✅ | `backend/pyproject.toml` |
| docker-compose.dev.yml | ✅ | `docker/docker-compose.dev.yml` |
| config.py | ✅ | `backend/app/config.py` |
| main.py | ✅ | `backend/app/main.py` |
| db/base.py | ✅ | `backend/app/db/base.py` |
| models/product.py | ✅ | `backend/app/db/models/product.py` |
| schemas/product.py | ✅ | `backend/app/schemas/product.py` |
| clickhouse/init.sql | ⚠️ | `docker/clickhouse/init.sql` |

### Sprint 3-4: Scrapers & Search ✅ (scrapers done)

| Компонент | Статус | Файл |
|-----------|--------|------|
| scrapers/__init__.py | ✅ | `backend/app/scrapers/__init__.py` |
| scrapers/base.py | ✅ | `backend/app/scrapers/base.py` |
| scrapers/ozon.py | ✅ | `backend/app/scrapers/ozon.py` |
| scrapers/wildberries.py | ✅ | `backend/app/scrapers/wildberries.py` |
| schemas/__init__.py | ✅ | `backend/app/schemas/__init__.py` |
| schemas/product.py | ✅ | `backend/app/schemas/product.py` |
| tests/test_scrapers/* | ✅ | `backend/tests/test_scrapers/` |
| Celery tasks | ⏳ | `backend/app/tasks/scraping.py` |
| Full-text search | ⏳ | `backend/app/services/search_service.py` |
| Qdrant integration | ⏳ | `backend/app/services/vector_search.py` |
| Hybrid search | ⏳ | `backend/app/services/hybrid_search.py` |

### Sprint 5-9: Core Features ⏳

| Компонент | Статус |
|-----------|--------|
| Frontend setup | ⏳ |
| Price history UI | ⏳ |
| User auth | ⏳ |
| Price alerts | ⏳ |
| Image search | ⏳ |

### Sprint 10-14: AI/ML ⏳

| Компонент | Статус |
|-----------|--------|
| Product matching | ⏳ |
| LLM Agent | ⏳ |
| Price forecasting | ⏳ |
| Review analysis | ⏳ |
| Anomaly detection | ⏳ |

---

## Созданные файлы (Sprint 3-4)

### Scrapers Module

```
backend/app/scrapers/
├── __init__.py          # Factory function, exports
├── base.py              # BaseScraper, PlaywrightScraper
├── ozon.py              # OzonScraper (Playwright-based)
└── wildberries.py       # WildberriesScraper (API-based)
```

### Schemas Module

```
backend/app/schemas/
├── __init__.py          # All schema exports
└── product.py           # ProductCreate, ProductResponse, etc.
```

### Tests

```
backend/tests/test_scrapers/
├── __init__.py
├── conftest.py          # Test fixtures
├── test_base.py         # BaseScraper tests
└── test_wildberries.py  # WildberriesScraper tests
```

---

## Использование скрейперов

### Пример: поиск на Wildberries

```python
from app.scrapers import get_scraper

async def search_products():
    async with get_scraper("wildberries") as scraper:
        products = await scraper.search("iphone 15", page=1)
        for p in products:
            print(f"{p.title}: {p.current_price} ₽")
```

### Пример: поиск на Ozon

```python
from app.scrapers import OzonScraper

async def search_ozon():
    async with OzonScraper(proxy_url="http://proxy:8080") as scraper:
        products = await scraper.search("ноутбук", page=1)
        return products
```

### Пример: поиск по всем маркетплейсам

```python
from app.scrapers import search_all_marketplaces

async def search_everywhere():
    results = await search_all_marketplaces("iphone 15")
    for marketplace, products in results.items():
        print(f"{marketplace}: {len(products)} товаров")
```

---

## Следующие шаги

1. **Celery Tasks** (`backend/app/tasks/scraping.py`)
   - Фоновое обновление цен
   - Периодический скрапинг категорий

2. **Search Service** (`backend/app/services/search_service.py`)
   - PostgreSQL full-text search
   - Фасетный поиск

3. **Vector Search** (`backend/app/services/vector_search.py`)
   - Qdrant integration
   - Embeddings indexing

4. **Yandex.Market Scraper** (`backend/app/scrapers/yandex_market.py`)

---

## Зависимости для скрейперов

```toml
# pyproject.toml additions
[project.dependencies]
httpx = ">=0.27.0"
playwright = ">=1.40.0"
selectolax = ">=0.3.17"
tenacity = ">=8.2.0"

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
]
```

Установка Playwright браузеров:
```bash
playwright install chromium
```
