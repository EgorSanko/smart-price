# -*- coding: utf-8 -*-
"""Inspect formatting of ДИПЛОМ.docx for normocontrol fixes."""
import io
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

SRC = r"C:/Users/egor3/Desktop/smart-price/ДИПЛОМ.docx"
doc = Document(SRC)

out = io.StringIO()

# 1. Styles overview
out.write("=== STYLES IN DOCUMENT ===\n")
for s in doc.styles:
    try:
        out.write(f"  {s.type}  {s.name!r}\n")
    except Exception:
        pass

# 2. Headings + subheadings: find numbered headings and chapter conclusions
out.write("\n=== HEADINGS / SUBHEADINGS / CONCLUSIONS ===\n")
import re

heading_re = re.compile(r"^\s*\d+(\.\d+){0,2}\s+\S")
for i, p in enumerate(doc.paragraphs):
    t = p.text.strip()
    if not t:
        continue
    is_h = heading_re.match(t)
    is_concl = "выводы по" in t.lower() or t.lower().startswith("выводы")
    is_bold = any(r.bold for r in p.runs if r.text.strip())
    if (
        is_h
        or is_concl
        or t
        in (
            "ВВЕДЕНИЕ",
            "ЗАКЛЮЧЕНИЕ",
            "РЕФЕРАТ",
            "СОДЕРЖАНИЕ",
            "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ",
        )
    ):
        pf = p.paragraph_format
        align = pf.alignment
        first_indent = pf.first_line_indent
        left_indent = pf.left_indent
        sb = pf.space_before
        sa = pf.space_after
        out.write(
            f"[{i}] style={p.style.name!r} bold={is_bold} align={align} "
            f"first_indent={first_indent} left={left_indent} "
            f"space_before={sb} space_after={sa}\n"
        )
        out.write(f"      text={t[:80]!r}\n")

with open(
    r"C:/Users/egor3/Desktop/smart-price/_format_inspect.txt", "w", encoding="utf-8"
) as f:
    f.write(out.getvalue())
print("OK headings written")
