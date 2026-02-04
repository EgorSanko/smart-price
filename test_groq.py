from groq import Groq
import json

client = Groq(api_key="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")

products = [
    {"title": "iPhone 16e EU 8/128 ГБ, белый", "price_num": 40728, "marketplace": "ozon"},
    {"title": "iPhone 16 128GB", "price_num": 52990, "marketplace": "wildberries"},
    {"title": "iPhone 16 128GB Black", "price_num": 54463, "marketplace": "wildberries"},
    {"title": "iPhone 16 Pro Dual SIM 8/128 ГБ", "price_num": 72648, "marketplace": "ozon"},
    {"title": "iPhone 16 Plus EU 8/128 ГБ", "price_num": 58365, "marketplace": "ozon"},
    {"title": "iPhone 16 256GB", "price_num": 64395, "marketplace": "wildberries"},
    {"title": "Смартфон Apple iPhone 16 128GB White", "price_num": 72764, "marketplace": "yandex"},
]

user_query = "iPhone 16 128GB"

prompt = f"""Пользователь ищет: "{user_query}"

Список найденных товаров:
{json.dumps(products, ensure_ascii=False, indent=2)}

Задача:
1. Определи какие товары ТОЧНО соответствуют запросу
2. iPhone 16e  это ДРУГАЯ модель (бюджетная), НЕ iPhone 16!
3. iPhone 16 Pro, Plus  тоже другие модели
4. Проверь объём памяти (128GB != 256GB)

Верни ТОЛЬКО JSON:
{{
  "matching_products": [
    {{"title": "...", "price_num": ..., "marketplace": "..."}}
  ],
  "excluded": [
    {{"title": "...", "reason": "..."}}
  ],
  "best_price": {{"title": "...", "price_num": ..., "marketplace": "..."}},
  "summary": "краткий вывод"
}}"""

print(" Спрашиваем Groq (Llama 3.3 70B)...\n")

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.1
)

print(response.choices[0].message.content)
