"""Проверка checker на временных примерах; реальные результаты не меняются."""

import argparse
import csv
import json
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["row", "pv_kpa_l", "suspicious"])
        writer.writeheader()
        writer.writerows(rows)


def fixture(root, raw):
    for name in ["data", "src", "results"]:
        (root / name).mkdir()
    (root / "data/measurements.csv").write_bytes(raw)
    (root / "src/build_pv.py").write_text("# Временная заглушка для проверки наличия файла.\n")
    source = list(csv.DictReader(raw.decode("utf-8").splitlines()))
    pv = [float(row["volume_l"]) * float(row["pressure_kpa"]) for row in source]
    med = statistics.median(pv)
    flags = [int(abs(value / med - 1) > 0.10) for value in pv]
    clean = [value for value, flag in zip(pv, flags) if not flag]
    rows = [{"row": i, "pv_kpa_l": value, "suspicious": flag}
            for i, (value, flag) in enumerate(zip(pv, flags), 1)]
    summary = {"n_total": len(pv), "n_suspicious": sum(flags),
               "mean_pv_clean": statistics.mean(clean),
               "std_pv_clean": statistics.stdev(clean),
               "relative_std_clean_percent": 100 * statistics.stdev(clean) / statistics.mean(clean)}
    write_csv(root / "results/pv.csv", rows)
    (root / "results/pv_summary.json").write_text(json.dumps(summary))
    return rows, summary


def main():
    project = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--checker", type=Path, default=Path(__file__).with_name("check.py"))
    parser.add_argument("--data", type=Path, default=project / "data/measurements.csv")
    args = parser.parse_args()
    raw = args.data.read_bytes()
    cases = [("good", "Правильный результат", 0),
             ("pv", "Испорчено одно pV", 1),
             ("flag", "Снят флаг строки №7", 1),
             ("summary", "Испорчено среднее сводки", 1),
             ("missing", "Потеряна строка результата", 1),
             ("raw", "Изменены исходные данные", 1)]
    failures = []
    for kind, label, expected in cases:
        with tempfile.TemporaryDirectory(prefix="boyle_checker_selftest_") as temp:
            root = Path(temp)
            rows, summary = fixture(root, raw)
            if kind == "pv":
                rows[0]["pv_kpa_l"] += 1
                write_csv(root / "results/pv.csv", rows)
            elif kind == "flag":
                rows[6]["suspicious"] = 0
                write_csv(root / "results/pv.csv", rows)
            elif kind == "summary":
                summary["mean_pv_clean"] += 1
                (root / "results/pv_summary.json").write_text(json.dumps(summary))
            elif kind == "missing":
                write_csv(root / "results/pv.csv", rows[:-1])
            elif kind == "raw":
                (root / "data/measurements.csv").write_bytes(raw.replace(b"247.036", b"248.036", 1))
            result = subprocess.run([sys.executable, str(args.checker.resolve()), str(root)],
                                    capture_output=True, text=True)
            ok = result.returncode == expected
            print(f"{'OK' if ok else 'ОШИБКА'}: {label}: код {result.returncode}, ожидается {expected}")
            if not ok:
                failures.append(label)
                print(result.stdout + result.stderr)
    if failures:
        print("Самопроверка не пройдена")
        return 1
    print("Самопроверка пройдена: 6 случаев. Реальные данные и результаты проекта не изменены.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
