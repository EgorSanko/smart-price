# -*- coding: utf-8 -*-
"""Apply term-italic / code-mono only to the 15 newly inserted table-ref sentences."""
import re
from copy import deepcopy
from docx import Document
from docx.oxml.ns import qn

SRC = r"C:/Users/egor3/Desktop/smart-price/ДИПЛОМ_нормоконтроль.docx"
doc = Document(SRC)

TOKEN = re.compile(r"[A-Za-z_][\w]*(?:[.\-/][\w]+)*(?:\([^)]*\))?(?:\[[^\]]*\])?")
CURATED_CODE = {
    "asyncio.gather",
    "EventSourceResponse",
    "EAliceOfferCard",
    "EAliceOffer",
    "EAliceOfferList",
    "app.ml",
    "app.celery_app",
    "app.main",
    "sse_starlette",
}


def classify(tok):
    if len(tok) < 2:
        return None
    if "_" in tok or "(" in tok or "[" in tok or tok in CURATED_CODE:
        return "code"
    if not re.search(r"[A-Za-z]", tok):
        return None
    return "term"


def segment(text):
    segs, pos = [], 0
    for m in TOKEN.finditer(text):
        if m.start() > pos:
            segs.append((text[pos : m.start()], None))
        segs.append((m.group(0), classify(m.group(0))))
        pos = m.end()
    if pos < len(text):
        segs.append((text[pos:], None))
    return segs


def _rpr(r):
    rPr = r.find(qn("w:rPr"))
    if rPr is None:
        rPr = r.makeelement(qn("w:rPr"), {})
        r.insert(0, rPr)
    return rPr


def set_italic(r):
    rPr = _rpr(r)
    i = rPr.find(qn("w:i"))
    if i is None:
        i = rPr.makeelement(qn("w:i"), {})
        rPr.append(i)
    i.set(qn("w:val"), "true")
    ics = rPr.find(qn("w:iCs"))
    if ics is None:
        ics = rPr.makeelement(qn("w:iCs"), {})
        rPr.append(ics)
    ics.set(qn("w:val"), "true")


def set_mono(r):
    rPr = _rpr(r)
    for tag in ("w:i", "w:iCs"):
        e = rPr.find(qn(tag))
        if e is not None:
            rPr.remove(e)
    rf = rPr.find(qn("w:rFonts"))
    if rf is None:
        rf = rPr.makeelement(qn("w:rFonts"), {})
        rPr.insert(0, rf)
    for a in ("w:ascii", "w:hAnsi", "w:cs"):
        rf.set(qn(a), "Consolas")


def process(p):
    n = 0
    for r in list(p.runs):
        re_el = r._element
        text = r.text
        if not text or not TOKEN.search(text):
            continue
        segs = segment(text)
        if not any(k for _, k in segs):
            continue
        if len(segs) == 1:
            k = segs[0][1]
            if k == "term":
                set_italic(re_el)
                n += 1
            elif k == "code":
                set_mono(re_el)
                n += 1
            continue
        parent = re_el.getparent()
        idx = list(parent).index(re_el)
        for off, (st, k) in enumerate(segs):
            nr = deepcopy(re_el)
            t = nr.find(qn("w:t"))
            if t is None:
                t = nr.makeelement(qn("w:t"), {})
                nr.append(t)
            t.text = st
            t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            if k == "term":
                set_italic(nr)
                n += 1
            elif k == "code":
                set_mono(nr)
                n += 1
            parent.insert(idx + off, nr)
        parent.remove(re_el)
    return n


ref_re = re.compile(r"в таблице \d+\.$")
total = 0
hit = 0
for p in doc.paragraphs:
    if ref_re.search(p.text.strip()):
        hit += 1
        total += process(p)
doc.save(SRC)
print(f"Ref sentences formatted: {hit}, latin runs styled: {total}")
