"""Собрать L1 из трёх уже созданных частей без вызова модели."""

from pathlib import Path
import re

project = Path(__file__).resolve().parents[1]
parts = []
for number, allowed in [(1, {1, 2}), (2, {3, 4, 5}), (3, {6, 7, 8, 9})]:
    path = project / f"memory/L1/part_{number:02d}.md"
    text = path.read_text(encoding="utf-8").strip()
    body = "\n".join(line for line in text.splitlines() if not line.startswith("#"))
    count = len(body.split())
    if not 100 <= count <= 150:
        raise ValueError(f"{path.name}: {count} слов без заголовка, требуется 100–150")
    refs = {int(n) for n in re.findall(r"\(с\.\s*(\d+)", body)}
    if not refs or not refs <= allowed:
        raise ValueError(f"{path.name}: проверьте ссылки на PDF-страницы {refs}")
    print(f"{path.name}: {count} слов, ссылки на страницы {sorted(refs)}")
    parts.append(text)

header = (
    "# L1 — реферат по частям\n\n"
    "Статья: Alexander A. Mushtukov, Albert Weng, Sergey S. Tsygankov, "
    "Ilya A. Mereminskiy. «Flickering pulsations in bright X-ray pulsars: "
    "the evidence of gravitationally lensed and eclipsed accretion column». "
    "arXiv:2404.04137v1 (2024), https://arxiv.org/abs/2404.04137v1.\n\n"
    "Страницы — по paper/paper.pdf, от 1 до 9.\n"
    "Части порождены deepseek-v4-flash/latest в отдельных сессиях. "
    "Здесь они собраны без изменения текста. Содержательная сверка с PDF впереди.\n\n"
)
result = header + "\n\n".join(parts) + "\n"
target = project / "memory/L1.md"
if target.exists():
    if target.read_text(encoding="utf-8") != result:
        raise FileExistsError("L1.md уже существует с другим содержимым; файл сохранён")
    print("L1.md уже собран, повторная запись не требуется.")
else:
    target.write_text(result, encoding="utf-8")
    print("Создан:", target)
print("Объём и страницы проверены; это не проверка научной точности.")
