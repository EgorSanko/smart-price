# -*- coding: utf-8 -*-
"""Audit caption placement:
   - table caption "Таблица N — ..." should be the paragraph immediately ABOVE the table
   - figure caption "Рисунок N — ..." should be immediately BELOW the image
"""
import io
import re
from docx import Document
from docx.oxml.ns import qn

SRC = r"C:/Users/egor3/Desktop/smart-price/ДИПЛОМ_нормоконтроль.docx"
doc = Document(SRC)
body = doc.element.body
children = list(body.iterchildren())


def ptext(el):
    if el.tag != qn("w:p"):
        return None
    return "".join(t.text or "" for t in el.findall(".//" + qn("w:t"))).strip()


def has_drawing(el):
    return el.tag == qn("w:p") and bool(el.findall(".//" + qn("w:drawing")))


tab_cap = re.compile(r"^Таблица\s+\d+\s*[—\-–]")
fig_cap = re.compile(r"^Рисунок\s+\d+\s*[—\-–]")

out = io.StringIO()

# Tables: caption above?
out.write("=== ТАБЛИЦЫ: подпись сверху? ===\n")
tbl_problems = 0
for i, el in enumerate(children):
    if el.tag == qn("w:tbl"):
        # find previous non-empty paragraph
        prev = None
        j = i - 1
        while j >= 0:
            if children[j].tag == qn("w:p"):
                t = ptext(children[j])
                if t:
                    prev = t
                    break
            j -= 1
        ok = prev and tab_cap.match(prev)
        if not ok:
            tbl_problems += 1
            out.write(
                f"  ⚠ таблица @child {i}: над ней не подпись, а: {str(prev)[:60]!r}\n"
            )
out.write(f"  Таблиц с проблемой подписи сверху: {tbl_problems}\n")

# Figures: caption below?
out.write("\n=== РИСУНКИ: подпись снизу? ===\n")
fig_problems = 0
fig_count = 0
for i, el in enumerate(children):
    if has_drawing(el):
        fig_count += 1
        # find next non-empty paragraph
        nxt = None
        j = i + 1
        while j < len(children):
            if children[j].tag == qn("w:p"):
                t = ptext(children[j])
                if t:
                    nxt = t
                    break
            j += 1
        ok = nxt and fig_cap.match(nxt)
        if not ok:
            fig_problems += 1
            out.write(
                f"  ⚠ рисунок @child {i}: под ним не подпись, а: {str(nxt)[:60]!r}\n"
            )
out.write(
    f"  Рисунков всего (с w:drawing): {fig_count}, с проблемой подписи снизу: {fig_problems}\n"
)

with open(
    r"C:/Users/egor3/Desktop/smart-price/_caption_audit.txt", "w", encoding="utf-8"
) as f:
    f.write(out.getvalue())
print(
    "Tables w/ caption issue:",
    tbl_problems,
    "| Figures w/ caption issue:",
    fig_problems,
    "| figs:",
    fig_count,
)
