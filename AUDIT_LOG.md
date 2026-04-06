# AUDIT LOG — Smart Price Project

> Создан: 2026-03-18
> Автор: Claude (архитектор проекта)

---

## ФАЗА 0: ПОЛНЫЙ АУДИТ

### 0.1 Общее состояние проекта

**КРИТИЧЕСКАЯ НАХОДКА:** В проекте существуют ДВА отдельных бэкенда:

1. **`smart_price_api.py`** (корень) — Flask-монолит (~37KB, 936 строк)
   - Реально работающий API на порту 5000
   - SQLite для истории цен
   - Парсеры: Onliner (BY), Yandex Market (RU)
   - AI-агент ЕГОРУШКА через Claude Haiku
   - SSE streaming для поиска и чата
   - **Фронтенд подключён к ЭТОМУ API**

2. **`backend/`** — FastAPI модульная архитектура
   - Правильная структура (models, services, API, scrapers)
   - SQLAlchemy 2.0 Mapped стиль
   - PostgreSQL + Redis + Qdrant + ClickHouse
   - Scrapers: Ozon, Wildberries, Yandex Market
   - **Но многое НЕ реализовано** (AI агенты, Celery задачи, семантический поиск)

**РЕШЕНИЕ:** Перенести всю логику из Flask-монолита в FastAPI backend, затем удалить монолит.

### 0.2 Структура корня проекта

#### ❌ Мусорные файлы (подлежат удалению):
- 25+ файлов `smart_price_api_v*.py` — старые версии API
- 15+ файлов `debug_*.py` — дебаг-скрипты
- 10+ файлов `test_*.py` (в корне) — ad-hoc тесты
- 7+ файлов `*.html` — дампы страниц (citilink, dns, ozon, wb, yandex, ekatalog)
- `*.json` — дампы данных (all_products, search_results, smart_price_results, wb_products)
- `*.py` скрипты: check_*, scrape_*, wb_api, smart_search, smart_price_scraper/final
- `price_history.db` — SQLite БД (перенести данные в PostgreSQL)
- `create_inits.ps1`, `organize_project.ps1` — одноразовые скрипты

#### ✅ Нужные корневые файлы:
- `.env` — переменные окружения
- `.gitignore` — правила игнорирования
- `.pre-commit-config.yaml` — хуки
- `README.md` — документация

### 0.3 Backend (`backend/`)

#### ✅ Работает и актуально:
- `app/db/base.py` — Base класс с миксинами (отлично)
- `app/db/models/product.py` — модель товара (GIN индекс, Mapped стиль)
- `app/db/models/marketplace.py` — маркетплейсы
- `app/db/models/category.py` — категории (иерархия)
- `app/db/models/price_history.py` — история цен
- `app/db/models/product_match.py` — сопоставление товаров
- `app/db/models/user.py` — пользователи
- `app/schemas/product.py` — Pydantic схемы (отлично)
- `app/schemas/search.py` — схемы поиска
- `app/services/product_service.py` — CRUD сервис (отлично)
- `app/api/v1/endpoints/products.py` — CRUD эндпоинты
- `app/api/v1/endpoints/health.py` — health checks
- `app/api/v1/deps.py` — зависимости
- `app/core/exceptions.py` — иерархия исключений
- `app/scrapers/base.py` — базовый класс парсера (anti-detection)
- `app/scrapers/wildberries.py` — WB парсер через API
- `app/scrapers/utils.py` — утилиты парсинга
- `app/scrapers/antidetect.py` — anti-detection система
- `app/main.py` — FastAPI app factory
- `alembic/` — миграции

#### ⚠️ Работает, но нужно улучшить:
- `app/db/models/alert.py` — check_condition() не реализован
- `app/db/session.py` — хрупкая проверка SQLite
- `app/services/search_service.py` — только keyword search, нет semantic/hybrid
- `app/api/v1/endpoints/search.py` — image search заглушка
- `app/scrapers/ozon.py` — не полностью проверен
- `app/ml/` — частичные реализации (embeddings, matcher, qdrant_service)
- `pyproject.toml` — не хватает scrapling в зависимостях

#### ❌ Сломано или отсутствует:
- `app/config.py` — ДУБЛИКАТ `app/core/config.py` (конфликт!)
- `app/scrapers/browserless_scrapers.py` — дубликат WB парсера
- AI агенты — полностью отсутствуют
- Chat endpoint — отсутствует
- Celery задачи — отсутствуют
- Парсер Onliner — отсутствует (есть только в Flask-монолите)
- Парсер AliExpress — отсутствует
- Парсер СберМегаМаркет — отсутствует

#### 🆕 Нужно создать:
- `app/agents/` — AI агенты (shopping, comparison, review, forecast)
- `app/api/v1/endpoints/chat.py` — SSE чат
- `app/scrapers/parsers/onliner.py` — Onliner парсер
- `app/scrapers/engines/` — движки парсинга (httpx, scrapling, firecrawl)
- `backend/scripts/run_dev.py` — локальный запуск
- `backend/scripts/seed_data.py` — обновить

### 0.4 Frontend (`frontend/`)

#### ✅ Работает:
- Next.js 14 App Router + TypeScript strict
- Tailwind CSS с темной темой (отличная цветовая схема)
- `page.tsx` — поиск с SSE streaming
- `chat/page.tsx` — AI чат
- `about/page.tsx` — о проекте
- `docs/page.tsx` — документация
- `lib/api.ts` — API клиент (SSE)
- `lib/utils.ts` — утилиты
- `components/product/ProductCard.tsx` — карточка товара

#### ⚠️ Проблемы:
- `var(--c3)` в chat/page.tsx — не определена в CSS
- ProductCard не используется на странице поиска
- FilterPanel не используется
- Header.tsx не интегрирован
- Дублирование интерфейса Product (api.ts vs types/index.ts)
- API URL хардкодит VPS (81.17.154.4:5000)
- Неиспользуемые зависимости: React Query, Zustand, recharts, clsx, tailwind-merge

#### 🆕 Отсутствуют:
- `product/[id]/page.tsx` — карточка товара
- `compare/page.tsx` — сравнение
- `dashboard/page.tsx` — аналитика
- `alerts/page.tsx` — уведомления
- Error boundaries

### 0.5 Docker (`docker/`)

#### ✅ Работает:
- `docker-compose.dev.yml` — полный стек (7 сервисов)
- PostgreSQL 16 + Redis 7 + Qdrant + ClickHouse + Browserless
- Celery worker + beat
- Правильные volumes и healthchecks

### 0.6 Зависимости

#### Backend:
- **КРИТИЧНО:** `scrapling` импортируется но НЕ указан в pyproject.toml
- `anthropic` версия устарела (>=0.18.0, нужно >=0.40.0)
- `firecrawl-py` отсутствует
- `pydantic-settings` отсутствует отдельно (включён в pydantic)

#### Frontend:
- 6 неиспользуемых пакетов (~25% deps)
- Можно удалить: @tanstack/react-query, @tanstack/react-query-devtools, zustand, clsx, tailwind-merge (если не нужен)

---

## ПЛАН ДЕЙСТВИЙ И СТАТУС

### Фаза 0: Аудит ✅ ЗАВЕРШЕН
- [x] Полное сканирование структуры — 120+ файлов проверено
- [x] AUDIT_LOG.md создан
- [x] Зависимости проверены
- Найдено: два бэкенда (Flask монолит + FastAPI), мусор в корне, дубликат конфига

### Фаза 1: Инфраструктура ✅ ЗАВЕРШЕНА
- [x] Устранён дубликат конфигов (app/core/config.py → реэкспорт из app/config.py)
- [x] app/config.py обновлён (добавлены: ENVIRONMENT, LOG_LEVEL, CELERY_*, FIRECRAWL_API_KEY, SCRAPING_*)
- [x] pyproject.toml обновлён (scrapling/firecrawl/playwright в optional [scraping], anthropic >=0.40.0)
- [x] .env.example обновлён со всеми переменными
- [x] scripts/run_dev.py создан (SQLite fallback для локальной разработки)

### Фаза 2: База данных ✅ ЗАВЕРШЕНА
- [x] Модели проверены — уже в Mapped стиле ✅
- [x] ChatSession, ChatMessage модели созданы (с MessageRole enum, JSONB products/tool_calls)
- [x] ScrapingJob модель создана (с JobStatus enum, lifecycle методы mark_running/completed/failed)
- [x] models/__init__.py обновлён (11 моделей экспортируется)
- [ ] Обновить Alembic миграции (при подключении к PostgreSQL)

### Фаза 3: Система парсинга ✅ ЗАВЕРШЕНА
- [x] Onliner парсер создан (standalone httpx, 35 результатов протестировано)
- [x] Yandex Market парсер создан (HTML regex parsing)
- [x] ScrapingManager создан (параллельный поиск по маркетплейсам)
- [x] scrapers/__init__.py переписан с lazy imports (без scrapling зависимости при старте)
- [x] Wildberries и Ozon парсеры — оставлены как есть (требуют scrapling)

### Фаза 4: AI Агенты ✅ ЗАВЕРШЕНА
- [x] BaseAgent создан (Anthropic SDK, tool_use + streaming)
- [x] ShoppingAgent (ЕГОРУШКА) создан с search_products tool
- [x] Compare agent создан (AI сравнение через SSE)

### Фаза 5: API Endpoints ✅ ЗАВЕРШЕНА
- [x] POST /api/v1/chat — AI чат с SSE (формат совместим с фронтендом)
- [x] GET /api/v1/live-search/stream — SSE поиск по маркетплейсам
- [x] POST /api/v1/ai/compare — AI сравнение товаров
- [x] Все 20 роутов зарегистрированы и работают

### Фаза 6: Frontend ✅ ЗАВЕРШЕНА
- [x] CSS баг исправлен (var(--c3) → var(--bl))
- [x] API клиент обновлён для FastAPI (новые URL пути)
- [x] API URL по умолчанию: localhost:8000
- [x] Header компонент обновлён (иконки, активная ссылка, мобильное меню)
- [x] Устранён дублирующийся header (pages → shared layout)
- [x] /compare — страница сравнения товаров (поиск + выбор + AI анализ)
- [x] Все 8 страниц собираются (Next.js build: 0 ошибок)
- [ ] product/[id] — оставлена на будущее (требует данные из БД)

### Фаза 7: Сервисы ✅ ЗАВЕРШЕНА
- [x] ProductService — полный CRUD + price history + upsert (уже был готов)
- [x] SearchService — full-text PostgreSQL search + facets + autocomplete (уже был готов)
- [x] AnalyticsService — создан (tracking scraping jobs, статистика по маркетплейсам)

### Фаза 8: Тесты ✅ ЗАВЕРШЕНА
- [x] conftest.py — SQLite in-memory с JSONB/ARRAY компатибильностью
- [x] 34 теста: все проходят
  - test_config (4) — настройки, реэкспорт, CORS
  - test_api/test_health (5) — health, liveness, docs, openapi
  - test_api/test_parsers (4) — список, структура, регионы, enabled
  - test_api/test_products (3) — список, создание, 404
  - test_models/test_chat (4) — сессии, сообщения, связи, enum
  - test_models/test_scraping_job (5) — создание, transitions, failure, metadata
  - test_scrapers/test_onliner (3) — импорт, mock search, empty results
  - test_scrapers/test_manager (6) — импорт, регистр, фильтр, сортировка, max_price

### Фаза 9-10: Деплой, документация ⏳ ВПЕРЕДИ
