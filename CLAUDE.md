# Smart Price — AI Price Aggregator

AI-powered meta-search сравнения цен по BY/RU маркетплейсам. Дипломный проект.

> **Obsidian-vault:** навигация и глубокий контекст — в `docs/`. Здесь только то, что должно автоматически грузиться в контекст Claude Code.

## Стек (актуально)
- **Backend:** Python **3.11**, FastAPI, SQLAlchemy 2.0 async (Mapped[]), asyncpg, Alembic, Pydantic v2, Celery, structlog
- **Frontend:** Next.js 14 App Router, TypeScript, Tailwind, zustand, @tanstack/react-query, lucide-react
- **AI:** **Gemini 2.5 Flash через OpenRouter** (`google/gemini-2.5-flash`). НЕ Anthropic/Claude.
- **DB/Cache:** PostgreSQL 16 + Redis 7
- **SSE** для live-поиска, **WebSocket reverse** (Алиса) для фичи «Найти дешевле»
- **Docker Compose** на VPS: `sp_nginx`, `sp_backend`, `sp_celery`, `sp_postgres`, `sp_redis`

## VPS (Smart Price ≠ LeadSeek)
- **IP: `5.42.123.75`** (НЕ 81.17.154.4 — это LeadSeek!)
- **Path: `/opt/smart-price/`**
- SSH: `ssh root@5.42.123.75`
- Compose: `/opt/smart-price/docker-compose.yml`
- Домен: `smrt-price.ru`, API: `api.smrt-price.ru`

## Парсеры (5 рабочих)
1. **Onliner.by** — публичный JSON API, без антибота (эталон)
2. **Яндекс Маркет** — HTML+regex, капча на повторах (писать именно «Яндекс Маркет», без точки)
3. **Wildberries** — `search.wb.ru/exactmatch/ru/common/v18/search`, IP rate-limit
4. **Регард** — regard.ru
5. **World Devices** — world-devices by

Ozon/Ситилинк/AliExpress упоминаются только в «перспективах развития». НЕ активны.

## Ключевые фичи
- **Live-search SSE:** `GET /api/v1/live-search/stream?q=&region=BY|RU|all` → `start`/`parsing`/`done`/`complete`
- **«Найти дешевле»** (`/cheaper`): реверс WebSocket Яндекс.Алисы, payload-типы `EAliceOfferCard`/`EAliceOffer`/`EAliceOfferList`. Воркер: `backend/app/workers/alisa.py`
- **AI-чат/анализ** через OpenRouter (Gemini 2.5 Flash)
- **Smart-icons** (`frontend/src/components/smart-icons.tsx`): inline-SVG + CSS keyframes, zero-dep (PriceTagHero, EmptyCart, RollingCart …)

## Deploy (frontend, tar-pipe)
```bash
cd frontend && npm run build   # выхлоп в out/
tar -cf - -C out . | ssh root@5.42.123.75 \
  "cd /opt/smart-price/frontend/out && tar -xf - && docker exec sp_nginx nginx -s reload"
```
⚠️ **НИКОГДА `rm -rf out/`** на VPS — это отвяжет bind-mount у `sp_nginx`, сайт отдаст дефолтный nginx 404 на всех URL.

## Deploy (backend)
Бэкенд-`.env` **ВПЕКАЕТСЯ в образ** (COPY .env /app/.env), а не монтируется. После правки `.env` нужен rebuild:
```bash
ssh root@5.42.123.75 "cd /opt/smart-price && docker compose build sp_backend && docker compose up -d sp_backend"
```

## Код — правила
- async/await для всего I/O, никаких sync-вызовов в хэндлерах
- Type hints: `list[str]`, `str | None`
- SQLAlchemy: только `Mapped[]`, не `Column()`
- Логи: structlog, никогда `print()`
- Scraper-контракт: `list[dict]` с ключами `title, price, price_num, url, marketplace, image, shop, specs, category, onliner_key`
- Конвенциональные коммиты + push origin/main после каждой правки; `git add <files>`, НЕ `git add .`

## Grep-карта (куда сразу идти)
| Нужно | Файл |
|---|---|
| SSE live-search | `backend/app/api/v1/endpoints/search_stream.py` |
| Реестр парсеров | `backend/app/scrapers/manager.py` |
| Эталон-парсер | `backend/app/scrapers/onliner.py` |
| Алиса «дешевле» | `backend/app/workers/alisa.py` |
| Главная/поиск UI | `frontend/src/app/page.tsx` |
| Страница «дешевле» | `frontend/src/app/cheaper/page.tsx` |
| Карточка товара | `frontend/src/app/product/page.tsx` |
| Шапка/авторизация | `frontend/src/components/layout/Header.tsx` |
| API-клиент+SSE | `frontend/src/lib/api.ts` |
| Smart-иконки | `frontend/src/components/smart-icons.tsx` |

## Подводные камни (подробно — `docs/GOTCHAS.md`)
- **styled-jsx + early return:** `<style jsx global>` в main return НЕ рендерится, если компонент вышел через `if (loading) return …`. Оборачивать early-return во Fragment со своим `<style jsx global>`.
- **OpenRouter гео-блок:** VPS в RU иногда режет, использовать модель `google/gemini-2.5-flash` и проверять заголовки.
- **Docker `.env` не mount:** см. выше про rebuild.
- **Bind-mount nginx:** см. выше про `rm -rf out/`.

## Что недавно изменилось
- Удалены разделы **pricing/payment** (страницы, Crown-бейдж, ссылка в dropdown). Dashboard упрощён до профиля + выхода.
- Диплом (`ДИПЛОМ.docx`) обновлён: добавлен раздел 3.13 «Найти дешевле», 5 парсеров, унификация «Яндекс Маркет», RFC 6455 вместо Anthropic в списке литературы.
- Мобильное приложение — **отложено**; решено делать на **Expo/React Native** (см. memory `project_smartprice_mobile_app.md`).

## Навигация по vault
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — модульная карта + data-flow
- [docs/DEPLOY.md](docs/DEPLOY.md) — подробный деплой, nginx, containers
- [docs/GOTCHAS.md](docs/GOTCHAS.md) — все известные грабли с объяснениями
- [docs/TASKS.md](docs/TASKS.md) — текущее состояние + отложенное
- [docs/CHEAPER_FEATURE_ROADMAP.md](docs/CHEAPER_FEATURE_ROADMAP.md) — фаза-план «дешевле»
