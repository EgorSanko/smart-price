# -*- coding: utf-8 -*-
"""Format Latin terms/code inside bold run-in lead-ins (from demoted x.x.x)."""
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


def is_bold(r):
    rPr = r.find(qn("w:rPr"))
    if rPr is None:
        return False
    b = rPr.find(qn("w:b"))
    if b is None:
        return False
    return b.get(qn("w:val")) not in ("0", "false")


n_runs = 0
for p in doc.paragraphs:
    for r in list(p.runs):
        re_el = r._element
        if not is_bold(re_el):
            continue
        # skip if has drawing/br
        if re_el.findall(".//" + qn("w:drawing")) or re_el.findall(".//" + qn("w:br")):
            continue
        if len(re_el.findall(qn("w:t"))) > 1:
            continue
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
                n_runs += 1
            elif k == "code":
                set_mono(re_el)
                n_runs += 1
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
                n_runs += 1
            elif k == "code":
                set_mono(nr)
                n_runs += 1
            parent.insert(idx + off, nr)
        parent.remove(re_el)

doc.save(SRC)
print(f"Bold lead-in latin runs styled: {n_runs}")
