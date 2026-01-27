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
│   │   │   ├── __init__.py           # ✅ Package exports
│   │   │   ├── base.py               # ✅ SQLAlchemy Base class
│   │   │   ├── session.py            # ✅ Async session factory
│   │   │   └── models/
│   │   │       ├── __init__.py       # ✅ Export all models
│   │   │       ├── marketplace.py    # ✅ Marketplace model
│   │   │       ├── category.py       # ✅ Category model
│   │   │       ├── product.py        # ✅ Product model
│   │   │       ├── price_history.py  # ✅ PriceHistory model
│   │   │       ├── product_match.py  # ✅ ProductMatch model
│   │   │       ├── user.py           # ✅ User model
│   │   │       └── alert.py          # ✅ PriceAlert, SearchHistory
│   │   │
│   │   ├── schemas/                  # Pydantic Schemas
│   │   │   ├── __init__.py
│   │   │   ├── product.py            # Product schemas
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
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # BaseScraper abstract class
│   │   │   ├── ozon.py               # Ozon scraper
│   │   │   ├── wildberries.py        # Wildberries scraper
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
│   │   └── test_services/
│   │       ├── __init__.py
│   │       └── test_product_service.py
│   │
│   ├── alembic/                      # Database Migrations
│   │   ├── env.py                    # ✅ Async migration env
│   │   ├── script.py.mako            # ✅ Migration template
│   │   ├── README                    # ✅ Migration docs
│   │   └── versions/
│   │       └── 001_initial_schema.py # ✅ Initial migration
│   │
│   ├── alembic.ini                   # ✅ Alembic config
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

### Sprint 1: Project Setup ✅

| Компонент | Статус | Файл |
|-----------|--------|------|
| pyproject.toml | ✅ | `backend/pyproject.toml` |
| docker-compose.dev.yml | ✅ | `docker/docker-compose.dev.yml` |
| config.py | ✅ | `backend/app/config.py` |
| main.py | ✅ | `backend/app/main.py` |

### Sprint 2: Database Models ✅

| Компонент | Статус | Файл |
|-----------|--------|------|
| db/base.py | ✅ | `backend/app/db/base.py` |
| db/session.py | ✅ | `backend/app/db/session.py` |
| db/__init__.py | ✅ | `backend/app/db/__init__.py` |
| models/marketplace.py | ✅ | `backend/app/db/models/marketplace.py` |
| models/category.py | ✅ | `backend/app/db/models/category.py` |
| models/product.py | ✅ | `backend/app/db/models/product.py` |
| models/price_history.py | ✅ | `backend/app/db/models/price_history.py` |
| models/product_match.py | ✅ | `backend/app/db/models/product_match.py` |
| models/user.py | ✅ | `backend/app/db/models/user.py` |
| models/alert.py | ✅ | `backend/app/db/models/alert.py` |
| models/__init__.py | ✅ | `backend/app/db/models/__init__.py` |
| alembic.ini | ✅ | `backend/alembic.ini` |
| alembic/env.py | ✅ | `backend/alembic/env.py` |
| alembic/script.py.mako | ✅ | `backend/alembic/script.py.mako` |
| Initial migration | ✅ | `backend/alembic/versions/001_initial_schema.py` |

### Sprint 3: Scrapers & Celery ⏳

| Компонент | Статус |
|-----------|--------|
| scrapers/base.py | ⏳ |
| scrapers/ozon.py | ⏳ |
| scrapers/wildberries.py | ⏳ |
| Celery tasks | ⏳ |

### Sprint 4: Search & API ⏳

| Компонент | Статус |
|-----------|--------|
| Full-text search | ⏳ |
| Qdrant integration | ⏳ |
| Hybrid search | ⏳ |
| API endpoints | ⏳ |

---

## Модели БД — ERD

```
┌───────────────────┐       ┌───────────────────┐
│   Marketplace     │       │     Category      │
├───────────────────┤       ├───────────────────┤
│ id                │       │ id                │
│ name (unique)     │       │ name              │
│ display_name      │       │ slug (unique)     │
│ base_url          │       │ parent_id ────────┼──┐
│ is_active         │       │ level             │  │
│ config (JSONB)    │       │ description       │  │
└─────────┬─────────┘       └─────────┬─────────┘  │
          │                           │            │
          │ 1:N                       │ 1:N        │ self-ref
          ▼                           ▼            │
┌───────────────────────────────────────────────┐  │
│                   Product                      │◄─┘
├───────────────────────────────────────────────┤
│ id                                             │
│ external_id                                    │
│ marketplace_id ─────────────────────────────►  │
│ title                                          │
│ description                                    │
│ brand                                          │
│ category_id ────────────────────────────────►  │
│ current_price                                  │
│ original_price                                 │
│ url, image_url, images[]                       │
│ rating, reviews_count                          │
│ specs (JSONB)                                  │
│ is_available                                   │
│ seller_name, seller_rating                     │
│ barcode                                        │
│ last_scraped_at                                │
└──────────┬────────────────────────────────────┘
           │
           │ 1:N                    1:N
           ▼                         │
┌───────────────────┐    ┌───────────────────────┐
│   PriceHistory    │    │    ProductMatch       │
├───────────────────┤    ├───────────────────────┤
│ id                │    │ id                    │
│ product_id ◄──────┤    │ canonical_product_id  │
│ price             │    │ matched_product_id    │
│ original_price    │    │ confidence_score      │
│ currency          │    │ match_method          │
│ recorded_at       │    │ verified              │
└───────────────────┘    └───────────────────────┘

┌───────────────────┐       ┌───────────────────┐
│       User        │       │    PriceAlert     │
├───────────────────┤       ├───────────────────┤
│ id                │       │ id                │
│ email (unique)    │──1:N──│ user_id ◄─────────┤
│ hashed_password   │       │ product_id ◄──────┤
│ is_active         │       │ target_price      │
│ is_verified       │       │ alert_type        │
│ is_superuser      │       │ status            │
│ full_name         │       │ triggered_at      │
│ oauth_provider    │       └───────────────────┘
│ oauth_id          │
│ last_login_at     │       ┌───────────────────┐
└─────────┬─────────┘       │  SearchHistory    │
          │                 ├───────────────────┤
          │ 1:N             │ id                │
          └────────────────►│ user_id           │
                            │ query             │
                            │ filters (JSONB)   │
                            │ results_count     │
                            │ session_id        │
                            │ clicked_product_id│
                            └───────────────────┘
```

---

## Команды для работы с миграциями

```bash
# Применить все миграции
docker exec smart_price_backend alembic upgrade head

# Создать новую миграцию
docker exec smart_price_backend alembic revision --autogenerate -m "description"

# Откатить последнюю миграцию
docker exec smart_price_backend alembic downgrade -1

# Посмотреть текущую версию
docker exec smart_price_backend alembic current

# История миграций
docker exec smart_price_backend alembic history --verbose
```

---

## Следующие шаги

### Sprint 3: Scrapers & Celery
- [ ] `scrapers/base.py` — Базовый класс парсера
- [ ] `scrapers/ozon.py` — Парсер Ozon
- [ ] `scrapers/wildberries.py` — Парсер Wildberries
- [ ] Celery конфигурация
- [ ] Задачи для фонового парсинга

### Sprint 4: Search & API
- [ ] `services/search_service.py` — Full-text search
- [ ] Qdrant интеграция — Vector search
- [ ] `services/hybrid_search.py` — Комбинированный поиск
- [ ] API endpoints для поиска и товаров
