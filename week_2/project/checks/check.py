"""Независимая проверка результатов pV. Запуск: python3 checks/check.py.

Проверяет фиксированный учебный набор Бойля и новые выходные файлы.
Допуск числовых результатов — 0.001, позволяющий округление до 3 знаков.
Обработчик src/build_pv.py не импортируется и не выполняется.
"""

import csv
import hashlib
import json
import math
import sys
from decimal import Decimal
from pathlib import Path


DATA_SHA256 = "93e92bf03cd81ae09f8d86e603c19e414c9cfad6fd17cdca8c95b3fb031aff74"
TOLERANCE = 0.001


def close_number(actual, expected):
    if isinstance(actual, bool):
        return False
    try:
        value = float(actual)
    except (TypeError, ValueError, OverflowError):
        return False
    return math.isfinite(value) and abs(value - expected) <= TOLERANCE


def verify(root):
    errors = []
    data_path = root / "data/measurements.csv"
    if not data_path.is_file():
        return ["Нет data/measurements.csv"]
    if hashlib.sha256(data_path.read_bytes()).hexdigest() != DATA_SHA256:
        return ["Исходные данные изменены: SHA-256 не совпадает"]

    with data_path.open(encoding="utf-8", newline="") as stream:
        source = list(csv.DictReader(stream))
    products = [Decimal(r["volume_l"]) * Decimal(r["pressure_kpa"]) for r in source]
    ordered = sorted(products)
    middle = len(ordered) // 2
    median = (ordered[middle - 1] + ordered[middle]) / 2 if len(ordered) % 2 == 0 else ordered[middle]
    flags = [int(abs(value / median - 1) > Decimal("0.10")) for value in products]
    clean = [float(value) for value, flag in zip(products, flags) if not flag]
    mean = math.fsum(clean) / len(clean)
    sd = math.sqrt(math.fsum((value - mean) ** 2 for value in clean) / (len(clean) - 1))

    if not (root / "src/build_pv.py").is_file():
        errors.append("Нет src/build_pv.py")

    csv_path = root / "results/pv.csv"
    if not csv_path.is_file():
        errors.append("Нет results/pv.csv")
    else:
        with csv_path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            header = reader.fieldnames
            rows = list(reader)
        if header != ["row", "pv_kpa_l", "suspicious"]:
            errors.append("Столбцы pv.csv должны быть row,pv_kpa_l,suspicious")
        else:
            if len(rows) != len(source):
                errors.append(f"В pv.csv {len(rows)} строк вместо {len(source)}")
            for number, (row, expected, flag) in enumerate(zip(rows, products, flags), 1):
                if row["row"] != str(number):
                    errors.append(f"Нарушены номера или порядок строк: позиция {number}")
                if not close_number(row["pv_kpa_l"], float(expected)):
                    errors.append(f"Неверное pV в строке {number}")
                if row["suspicious"] not in ["0", "1"] or row["suspicious"] != str(flag):
                    errors.append(f"Неверный флаг suspicious в строке {number}")

    summary_path = root / "results/pv_summary.json"
    if not summary_path.is_file():
        errors.append("Нет results/pv_summary.json")
    else:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if not isinstance(summary, dict):
            errors.append("pv_summary.json должен содержать JSON-объект")
        else:
            for key, expected in [("n_total", len(source)), ("n_suspicious", sum(flags))]:
                if type(summary.get(key)) is not int or summary.get(key) != expected:
                    errors.append(f"Неверное целочисленное поле {key}")
            for key, expected in [("mean_pv_clean", mean), ("std_pv_clean", sd),
                                  ("relative_std_clean_percent", 100 * sd / mean)]:
                if not close_number(summary.get(key), expected):
                    errors.append(f"Неверное поле {key}")
    return errors


def main():
    if len(sys.argv) > 2:
        print("Использование: python3 checks/check.py [папка проекта]")
        return 1
    root = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else Path(__file__).resolve().parents[1]
    try:
        errors = verify(root)
    except (OSError, ValueError, TypeError, KeyError, ArithmeticError, csv.Error) as exc:
        print(f"Результат не принят: {type(exc).__name__}: {exc}")
        return 1
    if errors:
        print("Результат не принят:\n- " + "\n- ".join(errors))
        return 1
    print("принято: 12 строк, расчёты и сводка верны, подозрительная строка №7, исходные данные сохранены")
    return 0


if __name__ == "__main__":
    sys.exit(main())
