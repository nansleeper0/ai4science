#!/usr/bin/env python3
"""Локальная проверка недели 4 по practice.md, не исходный checker курса.

Проверяет схему YAML, ссылки, типы отношений и записанные правила в закрытом
мире. Не проверяет научную истинность утверждений и фактическую приёмку человеком.
--strict делает нарушения правил ошибками; --ontology-only проверяет только схему.
"""

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import sys

import yaml

KINDS = {"some", "some_inverse", "some_inverse_any", "all_inverse", "defined",
         "defined_inverse", "defined_value", "section", "disjoint_properties"}
LINK = re.compile(r"\[\[([^\]\n]+)\]\]")


def sequence(value):
    return value if isinstance(value, list) else [value]


def visible(text):
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    return re.sub(r"`[^`\n]*`", "", text)


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*(?:\n|$)", text, re.S)
    return (yaml.safe_load(match.group(1)) or {}, text[match.end():]) if match else ({}, text)


def check(root, strict=False, ontology_only=False, mermaid=None):
    errors, warnings = [], []

    def require(ok, message):
        if not ok:
            errors.append(message)
        return ok

    def note(message):
        print("[OK] " + message)

    def finish():
        for message in errors:
            print("[НЕТ] " + message)
        for message in warnings:
            print("[СОВЕТ] " + message)
        print("\nЛокальная проверка структуры и правил; научные выводы проверяет человек.")
        print("Локальная проверка пройдена." if not errors else f"Ошибок: {len(errors)}")
        return int(bool(errors))

    try:
        schema = yaml.safe_load((root / "ontology.yaml").read_text(encoding="utf-8"))
        if not isinstance(schema, dict):
            raise ValueError("ожидается словарь YAML")
    except (OSError, ValueError, yaml.YAMLError) as error:
        require(False, f"ontology.yaml: {error}")
        return finish()
    classes, properties = schema.get("classes", {}), schema.get("properties", {})
    attributes, rules = schema.get("attributes", {}), schema.get("rules", [])
    if not all(isinstance(v, dict) for v in (classes, properties, attributes)) or not isinstance(rules, list):
        require(False, "classes/properties/attributes — словари, rules — список")
        return finish()
    require(bool(schema.get("ontology") and schema.get("goal")), "Нужны имя и цель онтологии")
    questions = schema.get("competency_questions", [])
    require(isinstance(questions, list) and 3 <= len(questions) <= 5 and all(isinstance(q, str) and q.strip() for q in questions), "Нужно 3–5 содержательных вопросов")
    require(len(classes) >= 3, "Нужно минимум три класса")
    require(len(rules) >= 2, "Нужно минимум два правила")
    require({"Задача", "Файл"} <= set(classes), "Нужны классы Задача и Файл")
    ancestors = {}
    for name, description in classes.items():
        if not isinstance(description, dict):
            require(False, f"Класс {name}: ожидается описание")
            continue
        require(bool(description.get("definition")), f"У класса {name} нет определения")
        seen, current = set(), name
        while current is not None:
            if current in seen:
                require(False, f"Цикл наследования класса {name}")
                break
            if current not in classes or not isinstance(classes[current], dict):
                require(False, f"Неизвестный надкласс {current}")
                break
            seen.add(current)
            current = classes[current].get("parent")
        ancestors[name] = seen
    for name, prop in properties.items():
        if not isinstance(prop, dict):
            require(False, f"Отношение {name}: ожидается описание")
            continue
        for side in ("domain", "range"):
            require(bool(prop.get(side)) and all(c in classes for c in sequence(prop.get(side))), f"{name}: неверный {side}")
    for name, attribute in attributes.items():
        require(isinstance(attribute, dict) and attribute.get("domain") in classes and bool(attribute.get("values")), f"Неверный атрибут {name}")
    require("status" in attributes and attributes["status"].get("domain") == "Задача", "Нужен status для Задача")
    require("подзадачаОт" in properties and properties["подзадачаОт"].get("domain") == "Задача" and properties["подзадачаОт"].get("range") == "Задача", "Нужно отношение подзадачаОт: Задача → Задача")

    derived, ids = {}, set()
    for rule in rules:
        if not isinstance(rule, dict):
            require(False, "Каждое правило — словарь")
            continue
        identifier, spec = rule.get("id"), rule.get("check")
        require(bool(identifier) and identifier not in ids, "Идентификаторы правил должны быть уникальны")
        ids.add(identifier)
        require(bool(rule.get("text") and rule.get("dl")), f"{identifier}: нужны text и dl")
        if not isinstance(spec, dict) or spec.get("kind") not in KINDS:
            require(False, f"{identifier}: неизвестный или отсутствующий вид check")
            continue
        if spec["kind"].startswith("defined"):
            name = spec.get("name")
            require(bool(name) and name not in derived and name not in classes, f"{identifier}: неоднозначный выводимый класс")
            if name:
                derived[name] = spec
    known_classes = set(classes) | set(derived)
    for rule in rules:
        spec = rule.get("check", {}) if isinstance(rule, dict) else {}
        kind = spec.get("kind")
        if kind not in KINDS:
            continue
        if kind != "disjoint_properties":
            require(spec.get("class") in known_classes, f"{rule.get('id')}: неизвестный class")
        for field in ("target", "source"):
            if field in spec:
                require(spec[field] in known_classes, f"{rule.get('id')}: неизвестный {field}")
        rels = sequence(spec["property"]) if "property" in spec else spec.get("properties", [])
        for relation in rels:
            require(relation in properties, f"{rule.get('id')}: неизвестное отношение {relation}")
        required = {"some": ("property", "target"), "some_inverse": ("property", "source"),
                    "some_inverse_any": ("properties",), "all_inverse": ("property", "source"),
                    "defined": ("name", "property", "target"), "defined_inverse": ("name", "properties"),
                    "defined_value": ("name", "attribute", "values"), "section": ("section",),
                    "disjoint_properties": ("properties",)}[kind]
        require(all(spec.get(key) for key in required), f"{rule.get('id')}: не заполнены поля {required}")
        if kind == "defined_value":
            require(spec.get("attribute") in attributes, f"{rule.get('id')}: неизвестный атрибут")
    if errors:
        return finish()
    note(f"Схема: {len(classes)} классов, {len(properties)} отношений, {len(rules)} правил")
    if ontology_only:
        print("Проверена только схема; наличие графа и выполнение недели этим не подтверждены.")
        return finish()

    for filename, key in [("app.json", "showUnsupportedFiles"), ("graph.json", "showAttachments")]:
        try:
            settings = json.loads((root / ".obsidian" / filename).read_text())
            require(settings.get(key) is True, f".obsidian/{filename}: включите {key}")
        except (OSError, ValueError) as error:
            require(False, f".obsidian/{filename}: {error}")
    objects, class_paths = {}, {}
    for name, desc in classes.items():
        path = root / "ontology" / f"{name}.md"
        if not require(path.is_file(), f"Нет заметки класса ontology/{name}.md"):
            continue
        try:
            meta, body = frontmatter(path)
            require(meta.get("kind") == "класс", f"{path.name}: нужен kind: класс")
            raw_parents = re.findall(r"^-\s*подклассОт:\s*\[\[([^\]]+)\]\]", visible(body), re.M)
            parents = [Path(raw.split("|", 1)[0].split("#", 1)[0]).name.removesuffix(".md") for raw in raw_parents]
            expected = [] if desc.get("parent") is None else [desc["parent"]]
            require(parents == expected, f"{path.name}: надкласс не совпадает с YAML")
            class_paths[path.relative_to(root).as_posix()] = name
        except (ValueError, yaml.YAMLError) as error:
            require(False, f"{path.name}: {error}")
    for folder in ("notes", "tasks", "reports"):
        for path in sorted((root / folder).rglob("*.md")):
            try:
                meta, body = frontmatter(path)
                kind = meta.get("type")
                if not require(kind in classes, f"{path.relative_to(root)}: нужен известный type"):
                    continue
                require(path.stem not in classes, f"{path.name}: имя экземпляра совпало с классом")
                if folder == "tasks":
                    require("Задача" in ancestors[kind], f"{path.name}: в tasks ожидается Задача")
                if folder == "reports":
                    require("Отчёт" in ancestors[kind], f"{path.name}: в reports ожидается Отчёт")
                objects[path.relative_to(root).as_posix()] = {"meta": meta, "body": visible(body), "type": kind}
            except (ValueError, yaml.YAMLError, TypeError) as error:
                require(False, f"{path}: {error}")
    require(len(objects) >= 10, f"Объектов {len(objects)}, нужно не меньше 10 (классы и файлы не считаются)")
    require(any("Задача" in ancestors[o["type"]] for o in objects.values()), "В графе нет задач")
    catalog, by_name = set(), defaultdict(list)
    for path in root.rglob("*"):
        if not path.is_file() or any(part in {".git", ".venv", "__pycache__", ".ipynb_checkpoints"} for part in path.relative_to(root).parts):
            continue
        rel = path.relative_to(root).as_posix()
        catalog.add(rel)
        by_name[path.name].append(rel)
        if path.suffix == ".md":
            by_name[path.stem].append(rel)

    def resolve(raw):
        target = raw.split("|", 1)[0].split("#", 1)[0].strip()
        if not target or Path(target).is_absolute() or ".." in Path(target).parts:
            return None
        if target in catalog:
            return target
        if target + ".md" in catalog:
            return target + ".md"
        matches = sorted(set(by_name.get(target, [])))
        return matches[0] if len(matches) == 1 else None

    memberships = {name: set() for name in known_classes}
    memberships["Файл"] = set(catalog)
    for key, obj in objects.items():
        for kind in ancestors[obj["type"]]:
            memberships[kind].add(key)
    edges, source_edges = defaultdict(set), defaultdict(list)
    for key, obj in objects.items():
        body = obj["body"]
        for raw in LINK.findall(body):
            require(resolve(raw) is not None, f"{key}: отсутствующая или неоднозначная ссылка [[{raw}]]")
        connections = re.search(r"^##\s+Связи\s*$([\s\S]*?)(?=^##\s|\Z)", body, re.M)
        typed_links = []
        if connections:
            for line in connections.group(1).splitlines():
                pair = re.match(r"^\s*-\s*([^:]+):\s*(.+)$", line)
                if not pair:
                    continue
                relation = pair.group(1).strip()
                for raw in LINK.findall(pair.group(2)):
                    target = resolve(raw)
                    if relation == "тип":
                        typed_links.append(class_paths.get(target))
                        continue
                    if relation not in properties:
                        require(False, f"{key}: отношение {relation} не объявлено")
                        continue
                    if target is None:
                        continue
                    edges[relation].add((key, target))
                    source_edges[key].append((relation, target))
                    prop = properties[relation]
                    require(any(key in memberships[c] for c in sequence(prop["domain"])), f"{key}: нарушен domain отношения {relation}")
                    require(any(target in memberships[c] for c in sequence(prop["range"])), f"{key}: нарушен range отношения {relation} → {target}")
        require(typed_links == [obj["type"]], f"{key}: нужна ровно одна связь тип с классом {obj['type']}")
        for attr, spec in attributes.items():
            if key in memberships[spec["domain"]]:
                require(obj["meta"].get(attr) in spec["values"], f"{key}: недопустимое или отсутствующее {attr}")
        if key in memberships["Задача"]:
            require(bool(re.search(r"Готово, когда:\s*\S", body)), f"{key}: нет условия «Готово, когда»")
            require(bool(re.search(r"Не входит:\s*\S", body)), f"{key}: нет границ «Не входит»")
            is_child = any(a == key for a, _ in edges.get("подзадачаОт", set()))
            if not is_child:
                require(bool(re.search(r"Запрос пользователя:\s*\S", body)), f"{key}: у верхней задачи нет запроса пользователя")
            if obj["meta"].get("status") == "принята":
                require(bool(re.search(r"Принято пользователем:\s*\S", body)), f"{key}: нет записи слов приёмки (её истинность проверяет человек)")
            if obj["meta"].get("status") == "заблокирована":
                require(bool(re.search(r"^##\s+Итог\s*\n\s*\S", body, re.M)), f"{key}: нет итога заблокированной задачи")

    # Finite monotone evaluation of only the derived class forms in the schema.
    for _ in range(len(derived) + 1):
        changed = False
        for name, spec in derived.items():
            base = memberships[spec["class"]]
            if spec["kind"] == "defined_value":
                result = {x for x in base if objects.get(x, {}).get("meta", {}).get(spec["attribute"]) in spec["values"]}
            elif spec["kind"] == "defined":
                result = {a for a, b in edges[spec["property"]] if a in base and b in memberships[spec["target"]]}
            else:
                result = {b for prop in spec["properties"] for a, b in edges[prop] if b in base}
            if result - memberships[name]:
                memberships[name].update(result)
                changed = True
        if not changed:
            break
    for rule in rules:
        spec, identifier = rule["check"], rule["id"]
        kind = spec["kind"]
        if kind.startswith("defined"):
            continue
        base = memberships.get(spec.get("class"), set())
        bad = set()
        if kind == "some":
            valid = {a for a, b in edges[spec["property"]] if b in memberships[spec["target"]]}
            bad = base - valid
        elif kind == "some_inverse":
            valid = {b for a, b in edges[spec["property"]] if a in memberships[spec["source"]]}
            bad = base - valid
        elif kind == "some_inverse_any":
            valid = {b for prop in spec["properties"] for a, b in edges[prop]}
            bad = base - valid
        elif kind == "all_inverse":
            bad = {b for a, b in edges[spec["property"]] if b in base and a not in memberships[spec["source"]]}
        elif kind == "section":
            bad = {x for x in base if not re.search(r"^##\s+" + re.escape(spec["section"]) + r"\s*\n\s*\S", objects.get(x, {}).get("body", ""), re.M)}
        elif kind == "disjoint_properties":
            seen = set()
            for prop in spec["properties"]:
                bad.update(seen & edges[prop])
                seen.update(edges[prop])
        if bad:
            message = f"Правило {identifier}: {rule['text']} Нарушения: {sorted(map(str, bad))}"
            (errors if strict else warnings).append(message)
    # Parent cycles are invalid even while tasks are still open.
    parents = defaultdict(set)
    for child, parent in edges.get("подзадачаОт", set()):
        parents[child].add(parent)
    def cycle(node, trail):
        return node in trail or any(cycle(parent, trail | {node}) for parent in parents[node])
    for node in list(parents):
        require(not cycle(node, set()), f"Цикл задач у {node}")
    note(f"Граф: {len(objects)} объектов, {sum(map(len, edges.values()))} типизированных связей")
    statuses = Counter(o["meta"].get("status") for o in objects.values() if "Задача" in ancestors[o["type"]])
    note("Статусы задач: " + ", ".join(f"{key}: {value}" for key, value in sorted(statuses.items(), key=lambda item: str(item[0]))))
    if mermaid:
        vertices = sorted(set(objects) | set(class_paths) | {b for pairs in edges.values() for _, b in pairs})
        ids = {node: f"n{i}" for i, node in enumerate(vertices)}
        lines = ["# Граф проекта", "", "```mermaid", "flowchart LR"]
        for node in vertices:
            label = node[:-3] if node.endswith(".md") else node
            lines.append(f"  {ids[node]}[{json.dumps(label, ensure_ascii=False)}]")
        for relation, pairs in sorted(edges.items()):
            for a, b in sorted(pairs):
                lines.append(f"  {ids[a]} -->|{relation}| {ids[b]}")
        for node, obj in objects.items():
            target = f"ontology/{obj['type']}.md"
            if target in ids:
                lines.append(f"  {ids[node]} -->|тип| {ids[target]}")
        for node, name in class_paths.items():
            parent = classes[name].get("parent")
            target = f"ontology/{parent}.md"
            if parent and target in ids:
                lines.append(f"  {ids[node]} -->|подклассОт| {ids[target]}")
        lines.append("```\n")
        output = mermaid if mermaid.is_absolute() else root / mermaid
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("\n".join(lines), encoding="utf-8")
        note(f"Схема Mermaid: {output}")
    return finish()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path, nargs="?", default=Path(__file__).resolve().parent)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--ontology-only", action="store_true")
    parser.add_argument("--mermaid", type=Path)
    args = parser.parse_args()
    try:
        sys.exit(check(args.project.resolve(), args.strict, args.ontology_only, args.mermaid))
    except (KeyError, TypeError, AttributeError, ValueError, RecursionError) as error:
        print(f"[НЕТ] Некорректная схема или структура: {error}")
        sys.exit(1)
