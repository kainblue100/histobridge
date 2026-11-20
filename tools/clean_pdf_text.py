"""Rejoin the one-word-per-line output that pypdf produces for this layout."""
import re

SRC = r"D:\coda_matlab\histobridge\docs\bbag255.txt"
DST = r"D:\coda_matlab\histobridge\docs\bbag255_clean.txt"

raw = open(SRC, encoding="utf-8").read()

out_pages = []
for page in raw.split("===== PAGE "):
    if not page.strip():
        continue
    try:
        num, body = page.split(" =====", 1)
    except ValueError:
        continue
    lines = [l.strip() for l in body.splitlines()]
    lines = [l for l in lines if l]
    # a "word line" is short and has no sentence-ending punctuation
    words = []
    for l in lines:
        if len(l) <= 24 and not re.search(r"[.:;]\s*$", l):
            words.append(l)
        else:
            if words:
                out_pages.append(" ".join(words))
                words = []
            out_pages.append(l)
    if words:
        out_pages.append(" ".join(words))
    out_pages.append(f"\n\n########## PAGE {num} ##########\n")

text = "\n".join(out_pages)
text = re.sub(r"\n{3,}", "\n\n", text)
open(DST, "w", encoding="utf-8").write(text)
print(f"wrote {DST}  {len(text):,} chars")
print("\n--- preview ---\n")
print(text[:3000])
