# Deploy

## VPS координаты
- IP: **5.42.123.75** (не путать с 81.17.154.4 — это LeadSeek)
- Path: **/opt/smart-price/**
- SSH: `ssh root@5.42.123.75`
- Домены: `smrt-price.ru` (фронт), `api.smrt-price.ru` (бэк)

## Контейнеры
| Container | Образ | Назначение |
|---|---|---|
| `sp_nginx` | nginx:alpine | отдаёт `out/` и проксирует `/api/*` |
| `sp_backend` | local build | FastAPI:8000 |
| `sp_celery` | local build | воркеры (alisa, ai) |
| `sp_postgres` | postgres:16 | основная БД |
| `sp_redis` | redis:7 | cache + Celery broker |

## Frontend deploy (tar-pipe, быстрый)
```bash
cd C:/Users/egor3/Desktop/smart-price/frontend
npm run build                  # next export → out/
tar -cf - -C out . | ssh root@5.42.123.75 \
  "cd /opt/smart-price/frontend/out && tar -xf - && docker exec sp_nginx nginx -s reload"
```
- `next.config.js` настроен на static export (`output: 'export'`)
- nginx bind-mount: `/opt/smart-price/frontend/out:/usr/share/nginx/html:ro`

### ⚠️ Критично
**НИКОГДА** не делать `rm -rf /opt/smart-price/frontend/out`:
- Docker mount зависнет на удалённом inode, контейнер продолжит видеть пустую директорию
- nginx начнёт отдавать дефолтный 404 на все URL
- Лечится только `docker restart sp_nginx` **после** того как директория снова существует
- Правильно: распаковывать поверх (tar -xf `.` затрёт файлы).

Если очень надо почистить — внутри директории: `cd out && find . -mindepth 1 -delete`.

## Backend deploy (rebuild)
`.env` **впекается** в образ (в Dockerfile: `COPY .env /app/.env`), не монтируется.
После изменений кода или `.env`:
```bash
ssh root@5.42.123.75 "cd /opt/smart-price && \
  git pull && \
  docker compose build sp_backend sp_celery && \
  docker compose up -d sp_backend sp_celery"
```

## Alembic миграции
```bash
ssh root@5.42.123.75 "cd /opt/smart-price && \
  docker compose exec sp_backend alembic upgrade head"
```
Создание миграции — локально против prod-схемы не делать; сделать на локальной Postgres, закоммитить, на VPS — только `upgrade`.

## Логи
```bash
ssh root@5.42.123.75 "docker logs -f --tail=200 sp_backend"
ssh root@5.42.123.75 "docker logs -f --tail=200 sp_celery"
ssh root@5.42.123.75 "docker logs -f --tail=50 sp_nginx"
```

## Откат фронта
Бэкапа нет — полагаемся на `git`. Фикс: `git checkout <прежний sha>` + `npm run build` + tar-pipe.

## Локально
```bash
# backend (SQLite)
cd backend && python -m uvicorn app.main:app --port 8000 --reload
# frontend
cd frontend && npm run dev      # :3000
```
- `backend/.env`: `DATABASE_URL=sqlite+aiosqlite:///./smartprice.db`
- `frontend/.env.local`: `NEXT_PUBLIC_API_URL=http://localhost:8000`
