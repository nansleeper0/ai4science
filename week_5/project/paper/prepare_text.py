"""Извлечь текст выбранной статьи с метками PDF-страниц. Без вызовов ИИ."""

from hashlib import sha256
from pathlib import Path
from pypdf import PdfReader

paper_dir = Path(__file__).resolve().parent
pdf_path = paper_dir / "paper.pdf"
text_path = paper_dir / "paper.txt"
source_path = paper_dir / "SOURCE.md"
if text_path.exists() or source_path.exists():
    raise FileExistsError("paper.txt или SOURCE.md уже есть: прежние файлы сохранены")

reader = PdfReader(pdf_path)
pages = [f"[с. {i}]\n{page.extract_text() or ''}" for i, page in enumerate(reader.pages, 1)]
text = "\n\n".join(pages) + "\n"
text_path.write_text(text, encoding="utf-8")
source_path.write_text(
    "# Источник статьи\n\n"
    "Alexander A. Mushtukov, Albert Weng, Sergey S. Tsygankov, Ilya A. Mereminskiy.\n"
    "Flickering pulsations in bright X-ray pulsars: the evidence of gravitationally "
    "lensed and eclipsed accretion column.\n\n"
    "arXiv:2404.04137v1 (2024): https://arxiv.org/abs/2404.04137v1\n\n"
    f"Локальная копия: paper.pdf; страниц PDF: {len(reader.pages)}.\n"
    f"SHA-256: {sha256(pdf_path.read_bytes()).hexdigest()}\n\n"
    "paper.txt извлечён pypdf с метками [с. N]. Номера соответствуют страницам "
    "PDF. Формулы и рисунки проверяются по PDF, а не по извлечённому тексту.\n",
    encoding="utf-8",
)
print("Страниц PDF:", len(reader.pages))
print("Слов в извлечённом тексте:", len(text.split()))
print("Созданы:", text_path, "и", source_path)
