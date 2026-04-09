# Smart Price — AI Price Aggregator

## What is this project
AI-powered meta-search for comparing product prices across Belarusian (Onliner.by) and Russian (Yandex Market, Wildberries, Ozon) marketplaces. Diploma project.

## Tech Stack
- **Backend:** Python 3.14, FastAPI, SQLAlchemy 2.0 async (Mapped[]), Pydantic v2, structlog
- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS, lucide-react
- **AI:** Anthropic Claude API (tool_use pattern, SSE streaming)
- **DB:** PostgreSQL (prod) / SQLite+aiosqlite (local dev), Redis (cache)
- **Scraping:** httpx (API-based), Scrapling (browser stealth + anti-detection), curl_cffi (TLS fingerprinting), Firecrawl (HTML→Markdown for AI)

## Project Structure
```
backend/app/
  main.py              # FastAPI app with lifespan
  config.py            # pydantic-settings, env vars
  api/v1/endpoints/    # search_stream.py (SSE), chat.py, compare.py, health.py
  db/models/           # SQLAlchemy 2.0 Mapped[] models (11 models)
  scrapers/            # onliner.py, yandex_market.py, wildberries.py, manager.py
  agents/              # base_agent.py, shopping_agent.py (ЕГОРУШКА)

frontend/src/
  app/page.tsx         # Home — search with SSE streaming
  app/chat/page.tsx    # AI chat assistant
  app/compare/page.tsx # Product comparison with AI
  lib/api.ts           # API client (SSE, fetch)
  components/layout/   # Header.tsx, Footer.tsx
```

## Running Locally
```bash
# Backend (uses SQLite locally)
cd backend && python -m uvicorn app.main:app --port 8000 --reload

# Frontend
cd frontend && npm run dev  # port 3000
```
- Backend .env: `DATABASE_URL=sqlite+aiosqlite:///./smartprice.db`
- Frontend .env.local: `NEXT_PUBLIC_API_URL=http://localhost:8000`

## Marketplace Scrapers

### Onliner.by (BY) — WORKING
- API: `https://catalog.onliner.by/sdapi/catalog.api/search/products?query={q}`
- Positions: `https://catalog.onliner.by/sdapi/catalog.api/products/{key}/positions`
- Public JSON API, no anti-bot, ~22 results typical
- Currency: BYN

### Yandex Market (RU) — PARTIAL
- HTML parsing with regex, captcha on repeated requests
- Improved headers with UA rotation, sec-ch-ua
- Currency: RUB

### Wildberries (RU) — WORKING (v18 API)
- API: `https://search.wb.ru/exactmatch/ru/common/v18/search` (version changes over time, try v17-v19)
- Params: appType=1, curr=rub, dest=-1257786, lang=ru, query={q}, resultset=catalog, sort=popular, spp=30
- Prices: in `sizes[0].price.product` (kopecks, divide by 100) or `salePriceU`
- Rate limit: 429 with X-Ratelimit-Retry header. Need 1-2s delay between requests
- Currency: RUB
- IMPORTANT: IP-based rate limiting. First request works, subsequent need delays

### Ozon (RU) — API + Playwright fallback
- JSON API: `https://www.ozon.ru/api/entrypoint-api.bx/page/json/v2?url=/search/?text={q}`
- Products in response.widgetStates["searchResultsV2-*"] (JSON string with items[])
- Cloudflare blocks after repeated requests
- Playwright fallback extracts data-state JSON from rendered page
- Currency: RUB

## SSE Search Flow
1. Frontend calls `GET /api/v1/live-search/stream?q={query}&region={BY|RU|all}`
2. Backend sends SSE events: `start` → `parsing` (per marketplace) → `done` (per marketplace) → `complete` (all results)
3. Region mapping: BY→[onliner], RU→[yandex, wildberries, ozon], all→[all four]

## Code Conventions
- Always async/await for I/O
- Type hints: `list[str]`, `str | None` (modern syntax)
- SQLAlchemy: `Mapped[]` style, not legacy `Column()`
- Logging: structlog, never print()
- Scrapers return `list[dict]` with keys: title, price, price_num, url, marketplace, image, shop, specs, category, onliner_key
- SQLite compatibility: JSONB→JSON, ARRAY→TEXT (patched in session.py)

## VPS Deployment
- IP: 81.17.154.4
- Path: /root/leadseek-app/ (shared infra)
- Docker compose for production

## Key Files to Know
- `backend/app/api/v1/endpoints/search_stream.py` — Main search SSE endpoint
- `backend/app/scrapers/manager.py` — Marketplace registry + parallel search
- `backend/app/scrapers/onliner.py` — Working scraper (reference implementation)
- `frontend/src/app/page.tsx` — Main search UI
- `frontend/src/lib/api.ts` — API client with SSE support

<!-- code-review-graph MCP tools -->
## MCP Tools: code-review-graph

**IMPORTANT: This project has a knowledge graph. ALWAYS use the
code-review-graph MCP tools BEFORE using Grep/Glob/Read to explore
the codebase.** The graph is faster, cheaper (fewer tokens), and gives
you structural context (callers, dependents, test coverage) that file
scanning cannot.

### When to use graph tools FIRST

- **Exploring code**: `semantic_search_nodes` or `query_graph` instead of Grep
- **Understanding impact**: `get_impact_radius` instead of manually tracing imports
- **Code review**: `detect_changes` + `get_review_context` instead of reading entire files
- **Finding relationships**: `query_graph` with callers_of/callees_of/imports_of/tests_for
- **Architecture questions**: `get_architecture_overview` + `list_communities`

Fall back to Grep/Glob/Read **only** when the graph doesn't cover what you need.

### Key Tools

| Tool | Use when |
|------|----------|
| `detect_changes` | Reviewing code changes — gives risk-scored analysis |
| `get_review_context` | Need source snippets for review — token-efficient |
| `get_impact_radius` | Understanding blast radius of a change |
| `get_affected_flows` | Finding which execution paths are impacted |
| `query_graph` | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes` | Finding functions/classes by name or keyword |
| `get_architecture_overview` | Understanding high-level codebase structure |
| `refactor_tool` | Planning renames, finding dead code |

### Workflow

1. The graph auto-updates on file changes (via hooks).
2. Use `detect_changes` for code review.
3. Use `get_affected_flows` to understand impact.
4. Use `query_graph` pattern="tests_for" to check coverage.
