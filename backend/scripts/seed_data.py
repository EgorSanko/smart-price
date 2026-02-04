"""
Seed database with test data for development.

Usage:
    python -m scripts.seed_data
    
Or via Docker:
    docker exec smart_price_backend python -m scripts.seed_data
"""

import asyncio
import random
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_maker
from app.db.models import Marketplace, Category, Product, PriceHistory


# Test data
MARKETPLACES = [
    {"name": "ozon", "display_name": "Ozon", "base_url": "https://www.ozon.ru", "is_active": True},
    {"name": "wildberries", "display_name": "Wildberries", "base_url": "https://www.wildberries.ru", "is_active": True},
    {"name": "yandex_market", "display_name": "Яндекс Маркет", "base_url": "https://market.yandex.ru", "is_active": True},
]

CATEGORIES = [
    {"name": "Смартфоны", "slug": "smartphones"},
    {"name": "Ноутбуки", "slug": "laptops"},
    {"name": "Наушники", "slug": "headphones"},
    {"name": "Телевизоры", "slug": "tvs"},
    {"name": "Планшеты", "slug": "tablets"},
]

PRODUCTS = [
    # Смартфоны
    {
        "title": "Apple iPhone 15 Pro Max 256GB",
        "brand": "Apple",
        "category_slug": "smartphones",
        "base_price": 129990,
        "description": "Флагманский смартфон Apple с чипом A17 Pro, титановым корпусом и продвинутой камерой",
        "rating": 4.9,
        "reviews_count": 1250,
    },
    {
        "title": "Apple iPhone 15 128GB",
        "brand": "Apple",
        "category_slug": "smartphones",
        "base_price": 84990,
        "description": "Смартфон Apple с Dynamic Island, камерой 48 Мп и чипом A16 Bionic",
        "rating": 4.8,
        "reviews_count": 3420,
    },
    {
        "title": "Apple iPhone 14 128GB",
        "brand": "Apple",
        "category_slug": "smartphones",
        "base_price": 69990,
        "description": "Смартфон с отличной камерой и долгим временем автономной работы",
        "rating": 4.7,
        "reviews_count": 5680,
    },
    {
        "title": "Samsung Galaxy S24 Ultra 256GB",
        "brand": "Samsung",
        "category_slug": "smartphones",
        "base_price": 119990,
        "description": "Флагман Samsung с AI-функциями, S Pen и камерой 200 Мп",
        "rating": 4.8,
        "reviews_count": 890,
    },
    {
        "title": "Samsung Galaxy S24 128GB",
        "brand": "Samsung",
        "category_slug": "smartphones",
        "base_price": 79990,
        "description": "Компактный флагман с мощным процессором и яркий AMOLED экраном",
        "rating": 4.7,
        "reviews_count": 1560,
    },
    {
        "title": "Xiaomi 14 Ultra 512GB",
        "brand": "Xiaomi",
        "category_slug": "smartphones",
        "base_price": 89990,
        "description": "Камерофон с оптикой Leica и флагманским процессором Snapdragon 8 Gen 3",
        "rating": 4.6,
        "reviews_count": 340,
    },
    {
        "title": "Google Pixel 8 Pro 128GB",
        "brand": "Google",
        "category_slug": "smartphones",
        "base_price": 84990,
        "description": "Смартфон Google с лучшей камерой в классе и чистым Android",
        "rating": 4.7,
        "reviews_count": 780,
    },
    # Ноутбуки
    {
        "title": "Apple MacBook Air 13 M3 256GB",
        "brand": "Apple",
        "category_slug": "laptops",
        "base_price": 109990,
        "description": "Ультратонкий ноутбук Apple с чипом M3 и дисплеем Liquid Retina",
        "rating": 4.9,
        "reviews_count": 560,
    },
    {
        "title": "Apple MacBook Pro 14 M3 Pro 512GB",
        "brand": "Apple",
        "category_slug": "laptops",
        "base_price": 199990,
        "description": "Профессиональный ноутбук с чипом M3 Pro и XDR дисплеем",
        "rating": 4.9,
        "reviews_count": 320,
    },
    {
        "title": "ASUS ROG Strix G16 RTX 4070",
        "brand": "ASUS",
        "category_slug": "laptops",
        "base_price": 159990,
        "description": "Игровой ноутбук с RTX 4070 и процессором Intel Core i9",
        "rating": 4.7,
        "reviews_count": 230,
    },
    {
        "title": "Lenovo ThinkPad X1 Carbon Gen 11",
        "brand": "Lenovo",
        "category_slug": "laptops",
        "base_price": 149990,
        "description": "Бизнес-ультрабук с процессором Intel Core i7 и 14\" 2.8K дисплеем",
        "rating": 4.8,
        "reviews_count": 180,
    },
    # Наушники
    {
        "title": "Apple AirPods Pro 2",
        "brand": "Apple",
        "category_slug": "headphones",
        "base_price": 24990,
        "description": "TWS наушники с активным шумоподавлением и пространственным звуком",
        "rating": 4.8,
        "reviews_count": 8900,
    },
    {
        "title": "Sony WH-1000XM5",
        "brand": "Sony",
        "category_slug": "headphones",
        "base_price": 34990,
        "description": "Полноразмерные наушники с лучшим шумоподавлением в классе",
        "rating": 4.9,
        "reviews_count": 4200,
    },
    {
        "title": "Samsung Galaxy Buds2 Pro",
        "brand": "Samsung",
        "category_slug": "headphones",
        "base_price": 14990,
        "description": "TWS наушники с Hi-Fi звуком и интеллектуальным ANC",
        "rating": 4.6,
        "reviews_count": 2300,
    },
    {
        "title": "JBL Tune 770NC",
        "brand": "JBL",
        "category_slug": "headphones",
        "base_price": 7990,
        "description": "Беспроводные наушники с шумоподавлением и 70 часами работы",
        "rating": 4.5,
        "reviews_count": 1890,
    },
    # Телевизоры
    {
        "title": "LG OLED55C3 55\"",
        "brand": "LG",
        "category_slug": "tvs",
        "base_price": 129990,
        "description": "OLED телевизор с идеальным чёрным и процессором α9 Gen6",
        "rating": 4.9,
        "reviews_count": 670,
    },
    {
        "title": "Samsung QE65QN85C 65\"",
        "brand": "Samsung",
        "category_slug": "tvs",
        "base_price": 149990,
        "description": "Neo QLED телевизор с Mini LED подсветкой и 4K 120Hz",
        "rating": 4.8,
        "reviews_count": 420,
    },
    {
        "title": "Xiaomi TV A Pro 55\"",
        "brand": "Xiaomi",
        "category_slug": "tvs",
        "base_price": 34990,
        "description": "4K телевизор с Google TV и Dolby Vision",
        "rating": 4.5,
        "reviews_count": 2100,
    },
    # Планшеты
    {
        "title": "Apple iPad Pro 11 M4 256GB",
        "brand": "Apple",
        "category_slug": "tablets",
        "base_price": 99990,
        "description": "Самый тонкий iPad с чипом M4 и OLED дисплеем",
        "rating": 4.9,
        "reviews_count": 280,
    },
    {
        "title": "Apple iPad Air 11 M2 128GB",
        "brand": "Apple",
        "category_slug": "tablets",
        "base_price": 59990,
        "description": "Планшет с чипом M2 и поддержкой Apple Pencil Pro",
        "rating": 4.8,
        "reviews_count": 560,
    },
    {
        "title": "Samsung Galaxy Tab S9 Ultra",
        "brand": "Samsung",
        "category_slug": "tablets",
        "base_price": 109990,
        "description": "Флагманский планшет с 14.6\" AMOLED экраном и S Pen",
        "rating": 4.7,
        "reviews_count": 340,
    },
]


def generate_price_variation(base_price: float, marketplace_index: int) -> float:
    """Generate price with variation for different marketplaces."""
    # Different marketplaces have slightly different prices
    variation = random.uniform(-0.08, 0.12)  # -8% to +12%
    marketplace_offset = (marketplace_index - 1) * 0.02  # Each marketplace slightly different
    
    price = base_price * (1 + variation + marketplace_offset)
    # Round to nice numbers
    return round(price / 100) * 100


def generate_price_history(
    current_price: float,
    days: int = 90
) -> list[tuple[datetime, float]]:
    """Generate realistic price history."""
    history = []
    price = current_price * random.uniform(1.05, 1.15)  # Start higher
    
    for i in range(days, 0, -1):
        date = datetime.utcnow() - timedelta(days=i)
        
        # Random daily fluctuation
        change = random.uniform(-0.02, 0.02)
        
        # Occasional sales (drop 10-20%)
        if random.random() < 0.05:  # 5% chance of sale
            change = random.uniform(-0.20, -0.10)
        
        # Occasional price increases
        if random.random() < 0.03:  # 3% chance
            change = random.uniform(0.05, 0.10)
        
        price = price * (1 + change)
        price = max(price, current_price * 0.8)  # Don't go too low
        price = min(price, current_price * 1.3)  # Don't go too high
        
        history.append((date, round(price / 100) * 100))
    
    # Last entry is current price
    history.append((datetime.utcnow(), current_price))
    
    return history


async def seed_marketplaces(session: AsyncSession) -> dict[str, Marketplace]:
    """Create marketplaces."""
    marketplaces = {}
    
    for mp_data in MARKETPLACES:
        # Check if exists
        result = await session.execute(
            select(Marketplace).where(Marketplace.name == mp_data["name"])
        )
        marketplace = result.scalar_one_or_none()
        
        if not marketplace:
            marketplace = Marketplace(**mp_data)
            session.add(marketplace)
            await session.flush()
            print(f"  ✅ Created marketplace: {mp_data['display_name']}")
        else:
            print(f"  ⏭️  Marketplace exists: {mp_data['display_name']}")
        
        marketplaces[mp_data["name"]] = marketplace
    
    return marketplaces


async def seed_categories(session: AsyncSession) -> dict[str, Category]:
    """Create categories."""
    categories = {}
    
    for cat_data in CATEGORIES:
        result = await session.execute(
            select(Category).where(Category.slug == cat_data["slug"])
        )
        category = result.scalar_one_or_none()
        
        if not category:
            category = Category(**cat_data)
            session.add(category)
            await session.flush()
            print(f"  ✅ Created category: {cat_data['name']}")
        else:
            print(f"  ⏭️  Category exists: {cat_data['name']}")
        
        categories[cat_data["slug"]] = category
    
    return categories


async def seed_products(
    session: AsyncSession,
    marketplaces: dict[str, Marketplace],
    categories: dict[str, Category]
) -> None:
    """Create products with price history."""
    mp_list = list(marketplaces.values())
    
    for product_data in PRODUCTS:
        category = categories.get(product_data["category_slug"])
        
        # Create product for each marketplace
        for i, marketplace in enumerate(mp_list):
            external_id = f"{product_data['title'][:20].replace(' ', '_')}_{marketplace.name}"
            
            # Check if exists
            result = await session.execute(
                select(Product).where(
                    Product.external_id == external_id,
                    Product.marketplace_id == marketplace.id
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"  ⏭️  Product exists: {product_data['title'][:30]}... on {marketplace.name}")
                continue
            
            current_price = generate_price_variation(product_data["base_price"], i)
            original_price = current_price * random.uniform(1.1, 1.3) if random.random() > 0.5 else None
            
            product = Product(
                external_id=external_id,
                marketplace_id=marketplace.id,
                category_id=category.id if category else None,
                title=product_data["title"],
                brand=product_data["brand"],
                description=product_data["description"],
                current_price=current_price,
                original_price=original_price,
                currency="RUB",
                url=f"{marketplace.base_url}/product/{external_id}",
                image_url=f"https://via.placeholder.com/400x400.png?text={product_data['brand']}",
                rating=product_data["rating"] + random.uniform(-0.2, 0.1),
                reviews_count=int(product_data["reviews_count"] * random.uniform(0.8, 1.2)),
                is_available=random.random() > 0.1,  # 90% in stock
                seller_name=f"{marketplace.display_name} Official",
                last_scraped_at=datetime.utcnow(),
            )
            session.add(product)
            await session.flush()
            
            # Generate price history
            history = generate_price_history(current_price)
            for date, price in history:
                price_record = PriceHistory(
                    product_id=product.id,
                    price=price,
                    original_price=original_price,
                    currency="RUB",
                    recorded_at=date,
                )
                session.add(price_record)
            
            print(f"  ✅ Created: {product_data['title'][:35]}... on {marketplace.name} — {current_price:,.0f} ₽")
    
    await session.flush()


async def main():
    """Run seeding."""
    print("\n🌱 Seeding database with test data...\n")
    
    async with async_session_maker() as session:
        try:
            print("📦 Creating marketplaces...")
            marketplaces = await seed_marketplaces(session)
            
            print("\n📁 Creating categories...")
            categories = await seed_categories(session)
            
            print("\n🛍️  Creating products...")
            await seed_products(session, marketplaces, categories)
            
            await session.commit()
            print("\n✅ Database seeded successfully!\n")
            
            # Print summary
            result = await session.execute(select(Product))
            products = result.scalars().all()
            print(f"📊 Total products: {len(products)}")
            
            result = await session.execute(select(PriceHistory))
            history = result.scalars().all()
            print(f"📈 Total price points: {len(history)}")
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ Error: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
