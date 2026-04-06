# Smart Price — Code Review Report

**Дата:** 2026-03-18
**Ревьюер:** Claude Code (Tech Lead mode)

## Summary

- **Критических багов (P0):** 5
- **Серьёзных (P1):** 7
- **Мелких (P2):** 8
- **Предложений по улучшению (P3):** 6

---

## Критические баги (P0 — исправить немедленно)

### BUG-001: Картинки не проксируются в chat.tsx и compare.tsx
- **Файлы:** `frontend/src/app/chat/page.tsx:187`, `frontend/src/app/compare/page.tsx:183,247`
- **Проблема:** Прямые URL картинок (hotlink) — WB/Yandex блокируют
- **Фикс:** Заменить `product.image` на `proxyImage(product.image)`

### BUG-002: func.now() вместо datetime в моделях
- **Файлы:** `backend/app/db/models/scraping_job.py:122,129,135`, `backend/app/db/models/user.py:145`
- **Проблема:** `func.now()` — SQL expression, не Python datetime. Падает при прямом присвоении
- **Фикс:** `datetime.now(timezone.utc)`

### BUG-003: Нет проверки API ключа перед созданием Claude клиента
- **Файлы:** `backend/app/agents/base_agent.py:18`, `backend/app/api/v1/endpoints/compare.py:96`
- **Проблема:** `AsyncAnthropic(api_key=None)` — падает при первом вызове
- **Фикс:** Проверка `if not settings.ANTHROPIC_API_KEY: raise`

### BUG-004: Swallowed exceptions в scrapers — молчаливые ошибки
- **Файл:** `backend/app/api/v1/endpoints/search_stream.py:40-41`
- **Проблема:** `except Exception: return []` — ошибки глотаются без логирования
- **Фикс:** Добавить `logger.error()`

### BUG-005: .env с секретами потенциально в git
- **Файлы:** `backend/.env`, `.env`
- **Проблема:** Пароли и ключи в .env файлах
- **Статус:** Dev-окружение, не продакшн — P2 по факту

---

## Серьёзные баги (P1 — исправить сегодня)

### BUG-006: React keys используют array index
- **Файлы:** `page.tsx:279`, `chat/page.tsx:140,176`, `compare/page.tsx:173,237`
- **Проблема:** `key={idx}` при сортировке — React теряет state
- **Фикс:** Использовать `product.url` как ключ

### BUG-007: Нет alt текста на картинках
- **Файлы:** `page.tsx:236,286`, `chat/page.tsx:187`, `compare/page.tsx:183,247`
- **Проблема:** `alt=""` — accessibility issue
- **Фикс:** `alt={product.title}`

### BUG-008: Задачи не отменяются при закрытии SSE
- **Файл:** `backend/app/api/v1/endpoints/search_stream.py:64`
- **Проблема:** `asyncio.create_task()` без отмены при disconnect
- **Фикс:** Добавить finally блок с task.cancel()

### BUG-009: Хардкоженная модель Claude
- **Файлы:** `backend/app/agents/base_agent.py:19`, `compare.py:98`
- **Проблема:** `model="claude-haiku-4-5-20251001"` — не конфигурируется
- **Фикс:** Вынести в config.py

### BUG-010: selectin lazy loading на Product relationships
- **Файл:** `backend/app/db/models/product.py:218-240`
- **Проблема:** `lazy="selectin"` для price_history загружает ВСЮ историю
- **Фикс:** Использовать `lazy="select"` или `lazy="raise"`

### BUG-011: Дублирование типа Product (frontend)
- **Файлы:** `frontend/src/lib/api.ts` vs `frontend/src/types/index.ts`
- **Проблема:** Два разных интерфейса Product с разными полями

### BUG-012: Неполная реализация alert conditions
- **Файл:** `backend/app/db/models/alert.py:185-192`
- **Проблема:** DROP_PERCENT и ANY_CHANGE не реализованы

---

## Мелкие баги (P2)

| # | Описание | Файл |
|---|----------|------|
| BUG-013 | Image search endpoint — заглушка без 501 | search.py:156 |
| BUG-014 | Missing health checks (Redis, Qdrant) | health.py:96 |
| BUG-015 | `any` тип в FilterPanel | FilterPanel.tsx:15 |
| BUG-016 | Нет логирования в deps.py except | deps.py:37 |
| BUG-017 | httpx AsyncClient создаётся каждый раз | onliner.py:73 |
| BUG-018 | Нет fallback placeholder для битых картинок | page.tsx |
| BUG-019 | Chat error state не визуально отличается | chat/page.tsx |
| BUG-020 | Dockerfile нет version pinning | Dockerfile |

---

## Предложения по улучшению (P3)

| # | Описание |
|---|----------|
| IMP-001 | Добавить rate limiting на API endpoints |
| IMP-002 | Добавить in-memory кэш с TTL для image proxy |
| IMP-003 | Mobile responsive тестирование |
| IMP-004 | Добавить pytest coverage для agents |
| IMP-005 | Вынести SECRET_KEY в required field |
| IMP-006 | Добавить timeout на fetch в frontend |

---

## Результаты исправлений

| # | Приоритет | Описание | Статус |
|---|-----------|----------|--------|
| BUG-001 | P0 | Картинки в chat/compare не проксируются | ✅ Fixed |
| BUG-002 | P0 | func.now() в моделях (scraping_job + user) | ✅ Fixed |
| BUG-003 | P0 | API key validation (base_agent + compare) | ✅ Fixed |
| BUG-004 | P0 | Swallowed exceptions — добавлен logger.error | ✅ Fixed |
| BUG-006 | P1 | React keys | ✅ Fixed |
| BUG-007 | P1 | Alt текст на картинках | ✅ Fixed |
| BUG-008 | P1 | Task cancellation при disconnect SSE | ✅ Fixed |
| BUG-009 | P1 | Хардкоженная модель → config.CLAUDE_MODEL | ✅ Fixed |
| BUG-018 | P2 | Image fallback onError | ✅ Fixed |
