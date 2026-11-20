"""Extract the review's text so it can be read and cited accurately."""
import os
import re

from pypdf import PdfReader

PDF = r"D:\coda_matlab\histobridge\docs\bbag255.pdf"
OUT = r"D:\coda_matlab\histobridge\docs\bbag255.txt"


def main():
    r = PdfReader(PDF)
    print(f"pages {len(r.pages)}")
    parts = []
    for i, p in enumerate(r.pages, 1):
        try:
            t = p.extract_text() or ""
        except Exception as e:
            t = f"[page {i} extraction failed: {e}]"
        parts.append(f"\n\n===== PAGE {i} =====\n{t}")
    text = "".join(parts)
    text = re.sub(r"[ \t]+\n", "\n", text)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"wrote {OUT}  {len(text):,} chars")
    print("\n--- first 2500 chars ---\n")
    print(text[:2500])


if __name__ == "__main__":
    main()
