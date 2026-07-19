# Tasks — текущее состояние

Дата синхронизации: **2026-04-15**.

## ✅ Недавно закрыто
- **Удалены тарифы/платежи** (`/pricing`, `/payment`, Crown-бейдж, ссылка в dropdown). Dashboard упрощён до карточки профиля + logout. Backend `/api/v1/payments/*` пока есть, но не используется (можно удалить позже).
- **Диплом `ДИПЛОМ.docx`** обновлён:
  - добавлен раздел 3.13 «Реализация функции Найти дешевле» (5 подразделов), 3.13 «Выводы» → 3.14
  - унификация «Яндекс Маркет» (7 замен)
  - парсеров 7 → 5 (Onliner.by, Яндекс Маркет, WB, Регард, World Devices); AliExpress-заглушка удалена, Ситилинк вычищен
  - «8-кратное» ускорение → «2,5-кратное»; TTFR «< 2 с» → «< 5 с» (табл. 13)
  - 18 рисунков (было 22), 2.2–2.6 → 2.1–2.5
  - Библиография: все 25 источников цитируются в тексте; [11] Anthropic Claude заменён на RFC 6455 (Fette, I.)
- **Fix loader на `/product`** — styled-jsx early-return (см. GOTCHAS #1)
- **RollingCart** добавлен в loader главной страницы
- **Обсидиан-vault** собран (этот `docs/` + `CLAUDE.md`)

## ⏸️ Отложено
- **Мобильное приложение на Expo/React Native** — решение принято, старт по команде. План в auto-memory: `project_smartprice_mobile_app.md`.
  - Stack: Expo SDK 52 + expo-router + NativeWind + @tanstack/react-query + zustand + react-native-sse + expo-secure-store + victory-native + reanimated
  - Переиспользовать: типы, API-клиент, auth, сторы, утилиты. Переписать: UI, навигацию, SSE, графики
  - Общий бэкенд `api.smrt-price.ru`, общий JWT
  - ~2 недели, M1 (auth+search+product+compare) → M2 (AI+анализ+каталог) → M3 (cheaper+графики+анимации)

## 🧹 Можно почистить, когда руки дойдут
- `backend/app/api/v1/endpoints/payments.py` (и модели `Subscription`, `Payment` если есть) — сейчас мёртвый код после удаления фронт-флоу
- `docs/CURRENT_STRUCTURE.md`, `CURRENT_STRUCTURE_ML.md`, `CURRENT_STRUCTURE_UPDATED.md` — устарели, заменены `ARCHITECTURE.md`. Архивировать/удалить.

## 🗺️ Активные направления
- **«Найти дешевле»** — фазовый план в `CHEAPER_FEATURE_ROADMAP.md`
- Улучшение стабильности парсеров (WB rate-limit, Яндекс капча)
