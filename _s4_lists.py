# -*- coding: utf-8 -*-
"""Script 4 — italic cleanup on Cyrillic + numbered-list normalization + красная строка.
   - Remove italic from runs that contain NO Latin letters (over-italicized Cyrillic).
   - Numbered list items 'N) ...' (body, not TOC): capitalize first letter, ';'->'.'.
   - List items (numbered & dash) get красная строка: first_line_indent 1.25, left 0.
"""
import re
from docx import Document
from docx.shared import Cm
from docx.oxml.ns import qn

HAS_LATIN = re.compile(r"[A-Za-z]")
NUM = re.compile(r"^(\d+)\)\s+")
DASH = re.compile(r"^[–—\-]\s+")
LOWER_FIRST = re.compile(r"^(\d+\)\s+)([a-zа-яё])")


def deitalicize_cyrillic(p):
    n = 0
    for r in p.runs:
        if not r.text:
            continue
        if HAS_LATIN.search(r.text):
            continue
        rPr = r._element.find(qn("w:rPr"))
        if rPr is None:
            continue
        for tag in ("w:i", "w:iCs"):
            e = rPr.find(qn(tag))
            if e is not None:
                rPr.remove(e)
                n += 1
    return n


def process(fn):
    d = Document(fn)
    deit = 0
    caps = 0
    semi = 0
    indent = 0
    for p in d.paragraphs:
        style = (p.style.name or "").lower()
        # italic cleanup everywhere
        deit += deitalicize_cyrillic(p)
        if "toc" in style or "содержание" in style or "heading" in style:
            continue
        t = p.text.strip()
        if not t:
            continue
        is_num = NUM.match(t)
        is_dash = DASH.match(t)
        if is_num:
            # capitalize first letter after 'N) '
            for r in p.runs:
                if r.text and NUM.match(r.text.lstrip()) is None and not r.text.strip():
                    continue
            # operate on first run holding 'N) x'
            for r in p.runs:
                m = LOWER_FIRST.match(r.text)
                if m:
                    r.text = m.group(1) + m.group(2).upper() + r.text[m.end() :]
                    caps += 1
                    break
                if r.text.strip():
                    break
            # trailing ';' -> '.'
            for r in reversed(p.runs):
                if r.text.strip():
                    rt = r.text.rstrip()
                    if rt.endswith(";"):
                        r.text = rt[:-1] + "."
                        semi += 1
                    break
        if is_num or is_dash:
            pf = p.paragraph_format
            pf.first_line_indent = Cm(1.25)
            pf.left_indent = Cm(0)
            indent += 1
    d.save(fn)
    return {"deitalic": deit, "caps": caps, "semi2period": semi, "indented": indent}


for fn in ["ДИПЛОМ_нормоконтроль.docx", "ВКР_Санько_итог.docx"]:
    print(fn, "->", process(fn))
