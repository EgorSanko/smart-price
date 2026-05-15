"""Test that accessory queries reach the user — regression for the bug where
"чехол iPhone 16 Pro" returned only one source because parsers and filters
treated every accessory title as junk.

Three layers must agree:
1. `detect_intent_from_keywords` correctly identifies the query category
2. Yandex Market scraper (playwright) keeps cases when query asks for them
3. `ai_filter_relevant` doesn't strip cases off the combined pool
"""

import pytest

from app.scrapers.category_extractor import detect_intent_from_keywords
from app.scrapers.playwright_scrapers import (
    _is_accessory,
    _should_drop_accessory,
)


class TestIntentDetection:
    """detect_intent_from_keywords — query → canonical category."""

    @pytest.mark.parametrize(
        "query,expected",
        [
            # — Case / cover queries —
            ("чехол iPhone 16 Pro", "accessory_case"),
            ("Чехол iPhone 16 Pro", "accessory_case"),
            ("чехлы для iphone", "accessory_case"),
            ("iphone 16 чехол", "accessory_case"),
            ("кейс для airpods", "accessory_case"),
            ("бампер iphone 15", "accessory_case"),
            ("защитное стекло iphone", "accessory_case"),
            ("гидрогелевая плёнка iphone", "accessory_case"),
            ("iPhone 16 cover", "accessory_case"),
            # — Cable / charger queries —
            ("кабель USB-C", "accessory_cable"),
            ("зарядка для iphone", "accessory_cable"),
            ("адаптер питания macbook", "accessory_cable"),
            ("блок питания ps5", "accessory_cable"),
            # — Mount queries —
            ("кронштейн для телевизора", "accessory_mount"),
            ("подставка для ipad", "accessory_mount"),
            # — Controller —
            ("геймпад ps5", "accessory_controller"),
            ("пульт для тв", "accessory_controller"),
            # — Spare parts —
            ("аккумулятор для iphone 12", "spare_part"),
            ("батарея для samsung s23", "spare_part"),
            ("дисплей для iphone 14", "spare_part"),
            ("тачскрин samsung", "spare_part"),
            # — Consumables —
            ("картридж HP 305", "consumable"),
            ("фильтр для пылесоса dyson", "consumable"),
            # — Devices (no accessory keyword) → None, fall to LLM —
            ("iPhone 16 Pro", None),
            ("Sony PlayStation 5", None),
            ("MacBook Air M3", None),
            ("Samsung Galaxy S24 Ultra", None),
            ("RTX 4090", None),
            ("робот-пылесос", None),
            # — Edge: bare accessory word without device — still classified —
            ("чехол", "accessory_case"),
            ("кабель", "accessory_cable"),
        ],
    )
    def test_classifies(self, query: str, expected: str | None) -> None:
        assert detect_intent_from_keywords(query) == expected


class TestShouldDropAccessory:
    """Parser-side filter: titles like 'Чехол силиконовый iPhone' must be
    kept when the user asked for a case and dropped when the user asked
    for an iPhone."""

    @pytest.mark.parametrize(
        "title,query_is_accessory,expected_drop",
        [
            # Query is a device — drop accessory titles
            ("Чехол силиконовый iPhone 16 Pro", False, True),
            ("Защитное стекло iPhone", False, True),
            ("Кабель USB-C 1m", False, True),
            # Query is for accessory — KEEP accessory titles
            ("Чехол силиконовый iPhone 16 Pro", True, False),
            ("Защитное стекло iPhone 16 Pro", True, False),
            ("Кабель USB-C для iPhone", True, False),
            # Regular product titles — kept regardless
            ("Apple iPhone 16 Pro 256GB", False, False),
            ("Apple iPhone 16 Pro 256GB", True, False),
        ],
    )
    def test_filter(self, title: str, query_is_accessory: bool, expected_drop: bool) -> None:
        assert _should_drop_accessory(title, query_is_accessory) is expected_drop

    def test_legacy_helper_still_works(self) -> None:
        """`_is_accessory(title)` (without query context) keeps its
        original behavior so we don't break callers that don't need
        intent-awareness."""
        assert _is_accessory("Чехол для iPhone")
        assert not _is_accessory("iPhone 16 Pro 256GB")
