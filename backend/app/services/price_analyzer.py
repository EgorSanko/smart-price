"""Price analyzer service — scrapes marketplaces and calls LLM for price analysis."""

import json
import statistics
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import structlog

from app.agents.base_agent import _get_ai_client
from app.config import settings
from app.schemas.analyze import (
    AnalyzeAlternatives,
    AnalyzeResult,
    LLMAnalyzePayload,
    OfferLite,
    PriceStats,
)
from app.scrapers.manager import ScrapingManager
from app.services import cleanup


logger = structlog.get_logger()

_VALID_REGIONS = {"BY", "RU"}
_MIN_OFFERS = 5


def _to_offer_lite(p: dict, currency: str) -> OfferLite:
    return OfferLite(
        title=p.get("title", ""),
        price_num=float(p.get("price_num", 0)),
        currency=currency,
        shop=p.get("shop") or p.get("marketplace"),
        marketplace=p.get("marketplace", ""),
        url=p.get("url", ""),
        image=p.get("image"),
    )


class PriceAnalyzer:
    """Orchestrates scraping + statistics + LLM price analysis for a product query."""

    async def stream(self, query: str, region: str) -> AsyncGenerator[dict, None]:
        # ── 1. Validation ────────────────────────────────────────────
        if region not in _VALID_REGIONS:
            yield {
                "status": "error",
                "message": f"Неподдерживаемый регион '{region}'. Допустимые значения: BY, RU.",
            }
            return

        logger.info("price_analyzer_start", query=query, region=region)

        # ── 2. Start event ────────────────────────────────────────────
        yield {"status": "start", "query": query, "region": region}

        # ── 3. Scraping ───────────────────────────────────────────────
        manager = ScrapingManager()
        yield {"status": "parsing", "sources": list(_enabled_sources(region))}

        logger.info("price_analyzer_scraping", query=query, region=region)
        raw_results: dict[str, list[dict]] = await manager.search_all(query, region)

        all_raw: list[dict] = []
        for products in raw_results.values():
            all_raw.extend(products)

        yield {"status": "scraped", "total": len(all_raw)}
        logger.info("price_analyzer_scraped", query=query, region=region, total=len(all_raw))

        # ── 4. Filter + clean ─────────────────────────────────────────
        filtered = cleanup.fast_filter(all_raw, query)
        filtered = cleanup.remove_price_outliers(filtered)
        filtered = [p for p in filtered if (p.get("price_num") or 0) > 0]

        logger.info("price_analyzer_filtered", query=query, region=region, count=len(filtered))

        # ── 5. Minimum offers check ───────────────────────────────────
        if len(filtered) < _MIN_OFFERS:
            msg = (
                f"Недостаточно предложений для анализа "
                f"(нужно минимум {_MIN_OFFERS}, нашли {len(filtered)})"
            )
            logger.warning(
                "price_analyzer_not_enough", query=query, region=region, found=len(filtered)
            )
            yield {"status": "error", "message": msg}
            return

        # ── 6. Statistics ─────────────────────────────────────────────
        currency = "BYN" if region == "BY" else "RUB"
        prices = [float(p["price_num"]) for p in filtered]
        prices_sorted = sorted(prices)

        stat_min = prices_sorted[0]
        stat_max = prices_sorted[-1]
        stat_median = statistics.median(prices_sorted)
        stat_mean = statistics.mean(prices_sorted)
        stat_stdev = statistics.pstdev(prices_sorted)

        stats = PriceStats(
            min=stat_min,
            max=stat_max,
            median=float(stat_median),
            mean=float(stat_mean),
            stdev=float(stat_stdev),
            count=len(filtered),
            currency=currency,
        )

        # ── 7. Best offer ─────────────────────────────────────────────
        best_raw = min(filtered, key=lambda p: float(p.get("price_num", 0)))
        best_offer = _to_offer_lite(best_raw, currency)

        # ── 8. Alternatives ───────────────────────────────────────────
        sorted_asc = sorted(filtered, key=lambda p: float(p.get("price_num", 0)))

        cheaper_raw = [
            p
            for p in sorted_asc
            if float(p.get("price_num", 0)) < stat_median and p is not best_raw
        ][:3]

        pricier_raw = sorted(
            [p for p in filtered if float(p.get("price_num", 0)) > stat_median],
            key=lambda p: float(p.get("price_num", 0)),
            reverse=True,
        )[:3]

        alternatives = AnalyzeAlternatives(
            cheaper=[_to_offer_lite(p, currency) for p in cheaper_raw],
            pricier=[_to_offer_lite(p, currency) for p in pricier_raw],
        )

        yield {"status": "stats", "stats": stats.model_dump()}
        logger.info(
            "price_analyzer_stats_ready",
            query=query,
            region=region,
            median=float(stat_median),
            count=stats.count,
        )

        # ── 9–10. LLM call ────────────────────────────────────────────
        yield {"status": "analyzing"}

        llm_payload, llm_source = await self._call_llm(
            query=query,
            region=region,
            currency=currency,
            stats=stats,
            best_offer=best_offer,
            alternatives=alternatives,
            filtered=filtered,
        )

        # ── 11–12. Build final result (prices always from Python, not LLM) ───
        result = AnalyzeResult(
            query=query,
            region=region,  # type: ignore[arg-type]
            currency=currency,
            verdict=llm_payload.verdict,
            score=llm_payload.score,
            stats=stats,
            best_offer=best_offer,
            red_flags=llm_payload.red_flags,
            value_analysis=llm_payload.value_analysis,
            alternatives=alternatives,
            generated_at=datetime.now(tz=UTC),
        )

        logger.info(
            "price_analyzer_done",
            query=query,
            region=region,
            verdict=result.verdict,
            score=result.score,
            llm_source=llm_source,
        )

        # ── 13. Final event ───────────────────────────────────────────
        # meta.source — "llm" if the real LLM returned a valid payload,
        # "fallback" if we used the deterministic Python fallback.
        # Used by deploy-verifier / chat-tester to distinguish real LLM path
        # from fallback. Frontend ignores meta.
        yield {
            "status": "result",
            "payload": result.model_dump(mode="json"),
            "meta": {
                "source": llm_source,
                "model": settings.AI_MODEL if llm_source == "llm" else None,
            },
        }

    # ── LLM helper ────────────────────────────────────────────────────

    async def _call_llm(
        self,
        *,
        query: str,
        region: str,
        currency: str,
        stats: PriceStats,
        best_offer: OfferLite,
        alternatives: AnalyzeAlternatives,
        filtered: list[dict],
    ) -> tuple[LLMAnalyzePayload, str]:
        """Call the LLM and return (payload, source). source ∈ {"llm","fallback"}."""
        today = datetime.now(tz=UTC).strftime("%Y-%m-%d")

        system_prompt = (
            "Ты — ценовой аналитик Smart Price. Твоя задача — оценить цену товара "
            "на основе РЕАЛЬНЫХ данных, переданных в блоке DATA.\n\n"
            "СТРОЖАЙШИЕ ПРАВИЛА:\n"
            "1. ЗАПРЕЩЕНО выдумывать, округлять или оценивать цены.\n"
            "2. В поле value_analysis ЗАПРЕЩЕНО писать ЛЮБЫЕ числа, цифры, суммы, проценты, "
            "валюты (руб, BYN, ₽, $, €, k, тыс) и слова-заменители цифр "
            "('около', 'примерно', 'приблизительно', '≈', '~'). "
            "Все численные данные уже показываются пользователю в отдельных полях "
            "(stats, best_offer, alternatives) — дублировать их словами НЕ НУЖНО.\n"
            "3. Описывай ценностное предложение СЛОВАМИ, без цифр: "
            "'существенно дешевле медианы', 'в рамках нормального рынка', "
            "'премиум-сегмент', 'подозрительно низкая цена для оригинала', и т.п.\n"
            "4. Верни ТОЛЬКО валидный JSON без markdown-обёртки, без пояснений, без ```json.\n"
            '5. Схема ответа: {"verdict": "good"|"fair"|"bad", "score": 0-100, '
            '"red_flags": [{"severity":"info|warn|danger","text":"..."}], '
            '"value_analysis": "2-4 предложения о ценности без единой цифры"}.\n'
            '6. verdict="good" — best_price существенно ниже медианы и рынок нормальный; '
            '"fair" — в пределах 10% от медианы; "bad" — выше медианы или много красных флагов.\n'
            "7. score — целое число 0-100, где 100 = идеальная сделка.\n"
            "8. red_flags — подозрительные моменты (слишком низкая цена → подделка, "
            "большой разброс → нет единого рынка, мало предложений → редкий товар и т.д.). "
            "Максимум 4 флага. В тексте red_flags цифры допустимы только в общих терминах "
            "(например 'разброс более чем в 2 раза') — но НЕ конкретные суммы.\n"
            "9. value_analysis — на русском, 2-4 предложения, без markdown, БЕЗ ЦИФР.\n\n"
            f"Сегодня: {today}."
        )

        # Top-5 cheaper / pricier for the LLM context
        top_cheaper = [
            {
                "title": o.title,
                "price_num": o.price_num,
                "shop": o.shop,
                "marketplace": o.marketplace,
            }
            for o in alternatives.cheaper[:5]
        ]
        top_pricier = [
            {
                "title": o.title,
                "price_num": o.price_num,
                "shop": o.shop,
                "marketplace": o.marketplace,
            }
            for o in alternatives.pricier[:5]
        ]

        user_content = json.dumps(
            {
                "query": query,
                "stats": stats.model_dump(),
                "best_offer": {
                    "title": best_offer.title,
                    "price_num": best_offer.price_num,
                    "shop": best_offer.shop,
                    "marketplace": best_offer.marketplace,
                },
                "cheaper": top_cheaper,
                "pricier": top_pricier,
            },
            ensure_ascii=False,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        for attempt in range(2):
            try:
                client = _get_ai_client()
                response = await client.chat.completions.create(
                    model=settings.AI_MODEL,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.2,
                    max_tokens=700,
                )
                raw_json = response.choices[0].message.content or "{}"
                payload = LLMAnalyzePayload.model_validate_json(raw_json)
                logger.info("price_analyzer_llm_ok", query=query, attempt=attempt)
                return payload, "llm"
            except Exception as e:
                logger.warning(
                    "price_analyzer_llm_error", query=query, attempt=attempt, error=str(e)
                )
                if attempt == 1:
                    break

        # Fallback: compute verdict/score deterministically
        fallback = self._fallback_payload(
            best_price=best_offer.price_num,
            median=stats.median,
            currency=currency,
        )
        return fallback, "fallback"

    @staticmethod
    def _fallback_payload(best_price: float, median: float, currency: str) -> LLMAnalyzePayload:
        """Deterministic fallback when LLM is unavailable."""
        if median > 0:
            deviation_pct = int((best_price - median) / median * 100)
            score = max(0, min(100, 100 - deviation_pct))
        else:
            deviation_pct = 0
            score = 50

        if score >= 60:
            verdict = "good"
        elif score >= 40:
            verdict = "fair"
        else:
            verdict = "bad"

        sign = "+" if deviation_pct >= 0 else ""
        value_analysis = (
            f"Автоматическая оценка: цена {best_price:.0f} {currency} "
            f"({sign}{deviation_pct}% от медианной по рынку {median:.0f} {currency})."
        )

        return LLMAnalyzePayload(
            verdict=verdict,  # type: ignore[arg-type]
            score=score,
            red_flags=[],
            value_analysis=value_analysis,
        )


def _enabled_sources(region: str) -> list[str]:
    """Return enabled source keys for a given region (for progress events)."""
    from app.scrapers.manager import get_parsers

    parsers = get_parsers(region)
    return [k for k, v in parsers.items() if v.get("enabled")]
