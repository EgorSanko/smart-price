# Gotchas (известные грабли)

Каждая запись: **симптом** → **причина** → **фикс**. Все проверены в боевых условиях.

---

## 1. styled-jsx `<style jsx global>` + early return
**Симптом:** CSS-анимация на странице `/product` в loading-состоянии пропадает; скелетон показывается без движения.

**Причина:** компонент содержал `if (loading) return <Loader/>` ДО основного `return`, а `<style jsx global>{…}</style>` был объявлен только в основном return. styled-jsx компилирует стили локально к тому JSX-дереву, в котором они находятся — early-return-ветка их не видит.

**Фикс:** обернуть early-return во Fragment и положить внутрь свой блок стилей:
```tsx
if (loading) return (
  <>
    <style jsx global>{`@keyframes spGlowPulse{…} .sp-loader-orbit{…}`}</style>
    <div className="sp-loader-…">…</div>
  </>
)
```
**Правило:** если у страницы есть animating loader и `<style jsx global>` в main return — продублировать в loading-return.

---

## 2. Docker `.env` не монтируется — впекается
**Симптом:** поменял `OPENROUTER_API_KEY`/`DATABASE_URL` в `/opt/smart-price/backend/.env`, перезапустил контейнер — старое значение.

**Причина:** в `backend/Dockerfile`: `COPY .env /app/.env`. Volume-маунта для `.env` в compose нет.

**Фикс:** `docker compose build sp_backend sp_celery && docker compose up -d sp_backend sp_celery`.
Никаких `docker restart` — не перечитает.

---

## 3. Bind-mount trap на фронте
**Симптом:** после деплоя сайт отдаёт дефолтный nginx 404 на все URL; в логах nginx 200, но тело пустое/дефолт.

**Причина:** кто-то сделал `rm -rf /opt/smart-price/frontend/out/`. Bind-mount `out → /usr/share/nginx/html` остался висеть на удалённом inode; новые файлы пишутся в «другой» out, контейнер видит пустоту.

**Фикс:** `docker restart sp_nginx` **после** того, как out/ снова существует с файлами.
**Профилактика:** деплой только через `tar -xf` поверх, никогда rm -rf.

---

## 4. OpenRouter гео-блок
**Симптом:** локально AI работает, на VPS — 403/451 от OpenRouter.

**Причина:** OpenRouter по региону может резать некоторые модели для RU IP.

**Фикс:**
- Использовать `google/gemini-2.5-flash` (чаще всего доступна)
- Задать в OpenRouter ключе приоритет провайдеров
- Передавать заголовки `HTTP-Referer: https://smrt-price.ru`, `X-Title: Smart Price`

---

## 5. Wildberries rate-limit
**Симптом:** первый запрос ок, второй — 429 с `X-Ratelimit-Retry`.

**Причина:** IP-based лимит на `search.wb.ru`.

**Фикс:** 1–2 сек delay между запросами, версия API меняется (пробовать v17/v18/v19), ретраи с экспонентой.

---

## 6. Яндекс Маркет капча
**Симптом:** HTML возвращается, но вместо результатов — капча.

**Фикс:** ротация UA, `sec-ch-ua-*` заголовки, при провале — skip, пометить `source_error`.

---

## 7. Яндекс Маркет — правописание
**Писать** «**Яндекс Маркет**» (без точки, с пробелом). Так на официальном сайте и в бренд-гайде. В дипломе была ошибка «Яндекс.Маркет» — исправлено скриптом `_patch_diploma.py`.

---

## 8. SQLite compat (локалка)
**Симптом:** локальные тесты падают на `JSONB`/`ARRAY`.

**Фикс:** `backend/app/db/session.py` патчит типы: JSONB→JSON, ARRAY→TEXT. Не удалять эти патчи.

---

## 9. Windows-окружение
- **НИКОГДА** `taskkill`/`kill` в bash на Windows в Claude Code — убивает сам Claude Code.
- Пути с forward-slash, `NUL` → `/dev/null`.
