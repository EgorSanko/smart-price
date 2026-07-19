# Architecture

## Общая схема
```
Browser ──(HTTPS)──► smrt-price.ru  (sp_nginx → static Next.js из /opt/smart-price/frontend/out)
         ──(HTTPS)──► api.smrt-price.ru (sp_nginx → sp_backend:8000)
                          │
                          ├─► sp_postgres (PG16, users/products/searches/alisa_cache)
                          ├─► sp_redis    (cache + Celery broker)
                          └─► sp_celery   (фоновые воркеры: alisa, ai-анализ, cheaper)
Внешние: OpenRouter (Gemini 2.5 Flash), WS Яндекс.Алиса, onliner.by, wb.ru, market.yandex, regard.ru, world-devices.by
```

## Backend (`backend/app/`)
```
main.py                     # FastAPI + lifespan
config.py                   # pydantic-settings
api/v1/endpoints/
  search_stream.py          # SSE live-search (start/parsing/done/complete)
  chat.py                   # AI-чат (OpenRouter, streaming)
  compare.py                # сравнение 2+ товаров AI
  cheaper.py                # "Найти дешевле"
  auth.py                   # JWT, email/password
  health.py
db/models/                  # SQLAlchemy 2.0 Mapped[]: User, Product, Search, AlisaCache, ChatMessage, Compare, …
db/session.py               # async engine + sqlite-compat patches (JSONB→JSON, ARRAY→TEXT)
scrapers/
  manager.py                # реестр + parallel asyncio.gather
  onliner.py                # эталон
  yandex_market.py
  wildberries.py
  regard.py
  world_devices.py
agents/
  base_agent.py             # OpenRouter wrapper, tool_use-like паттерн
  shopping_agent.py         # "ЕГОРУШКА"
workers/
  alisa.py                  # WS Alisa reverse (EAliceOfferCard/EAliceOffer/EAliceOfferList)
  ai_analyze.py
```

## Frontend (`frontend/src/`)
```
app/
  page.tsx                  # главная: SSE-поиск + RollingCart loader
  product/page.tsx          # карточка товара (сравнение цен, история, AI-анализ)
  compare/page.tsx
  cheaper/page.tsx          # "Найти дешевле" (WS результаты)
  chat/page.tsx             # AI-помощник
  analyze/page.tsx
  catalog/page.tsx
  dashboard/page.tsx        # профиль + logout (pricing удалён)
  login/page.tsx
  about/page.tsx
components/
  layout/Header.tsx         # nav + auth dropdown (Crown удалён)
  layout/Footer.tsx
  smart-icons.tsx           # inline-SVG + CSS-анимации
lib/
  api.ts                    # fetch + SSE (EventSource)
  auth.ts                   # zustand store + JWT в localStorage
  utils.ts
```

## Data flow: live search
1. UI: `EventSource("/api/v1/live-search/stream?q=…&region=all")`
2. `search_stream.py` → `scrapers/manager.py` → `asyncio.gather(*parsers)`
3. Каждый парсер по готовности шлёт `parsing`/`done` SSE
4. По завершении — `complete` с агрегированным массивом
5. UI: zustand-стор, потоковый рендер карточек

## Data flow: «Найти дешевле»
1. UI: POST `/api/v1/cheaper/start` с товаром
2. Celery-таск → `workers/alisa.py` открывает WS Alisa
3. Парсит `EAliceOfferCard` → `EAliceOffer` → `EAliceOfferList.offerList[]`
4. Результаты пишутся в `alisa_cache`, UI поллит/подписан на SSE
5. Подробнее — [CHEAPER_FEATURE_ROADMAP.md](CHEAPER_FEATURE_ROADMAP.md)

## Data flow: AI-чат
1. UI → `POST /api/v1/chat/stream` (SSE)
2. `agents/shopping_agent.py` → OpenRouter `google/gemini-2.5-flash`
3. Tool-use-like шаги: поиск товаров → подстановка в контекст → стрим токенов
