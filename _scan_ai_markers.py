# -*- coding: utf-8 -*-
"""Scan the stripped diploma text for common AI-generated patterns
and academic clichés the antiplagiat / detector tools flag.

Outputs a report with:
  - Frequency of each marker
  - Paragraph locations (so the author can rewrite them)
  - Top 10 longest paragraphs (AI tends to write 4+ sentence walls)
  - Sentence-length distribution (AI averages much higher than humans)
"""
import io
import re
from collections import defaultdict
from docx import Document

SRC = r"C:/Users/egor3/Desktop/smart-price/ДИПЛОМ_антиплагиат.docx"

# Categories of AI-typical phrases. Each tuple: (label, pattern).
# Patterns are case-insensitive, run against paragraph text.
AI_PHRASES = {
    "cliche_intro": [
        "стоит отметить",
        "следует отметить",
        "важно отметить",
        "необходимо отметить",
        "важно подчеркнуть",
        "следует подчеркнуть",
        "нельзя не отметить",
        "хочется отметить",
    ],
    "cliche_universal": [
        "в современном мире",
        "в эпоху цифровизации",
        "в условиях современных",
        "современные реалии",
        "стремительное развитие",
        "бурное развитие",
        "непрерывное развитие",
        "активное развитие",
    ],
    "cliche_transition": [
        "таким образом,",
        "в свою очередь",
        "в контексте",
        "в рамках данной",
        "в рамках настоящей",
        "безусловно,",
        "несомненно,",
        "очевидно, что",
        "принципиально важно",
        "ключевую роль играет",
        "особое внимание",
    ],
    "cliche_solution": [
        "данный подход позволяет",
        "предложенный подход",
        "разработанное решение позволяет",
        "разработанная система позволяет",
        "данное решение позволяет",
        "позволяет существенно",
        "обеспечивает высокую",
        "обеспечивает эффективное",
    ],
    "list_template": [
        "во-первых",
        "во-вторых",
        "в-третьих",
        "с одной стороны",
        "с другой стороны",
    ],
    "verbose_phrase": [
        "характеризуется",
        "представляет собой",
        "является ключевым",
        "является важным",
        "является одним из",
        "является основным",
        "отличительной особенностью",
        "примечательной особенностью",
    ],
    "mirror_pattern": [
        # X не только Y, но и Z
        r"не только\s+\S+.*?но и",
        # как с X, так и с Y
        r"как с\s+\S+.*?так и с",
    ],
    "gpt_signature": [
        # GPT often inserts these
        "в заключение",  # legitimate in "Заключение" header, but flagged inline
        "подводя итог",
        "обобщая вышесказанное",
        "резюмируя",
    ],
}

doc = Document(SRC)
paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
full_text = "\n".join(paragraphs)
total_chars = len(full_text)
total_words = sum(len(p.split()) for p in paragraphs)

out = io.StringIO()
out.write("============================================================\n")
out.write("AI-MARKER SCAN — ДИПЛОМ_антиплагиат.docx\n")
out.write("============================================================\n\n")
out.write(f"Paragraphs (non-empty): {len(paragraphs)}\n")
out.write(f"Total characters:       {total_chars:,}\n")
out.write(f"Total words:            {total_words:,}\n")
out.write(f"Avg paragraph length:   {total_chars // max(1, len(paragraphs))} chars\n\n")

# --- 1. Phrase frequency ----------------------------------------------------
phrase_hits = defaultdict(list)  # phrase -> list of (paragraph_idx, snippet)

for pi, para in enumerate(paragraphs):
    lower = para.lower()
    for category, patterns in AI_PHRASES.items():
        for pat in patterns:
            # Check if it's a regex (contains \s+ etc.) or a literal substring
            if any(esc in pat for esc in ("\\s", "\\S", ".*", "\\b")):
                matches = list(re.finditer(pat, lower, flags=re.IGNORECASE))
                for m in matches:
                    snippet_start = max(0, m.start() - 20)
                    snippet_end = min(len(para), m.end() + 20)
                    phrase_hits[(category, pat)].append(
                        (pi, para[snippet_start:snippet_end])
                    )
            else:
                if pat in lower:
                    # Count occurrences in paragraph
                    count = lower.count(pat)
                    for _ in range(count):
                        idx = lower.find(pat)
                        snippet_start = max(0, idx - 20)
                        snippet_end = min(len(para), idx + len(pat) + 20)
                        phrase_hits[(category, pat)].append(
                            (pi, para[snippet_start:snippet_end])
                        )
                        lower = lower[:idx] + " " * len(pat) + lower[idx + len(pat) :]

out.write("============================================================\n")
out.write("AI-CLICHÉ FREQUENCY (lower is better; > 3 occurrences = rewrite)\n")
out.write("============================================================\n\n")

by_category = defaultdict(int)
for (category, phrase), hits in sorted(phrase_hits.items(), key=lambda x: -len(x[1])):
    by_category[category] += len(hits)
    if not hits:
        continue
    severity = "⚠️ HIGH" if len(hits) > 5 else ("• med" if len(hits) > 2 else "· low")
    out.write(f"{severity}  [{category}] {phrase!r} — {len(hits)}×\n")
    for pi, snip in hits[:3]:
        out.write(f"         para {pi}: ...{snip.strip()}...\n")
    if len(hits) > 3:
        out.write(f"         (and {len(hits) - 3} more)\n")
    out.write("\n")

out.write("\n--- Totals by category ---\n")
for cat, total in sorted(by_category.items(), key=lambda x: -x[1]):
    bar = "#" * min(40, total)
    out.write(f"  {cat:20s} {total:3d}  {bar}\n")

# --- 2. Sentence length analysis -------------------------------------------
# Average sentence length: GPT typically 25-40 words, humans 12-22.
sentences = re.split(r"(?<=[.!?])\s+", full_text)
sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
sent_lengths = [len(s.split()) for s in sentences]
if sent_lengths:
    avg_sent = sum(sent_lengths) / len(sent_lengths)
    long_sentences = [s for s in sentences if len(s.split()) > 35]
else:
    avg_sent = 0
    long_sentences = []

out.write("\n============================================================\n")
out.write("SENTENCE LENGTH (human: 12–22 words; GPT: 25–40+; bot-clean: 18–25)\n")
out.write("============================================================\n\n")
out.write(f"  Total sentences:        {len(sentences)}\n")
out.write(f"  Avg words / sentence:   {avg_sent:.1f}\n")
out.write(
    f"  Sentences > 35 words:   {len(long_sentences)}  ({100*len(long_sentences)/max(1,len(sentences)):.1f}%)\n"
)

# Show top 5 longest sentences
sentences_with_len = sorted(zip(sentences, sent_lengths), key=lambda x: -x[1])
out.write("\n  Top 5 longest sentences (candidates to split):\n\n")
for s, ln in sentences_with_len[:5]:
    out.write(f'  [{ln}w] {s[:220]}{"..." if len(s)>220 else ""}\n\n')

# --- 3. Paragraph length analysis ------------------------------------------
para_lengths = [(pi, len(p.split())) for pi, p in enumerate(paragraphs)]
long_paras = [(pi, l) for pi, l in para_lengths if l > 150]

out.write("============================================================\n")
out.write("PARAGRAPH LENGTH (human academic: 60–120 words; GPT: 150–250+)\n")
out.write("============================================================\n\n")
out.write(f"  Total paragraphs:         {len(paragraphs)}\n")
out.write(f"  Paragraphs > 150 words:   {len(long_paras)}\n")
out.write(f"  Paragraphs > 250 words:   {sum(1 for _,l in para_lengths if l > 250)}\n")

# Show top 5 longest paragraphs
para_sorted = sorted(para_lengths, key=lambda x: -x[1])
out.write("\n  Top 5 longest paragraphs (candidates to split):\n\n")
for pi, ln in para_sorted[:5]:
    snippet = paragraphs[pi][:200]
    out.write(f"  para {pi} [{ln}w]: {snippet}...\n\n")

# Save
with open(
    r"C:/Users/egor3/Desktop/smart-price/_ai_marker_report.txt", "w", encoding="utf-8"
) as f:
    f.write(out.getvalue())

# Summary print (ASCII only — Windows console is cp1251)
print(f"AI cliche hits: {sum(len(v) for v in phrase_hits.values())} total")
print(f"Long sentences (>35 w): {len(long_sentences)}")
print(f"Long paragraphs (>150 w): {len(long_paras)}")
print(f"Avg sentence length: {avg_sent:.1f} words")
print("Report saved: _ai_marker_report.txt")
