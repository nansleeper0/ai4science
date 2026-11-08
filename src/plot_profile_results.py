#!/usr/bin/env python3
"""Построение воспроизводимых рисунков по готовым результатам ДЗ2.

Читает:
  results/hw2/real_corrected/profiles.npz
  results/hw2/real_corrected/real_metrics.csv
  results/hw2/real_corrected/real_summary.json

Рисунки (в results/hw2/figures/):
  1. profiles.png / profiles.pdf — десять средних нормированных профилей,
     цвет = средний темп счёта; окна W1 и W2 выделены.
  2. shape_vs_brightness.png / shape_vs_brightness.pdf — R от среднего
     темпа счёта, группы бинов 1–5 и 6–10, их средние R, E и 95% интервал.

Профили и bootstrap НЕ пересчитываются — только визуализация готовых данных.
"""

import csv
import json
import os

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "results", "hw2", "real_corrected")
FIG = os.path.join(ROOT, "results", "hw2", "figures")

N_PERIODS = 34


def main():
    os.makedirs(FIG, exist_ok=True)

    # --- входы ---------------------------------------------------------
    d = np.load(os.path.join(DATA, "profiles.npz"), allow_pickle=False)
    phase = d["phase"]
    brightness = d["brightness"]
    profiles = d["profiles"]  # (10, 100), уже нормированы на среднее

    with open(os.path.join(DATA, "real_metrics.csv"), newline="") as f:
        metrics = list(csv.DictReader(f))
    summary = json.load(open(os.path.join(DATA, "real_summary.json")))

    w1 = summary["parameters"]["windows"]["W1"]
    w2 = summary["parameters"]["windows"]["W2"]
    low_bins = summary["parameters"]["low_bins"]
    high_bins = summary["parameters"]["high_bins"]
    e_obs = summary["E_observed"]
    e_lo, e_hi = summary["bootstrap"]["interval"]

    # --- рисунок 1: профили -------------------------------------------
    cmap = plt.get_cmap("viridis")
    norm = plt.Normalize(vmin=brightness.min(), vmax=brightness.max())

    fig, ax = plt.subplots(figsize=(9, 5.5))
    for i in range(profiles.shape[0]):
        ax.plot(phase, profiles[i], color=cmap(norm(brightness[i])),
                linewidth=1.4, alpha=0.9)

    # окна W1 и W2
    for w, label in ((w1, "W1"), (w2, "W2")):
        ax.axvspan(w[0], w[1], color="gray", alpha=0.15, zorder=0)
        ax.text((w[0] + w[1]) / 2, ax.get_ylim()[1] * 0.98, label,
                ha="center", va="top", fontsize=11, color="dimgray")

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax)
    cbar.set_label("средний темп счёта, отсчёты/с")

    ax.set_xlabel("фаза вращения")
    ax.set_ylabel("интенсивность, делённая на среднюю")
    ax.set_title(f"Средние нормированные профили EXO2030+375 "
                 f"(каждый усреднён по {N_PERIODS} периодам)")
    ax.set_xlim(0, 1)
    ax.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "profiles.png"), dpi=150)
    fig.savefig(os.path.join(FIG, "profiles.pdf"))
    plt.close(fig)

    # --- рисунок 2: R от яркости --------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5.5))

    low = [r for r in metrics if int(r["bin_id"]) in low_bins]
    high = [r for r in metrics if int(r["bin_id"]) in high_bins]

    low_x = [float(r["brightness_count_per_s"]) for r in low]
    low_y = [float(r["R"]) for r in low]
    high_x = [float(r["brightness_count_per_s"]) for r in high]
    high_y = [float(r["R"]) for r in high]

    ax.scatter(low_x, low_y, color="tab:blue", s=60, label="бины 1–5", zorder=3)
    ax.scatter(high_x, high_y, color="tab:red", s=60, label="бины 6–10", zorder=3)

    # средние R по группам — подписанные пунктирные линии
    mean_low = float(np.mean(low_y))
    mean_high = float(np.mean(high_y))
    ax.axhline(mean_low, color="tab:blue", linestyle="--", alpha=0.6,
               linewidth=1.0, label=f"среднее R бинов 1–5 = {mean_low:.3f}")
    ax.axhline(mean_high, color="tab:red", linestyle="--", alpha=0.6,
               linewidth=1.0, label=f"среднее R бинов 6–10 = {mean_high:.3f}")

    # E и 95% интервал — текстовая аннотация (различие групповых средних R)
    e_pct = e_obs * 100
    lo_pct = e_lo * 100
    hi_pct = e_hi * 100
    ax.text(0.98, 0.04,
            f"Различие групповых средних R: {e_pct:.1f}%;\n"
            f"95% интервал: {lo_pct:.1f}–{hi_pct:.1f}%",
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=10, bbox=dict(boxstyle="round,pad=0.3",
                                   facecolor="white", alpha=0.85))

    ax.set_xlabel("средний темп счёта, отсчёты/с")
    ax.set_ylabel("R = интеграл W2 / интеграл W1")
    ax.set_title("Форма профиля против среднего темпа счёта (EXO2030+375)")
    ax.legend(loc="upper left")
    ax.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "shape_vs_brightness.png"), dpi=150)
    fig.savefig(os.path.join(FIG, "shape_vs_brightness.pdf"))
    plt.close(fig)

    print("Рисунки сохранены в", FIG)
    print("  profiles.png / profiles.pdf")
    print("  shape_vs_brightness.png / shape_vs_brightness.pdf")
    print(f"E = {e_obs:.4f}, 95% интервал [{e_lo:.4f}, {e_hi:.4f}]")
    print(f"Средние R: бины 1–5 = {mean_low:.4f}, бины 6–10 = {mean_high:.4f}")


if __name__ == "__main__":
    main()