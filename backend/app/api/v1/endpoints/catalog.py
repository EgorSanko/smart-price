"""Catalog endpoints — comprehensive product tree for price comparison."""

from fastapi import APIRouter, HTTPException, Query


router = APIRouter(prefix="/catalog", tags=["catalog"])


# ══════════════════════════════════════════════════════════════════
# FULL PRODUCT CATALOG
# Category → Subcategory → Brand → Models
# When user selects a model, frontend triggers multi-marketplace search
# ══════════════════════════════════════════════════════════════════

CATALOG = {
    # ── СМАРТФОНЫ ──────────────────────────────────────────────────
    "smartphones": {
        "name": "Смартфоны",
        "icon": "Smartphone",
        "parent": "smartphones-gadgets",
        "brands": {
            "Apple": [
                "Apple iPhone 17 Pro Max",
                "Apple iPhone 17 Pro",
                "Apple iPhone 17 Air",
                "Apple iPhone 17",
                "Apple iPhone 16 Pro Max",
                "Apple iPhone 16 Pro",
                "Apple iPhone 16 Plus",
                "Apple iPhone 16",
                "Apple iPhone 16e (SE 4)",
                "Apple iPhone 15 Pro Max",
                "Apple iPhone 15 Pro",
                "Apple iPhone 15 Plus",
                "Apple iPhone 15",
                "Apple iPhone 14 Pro Max",
                "Apple iPhone 14 Pro",
                "Apple iPhone 14 Plus",
                "Apple iPhone 14",
                "Apple iPhone 13",
                "Apple iPhone 13 mini",
            ],
            "Samsung": [
                "Samsung Galaxy S26 Ultra",
                "Samsung Galaxy S26+",
                "Samsung Galaxy S26",
                "Samsung Galaxy S25 Ultra",
                "Samsung Galaxy S25+",
                "Samsung Galaxy S25",
                "Samsung Galaxy S25 FE",
                "Samsung Galaxy S24 Ultra",
                "Samsung Galaxy S24+",
                "Samsung Galaxy S24",
                "Samsung Galaxy S24 FE",
                "Samsung Galaxy Z Fold7",
                "Samsung Galaxy Z Flip7",
                "Samsung Galaxy Z Fold6",
                "Samsung Galaxy Z Fold5",
                "Samsung Galaxy Z Flip6",
                "Samsung Galaxy Z Flip5",
                "Samsung Galaxy A56",
                "Samsung Galaxy A55",
                "Samsung Galaxy A36",
                "Samsung Galaxy A35",
                "Samsung Galaxy A26",
                "Samsung Galaxy A16",
                "Samsung Galaxy M55",
                "Samsung Galaxy M35",
                "Samsung Galaxy M15",
            ],
            "Xiaomi": [
                "Xiaomi 15 Ultra",
                "Xiaomi 15 Pro",
                "Xiaomi 15",
                "Xiaomi 14 Ultra",
                "Xiaomi 14 Pro",
                "Xiaomi 14",
                "Xiaomi 14T Pro",
                "Xiaomi 14T",
                "Xiaomi 13T Pro",
                "Xiaomi 13T",
                "Xiaomi 13",
                "Xiaomi Mix Fold 4",
                "Xiaomi Mix Flip",
                "Xiaomi Civi 4 Pro",
            ],
            "POCO": [
                "POCO F7 Ultra",
                "POCO F7 Pro",
                "POCO F7",
                "POCO X7 Pro",
                "POCO X7",
                "POCO F6 Pro",
                "POCO F6",
                "POCO M7 Pro",
                "POCO M6 Pro",
                "POCO C75",
                "POCO C65",
            ],
            "Redmi": [
                "Redmi Note 14 Pro+ 5G",
                "Redmi Note 14 Pro",
                "Redmi Note 14",
                "Redmi Note 13 Pro+",
                "Redmi Note 13 Pro",
                "Redmi Note 13",
                "Redmi K80 Pro",
                "Redmi K80",
                "Redmi Turbo 4",
                "Redmi 14C",
                "Redmi 13C",
                "Redmi A3",
            ],
            "realme": [
                "realme GT 7 Pro",
                "realme GT 7",
                "realme 14 Pro+ 5G",
                "realme 14 Pro",
                "realme 14x 5G",
                "realme 14T",
                "realme 13 Pro+",
                "realme 13 Pro",
                "realme 13",
                "realme C75",
                "realme C67",
                "realme Narzo 70 Pro",
            ],
            "HONOR": [
                "HONOR Magic7 Pro",
                "HONOR Magic7",
                "HONOR Magic7 RSR",
                "HONOR Magic V4",
                "HONOR Magic V3",
                "HONOR 400 Pro",
                "HONOR 400",
                "HONOR 300 Ultra",
                "HONOR 300 Pro",
                "HONOR 300",
                "HONOR 200 Pro",
                "HONOR 200",
                "HONOR X9c",
                "HONOR X9b",
                "HONOR X8b",
            ],
            "Huawei": [
                "Huawei Pura 80 Ultra",
                "Huawei Pura 80 Pro",
                "Huawei Pura 80",
                "Huawei Pura 70 Ultra",
                "Huawei Pura 70 Pro",
                "Huawei Pura 70",
                "Huawei Mate 70 Pro+",
                "Huawei Mate 70 Pro",
                "Huawei Mate 70",
                "Huawei Mate 70 RS Ultimate Design",
                "Huawei Mate X6",
                "Huawei nova 13 Pro",
                "Huawei nova 13",
                "Huawei nova 12 Ultra",
                "Huawei nova 12 Pro",
            ],
            "OnePlus": [
                "OnePlus 13",
                "OnePlus 13R",
                "OnePlus 13T",
                "OnePlus 12",
                "OnePlus Open 2",
                "OnePlus Open",
                "OnePlus Nord 4",
                "OnePlus Nord CE 4",
            ],
            "Google": [
                "Google Pixel 10 Pro XL",
                "Google Pixel 10 Pro",
                "Google Pixel 10",
                "Google Pixel 9a",
                "Google Pixel 9 Pro XL",
                "Google Pixel 9 Pro",
                "Google Pixel 9",
                "Google Pixel 9 Pro Fold",
            ],
            "Nothing": [
                "Nothing Phone (3)",
                "Nothing Phone (3a)",
                "Nothing Phone (2a) Plus",
                "Nothing Phone (2a)",
                "Nothing Phone (2)",
                "Nothing Phone (1)",
            ],
            "vivo": [
                "vivo X200 Ultra",
                "vivo X200 Pro Mini",
                "vivo X200 Pro",
                "vivo X200",
                "vivo V40 Pro",
                "vivo V40",
                "vivo Y100",
                "vivo Y58",
                "iQOO 13",
                "iQOO Neo 10 Pro",
                "iQOO Neo 10",
            ],
            "OPPO": [
                "OPPO Find X8 Ultra",
                "OPPO Find X8 Pro",
                "OPPO Find X8",
                "OPPO Find N5",
                "OPPO Reno 13 Pro",
                "OPPO Reno 13",
                "OPPO Reno 12 Pro",
                "OPPO Reno 12",
                "OPPO A5 Pro",
                "OPPO A79",
            ],
            "Motorola": [
                "Motorola Edge 60 Pro",
                "Motorola Edge 60",
                "Motorola Edge 50 Ultra",
                "Motorola Edge 50 Pro",
                "Motorola Razr 60 Ultra",
                "Motorola Razr 50 Ultra",
                "Motorola Moto G85",
                "Motorola Moto G75",
                "Motorola Moto G Power 2025",
            ],
            "Infinix": [
                "Infinix Note 50 Pro",
                "Infinix Note 40 Pro+",
                "Infinix Note 40 Pro",
                "Infinix Zero 40 5G",
                "Infinix Hot 50 Pro+",
                "Infinix Hot 50",
                "Infinix GT 20 Pro",
            ],
            "Tecno": [
                "Tecno Phantom V Fold 2",
                "Tecno Phantom V Flip 2",
                "Tecno Camon 30 Pro",
                "Tecno Camon 30",
                "Tecno Spark 30 Pro",
                "Tecno Spark 30",
                "Tecno Pova 6 Pro",
                "Tecno Pova 6 Neo",
            ],
            "ZTE": [
                "ZTE nubia Z70 Ultra",
                "ZTE nubia Z70S Ultra",
                "ZTE nubia Z60 Ultra",
                "ZTE Blade V70",
                "ZTE Blade V50",
                "Red Magic 10 Pro+",
                "Red Magic 10 Pro",
            ],
            "Sony": [
                "Sony Xperia 1 VI",
                "Sony Xperia 5 V",
                "Sony Xperia 10 VI",
            ],
            "ASUS": [
                "ASUS ROG Phone 9 Pro",
                "ASUS ROG Phone 9",
                "ASUS Zenfone 12 Ultra",
                "ASUS Zenfone 11 Ultra",
            ],
        },
    },
    # ── ПЛАНШЕТЫ ───────────────────────────────────────────────────
    "tablets": {
        "name": "Планшеты",
        "icon": "Tablet",
        "parent": "smartphones-gadgets",
        "brands": {
            "Apple": [
                "Apple iPad Pro 13 M4",
                "Apple iPad Pro 11 M4",
                "Apple iPad Air 13 M3",
                "Apple iPad Air 11 M3",
                "Apple iPad 11 поколение",
                "Apple iPad 10 поколение",
                "Apple iPad mini 7",
            ],
            "Samsung": [
                "Samsung Galaxy Tab S10 Ultra",
                "Samsung Galaxy Tab S10+",
                "Samsung Galaxy Tab S10 FE+",
                "Samsung Galaxy Tab S10 FE",
                "Samsung Galaxy Tab S9 FE+",
                "Samsung Galaxy Tab S9 FE",
                "Samsung Galaxy Tab A9+",
                "Samsung Galaxy Tab A9",
            ],
            "Xiaomi": [
                "Xiaomi Pad 7 Pro",
                "Xiaomi Pad 7",
                "Xiaomi Pad 6S Pro",
                "Xiaomi Redmi Pad Pro",
                "Xiaomi Redmi Pad SE",
            ],
            "Huawei": [
                "Huawei MatePad Pro 13.2",
                "Huawei MatePad 11.5",
                "Huawei MatePad SE 11",
                "Huawei MatePad T10",
            ],
            "Lenovo": [
                "Lenovo Tab P12 Pro",
                "Lenovo Tab P11 Pro",
                "Lenovo Tab P11",
                "Lenovo Tab M11",
                "Lenovo Tab M10 Plus",
            ],
            "HONOR": [
                "HONOR Pad 9",
                "HONOR Pad X9",
                "HONOR Pad V8 Pro",
            ],
            "OnePlus": [
                "OnePlus Pad 2",
                "OnePlus Pad",
            ],
            "realme": [
                "realme Pad 2",
                "realme Pad Mini",
            ],
        },
    },
    # ── НАУШНИКИ ───────────────────────────────────────────────────
    "headphones": {
        "name": "Наушники",
        "icon": "Headphones",
        "parent": "smartphones-gadgets",
        "brands": {
            "Apple": [
                "Apple AirPods 4",
                "Apple AirPods 4 ANC",
                "Apple AirPods Pro 3",
                "Apple AirPods Pro 2",
                "Apple AirPods Max 2024",
                "Apple AirPods Max",
                "Apple AirPods 3",
                "Apple EarPods USB-C",
                "Apple EarPods Lightning",
            ],
            "Sony": [
                "Sony WH-1000XM6",
                "Sony WH-1000XM5",
                "Sony WF-1000XM6",
                "Sony WF-1000XM5",
                "Sony WH-CH720N",
                "Sony WH-CH520",
                "Sony WF-C700N",
                "Sony WF-C500",
                "Sony LinkBuds Open",
                "Sony LinkBuds Fit",
                "Sony LinkBuds S",
                "Sony MDR-7506",
                "Sony MDR-ZX110",
            ],
            "Samsung": [
                "Samsung Galaxy Buds 3 Pro",
                "Samsung Galaxy Buds 3",
                "Samsung Galaxy Buds FE",
                "Samsung Galaxy Buds 2 Pro",
                "Samsung Galaxy Buds 2",
                "Samsung Galaxy Buds Live",
            ],
            "JBL": [
                "JBL Tour One M2",
                "JBL Tour Pro 3",
                "JBL Live 770NC",
                "JBL Live 670NC",
                "JBL Live 460NC",
                "JBL Tune 770NC",
                "JBL Tune 720BT",
                "JBL Tune 520BT",
                "JBL Tune 510BT",
                "JBL Tune Beam",
                "JBL Tune Flex",
                "JBL Tune Buds",
                "JBL Vibe 300TWS",
                "JBL Vibe 200TWS",
                "JBL Vibe Beam",
                "JBL Wave 300TWS",
                "JBL Wave Beam",
                "JBL Endurance Race",
                "JBL Reflect Flow Pro",
            ],
            "Marshall": [
                "Marshall Major V",
                "Marshall Major IV",
                "Marshall Monitor III ANC",
                "Marshall Monitor II ANC",
                "Marshall Motif II ANC",
                "Marshall Minor IV",
                "Marshall Mid ANC",
            ],
            "Bose": [
                "Bose QuietComfort Ultra Headphones",
                "Bose QuietComfort Headphones",
                "Bose QuietComfort Ultra Earbuds",
                "Bose QuietComfort Earbuds",
                "Bose 700",
                "Bose Sport Earbuds",
            ],
            "Sennheiser": [
                "Sennheiser Momentum 4 Wireless",
                "Sennheiser Momentum True Wireless 4",
                "Sennheiser Accentum Plus",
                "Sennheiser Accentum",
                "Sennheiser HD 660S2",
                "Sennheiser HD 560S",
                "Sennheiser HD 599",
                "Sennheiser IE 600",
                "Sennheiser IE 200",
            ],
            "Xiaomi": [
                "Xiaomi Buds 5 Pro",
                "Xiaomi Buds 5",
                "Xiaomi Buds 4 Pro",
                "Xiaomi Redmi Buds 6 Pro",
                "Xiaomi Redmi Buds 6 Play",
                "Xiaomi Redmi Buds 5 Pro",
                "Xiaomi Redmi Buds 5",
                "Xiaomi Redmi Buds 4",
                "Xiaomi Redmi Buds 4 Active",
            ],
            "Huawei": [
                "Huawei FreeBuds Pro 3",
                "Huawei FreeBuds Pro 2",
                "Huawei FreeBuds 6i",
                "Huawei FreeBuds 5i",
                "Huawei FreeBuds SE 3",
                "Huawei FreeBuds SE 2",
                "Huawei FreeClip",
            ],
            "Beats": [
                "Beats Studio Pro",
                "Beats Solo 4",
                "Beats Solo Buds",
                "Beats Fit Pro",
                "Beats Studio Buds+",
                "Beats Studio Buds",
                "Beats Flex",
            ],
            "Audio-Technica": [
                "Audio-Technica ATH-M50xBT2",
                "Audio-Technica ATH-M50x",
                "Audio-Technica ATH-M40x",
                "Audio-Technica ATH-M20xBT",
                "Audio-Technica ATH-SR50BT",
                "Audio-Technica ATH-SQ1TW",
            ],
            "AKG": [
                "AKG K371-BT",
                "AKG K361-BT",
                "AKG K240 Studio",
                "AKG N400NC",
                "AKG N5 Hybrid",
            ],
            "Jabra": [
                "Jabra Elite 10",
                "Jabra Elite 8 Active",
                "Jabra Elite 85t",
                "Jabra Elite 4",
                "Jabra Elite 3",
            ],
            "Skullcandy": [
                "Skullcandy Crusher ANC 2",
                "Skullcandy Hesh ANC",
                "Skullcandy Dime 3",
                "Skullcandy Sesh Evo",
            ],
            "QCY": [
                "QCY AilyBuds Pro 2",
                "QCY AilyBuds Pro",
                "QCY T18",
                "QCY T13",
                "QCY MeloBuds Pro",
                "QCY Crossky Link",
            ],
            "Edifier": [
                "Edifier W820NB Plus",
                "Edifier W820NB",
                "Edifier WH950NB",
                "Edifier W240TN",
                "Edifier TWS330NB",
                "Edifier X3",
            ],
            "Google": [
                "Google Pixel Buds Pro 2",
                "Google Pixel Buds A-Series",
            ],
            "Nothing": [
                "Nothing Ear",
                "Nothing Ear (a)",
                "Nothing Ear (open)",
            ],
            "HONOR": [
                "HONOR Earbuds X7",
                "HONOR Earbuds X6",
                "HONOR Choice Earbuds X5",
                "HONOR Choice Earbuds X3",
            ],
        },
    },
    # ── СМАРТ-ЧАСЫ ─────────────────────────────────────────────────
    "smartwatches": {
        "name": "Смарт-часы",
        "icon": "Watch",
        "parent": "smartphones-gadgets",
        "brands": {
            "Apple": [
                "Apple Watch Ultra 3",
                "Apple Watch Ultra 2",
                "Apple Watch Series 11 46mm",
                "Apple Watch Series 11 42mm",
                "Apple Watch Series 10 46mm",
                "Apple Watch Series 10 42mm",
                "Apple Watch SE 3 44mm",
                "Apple Watch SE 3 40mm",
            ],
            "Samsung": [
                "Samsung Galaxy Watch Ultra 2",
                "Samsung Galaxy Watch Ultra",
                "Samsung Galaxy Watch 8 44mm",
                "Samsung Galaxy Watch 8 40mm",
                "Samsung Galaxy Watch 7 44mm",
                "Samsung Galaxy Watch 7 40mm",
                "Samsung Galaxy Watch FE",
            ],
            "Huawei": [
                "Huawei Watch GT 5 Pro 46mm",
                "Huawei Watch GT 5 46mm",
                "Huawei Watch GT 5 42mm",
                "Huawei Watch GT 4 46mm",
                "Huawei Watch GT 4 41mm",
                "Huawei Watch D2",
                "Huawei Watch Fit 3",
            ],
            "Xiaomi": [
                "Xiaomi Watch S4",
                "Xiaomi Watch S3",
                "Xiaomi Watch 2 Pro",
                "Xiaomi Watch 2",
                "Xiaomi Watch S1 Active",
            ],
            "Garmin": [
                "Garmin Fenix 8",
                "Garmin Fenix 7X",
                "Garmin Fenix 7",
                "Garmin Epix Pro",
                "Garmin Venu 3",
                "Garmin Venu 3S",
                "Garmin Forerunner 965",
                "Garmin Forerunner 265",
                "Garmin Forerunner 165",
                "Garmin Vivoactive 5",
                "Garmin Instinct 2X Solar",
            ],
            "Amazfit": [
                "Amazfit T-Rex Ultra",
                "Amazfit T-Rex 3",
                "Amazfit GTR 4",
                "Amazfit GTS 4",
                "Amazfit GTS 4 Mini",
                "Amazfit Balance",
                "Amazfit Active",
                "Amazfit Bip 5",
            ],
            "Google": [
                "Google Pixel Watch 3 45mm",
                "Google Pixel Watch 3 41mm",
                "Google Pixel Watch 2",
            ],
            "HONOR": [
                "HONOR Watch GS Pro",
                "HONOR Watch 4 Pro",
                "HONOR Watch 4",
                "HONOR MagicWatch 2",
            ],
        },
    },
    # ── ФИТНЕС-БРАСЛЕТЫ ───────────────────────────────────────────
    "fitness-bands": {
        "name": "Фитнес-браслеты",
        "icon": "Activity",
        "parent": "smartphones-gadgets",
        "brands": {
            "Xiaomi": [
                "Xiaomi Smart Band 9 Pro",
                "Xiaomi Smart Band 9",
                "Xiaomi Smart Band 8 Pro",
                "Xiaomi Smart Band 8",
            ],
            "Huawei": ["Huawei Band 9", "Huawei Band 8"],
            "HONOR": ["HONOR Band 7", "HONOR Band 6"],
            "Samsung": ["Samsung Galaxy Fit 3"],
            "Amazfit": ["Amazfit Band 7"],
        },
    },
    # ── POWER BANK ─────────────────────────────────────────────────
    "powerbanks": {
        "name": "Power Bank",
        "icon": "BatteryCharging",
        "parent": "smartphones-gadgets",
        "brands": {
            "Xiaomi": [
                "Xiaomi Mi Power Bank 3 20000mAh",
                "Xiaomi Mi Power Bank 3 10000mAh",
                "Xiaomi Power Bank 4 20000mAh",
                "Xiaomi Pocket Edition Pro 10000mAh",
            ],
            "Anker": [
                "Anker PowerCore 26800",
                "Anker PowerCore 20000",
                "Anker PowerCore 10000",
                "Anker 737 PowerCore 24000",
                "Anker MagGo 10000",
            ],
            "Baseus": [
                "Baseus Adaman 20000mAh",
                "Baseus Bipow 10000mAh",
                "Baseus Elf 20000mAh",
            ],
            "Samsung": [
                "Samsung EB-P3400 10000mAh",
                "Samsung EB-P3400 20000mAh",
            ],
        },
    },
    # ── НОУТБУКИ ───────────────────────────────────────────────────
    "laptops": {
        "name": "Ноутбуки",
        "icon": "Laptop",
        "parent": "laptops-pcs",
        "brands": {
            "Apple": [
                "Apple MacBook Air 15 M4",
                "Apple MacBook Air 13 M4",
                "Apple MacBook Air 15 M3",
                "Apple MacBook Air 13 M3",
                "Apple MacBook Pro 16 M4 Pro",
                "Apple MacBook Pro 16 M4 Max",
                "Apple MacBook Pro 14 M4 Pro",
                "Apple MacBook Pro 14 M4",
            ],
            "Lenovo": [
                "Lenovo IdeaPad Slim 5 16",
                "Lenovo IdeaPad Slim 5 14",
                "Lenovo IdeaPad 1 15",
                "Lenovo IdeaPad Flex 5",
                "Lenovo ThinkPad X1 Carbon Gen 13",
                "Lenovo ThinkPad X1 Carbon Gen 12",
                "Lenovo ThinkPad T14 Gen 5",
                "Lenovo ThinkBook 16 Gen 7",
                "Lenovo ThinkBook 14 Gen 7",
                "Lenovo Yoga Slim 7 14",
                "Lenovo Yoga 9i",
            ],
            "ASUS": [
                "ASUS Vivobook 15",
                "ASUS Vivobook 16",
                "ASUS Vivobook S 16 OLED",
                "ASUS Zenbook 14 OLED",
                "ASUS Zenbook S 14",
                "ASUS Zenbook Duo",
                "ASUS ProArt Studiobook 16 OLED",
                "ASUS ExpertBook B5",
            ],
            "HP": [
                "HP Pavilion 15",
                "HP Pavilion 16",
                "HP Pavilion Plus 14",
                "HP Envy x360 15",
                "HP Spectre x360 14",
                "HP 15s",
                "HP 14s",
                "HP 250 G10",
            ],
            "Acer": [
                "Acer Aspire 5 15",
                "Acer Aspire 3 15",
                "Acer Aspire Vero",
                "Acer Swift 14 AI",
                "Acer Swift Go 14",
                "Acer Extensa 15",
            ],
            "Dell": [
                "Dell XPS 16 9640",
                "Dell XPS 14 9440",
                "Dell XPS 13 9345",
                "Dell Inspiron 16 5640",
                "Dell Inspiron 15 3535",
                "Dell Latitude 5540",
                "Dell Vostro 3520",
            ],
            "MSI": [
                "MSI Modern 15",
                "MSI Modern 14",
                "MSI Prestige 16",
                "MSI Creator Z16 HX",
                "MSI Summit E16 Flip",
            ],
            "Huawei": [
                "Huawei MateBook X Pro 2024",
                "Huawei MateBook D 16 2024",
                "Huawei MateBook D 14 2024",
                "Huawei MateBook 14",
            ],
            "HONOR": [
                "HONOR MagicBook X16 Pro",
                "HONOR MagicBook X14 Pro",
                "HONOR MagicBook Art 14",
            ],
            "Samsung": [
                "Samsung Galaxy Book 5 Pro 360",
                "Samsung Galaxy Book 5 Pro",
                "Samsung Galaxy Book 4 Ultra",
                "Samsung Galaxy Book 4 Pro",
            ],
            "Microsoft": [
                "Microsoft Surface Laptop 7",
                "Microsoft Surface Pro 11",
            ],
            "Xiaomi": [
                "Xiaomi RedmiBook 15",
                "Xiaomi RedmiBook Pro 14",
                "Xiaomi Notebook Pro 14",
            ],
        },
    },
    # ── ИГРОВЫЕ НОУТБУКИ ──────────────────────────────────────────
    "gaming-laptops": {
        "name": "Игровые ноутбуки",
        "icon": "Gamepad2",
        "parent": "laptops-pcs",
        "brands": {
            "ASUS": [
                "ASUS ROG Strix G16",
                "ASUS ROG Strix G18",
                "ASUS ROG Strix SCAR 16",
                "ASUS ROG Strix SCAR 18",
                "ASUS ROG Zephyrus G16",
                "ASUS ROG Zephyrus G14",
                "ASUS TUF Gaming F15",
                "ASUS TUF Gaming A16",
                "ASUS TUF Gaming A15",
            ],
            "MSI": [
                "MSI Raider GE78 HX",
                "MSI Raider GE68 HX",
                "MSI Titan 18 HX",
                "MSI Vector GP68 HX",
                "MSI Katana 15",
                "MSI Katana GF66",
                "MSI Cyborg 15",
                "MSI Thin GF63",
                "MSI Stealth 16",
                "MSI Stealth 14",
            ],
            "Lenovo": [
                "Lenovo Legion Pro 7 16",
                "Lenovo Legion Pro 5 16",
                "Lenovo Legion 5 16",
                "Lenovo Legion 5 15",
                "Lenovo Legion Slim 5 16",
                "Lenovo Legion Slim 7 16",
                "Lenovo IdeaPad Gaming 3 16",
            ],
            "Acer": [
                "Acer Predator Helios 18",
                "Acer Predator Helios 16",
                "Acer Nitro V 15",
                "Acer Nitro V 16",
                "Acer Nitro 5",
            ],
            "HP": [
                "HP Omen 16",
                "HP Omen 17",
                "HP Omen Transcend 16",
                "HP Victus 16",
                "HP Victus 15",
            ],
            "Dell": [
                "Dell G16 7630",
                "Dell G15 5530",
                "Dell Alienware m18 R2",
                "Dell Alienware m16 R2",
                "Dell Alienware x16 R2",
            ],
            "Gigabyte": [
                "Gigabyte AORUS 16X",
                "Gigabyte AORUS 15",
                "Gigabyte G5",
                "Gigabyte G6",
            ],
        },
    },
    # ── МОНИТОРЫ ───────────────────────────────────────────────────
    "monitors": {
        "name": "Мониторы",
        "icon": "Monitor",
        "parent": "laptops-pcs",
        "brands": {
            "Samsung": [
                'Samsung Odyssey OLED G8 32" 4K',
                'Samsung Odyssey OLED G6 27" QHD',
                'Samsung Odyssey G9 G95SC 49" OLED',
                'Samsung Odyssey G7 32" 2025',
                'Samsung ViewFinity S9 27" 5K',
                'Samsung ViewFinity S8 32"',
            ],
            "LG": [
                'LG UltraGear OLED 32GS95UE 32" 4K',
                'LG UltraGear OLED 27GS95QE 27"',
                'LG UltraGear 27GR93U 27" 4K 144Hz',
                'LG UltraWide 40WP95C 40" 5K2K',
                'LG UltraFine Ergo 32UN880 32"',
                'LG 27MR400 27"',
            ],
            "ASUS": [
                'ASUS ROG Swift OLED PG32UCDM 32" 4K',
                'ASUS ROG Swift OLED PG27AQDM 27"',
                'ASUS ProArt PA32UCXR 32" Mini LED',
                'ASUS ProArt PA278QV 27"',
                'ASUS TUF Gaming VG28UQL1A 28" 4K',
                'ASUS VZ27EHF 27"',
            ],
            "Dell": [
                'Dell UltraSharp U2725H 27" 4K IPS Black',
                'Dell UltraSharp U3225QE 32" 4K',
                'Dell Alienware AW2725DF 27" QD-OLED',
                'Dell S2725HS 27"',
            ],
            "BenQ": [
                'BenQ MOBIUZ EX2710U 27" 4K',
                'BenQ PD2706UA 27" 4K',
                "BenQ ScreenBar Halo",
                'BenQ GW2490 24"',
            ],
            "AOC": [
                'AOC AGON PRO AG276QZD2 27" OLED',
                'AOC U27G3X 27" 4K',
                'AOC CU34G3S 34" WQHD',
                'AOC 24G2SP 24"',
            ],
            "Xiaomi": [
                'Xiaomi G27i 27" 2025',
                'Xiaomi G34WQi 34" WQHD',
                'Xiaomi Monitor A27i 27"',
            ],
        },
    },
    # ── ПРОЦЕССОРЫ ─────────────────────────────────────────────────
    "cpus": {
        "name": "Процессоры",
        "icon": "Cpu",
        "parent": "pc-parts",
        "brands": {
            "Intel": [
                "Intel Core Ultra 9 285K",
                "Intel Core Ultra 9 285",
                "Intel Core Ultra 7 265K",
                "Intel Core Ultra 7 265KF",
                "Intel Core Ultra 7 265",
                "Intel Core Ultra 5 245K",
                "Intel Core Ultra 5 245KF",
                "Intel Core Ultra 5 245",
                "Intel Core i9-14900K",
                "Intel Core i7-14700K",
                "Intel Core i5-14600K",
                "Intel Core i5-14400F",
                "Intel Core i5-13400F",
                "Intel Core i3-14100F",
                "Intel Core i3-12100F",
            ],
            "AMD": [
                "AMD Ryzen 9 9950X3D",
                "AMD Ryzen 9 9950X",
                "AMD Ryzen 9 9900X3D",
                "AMD Ryzen 9 9900X",
                "AMD Ryzen 7 9800X3D",
                "AMD Ryzen 7 9700X",
                "AMD Ryzen 5 9600X",
                "AMD Ryzen 9 7950X",
                "AMD Ryzen 9 7900X",
                "AMD Ryzen 7 7800X3D",
                "AMD Ryzen 7 7700X",
                "AMD Ryzen 5 7600X",
                "AMD Ryzen 5 7600",
                "AMD Ryzen 5 7500F",
                "AMD Ryzen 5 5600X",
                "AMD Ryzen 5 5600",
            ],
        },
    },
    # ── ВИДЕОКАРТЫ ─────────────────────────────────────────────────
    "gpus": {
        "name": "Видеокарты",
        "icon": "Monitor",
        "parent": "pc-parts",
        "brands": {
            "NVIDIA": [
                "NVIDIA GeForce RTX 5090",
                "NVIDIA GeForce RTX 5080",
                "NVIDIA GeForce RTX 5070 Ti",
                "NVIDIA GeForce RTX 5070",
                "NVIDIA GeForce RTX 5060 Ti",
                "NVIDIA GeForce RTX 5060",
                "NVIDIA GeForce RTX 4090",
                "NVIDIA GeForce RTX 4080 SUPER",
                "NVIDIA GeForce RTX 4070 Ti SUPER",
                "NVIDIA GeForce RTX 4070 SUPER",
                "NVIDIA GeForce RTX 4070",
                "NVIDIA GeForce RTX 4060 Ti",
                "NVIDIA GeForce RTX 4060",
                "NVIDIA GeForce RTX 3060",
            ],
            "AMD": [
                "AMD Radeon RX 9070 XT",
                "AMD Radeon RX 9070",
                "AMD Radeon RX 9060 XT",
                "AMD Radeon RX 9060",
                "AMD Radeon RX 7900 XTX",
                "AMD Radeon RX 7900 XT",
                "AMD Radeon RX 7800 XT",
                "AMD Radeon RX 7700 XT",
                "AMD Radeon RX 7600 XT",
                "AMD Radeon RX 7600",
            ],
            "Intel": [
                "Intel Arc B580",
                "Intel Arc B570",
                "Intel Arc A770",
                "Intel Arc A750",
            ],
        },
    },
    # ── ОПЕРАТИВНАЯ ПАМЯТЬ ────────────────────────────────────────
    "ram": {
        "name": "Оперативная память",
        "icon": "HardDrive",
        "parent": "pc-parts",
        "brands": {
            "Kingston": [
                "Kingston FURY Beast DDR5 32GB 6000MHz",
                "Kingston FURY Beast DDR5 16GB 5600MHz",
                "Kingston FURY Renegade DDR5 32GB 7200MHz",
                "Kingston FURY Beast DDR4 16GB 3200MHz",
                "Kingston FURY Beast DDR4 8GB 3200MHz",
            ],
            "G.Skill": [
                "G.Skill Trident Z5 RGB DDR5 32GB 6400MHz",
                "G.Skill Trident Z5 DDR5 32GB 6000MHz",
                "G.Skill Ripjaws S5 DDR5 32GB 5600MHz",
            ],
            "Corsair": [
                "Corsair Vengeance DDR5 32GB 6000MHz",
                "Corsair Vengeance DDR5 16GB 5600MHz",
                "Corsair Dominator Platinum RGB DDR5 32GB 7200MHz",
                "Corsair Vengeance LPX DDR4 16GB 3200MHz",
            ],
            "Crucial": [
                "Crucial DDR5 32GB 5600MHz",
                "Crucial DDR5 16GB 4800MHz",
                "Crucial Ballistix DDR4 16GB 3200MHz",
            ],
            "ADATA": [
                "ADATA XPG Lancer DDR5 32GB 6000MHz",
                "ADATA XPG Gammix D45 DDR4 16GB 3200MHz",
            ],
        },
    },
    # ── SSD НАКОПИТЕЛИ ─────────────────────────────────────────────
    "ssd": {
        "name": "SSD накопители",
        "icon": "HardDrive",
        "parent": "pc-parts",
        "brands": {
            "Samsung": [
                "Samsung 990 EVO Plus 2TB",
                "Samsung 990 EVO Plus 1TB",
                "Samsung 990 PRO 2TB",
                "Samsung 990 PRO 1TB",
                "Samsung 980 PRO 1TB",
                "Samsung 870 EVO 1TB",
                "Samsung 870 EVO 500GB",
            ],
            "Kingston": [
                "Kingston NV3 2TB",
                "Kingston NV3 1TB",
                "Kingston KC3000 2TB",
                "Kingston KC3000 1TB",
                "Kingston A400 480GB",
                "Kingston A400 240GB",
            ],
            "WD": [
                "WD Black SN850X 2TB",
                "WD Black SN850X 1TB",
                "WD Blue SN580 1TB",
                "WD Blue SN580 500GB",
                "WD Green SN350 1TB",
            ],
            "Crucial": [
                "Crucial T700 2TB",
                "Crucial T700 1TB",
                "Crucial T500 2TB",
                "Crucial T500 1TB",
                "Crucial P3 Plus 1TB",
                "Crucial BX500 1TB",
            ],
            "Seagate": [
                "Seagate FireCuda 530 2TB",
                "Seagate FireCuda 530 1TB",
                "Seagate Barracuda Q5 1TB",
            ],
        },
    },
    # ── БЛОКИ ПИТАНИЯ ─────────────────────────────────────────────
    "psu": {
        "name": "Блоки питания",
        "icon": "Plug",
        "parent": "pc-parts",
        "brands": {
            "Corsair": [
                "Corsair RM1000x 1000W",
                "Corsair RM850x 850W",
                "Corsair RM750x 750W",
                "Corsair RM650x 650W",
                "Corsair CV550 550W",
            ],
            "Seasonic": [
                "Seasonic Prime TX-1000 1000W",
                "Seasonic Focus GX-850 850W",
                "Seasonic Focus GX-750 750W",
                "Seasonic Focus GX-650 650W",
            ],
            "be quiet!": [
                "be quiet! Dark Power 13 850W",
                "be quiet! Straight Power 12 750W",
                "be quiet! Pure Power 12 M 650W",
                "be quiet! System Power 10 550W",
            ],
            "DeepCool": [
                "DeepCool PX1200G 1200W",
                "DeepCool PQ850M 850W",
                "DeepCool PQ750M 750W",
                "DeepCool PF600 600W",
            ],
            "Chieftec": [
                "Chieftec Polaris Pro 850W",
                "Chieftec Proton 750W",
                "Chieftec A-135 650W",
            ],
        },
    },
    # ── КОРПУСА ────────────────────────────────────────────────────
    "cases": {
        "name": "Корпуса",
        "icon": "Box",
        "parent": "pc-parts",
        "brands": {
            "NZXT": [
                "NZXT H9 Elite",
                "NZXT H7 Elite",
                "NZXT H5 Elite",
                "NZXT H5 Flow",
                "NZXT H510 Flow",
            ],
            "Fractal Design": [
                "Fractal Design North",
                "Fractal Design North XL",
                "Fractal Design Torrent",
                "Fractal Design Pop XL Air",
                "Fractal Design Define 7",
            ],
            "be quiet!": [
                "be quiet! Dark Base 701",
                "be quiet! Pure Base 500DX",
                "be quiet! Shadow Base 800 FX",
            ],
            "Corsair": [
                "Corsair 5000D Airflow",
                "Corsair 4000D Airflow",
                "Corsair 3500X",
                "Corsair iCUE 6500X",
            ],
            "Lian Li": [
                "Lian Li O11 Dynamic EVO",
                "Lian Li Lancool III",
                "Lian Li Lancool 216",
                "Lian Li A4-H2O",
            ],
            "DeepCool": [
                "DeepCool CH780",
                "DeepCool CH560",
                "DeepCool CH510",
                "DeepCool CC560",
            ],
        },
    },
    # ── ОХЛАЖДЕНИЕ ─────────────────────────────────────────────────
    "cooling": {
        "name": "Охлаждение",
        "icon": "Fan",
        "parent": "pc-parts",
        "brands": {
            "Noctua": [
                "Noctua NH-D15 G2",
                "Noctua NH-D15",
                "Noctua NH-U12S redux",
                "Noctua NF-A12x25 PWM",
            ],
            "be quiet!": [
                "be quiet! Dark Rock Pro 5",
                "be quiet! Dark Rock 4",
                "be quiet! Pure Rock 2",
                "be quiet! Silent Wings 4",
            ],
            "DeepCool": [
                "DeepCool AK620",
                "DeepCool AK400",
                "DeepCool LS720",
                "DeepCool LT720",
                "DeepCool AG400",
            ],
            "Corsair": [
                "Corsair iCUE H170i Elite LCD",
                "Corsair iCUE H150i Elite",
                "Corsair iCUE H100i Elite",
            ],
            "Arctic": [
                "Arctic Liquid Freezer III 360",
                "Arctic Liquid Freezer III 240",
                "Arctic Freezer 36",
            ],
            "Thermalright": [
                "Thermalright Peerless Assassin 120 SE",
                "Thermalright Phantom Spirit 120",
                "Thermalright Assassin X 120",
            ],
        },
    },
    # ── МАТЕРИНСКИЕ ПЛАТЫ ──────────────────────────────────────────
    "motherboards": {
        "name": "Материнские платы",
        "icon": "Cpu",
        "parent": "pc-parts",
        "brands": {
            "ASUS": [
                "ASUS ROG Maximus Z890 Hero",
                "ASUS ROG Strix Z890-E Gaming",
                "ASUS TUF Gaming Z790-Plus WiFi",
                "ASUS TUF Gaming B760M-Plus WiFi",
                "ASUS ROG Crosshair X870E Hero",
                "ASUS ROG Strix X670E-E Gaming",
                "ASUS TUF Gaming B650-Plus WiFi",
                "ASUS Prime B550M-A WiFi II",
            ],
            "MSI": [
                "MSI MEG Z890 ACE",
                "MSI MAG Z890 Tomahawk WiFi",
                "MSI MAG B760M Mortar WiFi II",
                "MSI PRO B760M-A WiFi",
                "MSI MAG X870 Tomahawk WiFi",
                "MSI MAG B650 Tomahawk WiFi",
                "MSI PRO B650M-A WiFi",
            ],
            "Gigabyte": [
                "Gigabyte Z890 AORUS Master",
                "Gigabyte Z890 AORUS Elite WiFi",
                "Gigabyte B760M DS3H AX",
                "Gigabyte B760M Gaming X AX",
                "Gigabyte X870E AORUS Master",
                "Gigabyte B650 AORUS Elite AX",
            ],
            "ASRock": [
                "ASRock Z790 Taichi",
                "ASRock B760M Pro RS WiFi",
                "ASRock X870E Taichi",
                "ASRock B650M PG Riptide WiFi",
            ],
        },
    },
    # ── ТЕЛЕВИЗОРЫ ─────────────────────────────────────────────────
    "tvs": {
        "name": "Телевизоры",
        "icon": "Tv",
        "parent": "tv-audio",
        "brands": {
            "Samsung": [
                'Samsung QE65S95E QD-OLED 65"',
                'Samsung QE55S95E QD-OLED 55"',
                'Samsung QE75QN900E Neo QLED 8K 75"',
                'Samsung QE65QN900E Neo QLED 8K 65"',
                'Samsung QE65QN90E Neo QLED 65"',
                'Samsung QE55QN90E Neo QLED 55"',
                'Samsung The Frame LS03E 65"',
                'Samsung The Frame LS03E 55"',
                'Samsung UE55DU8000 Crystal UHD 55"',
                'Samsung UE50DU7100 50"',
                'Samsung UE43DU7100 43"',
            ],
            "LG": [
                'LG OLED77G5 evo 77"',
                'LG OLED65G5 evo 65"',
                'LG OLED65C5 65"',
                'LG OLED55C5 55"',
                'LG OLED55B5 55"',
                'LG OLED65B5 65"',
                'LG 75QNED91T6A 75"',
                'LG 65UT80006LA 65"',
                'LG 55UT80006LA 55"',
                'LG 43UT80006LA 43"',
            ],
            "Sony": [
                'Sony BRAVIA 9 XR-75X95M 75"',
                'Sony BRAVIA 9 XR-65X95M 65"',
                'Sony BRAVIA 8 XR-65A80M OLED 65"',
                'Sony BRAVIA 8 XR-55A80M OLED 55"',
                'Sony BRAVIA 7 XR-65X90M 65"',
                'Sony BRAVIA 3 KD-55X75WL 55"',
            ],
            "Hisense": [
                'Hisense 65U8NQ Mini LED 65"',
                'Hisense 55U7NQ Mini LED 55"',
                'Hisense 65E7NQ Pro QLED 65"',
                'Hisense 55A6N 55"',
                'Hisense 65A6N 65"',
                'Hisense 43A6N 43"',
            ],
            "TCL": [
                'TCL 65C855 QD-Mini LED 65"',
                'TCL 55C755 Mini LED 55"',
                'TCL 55T7E QLED 55"',
                'TCL 50P755 50"',
                'TCL 43P755 43"',
            ],
            "Xiaomi": [
                'Xiaomi TV S Pro 65" Mini LED',
                'Xiaomi TV A Pro 55" 2025',
                'Xiaomi TV A55 2025 55"',
                'Xiaomi TV A43 2025 43"',
            ],
        },
    },
    # ── АУДИОТЕХНИКА ───────────────────────────────────────────────
    "audio": {
        "name": "Аудиотехника",
        "icon": "Speaker",
        "parent": "tv-audio",
        "brands": {
            "JBL": [
                "JBL Charge 6",
                "JBL Charge 5",
                "JBL Flip 7",
                "JBL Flip 6",
                "JBL Go 4",
                "JBL Xtreme 4",
                "JBL Boombox 3",
                "JBL PartyBox 320",
                "JBL PartyBox 120",
                "JBL Clip 5",
            ],
            "Marshall": [
                "Marshall Stanmore III",
                "Marshall Acton III",
                "Marshall Woburn III",
                "Marshall Emberton III",
                "Marshall Willen II",
                "Marshall Middleton",
            ],
            "Harman Kardon": [
                "Harman Kardon Aura Studio 4",
                "Harman Kardon Onyx Studio 8",
                "Harman Kardon Luna саундбар",
            ],
            "Sony": [
                "Sony ULT Field 7",
                "Sony ULT Field 1",
                "Sony SRS-XB100",
                "Sony HT-A9M2 саундбар",
                "Sony HT-A7000 саундбар",
                "Sony BRAVIA Theatre Bar 9 саундбар",
            ],
            "Sonos": [
                "Sonos Arc Ultra саундбар",
                "Sonos Era 300",
                "Sonos Era 100",
                "Sonos Move 2",
                "Sonos Roam 2",
            ],
            "Xiaomi": [
                "Xiaomi Sound Pro",
                "Xiaomi Mi Portable Bluetooth Speaker 16W",
            ],
        },
    },
    # ── УМНЫЕ КОЛОНКИ ──────────────────────────────────────────────
    "smart-speakers": {
        "name": "Умные колонки",
        "icon": "Speaker",
        "parent": "tv-audio",
        "brands": {
            "Яндекс": [
                "Яндекс Станция Дуо Макс",
                "Яндекс Станция Макс 2",
                "Яндекс Станция 2",
                "Яндекс Станция Мини 3",
                "Яндекс Станция Лайт 2",
                "Яндекс Станция Миди 2",
            ],
            "Сбер": [
                "SberBoom Home",
                "SberBoom Mini 2",
                "SberBoom",
            ],
            "VK": [
                "VK Капсула Нео 2",
                "VK Капсула Мини",
            ],
            "Apple": [
                "Apple HomePod 2",
                "Apple HomePod mini",
            ],
        },
    },
    # ── ИГРОВЫЕ ПРИСТАВКИ ──────────────────────────────────────────
    "consoles": {
        "name": "Игровые приставки",
        "icon": "Gamepad2",
        "parent": "gaming",
        "brands": {
            "Sony": [
                "Sony PlayStation 5 Pro",
                "Sony PlayStation 5 Slim",
                "Sony PlayStation 5 Slim Digital",
                "Sony PlayStation 5",
                "Sony PlayStation 4 Slim",
                "Sony PS VR2",
            ],
            "Microsoft": [
                "Xbox Series X 2TB",
                "Xbox Series X Digital",
                "Xbox Series X",
                "Xbox Series S 1TB",
            ],
            "Nintendo": [
                "Nintendo Switch 2",
                "Nintendo Switch OLED",
                "Nintendo Switch Lite",
            ],
            "Valve": [
                "Valve Steam Deck OLED 1TB",
                "Valve Steam Deck OLED 512GB",
            ],
            "ASUS": [
                "ASUS ROG Ally X",
                "ASUS ROG Ally",
            ],
            "Lenovo": [
                "Lenovo Legion Go",
                "Lenovo Legion Go S",
            ],
            "MSI": [
                "MSI Claw 8 AI+",
                "MSI Claw A1M",
            ],
        },
    },
    # ── ИГРОВАЯ ПЕРИФЕРИЯ ──────────────────────────────────────────
    "gaming-peripherals": {
        "name": "Игровая периферия",
        "icon": "Mouse",
        "parent": "gaming",
        "brands": {
            "Logitech": [
                "Logitech G Pro X Superlight 2",
                "Logitech G502 X Lightspeed",
                "Logitech G502 X",
                "Logitech G305",
                "Logitech G203",
                "Logitech G Pro X TKL",
                "Logitech G Pro X 60",
                "Logitech G713",
                "Logitech G413 SE",
            ],
            "Razer": [
                "Razer Viper V3 Pro",
                "Razer DeathAdder V3",
                "Razer Basilisk V3",
                "Razer Orochi V2",
                "Razer Huntsman V3 Pro",
                "Razer BlackWidow V4",
                "Razer Ornata V3",
                "Razer BlackShark V2 Pro",
            ],
            "SteelSeries": [
                "SteelSeries Aerox 5 Wireless",
                "SteelSeries Prime Wireless",
                "SteelSeries Rival 3",
                "SteelSeries Apex Pro TKL",
                "SteelSeries Arctis Nova Pro Wireless",
            ],
            "HyperX": [
                "HyperX Pulsefire Haste 2",
                "HyperX Pulsefire Core",
                "HyperX Alloy Origins Core",
                "HyperX Cloud III Wireless",
                "HyperX Cloud Alpha",
            ],
            "Corsair": [
                "Corsair M75 Air Wireless",
                "Corsair Dark Core RGB Pro",
                "Corsair K70 RGB Pro",
                "Corsair K65 Plus Wireless",
                "Corsair HS80 Max Wireless",
            ],
        },
    },
    # ── КЛАВИАТУРЫ И МЫШИ ──────────────────────────────────────────
    "keyboards-mice": {
        "name": "Клавиатуры и мыши",
        "icon": "Keyboard",
        "parent": "peripherals",
        "brands": {
            "Logitech": [
                "Logitech MX Keys S",
                "Logitech MX Mechanical",
                "Logitech K380",
                "Logitech K780",
                "Logitech MX Master 3S",
                "Logitech MX Anywhere 3S",
                "Logitech M750",
                "Logitech Pebble Mouse 2",
            ],
            "Apple": [
                "Apple Magic Keyboard с Touch ID",
                "Apple Magic Keyboard",
                "Apple Magic Mouse",
                "Apple Magic Trackpad",
            ],
            "Razer": [
                "Razer Pro Type Ultra",
                "Razer Pro Click Mini",
            ],
            "Microsoft": [
                "Microsoft Ergonomic Keyboard",
                "Microsoft Sculpt Ergonomic Mouse",
                "Microsoft Modern Mobile Mouse",
            ],
        },
    },
    # ── СЕТЕВОЕ ОБОРУДОВАНИЕ ──────────────────────────────────────
    "networking": {
        "name": "Сетевое оборудование",
        "icon": "Wifi",
        "parent": "peripherals",
        "brands": {
            "TP-Link": [
                "TP-Link Archer AX73",
                "TP-Link Archer AX55",
                "TP-Link Archer AX23",
                "TP-Link Deco X50 Mesh",
                "TP-Link Deco X20 Mesh",
                "TP-Link TL-WR844N",
            ],
            "ASUS": [
                "ASUS RT-AX86U Pro",
                "ASUS RT-AX58U",
                "ASUS ZenWiFi XT9 Mesh",
            ],
            "Keenetic": [
                "Keenetic Giga KN-1012",
                "Keenetic Hopper KN-3810",
                "Keenetic Viva KN-1912",
                "Keenetic Speedster KN-3012",
                "Keenetic Lite KN-1311",
            ],
        },
    },
    # ── ПЫЛЕСОСЫ ───────────────────────────────────────────────────
    "vacuum-cleaners": {
        "name": "Пылесосы",
        "icon": "Sparkles",
        "parent": "home-appliances",
        "brands": {
            "Dyson": [
                "Dyson Gen5detect",
                "Dyson V15s Detect Submarine",
                "Dyson V15 Detect Absolute",
                "Dyson V12 Detect Slim Absolute",
                "Dyson WashG1",
            ],
            "Roborock": [
                "Roborock S9 MaxV Ultra",
                "Roborock S9 Max Plus",
                "Roborock S9 Max",
                "Roborock Qrevo MaxV",
                "Roborock Qrevo Slim",
                "Roborock Qrevo S",
                "Roborock Flexi Pro",
                "Roborock Flexi Lite",
            ],
            "Dreame": [
                "Dreame X40 Ultra",
                "Dreame X40 Master",
                "Dreame L40 Ultra",
                "Dreame L20 Ultra",
                "Dreame H14 Pro",
                "Dreame R20 Ultra",
            ],
            "Ecovacs": [
                "Ecovacs Deebot X5 Omni",
                "Ecovacs Deebot T50 Pro Omni",
                "Ecovacs Deebot T50 Omni",
                "Ecovacs Deebot X2 Omni",
            ],
            "Xiaomi": [
                "Xiaomi Robot Vacuum X20 Pro Plus",
                "Xiaomi Robot Vacuum X20 Max Plus",
                "Xiaomi Robot Vacuum X20 Max",
                "Xiaomi Truclean W20 Pro",
                "Xiaomi Vacuum Cleaner G20",
            ],
            "Samsung": [
                "Samsung Bespoke Jet Bot Combo AI",
                "Samsung Bespoke Jet AI",
                "Samsung Jet 95 Pro",
            ],
        },
    },
    # ── КОФЕМАШИНЫ ─────────────────────────────────────────────────
    "coffee-machines": {
        "name": "Кофемашины",
        "icon": "Coffee",
        "parent": "kitchen",
        "brands": {
            "De'Longhi": [
                "De'Longhi Rivelia EXAM440.55.BG",
                "De'Longhi Eletta Explore ECAM450.65.S",
                "De'Longhi Magnifica Evo ECAM290.61.B",
                "De'Longhi Dinamica Plus ECAM370.70.B",
                "De'Longhi Magnifica Start ECAM220.21",
                "De'Longhi Dedica Arte EC 885",
            ],
            "Jura": [
                "Jura J8",
                "Jura Z10",
                "Jura E8 2025",
                "Jura S8",
                "Jura ENA 4",
                "Jura ENA 8",
            ],
            "Nespresso": [
                "Nespresso Vertuo Creatista",
                "Nespresso Vertuo Pop+",
                "Nespresso Vertuo Next",
                "Nespresso Lattissima One",
                "Nespresso Pixie",
            ],
            "Philips": [
                "Philips EP5547/90 Series 5500",
                "Philips EP3349/70 Series 3300",
                "Philips EP2231/40 Series 2200",
                "Philips HD7769",
            ],
            "Krups": [
                "Krups Evidence Eco-Design EA897B",
                "Krups Intuition Preference+ EA875E",
                "Krups Essential EA8108",
            ],
        },
    },
    # ── КАМЕРЫ И БЕЗОПАСНОСТЬ ──────────────────────────────────────
    "security-cameras": {
        "name": "Камеры и безопасность",
        "icon": "Shield",
        "parent": "smart-home",
        "brands": {
            "Xiaomi": [
                "Xiaomi Smart Camera C500 Pro",
                "Xiaomi Smart Camera C400",
                "Xiaomi Smart Camera C200",
            ],
            "TP-Link": [
                "TP-Link Tapo C520WS",
                "TP-Link Tapo C225",
                "TP-Link Tapo C210",
                "TP-Link Tapo C110",
            ],
            "Aqara": [
                "Aqara Camera Hub G3",
                "Aqara Camera E1",
            ],
        },
    },
    # ── ФОТОАППАРАТЫ ───────────────────────────────────────────────
    "cameras": {
        "name": "Фотоаппараты и камеры",
        "icon": "Camera",
        "parent": "photo",
        "brands": {
            "Sony": [
                "Sony Alpha A9 III",
                "Sony Alpha A7R V",
                "Sony Alpha A7 IV",
                "Sony Alpha A7C II",
                "Sony Alpha A7C R",
                "Sony Alpha A6700",
                "Sony ZV-E10 II",
                "Sony ZV-1 II",
            ],
            "Canon": [
                "Canon EOS R1",
                "Canon EOS R5 Mark II",
                "Canon EOS R6 Mark III",
                "Canon EOS R8",
                "Canon EOS R50",
                "Canon EOS R100",
                "Canon PowerShot V10 II",
            ],
            "Nikon": [
                "Nikon Z8",
                "Nikon Z6 III",
                "Nikon Z50 II",
                "Nikon Zf",
                "Nikon Z30",
            ],
            "Fujifilm": [
                "Fujifilm X100VI",
                "Fujifilm X-T50",
                "Fujifilm X-T5",
                "Fujifilm X-M5",
                "Fujifilm X-S20",
                "Fujifilm GFX100S II",
            ],
            "GoPro": [
                "GoPro Hero 13 Black",
                "GoPro Hero 13 Black Mini",
                "GoPro Hero 12 Black",
            ],
            "DJI": [
                "DJI Osmo Action 5 Pro",
                "DJI Osmo Action 4",
                "DJI Osmo Pocket 3",
                "DJI Mini 4 Pro",
                "DJI Air 3S",
                "DJI Mavic 3 Pro",
            ],
        },
    },
    # ══════════════════════════════════════════════════════════════════
    # БЫТОВАЯ ТЕХНИКА — расширенные категории
    # ══════════════════════════════════════════════════════════════════
    # ── СТИРАЛЬНЫЕ МАШИНЫ ─────────────────────────────────────────────
    "washing-machines": {
        "name": "Стиральные машины",
        "icon": "Sparkles",
        "parent": "home-appliances",
        "brands": {
            "Samsung": [
                "Samsung Bespoke AI WW12BB944DGH 12kg",
                "Samsung Bespoke AI WW90DB7U44GB 9kg",
                "Samsung WW80T654DLH AddWash 8kg",
                "Samsung WW70AGAS21AE 7kg",
                "Samsung WD80T654DBH стирально-сушильная 8/5kg",
            ],
            "LG": [
                "LG F4WR909P2M AI DD ThinQ 9kg",
                "LG F2T9HS9W AI DD Steam 9kg",
                "LG F2V5HS0W 7kg Steam",
                "LG F4J3TM5W 8kg",
                "LG SIGNATURE WM6998HBA стирально-сушильная",
            ],
            "Bosch": [
                "Bosch Serie 8 WGB256A0BY 10kg i-DOS",
                "Bosch Serie 6 WGG254ZRSN 10kg",
                "Bosch Serie 6 WGG244A0BY 9kg",
                "Bosch WAN28263BY 8kg",
                "Bosch WNA144VLSN стирально-сушильная 9/5kg",
            ],
            "Haier": [
                "Haier I-Pro 7 Plus HW100-BD14876U1 10kg",
                "Haier HW80-BP14959S8U1 8kg Smart",
                "Haier HW70-BP14979A 7kg",
                "Haier HW60-BP12929A 6kg",
            ],
            "Beko": [
                "Beko B5WFT89418W SteamCure 9kg",
                "Beko WTE10746X0 10kg",
                "Beko WSPE7612A 7kg",
                "Beko WDPS72521MQ стирально-сушильная",
            ],
            "Electrolux": [
                "Electrolux EW8F169SA 9kg UltraCare",
                "Electrolux EW6F428BU 8kg",
                "Electrolux EW7WR268S стирально-сушильная 8/4kg",
            ],
            "Candy": [
                "Candy CS4 1072DE/2-07 7kg",
                "Candy CS34 1052DE/2-07 5kg",
                "Candy CSWS 4852DWE/1 стирально-сушильная",
            ],
        },
    },
    # ── ХОЛОДИЛЬНИКИ ──────────────────────────────────────────────────
    "refrigerators": {
        "name": "Холодильники",
        "icon": "Home",
        "parent": "home-appliances",
        "brands": {
            "Samsung": [
                "Samsung Bespoke RF24DB9900QL French Door AI 647л",
                "Samsung Bespoke RB7300T RB38A7B6F22 385л",
                "Samsung RS66A8101S9 Side-by-Side 641л",
                "Samsung RB38T602DB1 Bespoke 385л",
            ],
            "LG": [
                "LG InstaView GSXV91MBAF Side-by-Side 674л",
                "LG MoodUP GF-V700MBL LED 674л",
                "LG GBV3200CEP NoFrost 384л",
                "LG GA-B509CQSL 384л",
            ],
            "Bosch": [
                "Bosch Serie 8 KGN49AIBT VitaFresh 438л",
                "Bosch Serie 8 KFF96PIEP French Door 574л",
                "Bosch Serie 6 KGN39AICT NoFrost 368л",
                "Bosch KAI93VIFP Side-by-Side 562л",
            ],
            "Haier": [
                "Haier HTF-610DM7RU French Door 610л",
                "Haier HRF-541DG7RU Side-by-Side 541л",
                "Haier C2F636CWRG 364л",
                "Haier CEF535ACG 346л",
            ],
            "ATLANT": [
                "ATLANT ХМ 4624-101 361л",
                "ATLANT ХМ 4424-089-ND 334л",
                "ATLANT ХМ 4026-000 364л",
                "ATLANT ХМ 4214-000 292л",
            ],
            "Liebherr": [
                "Liebherr CNsdd 5253 372л",
                "Liebherr CBNa 5778 381л",
                "Liebherr CTNef 5215 414л",
            ],
            "Midea": [
                "Midea MDRB521MIE46OD NoFrost 421л",
                "Midea MRS518SNGBE1 Side-by-Side 510л",
                "Midea MDRF632FGF46 French Door 474л",
            ],
        },
    },
    # ── ПОСУДОМОЕЧНЫЕ МАШИНЫ ──────────────────────────────────────────
    "dishwashers": {
        "name": "Посудомоечные машины",
        "icon": "Droplets",
        "parent": "kitchen",
        "brands": {
            "Bosch": [
                "Bosch SMS6ZDI08E Serie 6 60см 14 комплектов",
                "Bosch SMS4HVW02E Serie 4 60см 14 комплектов",
                "Bosch SMV6ZCX42E встраиваемая Serie 6 60см",
                "Bosch SPV4EMX20E встраиваемая Serie 4 45см",
            ],
            "Electrolux": [
                "Electrolux EEM69410W встраиваемая 60см",
                "Electrolux ESA47210SW AirDry 60см",
                "Electrolux EES48400L встраиваемая 60см",
            ],
            "Midea": [
                "Midea MFD60S510Bi встраиваемая 60см",
                "Midea MFD45S510Wi 45см",
                "Midea MCFD55500W компактная",
            ],
            "Gorenje": [
                "Gorenje GS642E90W 60см 16 комплектов",
                "Gorenje GV643E90 встраиваемая 60см",
            ],
            "Beko": [
                "Beko BDFN26440XC AutoDose 60см",
                "Beko DIN48530 встраиваемая 60см",
                "Beko DTC36610W компактная",
            ],
            "Xiaomi": [
                "Xiaomi Mijia Smart Dishwasher P2 16 комплектов",
                "Xiaomi Mijia Smart Dishwasher 10 комплектов",
            ],
        },
    },
    # ── МИКРОВОЛНОВКИ ─────────────────────────────────────────────────
    "microwaves": {
        "name": "Микроволновые печи",
        "icon": "CookingPot",
        "parent": "kitchen",
        "brands": {
            "Samsung": [
                "Samsung ME88SUG/BW 23л",
                "Samsung MS30T5018AK/BW 30л",
                "Samsung MG23F302TAS/BW гриль 23л",
                "Samsung MC32B7358CC/BW конвекция 32л",
            ],
            "LG": [
                "LG MS2595GIS NeoChef 25л",
                "LG MH6535GIS гриль 25л",
                "LG MW25R95CIS конвекция 25л",
                "LG MS2042DB 20л",
            ],
            "Panasonic": [
                "Panasonic NN-GT261WZPE гриль 20л",
                "Panasonic NN-CD565BZPE конвекция 27л",
                "Panasonic NN-SD36HBZPE инвертор 23л",
            ],
            "Bosch": [
                "Bosch FFL020MS2 20л",
                "Bosch FEL023MS2 гриль 20л",
                "Bosch BFL634GS1 встраиваемая 21л",
            ],
            "Xiaomi": [
                "Xiaomi Microwave Oven 20л",
                "Xiaomi Mijia Microwave 23л",
            ],
        },
    },
    # ── КОНДИЦИОНЕРЫ ──────────────────────────────────────────────────
    "air-conditioners": {
        "name": "Кондиционеры",
        "icon": "Wind",
        "parent": "home-appliances",
        "brands": {
            "Daikin": [
                "Daikin FTXB25C/RXB25C 25м²",
                "Daikin FTXB35C/RXB35C 35м²",
                "Daikin Stylish FTXA20-35AW 20-35м²",
                "Daikin Emura FTXJ25-50MW 25-50м²",
            ],
            "Mitsubishi Electric": [
                "Mitsubishi Electric MSZ-AP25VGK 25м²",
                "Mitsubishi Electric MSZ-AP35VGK 35м²",
                "Mitsubishi Electric MSZ-LN25VGW 25м²",
                "Mitsubishi Electric MSZ-EF35VGKB 35м²",
            ],
            "Samsung": [
                "Samsung AR09BXFAMWKNEU Wind-Free 25м²",
                "Samsung AR12TXFCAWKNEU Wind-Free 35м²",
                "Samsung AR09TXHQASINEU 25м²",
            ],
            "LG": [
                "LG P09SP2 Dual Inverter 25м²",
                "LG P12EP2 Dual Inverter 35м²",
                "LG A09IWK Artcool Mirror 25м²",
                "LG PC12SQ Standard Plus 35м²",
            ],
            "Haier": [
                "Haier AS25S2SF1FA Flexis 25м²",
                "Haier AS35S2SF1FA Flexis 35м²",
                "Haier HSU-07HPL103 Lightera 20м²",
                "Haier AS09NS4ERA Dawn 25м²",
            ],
            "Ballu": [
                "Ballu BSUI-09HN8 iGreen Pro 25м²",
                "Ballu BSVP-09HN1 Vision Pro 25м²",
                "Ballu BSD-09HN1 Lagoon DC 25м²",
            ],
            "Hisense": [
                "Hisense AS-09UR4SYRDB Smart DC Inverter 25м²",
                "Hisense AS-13UR4SVPSC Premium 35м²",
            ],
        },
    },
    # ── ОБОГРЕВАТЕЛИ ──────────────────────────────────────────────────
    "heaters": {
        "name": "Обогреватели",
        "icon": "Flame",
        "parent": "home-appliances",
        "brands": {
            "Dyson": [
                "Dyson Purifier Hot+Cool Formaldehyde HP10",
                "Dyson Purifier Hot+Cool HP09",
                "Dyson Hot+Cool AM09",
            ],
            "Xiaomi": [
                "Xiaomi Smart Space Heater S 2200W",
                "Xiaomi Mi Smart Space Heater 1S 2200W",
                "Xiaomi Smartmi Smart Fan Heater",
            ],
            "Electrolux": [
                "Electrolux ECH/AG2T-2000 конвектор Transformer 2000W",
                "Electrolux EOH/M-9209 масляный 2000W",
                "Electrolux EFH/W-1020 тепловентилятор",
            ],
            "Ballu": [
                "Ballu BEC/EZMR-2000 Evolution конвектор",
                "Ballu BOH/CL-11BRN масляный",
                "Ballu BIH-APL-2.0 инфракрасный",
            ],
            "De'Longhi": [
                "De'Longhi TRRS1225 Dragon масляный 2500W",
                "De'Longhi HSX3320FTS Slim Style конвектор",
                "De'Longhi HFX65V20 Capsule керамический",
            ],
        },
    },
    # ── УВЛАЖНИТЕЛИ ВОЗДУХА ───────────────────────────────────────────
    "humidifiers": {
        "name": "Увлажнители воздуха",
        "icon": "Droplets",
        "parent": "home-appliances",
        "brands": {
            "Dyson": [
                "Dyson Purifier Big Quiet Formaldehyde BP04",
                "Dyson PH04 Purifier Humidify+Cool Formaldehyde",
                "Dyson PH03 Purifier Humidify+Cool",
            ],
            "Xiaomi": [
                "Xiaomi Smart Humidifier 2 Pro",
                "Xiaomi Smart Humidifier 2",
                "Xiaomi Smartmi Evaporative Humidifier 3",
                "Xiaomi Deerma DEM-F628S",
            ],
            "Boneco": [
                "Boneco U700 ультразвуковой",
                "Boneco U350 ультразвуковой",
                "Boneco W400 мойка воздуха",
                "Boneco E200 паровой",
            ],
            "Electrolux": [
                "Electrolux EHU-3710D ультразвуковой",
                "Electrolux EHU-3815D YOGAhealthline",
            ],
            "Philips": [
                "Philips HU3916/10 Series 3000",
                "Philips HU2716/10 Series 2000",
                "Philips AMF220/15 2-в-1 очиститель+увлажнитель",
            ],
        },
    },
    # ── УТЮГИ И ОТПАРИВАТЕЛИ ──────────────────────────────────────────
    "irons": {
        "name": "Утюги и отпариватели",
        "icon": "Sparkles",
        "parent": "home-appliances",
        "brands": {
            "Philips": [
                "Philips DST8050/20 Azur 8000 Series",
                "Philips DST7061/30 Series 7000",
                "Philips DST5040/80 Series 5000",
                "Philips STH7060/30 Stand Steamer 7000",
                "Philips STH3461/30 отпариватель 3000",
            ],
            "Tefal": [
                "Tefal FV9867 Ultimate Pure",
                "Tefal FV6870 Easygliss Plus",
                "Tefal GV9820 Pro Express Ultimate II парогенератор",
                "Tefal DT3041E0 Access Steam+ отпариватель",
            ],
            "Bosch": [
                "Bosch TDI903231A Sensixx'x DI90",
                "Bosch TDA3028210 Sensixx",
                "Bosch TDS6080 парогенератор EasyComfort",
            ],
            "Braun": [
                "Braun SI 9189 TexStyle 9 Pro",
                "Braun SI 7088 TexStyle 7 Pro",
                "Braun IS 7286 CareStyle 7 Pro парогенератор",
            ],
            "Xiaomi": [
                "Xiaomi Mijia Handheld Ironing Machine 2 Pro",
                "Xiaomi Mijia Handheld Ironing Machine 2",
            ],
        },
    },
    # ── ФЕНЫ И УКЛАДКА ────────────────────────────────────────────────
    "hair-styling": {
        "name": "Фены и стайлеры",
        "icon": "Wind",
        "parent": "beauty-health",
        "brands": {
            "Dyson": [
                "Dyson Supersonic Nural HD18",
                "Dyson Supersonic HD15",
                "Dyson Airwrap i.d. HS07",
                "Dyson Airwrap Complete Long HS05",
                "Dyson Airstrait HT01",
                "Dyson Corrale HS07 выпрямитель",
            ],
            "Philips": [
                "Philips BHD501/20 Series 5000 фен",
                "Philips BHD351/10 фен",
                "Philips BHA310/00 Airstyler",
                "Philips HP8663/00 StyleCare",
                "Philips BHS732/00 выпрямитель 7000",
            ],
            "Rowenta": [
                "Rowenta CV9920F0 Ultimate Experience фен",
                "Rowenta CF9620F0 Ultimate Experience стайлер",
                "Rowenta CV5820F0 Powerline фен",
            ],
            "Xiaomi": [
                "Xiaomi Water Ionic Hair Dryer H500",
                "Xiaomi Mi Ionic Hair Dryer H300",
                "Xiaomi ShowSee Hair Dryer A18",
            ],
            "Remington": [
                "Remington D5720 Thermacare Pro фен",
                "Remington AS8606 Curl & Straight стайлер",
                "Remington S8590 Keratin Therapy выпрямитель",
            ],
            "BaByliss": [
                "BaByliss 6720E Digital Sensor фен",
                "BaByliss AS960E Big Hair Luxe стайлер",
                "BaByliss ST492E SteamPure выпрямитель",
            ],
        },
    },
    # ── БРИТВЫ И ЭПИЛЯТОРЫ ────────────────────────────────────────────
    "shavers": {
        "name": "Бритвы и эпиляторы",
        "icon": "Scissors",
        "parent": "beauty-health",
        "brands": {
            "Philips": [
                "Philips S9986/59 Series 9000 Prestige SkinIQ",
                "Philips S7887/58 Series 7000",
                "Philips S5898/38 Series 5000",
                "Philips S3244/12 Series 3000",
                "Philips BRE740/10 Epilator Series 8000",
                "Philips MG9555/15 Multigroom All-in-One 9000",
            ],
            "Braun": [
                "Braun Series 9 Pro+ 9597cc",
                "Braun Series 8 8567cc",
                "Braun Series 7 71-N7200cc",
                "Braun Series 5 51-M1850s",
                "Braun Silk-épil 9 Flex 9-020 эпилятор",
                "Braun King C. Gillette Style Master",
            ],
            "Panasonic": [
                "Panasonic ES-LV9U Arc5 Premium",
                "Panasonic ES-LT6N Arc3",
                "Panasonic ES-RT87 Arc3",
                "Panasonic ER-GP86 триммер",
            ],
            "Xiaomi": [
                "Xiaomi Mijia Electric Shaver S700",
                "Xiaomi Mijia Electric Shaver S501",
                "Xiaomi Enchen BlackStone 3 Pro",
            ],
        },
    },
    # ── ЭЛЕКТРИЧЕСКИЕ ЗУБНЫЕ ЩЁТКИ ───────────────────────────────────
    "toothbrushes": {
        "name": "Электрические зубные щётки",
        "icon": "Smile",
        "parent": "beauty-health",
        "brands": {
            "Oral-B": [
                "Oral-B iO Series 10 с AI",
                "Oral-B iO Series 9",
                "Oral-B iO Series 7",
                "Oral-B iO Series 5",
                "Oral-B iO Series 4",
                "Oral-B Pro 3 3500",
                "Oral-B Vitality Pro",
            ],
            "Philips": [
                "Philips Sonicare DiamondClean 9900 Prestige HX9992",
                "Philips Sonicare DiamondClean 9000 HX9911",
                "Philips Sonicare ExpertClean 7300",
                "Philips Sonicare ProtectiveClean 6100",
                "Philips Sonicare 4100",
            ],
            "Xiaomi": [
                "Xiaomi Mi Smart Electric Toothbrush T700",
                "Xiaomi Mi Electric Toothbrush T500C",
                "Xiaomi Mi Electric Toothbrush T302",
            ],
            "Revyline": [
                "Revyline RL 070",
                "Revyline RL 060",
                "Revyline RL 050",
                "Revyline RL 040",
            ],
        },
    },
    # ── МУЛЬТИВАРКИ ───────────────────────────────────────────────────
    "multicookers": {
        "name": "Мультиварки",
        "icon": "CookingPot",
        "parent": "kitchen",
        "brands": {
            "Redmond": [
                "Redmond RMC-M252 Smart",
                "Redmond RMC-M225S",
                "Redmond RMC-PM504",
                "Redmond SkyCooker M903S",
            ],
            "Moulinex": [
                "Moulinex Cookeo Touch WiFi CE902832",
                "Moulinex Cookeo CE855A32",
                "Moulinex CE503132 мультиварка-скороварка",
            ],
            "Philips": [
                "Philips HD2151/80 All-in-One скороварка",
                "Philips HD2237/40 All-in-One Plus",
            ],
            "Xiaomi": [
                "Xiaomi Mijia Smart Rice Cooker Pro 4L",
                "Xiaomi Mijia Smart Pressure Cooker 2 5L",
            ],
            "Polaris": [
                "Polaris PMC 0556D",
                "Polaris PMC 0530AD WiFi",
                "Polaris PMC 0523AD",
            ],
        },
    },
    # ── ЧАЙНИКИ ───────────────────────────────────────────────────────
    "kettles": {
        "name": "Электрочайники",
        "icon": "CookingPot",
        "parent": "kitchen",
        "brands": {
            "Bosch": [
                "Bosch TWK8613P Styline 1.5л",
                "Bosch TWK7090B 1.5л",
                "Bosch TWK3A017 CompactClass 1.7л",
            ],
            "Philips": [
                "Philips HD9350/90 Daily Collection 1.7л",
                "Philips HD9365/10 Viva Collection 1.7л",
            ],
            "Xiaomi": [
                "Xiaomi Mi Smart Kettle Pro 2 1.5л",
                "Xiaomi Mijia Thermostatic Kettle 2 1.5л",
            ],
            "Tefal": [
                "Tefal KO855E30 Smart&Light 1.7л",
                "Tefal KI270D30 Express 1.7л",
                "Tefal KI583D10 Includeo 1.5л",
            ],
            "Redmond": [
                "Redmond SkyKettle M216S 1.7л",
                "Redmond RK-M170S-E 1.7л",
            ],
            "Kitfort": [
                "Kitfort KT-6115 1.5л",
                "Kitfort KT-639 1.7л с терморегулятором",
                "Kitfort KT-6603 1.7л",
            ],
        },
    },
    # ── БЛЕНДЕРЫ ──────────────────────────────────────────────────────
    "blenders": {
        "name": "Блендеры и миксеры",
        "icon": "CookingPot",
        "parent": "kitchen",
        "brands": {
            "Bosch": [
                "Bosch MSM67170 погружной 750W",
                "Bosch MMBM7G3M стационарный",
                "Bosch ErgoMixx MS6CB6110 погружной 1000W",
            ],
            "Philips": [
                "Philips HR2621/90 Viva ProMix погружной",
                "Philips HR3573/90 Avance стационарный",
                "Philips HR2500/00 Eco Conscious стационарный",
            ],
            "Braun": [
                "Braun MQ9187XLI MultiQuick 9 погружной",
                "Braun MQ7035X MultiQuick 7 погружной",
                "Braun JB3272SI PowerBlend 3 стационарный",
            ],
            "Xiaomi": [
                "Xiaomi Smart Blender 1000W",
                "Xiaomi Mijia Portable Blender Cup",
            ],
            "Kitfort": [
                "Kitfort KT-1370 погружной",
                "Kitfort KT-3022 стационарный",
            ],
        },
    },
    # ── УМНОЕ ОСВЕЩЕНИЕ ───────────────────────────────────────────────
    "smart-lighting": {
        "name": "Умное освещение",
        "icon": "Lightbulb",
        "parent": "smart-home",
        "brands": {
            "Yeelight": [
                "Yeelight LED Smart Bulb W4 E27",
                "Yeelight Arwen Ceiling Light 550S",
                "Yeelight LED Lightstrip Pro 2m",
                "Yeelight Staria Pro Bedside Lamp",
            ],
            "Philips Hue": [
                "Philips Hue White and Color Ambiance E27 Gen 3",
                "Philips Hue Go Portable Table Lamp",
                "Philips Hue Gradient Lightstrip 2m",
                "Philips Hue Play Light Bar набор",
                "Philips Hue Bridge 2.0",
            ],
            "Xiaomi": [
                "Xiaomi Smart LED Bulb Essential E27",
                "Xiaomi Mi LED Ceiling Light Pro",
                "Xiaomi Mi LED Desk Lamp Pro 2",
            ],
            "IKEA": [
                "IKEA DIRIGERA Hub умный дом",
                "IKEA TRADFRI LED лампа E27",
                "IKEA SYMFONISK WiFi колонка-лампа",
            ],
            "Aqara": [
                "Aqara LED Light Bulb T1 E27",
                "Aqara LED Strip T1",
                "Aqara Ceiling Light T1M",
            ],
        },
    },
}

# ── Группы верхнего уровня ────────────────────────────────────────
GROUPS = [
    {
        "slug": "smartphones-gadgets",
        "name": "Смартфоны и гаджеты",
        "icon": "Smartphone",
        "children": [
            "smartphones",
            "tablets",
            "headphones",
            "smartwatches",
            "fitness-bands",
            "powerbanks",
        ],
    },
    {
        "slug": "laptops-pcs",
        "name": "Ноутбуки и компьютеры",
        "icon": "Laptop",
        "children": ["laptops", "gaming-laptops", "monitors"],
    },
    {
        "slug": "pc-parts",
        "name": "Комплектующие для ПК",
        "icon": "Cpu",
        "children": ["cpus", "gpus", "motherboards", "ram", "ssd", "psu", "cases", "cooling"],
    },
    {
        "slug": "tv-audio",
        "name": "ТВ и аудио",
        "icon": "Tv",
        "children": ["tvs", "audio", "smart-speakers"],
    },
    {"slug": "photo", "name": "Фототехника", "icon": "Camera", "children": ["cameras"]},
    {
        "slug": "gaming",
        "name": "Игры и консоли",
        "icon": "Gamepad2",
        "children": ["consoles", "gaming-peripherals"],
    },
    {
        "slug": "peripherals",
        "name": "Периферия",
        "icon": "Keyboard",
        "children": ["keyboards-mice", "networking"],
    },
    {
        "slug": "home-appliances",
        "name": "Техника для дома",
        "icon": "Home",
        "children": [
            "vacuum-cleaners",
            "washing-machines",
            "refrigerators",
            "air-conditioners",
            "heaters",
            "humidifiers",
            "irons",
        ],
    },
    {
        "slug": "kitchen",
        "name": "Техника для кухни",
        "icon": "CookingPot",
        "children": [
            "coffee-machines",
            "dishwashers",
            "microwaves",
            "multicookers",
            "kettles",
            "blenders",
        ],
    },
    {
        "slug": "beauty-health",
        "name": "Красота и здоровье",
        "icon": "Heart",
        "children": ["hair-styling", "shavers", "toothbrushes"],
    },
    {
        "slug": "smart-home",
        "name": "Умный дом",
        "icon": "Lightbulb",
        "children": ["security-cameras", "smart-lighting"],
    },
]


# ── Count stats ───────────────────────────────────────────────────
def _count_models(slug: str) -> int:
    cat = CATALOG.get(slug, {})
    return sum(len(models) for models in cat.get("brands", {}).values())


def _count_brands(slug: str) -> int:
    return len(CATALOG.get(slug, {}).get("brands", {}))


# ══════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ══════════════════════════════════════════════════════════════════


@router.get("/tree")
async def get_catalog_tree():
    """Return catalog tree for top-level navigation."""
    result = []
    for group in GROUPS:
        children = []
        for child_slug in group["children"]:
            cat = CATALOG.get(child_slug, {})
            children.append(
                {
                    "name": cat.get("name", child_slug),
                    "slug": child_slug,
                    "icon": cat.get("icon", ""),
                    "brands_count": _count_brands(child_slug),
                    "models_count": _count_models(child_slug),
                }
            )
        result.append(
            {
                "name": group["name"],
                "slug": group["slug"],
                "icon": group["icon"],
                "children": children,
            }
        )
    return result


@router.get("/category/{slug}")
async def get_category(slug: str):
    """Get category with its brands and model counts."""
    cat = CATALOG.get(slug)
    if not cat:
        # Maybe it's a group slug
        for group in GROUPS:
            if group["slug"] == slug:
                children = []
                for child_slug in group["children"]:
                    c = CATALOG.get(child_slug, {})
                    children.append(
                        {
                            "name": c.get("name", child_slug),
                            "slug": child_slug,
                            "icon": c.get("icon", ""),
                            "brands_count": _count_brands(child_slug),
                            "models_count": _count_models(child_slug),
                        }
                    )
                return {
                    "name": group["name"],
                    "slug": slug,
                    "icon": group["icon"],
                    "children": children,
                    "type": "group",
                }
        raise HTTPException(status_code=404, detail="Category not found")

    brands = []
    for brand_name, models in cat["brands"].items():
        brands.append(
            {
                "name": brand_name,
                "count": len(models),
            }
        )
    brands.sort(key=lambda b: b["count"], reverse=True)

    return {
        "name": cat["name"],
        "slug": slug,
        "icon": cat.get("icon", ""),
        "brands": brands,
        "total_models": _count_models(slug),
        "type": "category",
    }


@router.get("/browse/{slug}")
async def browse_category(
    slug: str,
    brand: str = Query("", description="Filter by brand name"),
):
    """Browse a category — returns brands and product models.

    Without brand: returns all brands with counts
    With brand: returns models for that brand
    """
    cat = CATALOG.get(slug)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    all_brands = []
    for brand_name, models in cat["brands"].items():
        all_brands.append({"name": brand_name, "count": len(models)})
    all_brands.sort(key=lambda b: b["count"], reverse=True)

    if brand:
        models = cat["brands"].get(brand, [])
        # Also try case-insensitive
        if not models:
            for bname, bmodels in cat["brands"].items():
                if bname.lower() == brand.lower():
                    models = bmodels
                    break
        return {
            "name": cat["name"],
            "slug": slug,
            "brands": all_brands,
            "products": [{"title": m, "brand": brand} for m in models],
            "total": len(models),
            "filtered_by_brand": brand,
        }

    return {
        "name": cat["name"],
        "slug": slug,
        "brands": all_brands,
        "products": [],
        "total": _count_models(slug),
        "filtered_by_brand": None,
    }
