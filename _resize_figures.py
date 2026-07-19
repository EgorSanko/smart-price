# -*- coding: utf-8 -*-
"""Proportionally shrink any figure taller/wider than a page so it fits
on one page together with its caption. Aspect ratio preserved.

Limits chosen so image + «Рисунок N — ...» caption fit on one A4 page
with GOST margins:
  max width  = 16.5 cm  (text column)
  max height = 21.0 cm  (leaves room for the caption line(s))
"""
import io
from docx import Document
from docx.oxml.ns import qn

SRC = r"C:/Users/egor3/Desktop/smart-price/ДИПЛОМ_нормоконтроль.docx"
EMU = 360000
MAX_W = int(16.5 * EMU)
MAX_H = int(21.0 * EMU)

doc = Document(SRC)
report = io.StringIO()


# map each drawing to the following caption text for the report
def next_caption(p_index, paras):
    for q in paras[p_index + 1 : p_index + 5]:
        t = q.text.strip()
        if t.startswith("Рисунок"):
            return t[:55]
    return ""


paras = doc.paragraphs
changed = 0
for pi, p in enumerate(paras):
    drawings = p._element.findall(".//" + qn("w:drawing"))
    for dr in drawings:
        ext = dr.find(".//" + qn("wp:extent"))
        if ext is None:
            continue
        cx = int(ext.get("cx") or 0)
        cy = int(ext.get("cy") or 0)
        if cx <= 0 or cy <= 0:
            continue
        scale = min(MAX_W / cx, MAX_H / cy, 1.0)
        cap = next_caption(pi, paras)
        if scale < 0.999:
            ncx, ncy = int(cx * scale), int(cy * scale)
            ext.set("cx", str(ncx))
            ext.set("cy", str(ncy))
            for aext in dr.findall(".//" + qn("a:ext")):
                aext.set("cx", str(ncx))
                aext.set("cy", str(ncy))
            report.write(
                f"  ↓ {cx/EMU:.1f}x{cy/EMU:.1f} → {ncx/EMU:.1f}x{ncy/EMU:.1f} см  | {cap}\n"
            )
            changed += 1
        else:
            report.write(f"  = {cx/EMU:.1f}x{cy/EMU:.1f} см (ок)            | {cap}\n")

doc.save(SRC)
with open(
    r"C:/Users/egor3/Desktop/smart-price/_resize_report.txt", "w", encoding="utf-8"
) as f:
    f.write(report.getvalue())
print(f"Figures resized: {changed}")
