# -*- coding: utf-8 -*-
"""Reduce the gap above tables: remove the full empty paragraph I had added above
   each caption, replace with a small space_before (6 pt) on the caption itself.
   Caption stays glued to the table (space_after 0 + keepNext already set).
"""
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph


def ptext(e):
    return "".join(t.text or "" for t in e.findall(".//" + qn("w:t"))).strip()


def process(fn):
    d = Document(fn)
    body = d.element.body
    ch = list(body.iterchildren())
    removed = 0
    caps = 0
    for i, e in enumerate(ch):
        if e.tag != qn("w:tbl"):
            continue
        # caption above
        j = i - 1
        cap = None
        while j >= 0:
            if ch[j].tag == qn("w:p") and ptext(ch[j]):
                if ptext(ch[j]).startswith("Таблица"):
                    cap = j
                break
            j -= 1
        if cap is None:
            continue
        capP = ch[cap]
        # remove an empty paragraph directly above the caption
        prev = ch[cap - 1] if cap - 1 >= 0 else None
        if (
            prev is not None
            and prev.tag == qn("w:p")
            and not ptext(prev)
            and not prev.findall(".//" + qn("w:drawing"))
        ):
            prev.getparent().remove(prev)
            removed += 1
        # small gap before caption, hug the table below
        pp = Paragraph(capP, d)
        pp.paragraph_format.space_before = Pt(6)
        pp.paragraph_format.space_after = Pt(0)
        caps += 1
    d.save(fn)
    return {"empty_removed": removed, "captions_spaced": caps}


for fn in ["ДИПЛОМ_нормоконтроль.docx", "ВКР_Санько_итог.docx"]:
    print(fn, "->", process(fn))
