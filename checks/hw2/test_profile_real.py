"""Тесты расчёта реальных профилей и bootstrap (METHOD §6-8, ДЗ2).

Проверяют: построение круговых блоков, воспроизводимость seed, границы трёх
вердиктов по интервалу E и обработку невалидных повторов на независимых
примерах (не трогая реальные данные и ядро).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

SRC_DIR = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(SRC_DIR))

from profile_shape import N_BINS, N_PERIODS, ProfileShapeError
from profile_real import (BLOCK, DELTA, N_BOOT, N_STARTS, SEED,
                          _circular_block_indices, run_bootstrap, verdict)


def _phase():
    return (np.arange(N_BINS) + 0.5) / N_BINS


def _obs_list(rate: np.ndarray) -> list[dict[str, np.ndarray]]:
    """Десять наблюдений с одинаковым rate (34,100)."""
    return [{"rate": rate, "phase": _phase()} for _ in range(10)]


def _constant_rate(value: float) -> np.ndarray:
    """Постоянный rate (34,100) — все R=1, E=0."""
    return np.full((N_PERIODS, N_BINS), value, dtype=float)


# --- Построение круговых блоков -------------------------------------------

def test_block_indices_length_and_modulo():
    """12 начал блоков длины 3, индексы modulo 34, обрезка до 34 строк."""
    rng = np.random.default_rng(123)
    idx = _circular_block_indices(rng, N_PERIODS, BLOCK, N_STARTS)
    assert idx.shape == (N_PERIODS,)
    assert idx.dtype == np.int64 or idx.dtype == np.int32
    assert np.all(idx >= 0) and np.all(idx < N_PERIODS)
    # 12 блоков по 3 = 36 индексов, обрезано до 34.
    assert len(idx) == 34


def test_block_indices_reproducible():
    """Один seed даёт одинаковые индексы блоков."""
    a = _circular_block_indices(np.random.default_rng(7), N_PERIODS, BLOCK, N_STARTS)
    b = _circular_block_indices(np.random.default_rng(7), N_PERIODS, BLOCK, N_STARTS)
    np.testing.assert_array_equal(a, b)


def test_block_indices_differ_across_seeds():
    """Разные seed дают (почти наверняка) разные индексы."""
    a = _circular_block_indices(np.random.default_rng(1), N_PERIODS, BLOCK, N_STARTS)
    b = _circular_block_indices(np.random.default_rng(2), N_PERIODS, BLOCK, N_STARTS)
    assert not np.array_equal(a, b)


# --- Воспроизводимость bootstrap ------------------------------------------

def test_bootstrap_reproducible_seed():
    """Один seed даёт одинаковые E по повторам."""
    obs = _obs_list(_constant_rate(100.0))
    r1 = run_bootstrap(obs, n_boot=50, seed=SEED)
    r2 = run_bootstrap(obs, n_boot=50, seed=SEED)
    np.testing.assert_array_equal(r1["e_values"], r2["e_values"])
    assert r1["valid"] and r2["valid"]


def test_bootstrap_constant_rate_gives_E_zero():
    """Постоянный rate: все R=1, E=0, интервал [0,0]."""
    obs = _obs_list(_constant_rate(100.0))
    res = run_bootstrap(obs, n_boot=50, seed=SEED)
    assert res["valid"]
    assert res["interval"] == pytest.approx([0.0, 0.0], abs=1e-12)
    assert res["status"] == "ok"


# --- Границы трёх вердиктов (§8) ------------------------------------------

def test_verdict_interval_above_delta():
    """L > +δ → практически существенное различие."""
    assert verdict([DELTA + 0.01, DELTA + 0.5]) == \
        "практически существенное различие формы"


def test_verdict_interval_below_minus_delta():
    """U < −δ → практически существенное различие."""
    assert verdict([-0.5, -DELTA - 0.01]) == \
        "практически существенное различие формы"


def test_verdict_interval_inside():
    """L ≥ −δ и U ≤ +δ → практически мало."""
    assert verdict([-0.02, 0.02]) == "различие этой метрики практически мало"


def test_verdict_interval_crosses_boundary():
    """Интервал пересекает ±δ → неопределённый."""
    assert verdict([-0.02, 0.06]) == "неопределённый"
    assert verdict([-0.06, 0.02]) == "неопределённый"


def test_verdict_none_interval():
    """Нет интервала (невалидные повторы) → неопределённый."""
    assert verdict(None) == "неопределённый"


# --- Обработка невалидных повторов ----------------------------------------

def test_bootstrap_invalid_rep_not_removed():
    """Невалидный повтор: интервал не вычисляется, повторы не удаляются."""
    # Блок из 3 очень отрицательных периодов: когда он попадает в выборку,
    # средний профиль становится отрицательным → normalize отказывает.
    rate = _constant_rate(100.0)
    rate[0:3, :] = -1e6  # целый блок периодов отрицательный
    obs = _obs_list(rate)
    res = run_bootstrap(obs, n_boot=50, seed=SEED)
    # Хотя бы один повтор невалиден (первый период попадёт в выборку).
    assert not res["valid"]
    assert res["interval"] is None
    assert res["status"] == "undefined"
    assert len(res["invalid_reps"]) >= 1
    # Невалидные повторы сохранены, не удалены и не заменены.
    assert all(isinstance(x, tuple) and len(x) == 3 for x in res["invalid_reps"])
    # e_values имеет полную длину n_boot (невалидные помечены NaN).
    assert res["e_values"].shape == (50,)
    # NaN по одному на невалидный повтор (не на наблюдение).
    n_invalid_reps = len({r for r, _, _ in res["invalid_reps"]})
    assert np.isnan(res["e_values"]).sum() == n_invalid_reps


def test_bootstrap_invalid_rep_identifies_rep_number():
    """Номера невалидных повторов корректны и в диапазоне."""
    rate = _constant_rate(100.0)
    rate[0:3, :] = -1e6
    obs = _obs_list(rate)
    res = run_bootstrap(obs, n_boot=50, seed=SEED)
    reps = [r for r, _, _ in res["invalid_reps"]]
    assert all(0 <= r < 50 for r in reps)
    # Каждая запись — уникальная пара (повтор, bin_id).
    pairs = [(r, b) for r, b, _ in res["invalid_reps"]]
    assert len(set(pairs)) == len(pairs)


def test_bootstrap_all_valid_constant():
    """Полностью валидный случай: интервал вычисляется."""
    obs = _obs_list(_constant_rate(100.0))
    res = run_bootstrap(obs, n_boot=50, seed=SEED)
    assert res["valid"]
    assert res["interval"] is not None
    assert res["status"] == "ok"
    assert res["invalid_reps"] == []


# --- Независимые выборки индексов на наблюдение (§7) ----------------------

def test_bootstrap_uses_independent_idx_per_observation(monkeypatch):
    """На один повтор нужны 10 отдельных выборок индексов, а не одна общая."""
    calls = {"n": 0}

    def fake_indices(rng, n_periods, block, n_starts):
        calls["n"] += 1
        # Возвращаем разные индексы на каждый вызов (по счётчику).
        return np.full(n_periods, calls["n"] - 1, dtype=int)

    monkeypatch.setattr("profile_real._circular_block_indices", fake_indices)
    obs = _obs_list(_constant_rate(100.0))
    run_bootstrap(obs, n_boot=1, seed=SEED)
    # 10 наблюдений × 1 повтор = 10 независимых выборок.
    assert calls["n"] == 10


def test_bootstrap_resamples_rows_with_given_starts(monkeypatch):
    """Заранее заданные старты дают реальные пересэмплированные строки."""
    # Десять наблюдений с разными профилями (разные периоды).
    obs = []
    for k in range(10):
        rate = np.zeros((N_PERIODS, N_BINS), dtype=float)
        # Период k имеет отличный от остальных профиль.
        rate[k, :] = 1.0
        rate[(k + 1) % N_PERIODS, :] = 2.0
        obs.append({"rate": rate, "phase": _phase()})

    # Заранее заданные индексы на каждое наблюдение: выбираем период k.
    idx_list = [np.full(N_PERIODS, k, dtype=int) for k in range(10)]

    def fake_indices(rng, n_periods, block, n_starts):
        return idx_list.pop(0)

    monkeypatch.setattr("profile_real._circular_block_indices", fake_indices)
    res = run_bootstrap(obs, n_boot=1, seed=SEED)
    assert res["valid"]
    # Каждое наблюдение пересэмплировано своим периодом k: R_k = 2/1 = 2.
    # E = mean(R бинов 6-10)/mean(R бинов 1-5) - 1 = 2/2 - 1 = 0.
    assert res["e_values"][0] == pytest.approx(0.0, abs=1e-12)


def test_bootstrap_two_invalid_obs_same_rep(monkeypatch):
    """Два невалидных наблюдения в одном повторе: сохраняются оба bin_id."""
    # Наблюдения 3 и 7 имеют отрицательный блок периодов → normalize откажет.
    obs = []
    for k in range(10):
        rate = _constant_rate(100.0)
        if k in (2, 6):  # bin_id 3 и 7
            rate[0:3, :] = -1e6
        obs.append({"rate": rate, "phase": _phase()})

    def fake_indices(rng, n_periods, block, n_starts):
        return np.arange(n_periods, dtype=int)  # выбираем все периоды

    monkeypatch.setattr("profile_real._circular_block_indices", fake_indices)
    res = run_bootstrap(obs, n_boot=1, seed=SEED)
    assert not res["valid"]
    assert res["interval"] is None
    assert res["status"] == "undefined"
    # Оба невалидных наблюдения сохранены в одном повторе.
    assert len(res["invalid_reps"]) == 2
    bin_ids = sorted(b for _, b, _ in res["invalid_reps"])
    assert bin_ids == [3, 7]
    # E повтора = NaN.
    assert np.isnan(res["e_values"][0])