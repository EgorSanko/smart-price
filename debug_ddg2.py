from urllib.parse import unquote
import re

with open('ddg_debug.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Все результаты
results = re.findall(
    r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?class="result__snippet"[^>]*>(.*?)</a>',
    text, re.DOTALL
)

print(f"Found {len(results)} results\n")

for i, (link, title_html, snippet) in enumerate(results[:10]):
    # Decode URL
    real_url = link
    uddg = re.search(r'uddg=([^&]+)', link)
    if uddg:
        real_url = unquote(uddg.group(1))
    
    title = re.sub(r'<[^>]+>', '', title_html).strip()
    snippet_clean = re.sub(r'<[^>]+>', '', snippet).strip()
    
    # Search for prices
    prices = re.findall(r'(\d[\d\s]*)\s*[₽руб]', snippet_clean)
    
    print(f"--- Result {i+1} ---")
    print(f"Title: {title}")
    print(f"URL: {real_url}")
    print(f"Snippet: {snippet_clean[:150]}")
    print(f"Prices: {prices}")
    print()
