# "Найти дешевле" — Роадмап

Функция: юзер вставляет ссылку на товар с любого из 53 магазинов — Smart Price через реверс-инжиниринг Алисы AI находит цены дешевле.

## Архитектура

```
[Юзер на smrt-price.ru/cheaper]
    ↓ paste URL
[Frontend Next.js] ──WebSocket──> [FastAPI backend]
                                    ↓
                              [Redis: task queue + pubsub]
                                    ↓
                    [Playwright worker в Docker (ms-edge)]
                                    ↓
                    [wss://uniproxy.alice.yandex.ru/uni.ws]
                                    ↓
                              [парсер фреймов]
                                    ↓
                          [PostgreSQL: cheaper_searches]
```

## Зафиксированные решения

- **Фотки товаров:** `imgUrl` из `EAliceOfferCard` (avatars.mds.yandex.net), проксируем через наш бэк, кэшируем в `/opt/smart-price/product-cache/`
- **Real-time:** WebSocket FastAPI ↔ Next.js (не polling). Не создаёт риска бана — это наш внутренний канал
- **Smart input:** URL-детект → og:image fallback (без статичного whitelist — Алиса сама выбирает магазины под категорию)
- **Список магазинов динамический:** берём из первого `json_rephrase_items` RECV-фрейма. Размер и состав зависят от категории товара (проверено на 4 URL: БП=8, пылесос=6, продукты=20, айфон=26)
- **Очередь:** Redis + 1 браузер для старта, масштабируем до 2-3 при нагрузке
- **Дуал-деплой:** smrt-price.ru (public) + функция в Telegram WebApp

## Ключи WS-протокола Алисы (реверс)

### SEND: активация режима + URL
```json
{
  "event": {
    "header": { "namespace": "Vins", "name": "TextInput" },
    "payload": {
      "header": { "dialog_id": "<uuid>", "dialog_type": 2 },
      "request": {
        "event": { "type": "text_input", "text": "<product_url>" }
      }
    }
  }
}
```

### RECV: ключевые namespace'ы
- `System/Ping` — пропускаем
- `System/DialogHistoryMessage` — служебное
- `Vins/VinsResponse` — стартовый ответ
- `Vins/DeferredAliceResponse` — стриминг прогресса + финальных карточек

### Полезные поля в RECV:
- `json_rephrase_items` → `[{Domain, Query: "ozon.ru"}, ...]` — список магазинов для проверки
- `EAliceOfferCard.json_data` → `{url, imgUrl, price.value, rating, review_cnt, productName, is_best_price_agent}` — найденное предложение
- `text` в `text_card` → прогресс-сообщения ("## 🎉 Первая победа — экономия 1490 ₽")
- "Смотрю в магазинах X" — НЕ в WS явно, рендерится фронтом Алисы; для Smart Price возьмём из DOM-polling **либо** из `json_rephrase_items` + локальный таймер

## UI/UX

### Страница `/cheaper`
- Hero: "Найдём дешевле в десятках магазинов" (конкретное N подставляем после первого WS-фрейма)
- Smart input: детект URL vs текст, превью магазина и товара
- Кнопка "Найти дешевле" активна только при валидном URL

### Loading modal (полноэкранный)
- Прогресс-бар X/N (N — динамический, из первого json_rephrase_items)
- "Сейчас проверяем: dns-shop.ru" (обновляется)
- Сетка магазинов строится после первого WS-фрейма со списком
- До получения списка: скелетон "Анализируем товар..."
- Сетка магазинов: ✓ проверен / → сейчас / · ожидает
- Live-карточки находок ("🎉 Нашли дешевле на 1490₽ в armadatv.ru")
- ETA: ~6 мин осталось
- [Свернуть и ждать] → floating pill
- "Закройте вкладку — пришлём в ТГ"

### Результаты
- 🥇🥈🥉 топ-3 с картинками, рейтингом, ссылкой "В магазин"
- Остальные компактным списком
- Сохранение в «Мои поиски»

### Instructions section
- Что хорошо ищется: электроника, БТ, инструменты, ДТ, игрушки
- Что не ищется: одежда, продукты, авто, услуги, 18+
- Доставка не учитывается, цены меняются

## Phases

### Phase 1: Frontend mockup (0.5-1 день) ← СТАРТУЕМ ОТСЮДА
- [ ] Route `/cheaper/page.tsx` (Next.js)
- [ ] `<SmartInput />` с URL-детектом
- [ ] `<LoadingModal />` (mocked progress)
- [ ] `<OfferCard />`, `<ShopGrid />`, `<FloatingPill />`
- [ ] `<InstructionsSection />`
- [ ] Фейковые данные для визуальной отладки
- [ ] i18n (ru/en), адаптив под мобилку
- [ ] Визуальное ревью пользователем

### Phase 2: Backend skeleton (1 день)
- [ ] FastAPI endpoint `POST /api/cheaper/search` → task_id
- [ ] `GET /api/cheaper/{task_id}` (polling fallback)
- [ ] `WS /ws/cheaper/{task_id}` (live stream)
- [ ] Redis pubsub `cheaper:task:{id}`
- [ ] PostgreSQL: миграция `cheaper_searches` table
- [ ] Модель `CheaperSearch` (SQLAlchemy/Pydantic)

### Phase 3: Playwright worker (1-2 дня)
- [ ] Docker-сервис `alisa_worker` с `mcr.microsoft.com/playwright/python`
- [ ] Volume для user data dir Yandex
- [ ] Celery task `search_cheaper(url, task_id)`
- [ ] Автоматизация UI-flow (Меню → Найти дешевле β → paste URL)
- [ ] WS frame parser
- [ ] Публикация прогресса в Redis pubsub
- [ ] Сохранение финала в БД
- [ ] Обработка ошибок: captcha, timeout, logout

### Phase 4: Integration & polish (1 день)
- [ ] Frontend заменяет моки реальным API
- [ ] Кэш 24ч на одинаковые URL
- [ ] Rate limit: 1 поиск / 3 мин на юзера, 10/день
- [ ] ТГ-нотификация о завершении
- [ ] Прокси/кэш картинок через наш бэк (`/api/image-proxy?url=`)
- [ ] Fallback: если Алиса упала — показываем info-экран

### Phase 5: Testing & deploy (0.5 дня)
- [ ] Playwright e2e: happy path
- [ ] Health-check alisa (каждые 6ч, алерт в ТГ)
- [ ] Деплой на VPS: scp → docker compose up -d --build
- [ ] Мониторинг: Prometheus metric `cheaper_search_duration_seconds`

## Ожидаемая конверсия поиска по категориям

Замерено 2026-04-14 на 4 Ozon-URL (6 мин per URL, WS-капча):

| Категория | Запланировано | Реально нашли дешевле | Конверсия |
|---|---|---|---|
| Продукты (пудинг) | 20 | 9 (100-144₽ vs Ozon 2232₽) | **~45%** |
| Ноутбучный БП (HP) | 8 | 0 (только ориг. Ozon) | 0% |
| Пылесос (Weissgauff) | 6 | 0 | 0% |
| Смартфон (iPhone 17) | 26 | 0 | 0% |

### Выводы

- **Продукты/FMCG** — топ-категория: много магазинов с разными ценами, почти всегда есть дешевле.
- **Электроника/БТ** — ~50% поисков вернут только оригинал (Алиса не находит конкурентов). Нужен fallback UI-экран "Дешевле не нашли, лучшая цена на Ozon".
- **Нишевые запчасти** (БП, автозапчасти) — низкая конверсия, нужна установка ожиданий на этапе ввода URL.

### Рекомендации для UX

1. **Категоризация по URL** → показывать ожидаемое время + вероятность успеха перед стартом (например, "электроника: обычно 2-3 магазина дешевле").
2. **Graceful empty state** — не "ошибка", а "Алиса проверила 26 магазинов, но дешевле не нашла — лучшая цена на Ozon 60 847₽". Сохранить исходную карточку из `EAliceOfferCard` с рейтингом.
3. **Прогресс-бар показывает и N=planned, и K=offers_found** — юзер видит "проверено 12/26, найдено 3 дешевле".

## Риски и митигации

| Риск | Митигация |
|---|---|
| Яндекс банит аккаунт | 3-5 backup аккаунтов с ротацией, human-like delays |
| Капча | Remote debug для ручного обхода, алерт админу |
| UI Алисы меняется | Daily health-check, координатный click с fallback селекторами |
| Медленно (8-10 мин) | Async очередь + фоновые ТГ-нотификации + 24ч кэш |
| ToS | Позиционируем как "proof-of-concept" для диплома |

## Магазины — динамический список (по категориям)

Алиса выбирает магазины адаптивно под товар. Никакого whitelist не держим — берём `json_rephrase_items` из первого RECV-фрейма после отправки URL и показываем как есть.

### Примеры (замерено 2026-04-14 по 4 Ozon-URL):

| Категория | N | Характерные магазины |
|---|---|---|
| Ноутбучный БП (HP) | 8 | partsdirect.ru, nbdoc.ru, chipdip, ozon, wb, market.yandex, aliexpress, onlinetrade |
| Пылесос (Weissgauff) | 6 | leroymerlin, tehnostudio, weissgauff.ru (бренд), ozon, wb, market.yandex |
| Продукты (пудинг) | 20 | 5ka, auchan, vkusvill, perekrestok, lenta, lavka.yandex, kuper, okeydostavka, dixy, vodovoz + общие |
| Смартфон (iPhone 17) | 26 | dns-shop, eldorado, re-store, shop.mts, apple-tut, stores-apple, pitergsm, ibrat, quke + спец. |

**Общее ядро:** ozon, wildberries, market.yandex (иногда aliexpress).
**Вывод:** в UI показываем реальный список с бекенда, а не хардкод.
