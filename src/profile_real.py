"""Расчёт реальных профилей EXO2030+375 и их неопределённости (METHOD §6-8, ДЗ2).

Загружает десять наблюдений через load_dataset, строит средние нормированные
профили, метрику R каждого наблюдения, групповой контраст E по фиксированным
группам (бины 1-5 и 6-10) и круговой блочный bootstrap (2000 повторов,
seed 20261106, блок 3 периода). Яркость — mean_rate_trimmed_count_per_s из
manifest.csv (не физическая светимость).

Невалидные повторы не удаляются и не заменяются; при любом невалидном повторе
интервал не вычисляется и возвращается явный статус.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

import numpy as np

from profile_shape import (N_BINS, N_PERIODS, W1, W2, ProfileShapeError,
                           group_contrast_E, load_dataset, mean_profile,
                           metric_R, normalize)

# Параметры bootstrap (METHOD §7).
N_BOOT = 2000
SEED = 20261106
BLOCK = 3
N_STARTS = 12
ALPHA = 0.05
# Аналитический порог практической значимости (METHOD §6).
DELTA = 0.05

# Фиксированные группы наблюдений (бины 1-5 и 6-10, METHOD §6).
LOW_BINS = (1, 2, 3, 4, 5)
HIGH_BINS = (6, 7, 8, 9, 10)


def brightness_from_manifest(folder: Path) -> list[float]:
    """Яркость наблюдений по mean_rate_trimmed_count_per_s в порядке bin_id 1..10."""
    folder = Path(folder)
    manifest = folder / "manifest.csv"
    if not manifest.is_file():
        raise ProfileShapeError(f"нет manifest.csv в {folder}")
    with open(manifest) as f:
        rows = list(csv.DictReader(f))
    bin_ids = [int(r["bin_id"]) for r in rows]
    if sorted(bin_ids) != list(range(1, 11)):
        raise ProfileShapeError("bin_id в manifest должны быть ровно 1..10")
    by_id = {int(r["bin_id"]): r for r in rows}
    return [float(by_id[i]["mean_rate_trimmed_count_per_s"]) for i in range(1, 11)]


def real_profiles(obs_list: list[dict[str, np.ndarray]]) -> list[np.ndarray]:
    """Средние нормированные профили p = mean(rate,axis=0)/mean(profile) (§5)."""
    profiles = []
    for obs in obs_list:
        prof = mean_profile(obs["rate"])
        p, _ = normalize(prof)
        profiles.append(p)
    return profiles


def real_R(obs_list: list[dict[str, np.ndarray]]) -> list[float]:
    """R каждого наблюдения по среднему профилю (§5)."""
    phase = obs_list[0]["phase"]
    return [metric_R(mean_profile(obs["rate"]), phase) for obs in obs_list]


def real_E(r_values: list[float]) -> float:
    """E = mean(R бинов 6-10)/mean(R бинов 1-5) - 1 (§6)."""
    r_high = [r_values[i - 1] for i in HIGH_BINS]
    r_low = [r_values[i - 1] for i in LOW_BINS]
    return group_contrast_E(r_high, r_low)


def _circular_block_indices(rng: np.random.Generator, n_periods: int,
                            block: int, n_starts: int) -> np.ndarray:
    """12 начал круговых блоков длины block, индексы modulo n_periods,
    последовательность обрезается до n_periods строк."""
    starts = rng.integers(0, n_periods, size=n_starts)
    idx = []
    for s in starts:
        idx.extend((s + np.arange(block)) % n_periods)
    return np.asarray(idx[:n_periods], dtype=int)


def _E_from_resample(obs_list: list[dict[str, np.ndarray]],
                     phase: np.ndarray,
                     idx_list: list[np.ndarray]) -> float:
    """E по пересэмплированным целым периодам (без шума из ERROR).

    Каждое наблюдение пересэмплируется своим набором индексов idx_list[i]
    (независимые выборки блоков на наблюдение, METHOD §7).
    """
    r = []
    for obs, idx in zip(obs_list, idx_list):
        resampled = obs["rate"][idx]
        r.append(metric_R(mean_profile(resampled), phase))
    return real_E(r)


def run_bootstrap(obs_list: list[dict[str, np.ndarray]],
                  n_boot: int = N_BOOT, seed: int = SEED,
                  block: int = BLOCK, n_starts: int = N_STARTS) -> dict:
    """Круговой блочный bootstrap E по 2000 повторам (§7).

    Внутри каждого повтора для КАЖДОГО наблюдения независимо выбираются
    n_starts начал блоков длины block (modulo N_PERIODS), последовательность
    обрезается до N_PERIODS строк. Один RNG с seed создаётся до всех повторов
    и не переинициализируется внутри циклов.

    Возвращает dict с полями:
      e_values      — массив E по повторам (длина n_boot)
      valid         — bool: все повторы валидны
      invalid_reps  — список (rep_index, bin_id, reason) невалидных наблюдений
      interval      — [L, U] процентили 2.5/97.5 или None при невалидности
      status        — 'ok' или 'undefined'
    """
    phase = obs_list[0]["phase"]
    rng = np.random.default_rng(seed)
    e_values = np.empty(n_boot, dtype=float)
    invalid = []
    for rep in range(n_boot):
        # Независимые выборки индексов на каждое наблюдение.
        idx_list = [_circular_block_indices(rng, N_PERIODS, block, n_starts)
                    for _ in obs_list]
        rep_invalid = []
        r = []
        for i, (obs, idx) in enumerate(zip(obs_list, idx_list)):
            try:
                resampled = obs["rate"][idx]
                r.append(metric_R(mean_profile(resampled), phase))
            except ProfileShapeError as exc:
                # Невалидное наблюдение: сохраняем повтор, bin_id и причину.
                rep_invalid.append((rep, i + 1, str(exc)))
        if rep_invalid:
            # E повтора = NaN; сохраняем все отказы этого повтора.
            e_values[rep] = np.nan
            invalid.extend(rep_invalid)
        else:
            e_values[rep] = real_E(r)
    valid = len(invalid) == 0
    if valid:
        lo, hi = np.percentile(e_values, [100 * ALPHA / 2,
                                          100 * (1 - ALPHA / 2)])
        interval = [float(lo), float(hi)]
        status = "ok"
    else:
        interval = None
        status = "undefined"
    return {
        "e_values": e_values,
        "valid": valid,
        "invalid_reps": invalid,
        "interval": interval,
        "status": status,
    }


def verdict(interval: list[float] | None, delta: float = DELTA) -> str:
    """Три исхода по реальному 95% интервалу E (§8)."""
    if interval is None:
        return "неопределённый"
    L, U = interval
    if L > delta or U < -delta:
        return "практически существенное различие формы"
    if L >= -delta and U <= delta:
        return "различие этой метрики практически мало"
    return "неопределённый"


def compute_real(folder: Path) -> dict:
    """Полный расчёт реальных данных: профили, R, E, bootstrap, вердикт."""
    folder = Path(folder)
    obs_list = load_dataset(folder)
    brightness = brightness_from_manifest(folder)
    phase = obs_list[0]["phase"]
    profiles = real_profiles(obs_list)
    r_values = real_R(obs_list)
    e_obs = real_E(r_values)
    boot = run_bootstrap(obs_list)
    return {
        "brightness": brightness,
        "phase": phase,
        "profiles": profiles,
        "r_values": r_values,
        "E_observed": e_obs,
        "bootstrap": boot,
        "verdict": verdict(boot["interval"]),
    }


def save_real(result: dict, out_dir: Path) -> None:
    """Сохраняет profiles.npz, real_metrics.csv, real_bootstrap.csv,
    real_summary.json в out_dir."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    # profiles.npz
    np.savez(out_dir / "profiles.npz",
             phase=result["phase"],
             brightness=np.asarray(result["brightness"]),
             profiles=np.stack(result["profiles"]),
             r_values=np.asarray(result["r_values"]))
    # real_metrics.csv
    with open(out_dir / "real_metrics.csv", "w") as f:
        f.write("bin_id,brightness_count_per_s,R\n")
        for i, (b, r) in enumerate(zip(result["brightness"],
                                       result["r_values"]), start=1):
            f.write(f"{i},{b:.10g},{r:.10g}\n")
    # real_bootstrap.csv
    boot = result["bootstrap"]
    with open(out_dir / "real_bootstrap.csv", "w") as f:
        f.write("rep,E\n")
        for rep, e in enumerate(boot["e_values"]):
            f.write(f"{rep},{e:.10g}\n")
    # real_summary.json
    summary = {
        "parameters": {
            "n_obs": 10,
            "n_periods": N_PERIODS,
            "n_bins": N_BINS,
            "windows": {"W1": list(W1), "W2": list(W2)},
            "delta": DELTA,
            "low_bins": list(LOW_BINS),
            "high_bins": list(HIGH_BINS),
            "bootstrap": {
                "n_boot": N_BOOT,
                "seed": SEED,
                "block": BLOCK,
                "n_starts": N_STARTS,
                "alpha": ALPHA,
            },
        },
        "E_observed": result["E_observed"],
        "bootstrap": {
            "valid": boot["valid"],
            "n_invalid": len(boot["invalid_reps"]),
            "invalid_reps": boot["invalid_reps"],
            "interval": boot["interval"],
            "status": boot["status"],
        },
        "verdict": result["verdict"],
    }
    with open(out_dir / "real_summary.json", "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Реальные профили EXO2030+375")
    ap.add_argument("--data", default="data/profile_luminosity_10bins")
    ap.add_argument("--out", default="results/hw2/real")
    args = ap.parse_args()
    result = compute_real(Path(args.data))
    save_real(result, Path(args.out))
    boot = result["bootstrap"]
    print(f"E_observed = {result['E_observed']:.6g}")
    print(f"bootstrap valid = {boot['valid']}, "
          f"invalid = {len(boot['invalid_reps'])}")
    print(f"interval = {boot['interval']}")
    print(f"verdict = {result['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())