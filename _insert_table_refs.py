# -*- coding: utf-8 -*-
"""Insert in-text references before the 15 unreferenced tables.

For each table caption "Таблица N — Title", insert a body paragraph right
before it: "{Title} {verb} в таблице N." with the verb agreed in
gender/number with the title's head noun (hardcoded per table — titles known).
"""
import re
from docx import Document

SRC = r"C:/Users/egor3/Desktop/smart-price/ДИПЛОМ_нормоконтроль.docx"
doc = Document(SRC)

# Verb agreement per table number (приведено/приведены/приведена/приведён)
VERB = {
    3: "приведено",
    4: "приведено",
    5: "приведено",
    6: "приведены",
    7: "приведены",
    8: "приведено",
    9: "приведено",
    10: "приведено",
    12: "приведены",
    13: "приведены",
    14: "приведены",
    15: "приведены",
    16: "приведена",  # сравнительная оценка
    17: "приведён",  # экономический анализ
    18: "приведено",  # сравнение
}
TARGET = set(VERB.keys())

cap_re = re.compile(r"^Таблица\s+(\d+)\s*[—\-–]\s*(.+?)\s*$")
inserted = 0
done = set()

for p in list(doc.paragraphs):
    m = cap_re.match(p.text.strip())
    if not m:
        continue
    n = int(m.group(1))
    if n not in TARGET or n in done:
        continue
    title = m.group(2).rstrip(".")
    # lead-in sentence: title stays as-is (capitalized), verb agreed
    sentence = f"{title} {VERB[n]} в таблице {n}."
    new_p = p.insert_paragraph_before(sentence)
    # ensure not bold / normal body look
    for r in new_p.runs:
        r.bold = False
        r.italic = False
    done.add(n)
    inserted += 1

doc.save(SRC)
print(f"Inserted references: {inserted}")
print("Tables covered:", sorted(done))
missing = TARGET - done
if missing:
    print("NOT FOUND captions for:", sorted(missing))
