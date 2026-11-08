"""Парный синтетический эксперимент по METHOD §9 (ДЗ2).

Проверяет восстановление известного эффекта: baseline (постоянная форма,
E=0) против контроля (у наблюдений 6-10 W2 умножен на 1.2, E=0.2).
Использует проверенные mean_profile, metric_R и group_contrast_E из
profile_shape.py. Один и тот же массив стандартного шума (10,34,100)
используется в baseline и контроле; seed меняет только шум.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy import stats

from profile_shape import (N_BINS, W1, W2, group_contrast_E, mean_profile,
                           metric_R, normalize)

# Параметры эксперимента (METHOD §9).
N_OBS = 10
N_PERIODS = 34
N_SEEDS = 30
SEEDS = list(range(N_SEEDS))
AMPLITUDES = np.geomspace(60.0, 1800.0, N_OBS)  # по одному на наблюдение
SIGMA_FRAC = 0.2          # σ_i = 0.2 * A_i
CONTROL_W2_SCALE = 1.2    # у наблюдений 6-10 умножить W2 на 1.2
CONTROL_OBS = (5, 6, 7, 8, 9)  # индексы 0-based наблюдений 6-10

# Критерии контроля (METHOD §9).
GATE_E_BASELINE = (-0.05, 0.05)
GATE_D = (0.15, 0.25)


def _window_mask(phase: np.ndarray, lo: float, hi: float) -> np.ndarray:
    return (phase >= lo) & (phase < hi)


def base_form(phase: np.ndarray) -> np.ndarray:
    """p0_raw = 1 + indicator(W1) + indicator(W2), нормировка на среднее."""
    p0_raw = 1.0 + _window_mask(phase, *W1).astype(float) \
        + _window_mask(phase, *W2).astype(float)
    p0, _ = normalize(p0_raw)
    return p0


def control_form(phase: np.ndarray) -> np.ndarray:
    """Контроль: p0_raw = 1 + I(W1) + I(W2), затем ВСЕ значения внутри W2
    умножить на 1.2, затем нормировать весь профиль на его среднее.

    До нормировки: внутри W2 = 2.4, внутри W1 = 2. Общая нормировка
    сокращается в R, поэтому без шума R_baseline=1, R_control_high=1.2,
    E_control=0.2.
    """
    p0_raw = 1.0 + _window_mask(phase, *W1).astype(float) \
        + _window_mask(phase, *W2).astype(float)
    w2 = _window_mask(phase, *W2)
    p0_raw = np.where(w2, p0_raw * CONTROL_W2_SCALE, p0_raw)
    p0, _ = normalize(p0_raw)
    return p0


def build_observation(form: np.ndarray, amplitude: float,
                      noise: np.ndarray) -> np.ndarray:
    """Одно наблюдение: rate = A * form + σ*noise, форма (34,100).

    noise — стандартный гауссовский массив формы (34,100).
    """
    sigma = SIGMA_FRAC * amplitude
    return amplitude * form[None, :] + sigma * noise


def run_seed(seed: int, phase: np.ndarray) -> dict:
    """Один seed: baseline и контроль на общем массиве шума.

    Возвращает E_baseline, E_control, D = E_control - E_baseline.
    """
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal((N_OBS, N_PERIODS, N_BINS))

    p0 = base_form(phase)
    p0c = control_form(phase)

    r_baseline = []
    r_control = []
    for i in range(N_OBS):
        form_b = p0
        form_c = p0c if i in CONTROL_OBS else p0
        rate_b = build_observation(form_b, AMPLITUDES[i], noise[i])
        rate_c = build_observation(form_c, AMPLITUDES[i], noise[i])
        r_baseline.append(metric_R(mean_profile(rate_b), phase))
        r_control.append(metric_R(mean_profile(rate_c), phase))

    e_baseline = group_contrast_E(r_baseline[5:], r_baseline[:5])
    e_control = group_contrast_E(r_control[5:], r_control[:5])
    return {
        "seed": seed,
        "E_baseline": e_baseline,
        "E_control": e_control,
        "D": e_control - e_baseline,
    }


def t_interval(values: np.ndarray, alpha: float = 0.05) -> dict:
    """95% t-интервал среднего: mean ± t(0.975, n-1)*std(ddof=1)/sqrt(n)."""
    n = values.size
    mean = float(np.mean(values))
    std = float(np.std(values, ddof=1))
    tcrit = float(stats.t.ppf(1 - alpha / 2, df=n - 1))
    half = tcrit * std / np.sqrt(n)
    return {"mean": mean, "std": std, "t_crit": tcrit,
            "lower": mean - half, "upper": mean + half}


def main() -> int:
    ap = argparse.ArgumentParser(description="Парный синтетический эксперимент")
    ap.add_argument("--output-dir", default="results/hw2")
    args = ap.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 100 фазовых центров (как в данных).
    phase = (np.arange(N_BINS) + 0.5) / N_BINS

    rows = [run_seed(s, phase) for s in SEEDS]

    e_b = np.array([r["E_baseline"] for r in rows])
    e_c = np.array([r["E_control"] for r in rows])
    d = np.array([r["D"] for r in rows])

    int_b = t_interval(e_b)
    int_c = t_interval(e_c)
    int_d = t_interval(d)

    gate_b = bool(int_b["lower"] >= GATE_E_BASELINE[0] and
                  int_b["upper"] <= GATE_E_BASELINE[1])
    gate_d = bool(int_d["lower"] >= GATE_D[0] and
                  int_d["upper"] <= GATE_D[1])
    passed = bool(gate_b and gate_d)

    # CSV: 30 строк.
    csv_path = out_dir / "synthetic_runs.csv"
    with open(csv_path, "w") as f:
        f.write("seed,E_baseline,E_control,D\n")
        for r in rows:
            f.write(f"{r['seed']},{r['E_baseline']:.10g},"
                    f"{r['E_control']:.10g},{r['D']:.10g}\n")

    summary = {
        "parameters": {
            "n_bins": N_BINS,
            "n_periods": N_PERIODS,
            "n_obs": N_OBS,
            "n_seeds": N_SEEDS,
            "seeds": SEEDS,
            "amplitudes": AMPLITUDES.tolist(),
            "sigma_frac": SIGMA_FRAC,
            "control_w2_scale": CONTROL_W2_SCALE,
            "control_obs_1based": [i + 1 for i in CONTROL_OBS],
            "w1": list(W1),
            "w2": list(W2),
            "true_E_baseline": 0.0,
            "true_E_control": 0.2,
        },
        "statistics": {
            "E_baseline": int_b,
            "E_control": int_c,
            "D": int_d,
        },
        "gates": {
            "E_baseline_interval": [int_b["lower"], int_b["upper"]],
            "E_baseline_target": list(GATE_E_BASELINE),
            "E_baseline_passed": gate_b,
            "D_interval": [int_d["lower"], int_d["upper"]],
            "D_target": list(GATE_D),
            "D_passed": gate_d,
            "passed": passed,
        },
        "dependencies": {
            "numpy": np.__version__,
            "scipy": stats.__version__ if hasattr(stats, "__version__")
            else "unknown",
        },
    }

    with open(out_dir / "synthetic_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"E_baseline: mean={int_b['mean']:.4f} "
          f"95%CI=[{int_b['lower']:.4f},{int_b['upper']:.4f}]")
    print(f"E_control : mean={int_c['mean']:.4f} "
          f"95%CI=[{int_c['lower']:.4f},{int_c['upper']:.4f}]")
    print(f"D         : mean={int_d['mean']:.4f} "
          f"95%CI=[{int_d['lower']:.4f},{int_d['upper']:.4f}]")
    print(f"Gates passed: {passed} "
          f"(E_baseline={gate_b}, D={gate_d})")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())