#!/usr/bin/env python3
"""
Анализ закона Бойля–Мариотта: p·V = const при постоянной температуре.

Читает data/measurements.csv, вычисляет pV для каждого измерения,
рассчитывает статистику и находит аномальные точки.
"""

import csv
import math
import statistics
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CSV_PATH = BASE / "data" / "measurements.csv"
RESULTS_PATH = BASE / "results" / "analysis.txt"


def read_measurements(path: Path) -> list[dict]:
    """Прочитать CSV и вернуть список измерений."""
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


def compute_pv(rows: list[dict]) -> list[float]:
    """Вычислить p·V для каждого измерения."""
    return [r["pressure_kpa"] * r["volume_l"] for r in rows]


def detect_anomalies_iqr(pv_values: list[float]) -> list[int]:
    """
    Обнаружение аномалий через IQR-метод (1.5 * IQR).
    Возвращает индексы аномальных измерений.
    """
    sorted_vals = sorted(pv_values)
    n = len(sorted_vals)
    q1_idx = n // 4
    q3_idx = 3 * n // 4
    q1 = sorted_vals[q1_idx]
    q3 = sorted_vals[q3_idx]
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    anomalies = []
    for i, v in enumerate(pv_values):
        if v < lower_bound or v > upper_bound:
            anomalies.append(i)
    return anomalies, lower_bound, upper_bound


def detect_anomalies_zscore(pv_values: list[float], threshold: float = 2.0) -> list[int]:
    """
    Обнаружение аномалий через Z-score.
    Возвращает индексы аномальных измерений.
    """
    mean = statistics.mean(pv_values)
    stdev = statistics.stdev(pv_values)
    anomalies = []
    for i, v in enumerate(pv_values):
        z = abs(v - mean) / stdev if stdev > 0 else 0
        if z > threshold:
            anomalies.append(i)
    return anomalies, mean, stdev


def main():
    rows = read_measurements(CSV_PATH)
    pv_values = compute_pv(rows)

    # Статистика
    mean_pv = statistics.mean(pv_values)
    median_pv = statistics.median(pv_values)
    stdev_pv = statistics.stdev(pv_values)

    # Аномалии: IQR-метод
    anomalies_iqr, lower_iqr, upper_iqr = detect_anomalies_iqr(pv_values)

    # Аномалии: Z-score метод
    anomalies_zscore, mean_z, stdev_z = detect_anomalies_zscore(pv_values)

    # Объединяем аномалии (обеих методов)
    all_anomalies = sorted(set(anomalies_iqr) | set(anomalies_zscore))

    # Формируем отчёт
    lines = []
    lines.append("=" * 60)
    lines.append("АНАЛИЗ ЗАКОНА БОЙЛЯ–МАРИОТТА")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Количество измерений: {len(rows)}")
    lines.append(f"Температура: {rows[0]['temperature_k']:.2f} K (постоянная)")
    lines.append("")

    lines.append("-" * 60)
    lines.append("p·V для каждого измерения:")
    lines.append("-" * 60)
    lines.append(f"{'№':>3} | {'V (л)':>7} | {'P (кПа)':>8} | {'T (K)':>7} | {'p·V':>10}")
    lines.append("-" * 60)
    for i, r in enumerate(rows):
        pv = pv_values[i]
        marker = " <-- АНОМАЛИЯ" if i in all_anomalies else ""
        lines.append(
            f"{i + 1:>3} | {r['volume_l']:>7.2f} | {r['pressure_kpa']:>8.3f} | "
            f"{r['temperature_k']:>7.2f} | {pv:>10.3f}{marker}"
        )
    lines.append("-" * 60)
    lines.append("")

    lines.append("-" * 60)
    lines.append("Статистика p·V:")
    lines.append("-" * 60)
    lines.append(f"  Среднее:   {mean_pv:.3f}")
    lines.append(f"  Медиана:   {median_pv:.3f}")
    lines.append(f"  Ст. откл:  {stdev_pv:.3f}")
    lines.append(f"  Мин:       {min(pv_values):.3f}")
    lines.append(f"  Макс:      {max(pv_values):.3f}")
    lines.append("")

    lines.append("-" * 60)
    lines.append("Обнаруженные аномалии:")
    lines.append("-" * 60)
    if all_anomalies:
        for idx in all_anomalies:
            r = rows[idx]
            pv = pv_values[idx]
            lines.append(
                f"  Измерение #{idx + 1}: V={r['volume_l']:.2f} л, "
                f"P={r['pressure_kpa']:.3f} кПа, p·V={pv:.3f}"
            )
        lines.append("")
        lines.append("Критерий обнаружения:")
        sorted_pv = sorted(pv_values)
        n = len(sorted_pv)
        q1_val = sorted_pv[n // 4]
        q3_val = sorted_pv[3 * n // 4]
        iqr_val = q3_val - q1_val
        lines.append(f"  IQR-метод: Q1={q1_val:.3f}, Q3={q3_val:.3f}, "
                      f"IQR={iqr_val:.3f}")
        lines.append(f"  Границы: [{lower_iqr:.3f}, {upper_iqr:.3f}]")
        lines.append(f"  Метод: Q1 — элемент [n//4], Q3 — элемент [3n//4] "
                      f"в отсортированном ряду (n={n}).")
        lines.append(f"  Z-score метод: порог > 2.0 сигм от среднего")
        lines.append("")
        lines.append("Объяснение:")
        lines.append(
            "  Значение p·V для аномальных измерений значительно отклоняется "
            "от остального набора данных. При постоянной температуре закон "
            "Бойля–Мариотта предсказывает постоянство произведения p·V. "
            "Аномальные точки указывают на ошибку измерения или внешний "
            "возмущающий фактор."
        )
    else:
        lines.append("  Аномалии не обнаружены.")
    lines.append("")

    lines.append("-" * 60)
    lines.append("Вывод:")
    lines.append("-" * 60)
    # Исключая аномалии, пересчитаем статистику
    clean_pv = [pv_values[i] for i in range(len(pv_values)) if i not in all_anomalies]
    if clean_pv:
        clean_mean = statistics.mean(clean_pv)
        clean_stdev = statistics.stdev(clean_pv) if len(clean_pv) > 1 else 0
        lines.append(
            f"  Без аномалий: среднее p·V = {clean_mean:.3f}, "
            f"ст. откл = {clean_stdev:.3f}"
        )
        lines.append(
            f"  Относительный разброс: {clean_stdev/clean_mean*100:.2f}%"
        )
        lines.append(
            "после исключения аномальных измерений."
        )
    lines.append("")
    lines.append("  Статистика 11 наблюдений (без измерения №7):")
    lines.append(f"    n = {len(clean_pv)}")
    lines.append(f"    Среднее p·V = {clean_mean:.3f} кПа·л")
    lines.append(f"    Медиана p·V = {statistics.median(clean_pv):.3f} кПа·л")
    lines.append(f"    Ст. откл    = {clean_stdev:.3f} кПа·л")
    lines.append(f"    Мин         = {min(clean_pv):.3f} кПа·л")
    lines.append(f"    Макс        = {max(clean_pv):.3f} кПа·л")
    lines.append("")
    lines.append("  Причина отклонения измерения №7 пока не установлена.")
    lines.append("  Требуется проверка по источнику данных.")
    lines.append("")
    lines.append("=" * 60)

    report = "\n".join(lines)

    # Сохраняем результат
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(report + "\n", encoding="utf-8")
    print(report)
    print(f"\nРезультаты сохранены в: {RESULTS_PATH}")


if __name__ == "__main__":
    main()