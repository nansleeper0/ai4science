"""Разделить PDF на последовательные части, не вызывая агента."""

from pathlib import Path
from pypdf import PdfReader

paper_dir = Path(__file__).resolve().parent
reader = PdfReader(paper_dir / "paper.pdf")
parts, current, count = [], [], 0
for number, page in enumerate(reader.pages, 1):
    text = page.extract_text() or ""
    current.append((number, text))
    count += len(text.split())
    if count >= 1500:
        parts.append(current)
        current, count = [], 0
if current:
    parts.append(current)

parts_dir = paper_dir / "parts"
targets = [parts_dir / f"part_{i:02d}.md" for i in range(1, len(parts) + 1)]
existing = [p for p in targets if p.exists()]
if existing:
    raise FileExistsError(f"Части уже существуют и сохранены: {existing}")

parts_dir.mkdir(parents=True, exist_ok=True)
(paper_dir.parent / "memory/L1").mkdir(parents=True, exist_ok=True)
for i, (pages, target) in enumerate(zip(parts, targets), 1):
    first, last = pages[0][0], pages[-1][0]
    body = "\n\n".join(f"[с. {number}]\n{text}" for number, text in pages)
    target.write_text(f"# Часть {i}: с. {first}–{last}\n\n{body}\n", encoding="utf-8")
    print(f"{target.name}: PDF-страницы {first}–{last}, слов {sum(len(t.split()) for _, t in pages)}")
print("Частей:", len(parts), "| Сжатие агентом ещё не выполнялось.")
