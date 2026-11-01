"""Локальная проверка наставника по практике недели 3. Не официальный check_week3.py.

Проверяет структуру, цитаты на PDF-страницах, сохранённые свидетельства и git.
Не устанавливает научную правильность тезисов и не заменяет чтение человеком.
"""

import argparse
import ast
import csv
import json
from pathlib import Path
import re
import subprocess
import unicodedata


def normalize(text):
    text = re.sub(r"(\w)-\s+(\w)", r"\1\2", text)
    text = unicodedata.normalize("NFKC", text).replace("\u00ad", "")
    return re.sub(r"\s+", "", text).casefold()


def table_rows(text, headings):
    result, active = [], False
    for line in text.splitlines():
        if not line.startswith("|"):
            if active and line.strip():
                active = False
            continue
        cells = [v.strip() for v in line.strip().strip("|").split("|")]
        if cells == headings:
            active = True
        elif active and len(cells) == len(headings) and cells[0].isdigit():
            result.append(cells)
    return result


def quote_matches(cell, page_texts, page_numbers):
    fragments = re.findall(r'"([^"\n]+)"|«([^»\n]+)»|“([^”\n]+)”', cell)
    quotes = [next(s for s in group if s) for group in fragments]
    if not quotes:
        quotes = [cell.strip()]
    valid_pages = [page_texts[p - 1] for p in page_numbers if 1 <= p <= len(page_texts)]
    return bool(valid_pages) and all(
        len(normalize(q)) >= (8 if any(c.isdigit() for c in q) else 12) and any(normalize(q) in normalize(p) for p in valid_pages)
        for q in quotes
    )


def strip_docs(tree):
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                node.body.pop(0)
    return ast.dump(tree, include_attributes=False)


def check(root, section="all", no_git=False):
    failures = []

    def require(ok, message):
        print(("[OK] " if ok else "[НЕТ] ") + message)
        if not ok:
            failures.append(message)

    def read(relative):
        p = root / relative
        if not p.is_file():
            require(False, f"Нет файла {relative}")
            return ""
        return p.read_text(encoding="utf-8")

    if section in ("all", "article"):
        from pypdf import PdfReader
        pdf = root / "paper/paper.pdf"
        try:
            pages = [p.extract_text() or "" for p in PdfReader(pdf).pages]
            require(8 <= len(pages) <= 30, f"PDF: {len(pages)} страниц")
        except Exception as error:
            pages = []
            require(False, f"PDF не прочитан: {error}")
        l1, l2, l3 = [read(f"memory/L{i}.md") for i in (1, 2, 3)]
        require("2404.04137v1" in l1, "L1 содержит источник с версией")
        for number, allowed in [(1, {1, 2}), (2, {3, 4, 5}), (3, {6, 7, 8, 9})]:
            text = read(f"memory/L1/part_{number:02d}.md")
            body = "\n".join(s for s in text.splitlines() if not s.startswith("#"))
            refs = {int(n) for n in re.findall(r"\(с\.\s*(\d+)", body)}
            count = len(body.split())
            require(100 <= count <= 150 and bool(refs) and refs <= allowed,
                    f"L1 part_{number:02d}: {count} слов, корректный диапазон страниц")
        claims = re.findall(r"^(\d+)\.\s+(.+)$", l2, re.M)
        claim_ids = {int(n) for n, _ in claims}
        require(5 <= len(claims) <= 10 and len(claim_ids) == len(claims), "L2: 5–10 уникально пронумерованных тезисов")
        require(all(re.search(r"\(с\.\s*\d+", text) for _, text in claims) and bool(claims), "У каждого тезиса L2 есть страница")
        body3 = [s.strip() for s in l3.splitlines() if s.strip() and not s.startswith("#")]
        require(len(body3) == 1 and 1 <= len(body3[0].split()) <= 30, "L3: одна фраза до 30 слов")
        checked = set()
        rows = table_rows(l2, ["№", "Тезис", "Стр.", "Цитата из оригинала", "Итог"])
        for row in rows:
            if not row[1].isdigit() or not row[3] or not row[4]:
                continue
            cid = int(row[1]); nums = [int(n) for n in re.findall(r"\d+", row[2])]
            outcome = row[4].casefold()
            ok = cid in claim_ids and quote_matches(row[3], pages, nums) and any(outcome.startswith(s) for s in ("подтверждено", "исправлено", "расходится")) and "ЗАПОЛНИ" not in " ".join(row)
            require(ok, f"Сверка тезиса {cid}: цитата найдена на указанных страницах и есть итог")
            if ok:
                checked.add(cid)
        require(len(checked) >= 3, f"Сверено различных тезисов: {len(checked)} из минимум 3")
        answers = read("results/week3_answers_review.md")
        checked_answers = set()
        for row in table_rows(answers, ["Вопрос", "Стр.", "Цитата из оригинала", "Итог"]):
            nums = [int(n) for n in re.findall(r"\d+", row[1])]
            ok = bool(row[2] and row[3]) and quote_matches(row[2], pages, nums) and "ЗАПОЛНИ" not in " ".join(row)
            require(ok, f"Сверка исходного ответа {row[0]}: цитата и итог заполнены")
            if ok:
                checked_answers.add(int(row[0]))
        require({1, 2, 3} <= checked_answers, "Сверены все три ответа из полного окна")
        original = read("results/week3_article_full_context.md")
        require("15964" in original and "21369" in original and "1048576" in original, "Исходный статус и ответы сохранены")
        require((root / "paper/METHOD.md").is_file(), "Методика статьи сохранена")
        try:
            journal = list(csv.DictReader((root / "journal.csv").open(encoding="utf-8")))
            require(bool(journal) and journal[-1].get("φ") == "1", "Журнал собственной задачи заканчивается φ=1")
            notebook = json.loads(read("notebooks/agent_loop.ipynb"))
            own = [c for c in notebook.get("cells", []) if "my_journal, my_context = run" in "".join(c.get("source", []))]
            output = "".join("".join(o.get("text", [])) for c in own for o in c.get("outputs", []))
            require("φ = 1" in output and "249.3182" in output, "Собственный прогон сохранён в notebook")
        except (OSError, ValueError, TypeError) as error:
            require(False, f"Журнал/notebook: {error}")

    if section in ("all", "project"):
        agents, index, status = [read(p) for p in ("AGENTS.md", "INDEX.md", "STATUS.md")]
        require(not (root / "AGENT.md").exists(), "Нет второго договора AGENT.md")
        require(len(re.findall(r"^## ", agents, re.M)) >= 5, "AGENTS: минимум пять разделов")
        conventions = re.search(r"^### Чего агент не может знать сам\s*$(.*?)(?=^## |\Z)", agents, re.M | re.S)
        count = len(re.findall(r"^- ", conventions.group(1), re.M)) if conventions else 0
        require(count >= 3, f"Соглашений «Чего агент не может знать сам»: {count}")
        require(len([s for s in agents.splitlines() if "[W3-ROUND]" in s]) == 1, "Одна строка округления [W3-ROUND] для сравнения")
        require("INDEX.md" in agents and "STATUS.md" in agents, "AGENTS ссылается на указатель и состояние")
        paths = re.findall(r"`([^`]+)`", index)
        invalid = []
        for path in paths:
            if " " in path or "(" in path or ")" in path:
                invalid.append(path); continue
            relative, _, symbol = path.partition("::")
            p = root / relative
            if not p.exists():
                invalid.append(path)
            elif symbol:
                try:
                    functions = {n.name for n in ast.walk(ast.parse(p.read_text())) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
                    if symbol not in functions:
                        invalid.append(path)
                except (ValueError, OSError, SyntaxError):
                    invalid.append(path)
        require(len(paths) >= 5 and not invalid, f"INDEX: {len(paths)} путей, отсутствующие/неверные: {invalid}")
        require("memory/L2.md" in paths, "INDEX включает memory/L2.md")
        require(all(s in status for s in ("## Где мы", "## Дальше", "## Действует")), "STATUS содержит состояние, следующий шаг и ограничения")
        source = read("src/build_pv.py")
        baseline = read("results/week3_before_finish/build_pv.py")
        try:
            tree = ast.parse(source)
            funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
            for name in ("read_measurements", "median", "sample_stdev"):
                doc = ast.get_docstring(funcs[name]) or ""
                require(all(label in doc for label in ("Данные:", "Проверка:", "Используется в:")), f"Пометки функции {name}")
            require(strip_docs(ast.parse(source)) == strip_docs(ast.parse(baseline)), "В вычислительном коде изменены только строки документации")
        except (SyntaxError, KeyError) as error:
            require(False, f"Пометки/синтаксис: {error}")

    if section == "all":
        for relative in ("results/week3_ab.md", "results/week3_navigation.md"):
            text = read(relative)
            require(len(text) >= 150 and "ЗАПОЛНИ" not in text, f"Заполнено свидетельство {relative}")
            numbers = [int(n) for n in re.findall(r"Вызовы инструментов:\s*(\d+)", text)]
            require(len(numbers) == (2 if "_ab." in relative else 1) and all(n > 0 for n in numbers), f"Указано фактическое число вызовов в {relative}")
            if "navigation" in relative:
                require(bool(numbers) and numbers[0] <= 3 and "src/build_pv.py" in text and re.search(r"\bmain\b", text) is not None, "Навигация: правильная функция за 1–3 вызова")
        try:
            ab = json.loads(read("results/week3_ab_paths.json"))
            with_text, without_text = ab["with_contract"], ab["without_contract"]
            expected = "".join(s for s in with_text.splitlines(keepends=True) if "[W3-ROUND]" not in s)
            differences = [k for k in set(ab["with_hashes"]) | set(ab["without_hashes"]) if ab["with_hashes"].get(k) != ab["without_hashes"].get(k)]
            require(expected == without_text and "[W3-ROUND]" not in without_text and differences == ["AGENTS.md"], "A/B-копии различались одной строкой договора")
            committed_method = subprocess.check_output(["git", "show", ab["precommit"] + ":results/week3_ab_METHOD.md"], cwd=root, text=True)
            require(bool(committed_method.strip()), "Методика A/B есть в коммите до подготовки запусков")
        except (ValueError, KeyError, subprocess.CalledProcessError) as error:
            require(False, f"Методика/подготовка A/B: {error}")
        diary = read("diary.md")
        require(all(s in diary for s in ("15 964", "L1", "L2", "L3")), "Дневник содержит итог работы со статьёй и размер контекста")
        require((root / "cycle_table.md").is_file(), "Разбор цикла notebook сохранён")

    if not no_git:
        result = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True)
        require(result.returncode == 0 and not result.stdout.strip(), "Рабочее дерево git чистое")

    print("\nЭто локальная проверка структуры и свидетельств; научный смысл проверяет человек.")
    print("Локальные проверки пройдены." if not failures else f"Не пройдено пунктов: {len(failures)}")
    return 0 if not failures else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-git", action="store_true")
    parser.add_argument("--section", choices=("all", "article", "project"), default="all")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    raise SystemExit(check(args.root.resolve(), args.section, args.no_git))
