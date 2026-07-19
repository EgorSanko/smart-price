# -*- coding: utf-8 -*-
"""Open the final docx in Word, update the TOC + all fields, export to PDF."""
import os
import win32com.client as win32

DOCX = r"C:\Users\egor3\Desktop\smart-price\ВКР_Санько_итог.docx"
PDF = r"C:\Users\egor3\Desktop\smart-price\ВКР_Санько_итог.pdf"

wdFormatPDF = 17
wdAlertsNone = 0

word = win32.Dispatch("Word.Application")
word.Visible = False
word.DisplayAlerts = wdAlertsNone
try:
    doc = word.Documents.Open(DOCX, ReadOnly=False)
    # update Table(s) of Contents
    try:
        for i in range(1, doc.TablesOfContents.Count + 1):
            doc.TablesOfContents(i).Update()
    except Exception as e:
        print("TOC update warn:", e)
    # update all fields in every story (TOC PAGEREF, PAGE numbers, etc.)
    try:
        for story in doc.StoryRanges:
            story.Fields.Update()
    except Exception as e:
        print("fields update warn:", e)
    # save the docx too (so TOC stays populated) then export PDF
    doc.Save()
    doc.SaveAs(PDF, FileFormat=wdFormatPDF)
    doc.Close(False)
    print("PDF created:", PDF, "| size", os.path.getsize(PDF), "bytes")
finally:
    word.Quit()
