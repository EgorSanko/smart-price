# -*- coding: utf-8 -*-
"""Left-align tables for real + left-align captions + add a blank line ABOVE each table.
   Root cause of 'centered': jc=center sat on BOTH tblPr AND every row's trPr,
   so table-level left was overridden. Remove jc everywhere -> default = left.
"""
from docx import Document
from docx.shared import Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def ptext(e):
    return "".join(t.text or "" for t in e.findall(".//" + qn("w:t"))).strip()


def process(fn):
    d = Document(fn)
    body = d.element.body

    # 1. kill center on tables: tblPr jc + every row trPr jc
    tbl_fixed = row_jc_removed = 0
    for t in d.tables:
        tblPr = t._tbl.find(qn("w:tblPr"))
        if tblPr is not None:
            jc = tblPr.find(qn("w:jc"))
            if jc is not None:
                tblPr.remove(jc)
                tbl_fixed += 1
            ind = tblPr.find(qn("w:tblInd"))
            if ind is not None:
                ind.set(qn("w:w"), "0")
                ind.set(qn("w:type"), "dxa")
        for row in t.rows:
            trPr = row._tr.find(qn("w:trPr"))
            if trPr is not None:
                rjc = trPr.find(qn("w:jc"))
                if rjc is not None:
                    trPr.remove(rjc)
                    row_jc_removed += 1

    # 2+3. captions LEFT (no indent) + blank line above each table
    ch = list(body.iterchildren())
    cap_left = added_above = 0
    for i, e in enumerate(ch):
        if e.tag != qn("w:tbl"):
            continue
        # find caption paragraph above
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
        from docx.text.paragraph import Paragraph

        pp = Paragraph(capP, d)
        pp.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY  # match Maxim's reference
        pp.paragraph_format.first_line_indent = Cm(0)
        pp.paragraph_format.left_indent = Cm(0)
        cap_left += 1
        # blank line above caption (if not already blank)
        prev = ch[cap - 1] if cap - 1 >= 0 else None
        prev_blank = (
            prev is not None
            and prev.tag == qn("w:p")
            and not ptext(prev)
            and not prev.findall(".//" + qn("w:drawing"))
        )
        if not prev_blank:
            newp = OxmlElement("w:p")
            capP.addprevious(newp)
            added_above += 1

    d.save(fn)
    return {
        "tbl_jc_removed": tbl_fixed,
        "row_jc_removed": row_jc_removed,
        "cap_left": cap_left,
        "blank_above": added_above,
    }


for fn in ["ДИПЛОМ_нормоконтроль.docx", "ВКР_Санько_итог.docx"]:
    print(fn, "->", process(fn))
