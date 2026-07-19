# -*- coding: utf-8 -*-
"""Extract starting page for each heading from rendered ДИПЛОМ.pdf"""
import re
import io

try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader

reader = PdfReader(r"C:/Users/egor3/Desktop/smart-price/ДИПЛОМ.pdf")
n = len(reader.pages)
print(f"Total pages: {n}")

# Heading patterns we care about — must match TOC entries
HEADINGS = [
    "ВВЕДЕНИЕ",
    "1 АНАЛИЗ ПРЕДМЕТНОЙ ОБЛАСТИ",
    "1.1 Рынок электронной коммерции",
    "1.2 Анализ существующих решений",
    "1.3 Технологический обзор",
    "1.4 Выводы по первой главе",
    "2 ПРОЕКТИРОВАНИЕ СИСТЕМЫ",
    "2.1 Анализ требований",
    "2.2 Архитектурное проектирование",
    "2.3 Проектирование базы данных",
    "2.4 Проектирование API",
    "2.5 Проектирование пользовательского",
    "2.6 Проектирование развёртывания",
    "2.7 Проектирование обработки",
    "2.8 Проектирование кэширования",
    "2.9 Выводы по второй главе",
    "3 РЕАЛИЗАЦИЯ СИСТЕМЫ",
    "3.1 Реализация парсеров",
    "3.2 Реализация AI-коррекции",
    "3.3 Реализация гибридной",
    "3.4 Реализация AI-ассистента",
    "3.5 Реализация SSE",
    "3.6 Реализация фронтенда",
    "3.7 Интеграция с Gemini",
    "3.8 Реализация системы аутентификации",
    "3.9 Реализация прокси-сервера",
    "3.10 Реализация модуля истории",
    "3.11 Реализация AI-анализа",
    "3.12 Развёртывание",
    "3.13 Реализация функции",
    "3.14 Выводы по третьей главе",
    "4 ТЕСТИРОВАНИЕ",
    "4.1 Методология тестирования",
    "4.2 Результаты функционального",
    "4.3 Результаты тестирования AI-ассистента",
    "4.4 Результаты тестирования производительности",
    "4.5 Сквозное тестирование",
    "4.6 Тестирование адаптивной",
    "4.7 Сравнение с существующими",
    "4.8 Экономический анализ",
    "4.9 Выводы по четвёртой главе",
    "ЗАКЛЮЧЕНИЕ",
    "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ",
    "ПРИЛОЖЕНИЕ А",
    "ПРИЛОЖЕНИЕ Б",
]

# Extract text from each page
page_texts = []
for i, page in enumerate(reader.pages):
    try:
        page_texts.append(page.extract_text() or "")
    except Exception as e:
        page_texts.append("")

# For each heading, find first page where it appears (skipping TOC pages 1-3)
TOC_END_PAGE = 7  # cover(1-2) + abstract(3-4) + TOC(5-6) → content starts p.7

results = {}
for h in HEADINGS:
    h_norm = h.lower().replace(" ", "").replace("ё", "е")
    found = None
    # Heading line pattern: search for the heading prefix on a line that doesn't contain "....."
    # (TOC dots) — i.e., a real heading occurrence, not a TOC reference.
    for pi, text in enumerate(page_texts):
        if pi < TOC_END_PAGE - 1:
            continue
        for line in text.split("\n"):
            line_norm = line.lower().replace(" ", "").replace("ё", "е")
            if "...." in line:
                continue  # skip TOC-style lines
            if h_norm[:30] in line_norm:
                found = pi + 1
                break
        if found:
            break
    results[h] = found

out = io.StringIO()
out.write(f"Total pages in PDF: {n}\n\n")
out.write("Heading -> page mapping:\n")
for h, p in results.items():
    out.write(f"  p{p}\t{h}\n")

with open(r"C:/Users/egor3/Desktop/smart-price/_pages.txt", "w", encoding="utf-8") as f:
    f.write(out.getvalue())

print("Written _pages.txt")
