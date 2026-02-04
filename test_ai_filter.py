import anthropic
import json

# Результаты поиска (пример)
products = [
    {"title": "iPhone 16e EU 8/128 ГБ, белый", "price_num": 40728, "marketplace": "ozon"},
    {"title": "iPhone 16 128GB", "price_num": 52990, "marketplace": "wildberries"},
    {"title": "iPhone 16 128GB Black", "price_num": 54463, "marketplace": "wildberries"},
    {"title": "iPhone 16 Pro Dual SIM 8/128 ГБ", "price_num": 72648, "marketplace": "ozon"},
    {"title": "iPhone 16 Plus EU 8/128 ГБ", "price_num": 58365, "marketplace": "ozon"},
    {"title": "iPhone 16 256GB", "price_num": 64395, "marketplace": "wildberries"},
]

user_query = "iPhone 16 128GB"

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": f"""Пользователь ищет: "{user_query}"

Вот список найденных товаров:
{json.dumps(products, ensure_ascii=False, indent=2)}

Задача:
1. Определи какие товары ТОЧНО соответствуют запросу (та же модель, тот же объём памяти)
2. Исключи другие модели (16e, 16 Pro, 16 Plus, другой объём памяти)
3. Верни JSON со структурой:

{{
  "query_interpreted": "что именно ищет пользователь",
  "matching_products": [список индексов товаров которые подходят],
  "excluded": [
    {{"index": 0, "reason": "причина исключения"}}
  ],
  "best_match": {{
    "index": номер лучшего товара,
    "title": "название",
    "price": цена,
    "marketplace": "площадка"
  }},
  "warning": "предупреждение если есть похожие но не те товары"
}}

Только JSON, без пояснений."""
    }]
)

print("=== AI АНАЛИЗ ===\n")
print(response.content[0].text)
