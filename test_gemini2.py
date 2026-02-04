from google import genai
import json

client = genai.Client(api_key="AIzaSyAeugEv0zUYClmT1RA61EWOTMdeGaKvTM4")

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
2. iPhone 16e  это ДРУГАЯ модель (бюджетная), не iPhone 16!
3. iPhone 16 Pro, Plus  тоже другие модели
4. Проверь объём памяти (128GB  256GB)

Верни ТОЛЬКО JSON:
{{
  "matching_products": [
    {{"title": "...", "price_num": ..., "marketplace": "...", "why": "почему подходит"}}
  ],
  "excluded": [
    {{"title": "...", "reason": "почему не подходит"}}
  ],
  "best_price": {{"title": "...", "price_num": ..., "marketplace": "..."}},
  "summary": "краткий вывод для пользователя"
}}"""

print(" Спрашиваем Gemini...\n")
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=prompt
)
print(response.text)
