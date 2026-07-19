# -*- coding: utf-8 -*-
"""Convert РЕЧЬ_ЗАЩИТА_v3.md → PDF via Edge headless."""
import markdown
import subprocess
import os
import re

SRC = r"C:/Users/egor3/Desktop/smart-price/РЕЧЬ_ЗАЩИТА_v3.md"
HTML_TMP = r"C:/Users/egor3/Desktop/smart-price/_speech_v3.html"
DST = r"C:/Users/egor3/Desktop/smart-price/РЕЧЬ_ЗАЩИТА_v3.pdf"

with open(SRC, "r", encoding="utf-8") as f:
    md_text = f.read()

EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F9FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U00002600-\U000027BF"
    "\U0001F1E0-\U0001F1FF"
    "]+",
    flags=re.UNICODE,
)
md_text = EMOJI_RE.sub("", md_text)

html_body = markdown.markdown(
    md_text, extensions=["tables", "fenced_code", "nl2br", "sane_lists"]
)
html_body = html_body.replace("<blockquote>", '<blockquote class="speech">')

CSS = """
@page { size: A4; margin: 1.8cm 1.6cm; }
* { box-sizing: border-box; }
body { font-family: 'Segoe UI', 'Helvetica', 'Arial', sans-serif; font-size: 10.5pt; line-height: 1.5; color: #1a1a2e; margin: 0; }
h1 { font-size: 22pt; color: #4c3fd1; border-bottom: 3px solid #4c3fd1; padding-bottom: 8px; margin: 0 0 18px 0; letter-spacing: -0.02em; }
h2 { font-size: 14pt; color: #2c2c4a; margin-top: 24px; margin-bottom: 10px; padding-top: 8px; padding-bottom: 4px; border-top: 1px solid #d8d8e8; page-break-after: avoid; }
h3 { font-size: 11.5pt; color: #4c3fd1; margin-top: 14px; margin-bottom: 6px; page-break-after: avoid; }
p { margin: 0 0 8px 0; }
ul, ol { margin: 4px 0 10px 22px; padding: 0; }
li { margin-bottom: 4px; }
blockquote.speech, blockquote { margin: 10px 0 12px 0; padding: 12px 16px; background-color: #f3f0ff; border-left: 4px solid #4c3fd1; border-radius: 0 6px 6px 0; color: #1a1a2e; font-size: 11pt; line-height: 1.55; page-break-inside: avoid; }
blockquote.speech p, blockquote p { margin: 4px 0; }
code { font-family: 'Consolas', 'Courier New', monospace; background-color: #f0f0f5; padding: 1px 5px; border-radius: 3px; font-size: 9.5pt; color: #3c2fb1; }
em { color: #7d6def; font-style: italic; font-size: 9.5pt; }
strong { color: #1a1a2e; font-weight: 700; }
hr { border: none; border-top: 1px dashed #c8c8d8; margin: 18px 0; }
table { border-collapse: collapse; width: 100%; margin: 10px 0 14px 0; font-size: 9.5pt; page-break-inside: avoid; }
th { background-color: #4c3fd1; color: #ffffff; padding: 7px 9px; text-align: left; font-weight: 700; font-size: 9pt; letter-spacing: 0.02em; }
td { border: 1px solid #d8d8e8; padding: 6px 9px; vertical-align: top; }
tr:nth-child(even) td { background-color: #f8f7fd; }
"""

HEAD = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8" />
<title>Smart Price - speech v3</title>
<style>{CSS}</style>
</head>
<body>
{html_body}
</body>
</html>
"""

with open(HTML_TMP, "w", encoding="utf-8") as f:
    f.write(HEAD)

EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]
edge = next((p for p in EDGE_CANDIDATES if os.path.exists(p)), None)

file_url = "file:///" + HTML_TMP.replace("\\", "/")

cmd = [
    edge,
    "--headless=new",
    "--disable-gpu",
    "--no-sandbox",
    f"--print-to-pdf={DST}",
    "--print-to-pdf-no-header",
    file_url,
]
subprocess.run(cmd, capture_output=True, timeout=60)

if os.path.exists(DST):
    print(f"OK: {DST} ({os.path.getsize(DST)//1024} KB)")
else:
    print("FAIL")
