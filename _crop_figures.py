# -*- coding: utf-8 -*-
"""Crop over-long screenshots (aspect H/W > 2) to their top portion via
non-destructive a:srcRect, then set a normal display size (~10×15 cm).
Shows header + first content, drops the long tail. Source image untouched.
"""
import io
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

SRC = r"C:/Users/egor3/Desktop/smart-price/ДИПЛОМ_нормоконтроль.docx"
EMU = 360000
TALL = 2.0  # only crop images taller than 2:1
TARGET_ASPECT = 1.5  # visible H/W after crop (normal portrait figure)
NEW_W = int(10 * EMU)  # 10 cm display width
NEW_H = int(NEW_W * TARGET_ASPECT)  # 15 cm

doc = Document(SRC)
report = io.StringIO()
paras = doc.paragraphs


def next_caption(pi):
    for q in paras[pi + 1 : pi + 5]:
        t = q.text.strip()
        if t.startswith("Рисунок"):
            return t[:55]
    return ""


cropped = 0
for pi, p in enumerate(paras):
    for dr in p._element.findall(".//" + qn("w:drawing")):
        ext = dr.find(".//" + qn("wp:extent"))
        if ext is None:
            continue
        cx = int(ext.get("cx") or 0)
        cy = int(ext.get("cy") or 0)
        if cx <= 0 or cy <= 0:
            continue
        aspect = cy / cx
        cap = next_caption(pi)
        if aspect <= TALL:
            continue
        keep = TARGET_ASPECT / aspect  # top fraction to keep
        b = max(0, min(95000, round((1 - keep) * 100000)))  # crop bottom (1/1000 %)
        # set display size
        ext.set("cx", str(NEW_W))
        ext.set("cy", str(NEW_H))
        for aext in dr.findall(".//" + qn("a:ext")):
            aext.set("cx", str(NEW_W))
            aext.set("cy", str(NEW_H))
        # add srcRect crop into pic:blipFill
        blipFill = dr.find(".//" + qn("pic:blipFill"))
        if blipFill is not None:
            for old in blipFill.findall(qn("a:srcRect")):
                blipFill.remove(old)
            sr = OxmlElement("a:srcRect")
            sr.set("l", "0")
            sr.set("t", "0")
            sr.set("r", "0")
            sr.set("b", str(b))
            blip = blipFill.find(qn("a:blip"))
            if blip is not None:
                blip.addnext(sr)
            else:
                blipFill.insert(0, sr)
            report.write(f"  ✂ crop bottom {b/1000:.0f}%  → 10.0x15.0 см  | {cap}\n")
            cropped += 1

doc.save(SRC)
with open(
    r"C:/Users/egor3/Desktop/smart-price/_crop_report.txt", "w", encoding="utf-8"
) as f:
    f.write(report.getvalue())
print(f"Figures cropped: {cropped}")
