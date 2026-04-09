"""Per-category negative keyword dictionaries.

When the query's category is X, any candidate title containing a keyword
from NEGATIVES[X] is dropped — it's almost certainly a different kind of
product that happens to share tokens with the real one (cases, cables,
replicas, used parts, accessories "for X"). This is a cheap regex stage
that runs AFTER we know the query category but BEFORE the expensive
per-item LLM classification, so it also cuts LLM cost.

Design rules used when picking keywords:

1. Each keyword must be IMPOSSIBLE to appear in a legitimate listing of
   the target category. "чехол" in an electronics_device listing is
   always wrong (the product IS a phone, not a case for one). But "для"
   alone is too noisy (appears in honest headlines like "наушники для
   звонков") so we use tighter phrases.

2. Cyrillic and Latin variants of the same concept both listed.

3. Sub-string matching on lowercased title — no regex anchors, because
   marketplace titles pack words together inconsistently.

4. Asymmetry matters: NEGATIVES[electronics_device] must NOT contain
   "чехол" if we ever want to keep phones, but NEGATIVES[accessory_case]
   must NOT contain anything that would hit real cases. Most accessory
   categories therefore have an empty or tiny list — the real cleanup
   happens on the device categories.

Keep this file data, not logic. If you need branching, put it in
category_extractor.py instead.
"""

NEGATIVES: dict[str, tuple[str, ...]] = {
    "electronics_device": (
        # cases / covers / films / screen protectors
        "чехол",
        "кейс-",
        " case ",
        " case,",
        "cover ",
        "бампер",
        "накладка на",
        "стекло защит",
        "защитное стекло",
        "защитная плёнка",
        "защитная пленка",
        "гидрогел",
        "пленка для",
        "плёнка для",
        "наклейка",
        # cables / chargers / adapters (sold standalone)
        "кабель для",
        "зарядка для",
        "зарядное для",
        "переходник для",
        "адаптер питания для",
        "блок питания для",
        # spare parts / disassembly
        "разбор",
        "запчаст",
        "аккумулятор для",
        "батарея для",
        "акб для",
        "дисплей для",
        "матрица для",
        "экран для",
        "тачскрин",
        "шлейф ",
        "корпус для",
        "задняя крышка",
        "стекло задней",
        # fakes / used / display samples
        "копия ",
        "копии ",
        "реплика",
        "аналог ",
        "fake",
        "подделк",
        " б/у",
        "бу ",
        " бу,",
        "витринный",
        "восстанов",
        "refurb",
        # content / media (for consoles especially)
        "игра для",
        "диск для",
        "подписк",
        "gift card",
        "подарочная карт",
        # mounts / holders
        "кронштейн для",
        "подставка для",
        "держатель для",
        # ancillary
        "термопаста",
        "стикер",
        "наклейк",
    ),
    "computer_component": (
        "кабель для",
        "кабель питания",
        "питания для",
        "переходник для",
        "адаптер для",
        "подставка для",
        "кронштейн для",
        "держатель для",
        "стикер",
        "наклейк",
        "термопаст",
        "паста термо",
        "копия ",
        "реплика",
        "подделк",
        " б/у",
        "бу ",
        "витринный",
        "восстанов",
        "refurb",
        "разбор",
        "запчаст",
    ),
    "audio_device": (
        # headphone/earbud accessories
        "чехол",
        "футляр для",
        "кейс для",
        "амбушюр",
        "накладк",
        "ушные",
        "кабель для",
        "зарядка для",
        "зарядное для",
        "переходник для",
        # fakes
        "копия ",
        "реплика",
        "аналог ",
        "fake",
        "подделк",
        " б/у",
        "бу ",
        "витринный",
        "восстанов",
        "refurb",
    ),
    "wearable": (
        # straps / bands (the most common confusion)
        "ремешок",
        "ремешки",
        "браслет для",
        "ремень для",
        "застёжк",
        "застежк",
        # films / cases
        "чехол",
        "стекло защит",
        "защитное стекло",
        "защитная плёнка",
        "защитная пленка",
        "плёнка для",
        "пленка для",
        # chargers
        "кабель для",
        "зарядка для",
        "зарядное для",
        # fakes
        "копия ",
        "реплика",
        "аналог ",
        "fake",
        "подделк",
        " б/у",
        "бу ",
        "витринный",
        "восстанов",
        "refurb",
    ),
    "home_appliance": (
        # spare filters / bags / brushes (not the appliance itself)
        "фильтр для",
        "фильтр hepa",
        "hepa для",
        "сменный фильтр",
        "мешок для",
        "мешки для",
        "щётка для",
        "щетка для",
        "насадка для",
        "насадки для",
        "аксессуар",
        "запчаст",
        # fakes
        "копия ",
        "реплика",
        "подделк",
        " б/у",
        "бу ",
        "восстанов",
        "refurb",
    ),
    # Accessory categories usually need no negatives — they ARE the
    # "for X" thing. Leaving these lists empty so accessory_case queries
    # are never accidentally stripped.
    "accessory_case": (),
    "accessory_cable": (),
    "accessory_mount": (),
    "accessory_controller": (
        # only fakes — cases "для геймпада" are legit if user wants them
        "копия ",
        "реплика",
        "подделк",
        "fake",
        "чехол для джойстика",
        "чехол для геймпада",
    ),
    "spare_part": (),  # user explicitly wants replacement parts
    "consumable": (),
    "videogame": (
        # cases for game discs, steelbook-only listings w/o disc
        "стилбук пустой",
        "steelbook only",
        "без диска",
        "футляр для диска",
        "бокс для диска",
    ),
    "media_content": (),
    "other": (),
}


def negatives_for(category: str | None) -> tuple[str, ...]:
    """Return the negative keyword tuple for a category, or an empty tuple."""
    if not category:
        return ()
    return NEGATIVES.get(category, ())
