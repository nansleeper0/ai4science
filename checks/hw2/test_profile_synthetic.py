"""Тесты парного синтетического эксперимента (METHOD §9, ДЗ2).

Проверяют: известные E=0 и E=0.2 без шума, воспроизводимость seed,
независимость шума между наблюдениями и парность между сценариями,
полный 30-seed контроль и гейты.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

# Импорт из проектного src до импорта модулей проекта.
SRC_DIR = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(SRC_DIR))

from profile_shape import N_BINS, N_PERIODS, W1, W2, group_contrast_E, \
    metric_R, mean_profile
from profile_synthetic import (AMPLITUDES, CONTROL_OBS, CONTROL_W2_SCALE,
                               GATE_D, GATE_E_BASELINE, N_OBS, N_SEEDS,
                               SEEDS, SIGMA_FRAC, base_form, build_observation,
                               control_form, run_seed, t_interval)


def _phase():
    return (np.arange(N_BINS) + 0.5) / N_BINS


def _no_noise_rates(form, amplitudes):
    """rate = A*form без шума, форма (N_OBS, N_PERIODS, N_BINS)."""
    return np.stack([amplitudes[i] * np.broadcast_to(form, (N_PERIODS, N_BINS))
                     for i in range(N_OBS)])


def test_known_E_baseline_zero_no_noise():
    """Без шума baseline даёт E=0 (постоянная форма)."""
    phase = _phase()
    p0 = base_form(phase)
    rates = _no_noise_rates(p0, AMPLITUDES)
    r = [metric_R(mean_profile(rates[i]), phase) for i in range(N_OBS)]
    e = group_contrast_E(r[5:], r[:5])
    assert e == pytest.approx(0.0, abs=1e-12)


def test_known_E_control_02_no_noise():
    """Без шума контроль даёт E=0.2 (W2 у 6-10 умножен на 1.2)."""
    phase = _phase()
    p0 = base_form(phase)
    p0c = control_form(phase)
    rates = np.stack([
        np.broadcast_to((p0c if i in CONTROL_OBS else p0),
                        (N_PERIODS, N_BINS)) * AMPLITUDES[i]
        for i in range(N_OBS)
    ])
    r = [metric_R(mean_profile(rates[i]), phase) for i in range(N_OBS)]
    e = group_contrast_E(r[5:], r[:5])
    assert e == pytest.approx(0.2, abs=1e-9)


def test_seed_reproducible():
    """Один и тот же seed даёт одинаковые E_baseline/E_control/D."""
    phase = _phase()
    a = run_seed(7, phase)
    b = run_seed(7, phase)
    assert a["E_baseline"] == pytest.approx(b["E_baseline"], abs=1e-12)
    assert a["E_control"] == pytest.approx(b["E_control"], abs=1e-12)
    assert a["D"] == pytest.approx(b["D"], abs=1e-12)


def test_noise_independent_across_observations():
    """Шум независим между наблюдениями: cov(noise_i, noise_j) мала.

    Выборочная ковариация независимых массивов не обязана быть строго
    нулевой, поэтому проверяем лишь порядок величины (мала относительно
    дисперсии), а не abs(cov) < 1e-10.
    """
    rng = np.random.default_rng(3)
    noise = rng.standard_normal((N_OBS, N_PERIODS, N_BINS))
    for i in range(N_OBS):
        for j in range(i + 1, N_OBS):
            c = np.cov(noise[i].ravel(), noise[j].ravel())[0, 1]
            assert abs(c) < 0.05


def test_noise_paired_between_scenarios(monkeypatch):
    """run_seed: отдельный шум каждого наблюдения, общий массив между
    baseline и контролем.

    Перехватываем build_observation и проверяем, что для каждого
    наблюдения baseline и контроль получают один и тот же массив шума,
    а разные наблюдения — разные массивы.
    """
    phase = _phase()
    calls = []

    def fake_build(form, amplitude, noise):
        calls.append((form.copy(), amplitude, noise.copy()))
        # валидный профиль (не нулевой), чтобы mean_profile не падал.
        return np.broadcast_to(form, (N_PERIODS, N_BINS))

    monkeypatch.setattr("profile_synthetic.build_observation", fake_build)
    run_seed(11, phase)

    # 10 наблюдений × 2 сценария = 20 вызовов.
    assert len(calls) == 2 * N_OBS
    for i in range(N_OBS):
        b = calls[2 * i][2]
        c = calls[2 * i + 1][2]
        # baseline и контроль одного наблюдения — общий массив шума.
        assert np.array_equal(b, c)
        # разные наблюдения — разные массивы шума.
        for j in range(i + 1, N_OBS):
            assert not np.array_equal(b, calls[2 * j][2])


def test_full_30_seed_control_and_gates():
    """Полный 30-seed контроль: гейты E_baseline и D проходят."""
    phase = _phase()
    e_b = np.array([run_seed(s, phase)["E_baseline"] for s in SEEDS])
    d = np.array([run_seed(s, phase)["D"] for s in SEEDS])
    int_b = t_interval(e_b)
    int_d = t_interval(d)
    assert int_b["lower"] >= GATE_E_BASELINE[0]
    assert int_b["upper"] <= GATE_E_BASELINE[1]
    assert int_d["lower"] >= GATE_D[0]
    assert int_d["upper"] <= GATE_D[1]


def test_cli_runs_and_writes_outputs(tmp_path):
    """CLI завершается кодом 0 и пишет CSV (30 строк) и JSON."""
    out = tmp_path / "out"
    proc = subprocess.run(
        [sys.executable, str(SRC_DIR / "profile_synthetic.py"),
         "--output-dir", str(out)],
        capture_output=True, text=True, cwd=SRC_DIR)
    assert proc.returncode == 0, proc.stderr
    csv_path = out / "synthetic_runs.csv"
    json_path = out / "synthetic_summary.json"
    assert csv_path.is_file()
    assert json_path.is_file()
    rows = csv_path.read_text().strip().splitlines()
    assert len(rows) == N_SEEDS + 1  # заголовок + 30 строк
    assert rows[0].split(",") == ["seed", "E_baseline", "E_control", "D"]
    summary = json.loads(json_path.read_text())
    assert summary["gates"]["passed"] is True
    assert summary["parameters"]["n_seeds"] == N_SEEDS