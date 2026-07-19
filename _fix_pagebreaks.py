# -*- coding: utf-8 -*-
"""Make EVERY structural section start on a new page, uniformly.

- Remove all manual <w:br w:type="page"/> (the old mechanism that left
  ВВЕДЕНИЕ without a break and risks double-breaks vs page_break_before).
- Set page_break_before=True on every section start:
    РЕФЕРАТ, СОДЕРЖАНИЕ, and every Heading 1 paragraph
    (ВВЕДЕНИЕ, главы 1-4, ЗАКЛЮЧЕНИЕ, СПИСОК…, ПРИЛОЖЕНИЯ).
  TOC-entry duplicates are NOT Heading 1, so they are untouched.
- Re-assert updateFields=true so Word refreshes the TOC page numbers on open.
"""
import io
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

SRC = r"C:/Users/egor3/Desktop/smart-price/ДИПЛОМ_нормоконтроль.docx"
doc = Document(SRC)
body = doc.element.body

# 1. remove all page-type breaks
removed_br = 0
for br in body.findall(".//" + qn("w:br")):
    if br.get(qn("w:type")) == "page":
        br.getparent().remove(br)
        removed_br += 1

# 2. set page_break_before on section starts
set_pbb = 0
report = io.StringIO()
for p in doc.paragraphs:
    t = p.text.strip()
    is_section = (p.style.name == "Heading 1") or (t in ("РЕФЕРАТ", "СОДЕРЖАНИЕ"))
    if is_section:
        p.paragraph_format.page_break_before = True
        set_pbb += 1
        report.write(f"  ✓ new page: {t[:50]}\n")

# 3. re-assert updateFields=true
s = doc.settings.element
for e in s.findall(qn("w:updateFields")):
    s.remove(e)
uf = OxmlElement("w:updateFields")
uf.set(qn("w:val"), "true")
s.insert(0, uf)

doc.save(SRC)
with open(
    r"C:/Users/egor3/Desktop/smart-price/_pbb_set.txt", "w", encoding="utf-8"
) as f:
    f.write(report.getvalue())
print(f"Removed page-breaks: {removed_br}; page_break_before set: {set_pbb}")
