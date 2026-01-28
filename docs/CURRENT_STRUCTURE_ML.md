# Smart Price — ML Components (Task 06)

## Созданные файлы

```
backend/app/
├── ml/
│   ├── __init__.py              
│   ├── embeddings/
│   │   ├── __init__.py          
│   │   └── encoder.py           # EmbeddingService
│   └── matching/
│       ├── __init__.py          
│       └── matcher.py           # ProductMatcher
│
├── services/
│   ├── qdrant_service.py        # QdrantService
│   └── product_indexer.py       # ProductIndexer
│
└── tests/test_ml/
    ├── __init__.py
    ├── test_encoder.py
    └── test_matcher.py
```

---

## Использование

### 1. EmbeddingService

```python
from app.ml.embeddings import EmbeddingService

# Автоматически выбирает OpenAI или TF-IDF fallback
service = EmbeddingService()

# Эмбеддинг текста
embedding = await service.encode("iPhone 15 Pro Max 256GB")

# Эмбеддинг продукта
product = {
    "title": "iPhone 15 Pro Max 256GB",
    "brand": "Apple",
    "description": "Флагманский смартфон",
}
embedding = await service.encode_product(product)
print(len(embedding))  # 1536 (OpenAI) или 256 (TF-IDF)
```

### 2. QdrantService

```python
from app.services.qdrant_service import get_qdrant_service

qdrant = get_qdrant_service(host="qdrant", port=6333)

# Инициализация коллекции
await qdrant.init_collection("products", dimension=1536)

# Добавление товара
await qdrant.upsert_product(
    product_id=123,
    embedding=embedding,
    title="iPhone 15 Pro",
    marketplace_id=1,
    price=99990,
    brand="Apple",
)

# Поиск
results = await qdrant.search_products(
    query_vector=embedding,
    limit=20,
    marketplace_ids=[1, 2],
    max_price=100000,
)
```

### 3. ProductMatcher

```python
from app.ml.matching import ProductMatcher

matcher = ProductMatcher(embedding_service, qdrant_service)

# Найти совпадения
matches = await matcher.find_matches(product_id=123)

for match in matches:
    print(f"{match.title}: {match.score:.2f} ({match.match_type})")

# Сравнение цен
comparison = await matcher.compare_prices(product_id=123)
print(f"Лучшая цена: {comparison['best_price']['price']}")
```

### 4. ProductIndexer

```python
from app.services.product_indexer import ProductIndexer

indexer = ProductIndexer(embedding_service, qdrant_service)

# Инициализация индекса
await indexer.init_index()

# Индексация товара
await indexer.index_product(product)

# Batch индексация
await indexer.index_products(products, batch_size=100)
```

---

## Конфигурация

```env
# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# OpenAI (опционально)
OPENAI_API_KEY=sk-...
```

**Без OPENAI_API_KEY** — используется TF-IDF fallback (dimension=256).

---

## Тестирование

```bash
# Запуск тестов
docker compose exec backend pytest tests/test_ml/ -v

# Проверка Qdrant
curl http://localhost:6333/collections
```
