# -*- coding: utf-8 -*-
"""Heuristic plagiarism risk scan.

We can't talk to antiplagiat.ru (needs paid institutional account), but we
CAN flag paragraphs that look "encyclopedic" — generic, definition-like
prose that often gets paraphrased from Wikipedia, vendor docs, or industry
reports and therefore reads identically across many sources.

Heuristics:
  1. Vendor/product definitions: ("X — это Y, разработанная в году Z")
  2. Industry statistics with specific numbers ("оборот рынка составил X
     рублей по данным АКИТ")
  3. Framework descriptions ("FastAPI представляет собой современный
     веб-фреймворк, поддерживающий асинхронность...")
  4. Definitions of technical concepts ("WebSocket — это полнодуплексный
     протокол...")
  5. Paragraphs without any project-specific concrete details (no smrt-,
     no Smart Price, no Onliner-specific numbers).

We do NOT auto-rewrite — these need human judgment.
"""
import io
import re
from docx import Document

SRC = r"C:/Users/egor3/Desktop/smart-price/ДИПЛОМ_антиплагиат.docx"
doc = Document(SRC)
paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

PROJECT_MARKERS = (
    "smart price",
    "smrt-price",
    "smrt_price",
    "onliner",
    "wildberries",
    "ozon",
    "yandex",
    "яндекс",
    "регард",
    "world devices",
    "1click",
    "biggeek",
    "eaiceoffer",
    "ealiceoffer",
    "cheaper",
    "найти дешевле",
)

DEFINITION_PATTERNS = [
    r"\bпредставляет\s+собой\b",
    r"\bявляется\s+\S+\s+(?:фреймворк|библиотек|стандарт|сервис|инструмент)",
    r"\b(?:был|была|было)\s+разработан",
    r"\b— это\s+",
    r"\bоснован\w*\s+(?:в\s+\d{4}|на\s+принц)",
]

STATS_PATTERNS = [
    r"\bпо\s+данным\s+\S+",
    r"\bобъём\s+\S+\s+(?:рынка|продаж)",
    r"\b\d{4}\s+году\s+составил",
    r"\b(?:АКИТ|Data\s+Insight)",
    r"\b\d+\s+процентов",  # generic % statistics
    r"\b\d+[,.]?\d*\s+(?:триллиона|миллиарда|миллиона)\s+руб",
]

VENDOR_DOC_HINTS = [
    "асинхронн",
    "высокая производительность",
    "нативная поддержка",
    "полнодуплекс",
    "веб-фреймворк",
    "open[- ]?source",
    "мульти-?платформ",
    "кроссплатформ",
]

out = io.StringIO()
out.write("============================================================\n")
out.write("PLAGIARISM RISK HEURISTIC — paragraphs to manually rephrase\n")
out.write("============================================================\n\n")

# Score each paragraph
risky = []
for pi, para in enumerate(paragraphs):
    lower = para.lower()
    score = 0
    reasons = []
    if not any(m in lower for m in PROJECT_MARKERS):
        score += 1
        reasons.append("no project-specific markers")
    for pat in DEFINITION_PATTERNS:
        if re.search(pat, lower):
            score += 2
            reasons.append(f"definition pattern")
            break
    for pat in STATS_PATTERNS:
        if re.search(pat, lower):
            score += 2
            reasons.append("generic statistic")
            break
    vd_hits = sum(1 for h in VENDOR_DOC_HINTS if h in lower)
    if vd_hits >= 2:
        score += 2
        reasons.append(f"vendor-doc style ({vd_hits} hints)")

    # Skip too-short paragraphs
    if len(para.split()) < 25:
        continue

    if score >= 3:
        risky.append((pi, score, list(set(reasons)), para))

# Sort by score desc
risky.sort(key=lambda x: -x[1])

out.write(f"Flagged paragraphs: {len(risky)}\n\n")
out.write("Each paragraph below either lacks project-specific anchors OR\n")
out.write("reads like a generic vendor / Wikipedia / report description.\n")
out.write("Manual action: add a smart-price-specific detail or rewrite to\n")
out.write("reference the actual implementation.\n\n")

for pi, score, reasons, text in risky[:25]:
    out.write(f"--- para {pi}  score={score}  reasons={reasons} ---\n")
    out.write(text[:500] + ("..." if len(text) > 500 else "") + "\n\n")

with open(
    r"C:/Users/egor3/Desktop/smart-price/_plagiarism_risk.txt", "w", encoding="utf-8"
) as f:
    f.write(out.getvalue())

print(f"Risky paragraphs flagged: {len(risky)}")
print("Report saved: _plagiarism_risk.txt")
