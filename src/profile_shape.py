"""Измеритель формы профиля EXO2030+375 по методике METHOD.md (ДЗ2).

Чистые функции: загрузка подготовленного набора, средний профиль,
нормировка, метрика R и групповой контраст E. Все расчёты — по §5 и §6
методики. Явные отказы вместо маскировки неопределённости.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np

# Окна метрики (зафиксированы в METHOD §5).
W1 = (0.10, 0.35)
W2 = (0.40, 0.65)

# Договор о схеме данных (METHOD §3).
N_PERIODS = 34
N_BINS = 100
REQUIRED_KEYS = ("rate", "error", "time", "phase")


class ProfileShapeError(ValueError):
    """Явный отказ: входы или метрика не позволяют корректный расчёт."""


def _check_contract(rate: np.ndarray, error: np.ndarray, time: np.ndarray,
                    phase: np.ndarray) -> None:
    """Проверка договора о схеме данных. Бросает ProfileShapeError."""
    if rate.shape != (N_PERIODS, N_BINS):
        raise ProfileShapeError(
            f"rate.shape={rate.shape}, ожидается ({N_PERIODS},{N_BINS})")
    if error.shape != (N_PERIODS, N_BINS):
        raise ProfileShapeError(
            f"error.shape={error.shape}, ожидается ({N_PERIODS},{N_BINS})")
    if time.shape != (N_PERIODS, N_BINS):
        raise ProfileShapeError(
            f"time.shape={time.shape}, ожидается ({N_PERIODS},{N_BINS})")
    if phase.shape != (N_BINS,):
        raise ProfileShapeError(
            f"phase.shape={phase.shape}, ожидается ({N_BINS},)")
    if not np.all(np.isfinite(rate)):
        raise ProfileShapeError("rate содержит неконечные значения")
    if not np.all(np.isfinite(error)):
        raise ProfileShapeError("error содержит неконечные значения")
    if not np.all(np.isfinite(time)):
        raise ProfileShapeError("time содержит неконечные значения")
    if not np.all(np.isfinite(phase)):
        raise ProfileShapeError("phase содержит неконечные значения")
    if not np.all(error > 0):
        raise ProfileShapeError("error должен быть строго положителен всюду")
    if np.any(phase < 0) or np.any(phase >= 1):
        raise ProfileShapeError("phase вне диапазона [0,1)")
    if np.any(np.diff(phase) <= 0):
        raise ProfileShapeError("phase не монотонно возрастает")


def load_npz(path: Path) -> dict[str, np.ndarray]:
    """Читает один NPZ через allow_pickle=False и проверяет договор."""
    path = Path(path)
    with np.load(path, allow_pickle=False) as lc:
        missing = [k for k in REQUIRED_KEYS if k not in lc.files]
        if missing:
            raise ProfileShapeError(f"{path.name}: нет ключей {missing}")
        rate = lc["rate"]
        error = lc["error"]
        time = lc["time"]
        phase = lc["phase"]
    _check_contract(rate, error, time, phase)
    return {"rate": rate, "error": error, "time": time, "phase": phase}


def load_dataset(folder: Path) -> list[dict[str, np.ndarray]]:
    """Загружает десять NPZ из каталога, отсортированных по имени."""
    folder = Path(folder)
    paths = sorted(folder.glob("bin_*.npz"))
    if len(paths) != 10:
        raise ProfileShapeError(
            f"ожидается 10 NPZ, найдено {len(paths)}")
    return [load_npz(p) for p in paths]


def mean_profile(rate: np.ndarray) -> np.ndarray:
    """Средний профиль по периодам: mean(rate, axis=0), вектор из 100."""
    return np.mean(rate, axis=0)


def normalize(profile: np.ndarray) -> tuple[np.ndarray, float]:
    """Нормированный профиль p = profile / B, где B = mean(profile).

    Возвращает (p, B). Бросает ProfileShapeError, если B неположителен
    (не добавляется epsilon — см. METHOD §3 fail-fast).
    """
    B = float(np.mean(profile))
    if not np.isfinite(B) or B <= 0:
        raise ProfileShapeError(
            f"среднее профиля B={B} неположительно/неконечно — R не определён")
    return profile / B, B


def _window_mask(phase: np.ndarray, lo: float, hi: float) -> np.ndarray:
    return (phase >= lo) & (phase < hi)


def metric_R(profile: np.ndarray, phase: np.ndarray,
             w1: tuple[float, float] = W1,
             w2: tuple[float, float] = W2) -> float:
    """R = интеграл p по W2 / интеграл p по W1 (отношение интегралов).

    Интеграл по окну = sum(p[окно]) * Δφ. Бросает ProfileShapeError при
    неположительном интеграле W1 или W2.
    """
    p, _ = normalize(profile)
    dphi = 1.0 / N_BINS
    m1 = _window_mask(phase, *w1)
    m2 = _window_mask(phase, *w2)
    i1 = float(np.sum(p[m1]) * dphi)
    i2 = float(np.sum(p[m2]) * dphi)
    if not (np.isfinite(i1) and i1 > 0):
        raise ProfileShapeError(f"интеграл W1={i1} неположителен — R не определён")
    if not (np.isfinite(i2) and i2 > 0):
        raise ProfileShapeError(f"интеграл W2={i2} неположителен — R не определён")
    return i2 / i1


def group_contrast_E(r_high: Iterable[float], r_low: Iterable[float]) -> float:
    """E = mean(R бинов 6-10) / mean(R бинов 1-5) - 1 (равные веса, §6)."""
    rh = np.asarray(list(r_high), dtype=float)
    rl = np.asarray(list(r_low), dtype=float)
    if rh.size == 0 or rl.size == 0:
        raise ProfileShapeError("пустая группа для контраста E")
    if not np.all(np.isfinite(rh)) or not np.all(np.isfinite(rl)):
        raise ProfileShapeError("R содержит неконечные значения")
    mean_low = float(np.mean(rl))
    if mean_low <= 0:
        raise ProfileShapeError("среднее R нижней группы неположительно")
    return float(np.mean(rh)) / mean_low - 1.0