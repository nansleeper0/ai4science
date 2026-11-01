#!/usr/bin/env python3
"""
Вычисление pV по data/measurements.csv, обнаружение подозрительных строк,
сохранение результатов в results/pv.csv и results/pv_summary.json.
"""

import csv
import json
import math
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CSV_PATH = BASE / "data" / "measurements.csv"
PV_CSV_PATH = BASE / "results" / "pv.csv"
SUMMARY_JSON_PATH = BASE / "results" / "pv_summary.json"


def read_measurements(path: Path) -> list[dict]:
    rows = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "volume_l": float(row["volume_l"]),
                "pressure_kpa": float(row["pressure_kpa"]),
                "temperature_k": float(row["temperature_k"]),
            })
    return rows


def median(values: list[float]) -> float:
    s = sorted(values)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2


def sample_stdev(values: list[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    return math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1))


def main():
    rows = read_measurements(CSV_PATH)

    # Вычислить pV для каждой строки
    pv_values = [r["volume_l"] * r["pressure_kpa"] for r in rows]

    # Медиана по всем строкам
    med = median(pv_values)

    # Отметить подозрительные: abs(pV / median - 1) > 0.10
    suspicious_flags = [1 if abs(pv / med - 1) > 0.10 else 0 for pv in pv_values]

    # Записать pv.csv
    PV_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PV_CSV_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["row", "pv_kpa_l", "suspicious"])
        for i, pv in enumerate(pv_values):
            writer.writerow([i + 1, pv, suspicious_flags[i]])

    # Статистика по чистым строкам
    clean_pv = [pv for pv, s in zip(pv_values, suspicious_flags) if s == 0]
    n_total = len(rows)
    n_suspicious = sum(suspicious_flags)
    mean_clean = sum(clean_pv) / len(clean_pv)
    std_clean = sample_stdev(clean_pv)
    rel_std = 100.0 * std_clean / mean_clean

    # Записать summary JSON
    SUMMARY_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "n_total": n_total,
        "n_suspicious": n_suspicious,
        "mean_pv_clean": mean_clean,
        "std_pv_clean": std_clean,
        "relative_std_clean_percent": rel_std,
    }
    with open(SUMMARY_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"n_total={n_total}, n_suspicious={n_suspicious}")
    print(f"median(pV)={med:.6f}")
    print(f"mean_pv_clean={mean_clean:.6f}")
    print(f"std_pv_clean={std_clean:.6f}")
    print(f"relative_std_clean_percent={rel_std:.4f}%")
    print(f"Результаты: {PV_CSV_PATH}, {SUMMARY_JSON_PATH}")


if __name__ == "__main__":
    main()