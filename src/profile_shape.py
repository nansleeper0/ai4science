"""Измеритель формы профиля EXO2030+375 по методике METHOD.md (ДЗ2).

Чистые функции: загрузка подготовленного набора, средний профиль,
нормировка, метрика R и групповой контраст E. Все расчёты — по §5 и §6
методики. Явные отказы вместо маскировки неопределённости.
"""
from __future__ import annotations

import csv
import hashlib
import math
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
        meta = {k: lc[k] for k in ("bin_id", "source_filename", "obs_id")
                if k in lc.files}
    _check_contract(rate, error, time, phase)
    return {"rate": rate, "error": error, "time": time, "phase": phase, **meta}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_dataset(folder: Path) -> list[dict[str, np.ndarray]]:
    """Загружает десять NPZ по manifest.csv, в порядке bin_id.

    Проверяет: ровно 10 уникальных bin_id 1..10, соответствие списка NPZ
    таблице, SHA256 каждого NPZ по output_sha256 (до загрузки), согласованность
    bin_id/source_filename/obs_id внутри NPZ и средний RATE по
    mean_rate_trimmed_count_per_s. Возвращает наблюдения в порядке bin_id.
    """
    folder = Path(folder)
    manifest = folder / "manifest.csv"
    if not manifest.is_file():
        raise ProfileShapeError(f"нет manifest.csv в {folder}")
    with open(manifest) as f:
        rows = list(csv.DictReader(f))
    bin_ids = [int(r["bin_id"]) for r in rows]
    if sorted(bin_ids) != list(range(1, 11)):
        raise ProfileShapeError(
            f"bin_id должны быть ровно 1..10, получено {sorted(bin_ids)}")
    if len(set(bin_ids)) != 10:
        raise ProfileShapeError("дубликаты bin_id в manifest")

    by_id: dict[int, dict] = {int(r["bin_id"]): r for r in rows}
    expected_files = {r["output_file"] for r in rows}
    actual_files = {p.name for p in folder.glob("bin_*.npz")}
    if actual_files != expected_files:
        raise ProfileShapeError(
            f"набор NPZ не совпадает с manifest: лишние "
            f"{sorted(actual_files - expected_files)}, отсутствуют "
            f"{sorted(expected_files - actual_files)}")
    obs_by_id: dict[int, dict[str, np.ndarray]] = {}
    for bid in range(1, 11):
        row = by_id[bid]
        path = folder / row["output_file"]
        if not path.is_file():
            raise ProfileShapeError(f"нет файла {row['output_file']}")
        actual = _sha256(path)
        if actual != row["output_sha256"]:
            raise ProfileShapeError(
                f"{row['output_file']}: SHA256 {actual[:12]}… != "
                f"{row['output_sha256'][:12]}…")
        obs = load_npz(path)
        # согласованность имени файла с manifest (bin_id, source_filename, obs_id)
        if path.name != row["output_file"]:
            raise ProfileShapeError(
                f"{path.name} != output_file {row['output_file']}")
        if not path.name.startswith(f"bin_{bid:02d}_"):
            raise ProfileShapeError(
                f"{path.name} не соответствует bin_id {bid}")
        if row["obs_id"] not in path.name:
            raise ProfileShapeError(
                f"{path.name} не содержит obs_id {row['obs_id']}")
        # сверка метаданных внутри NPZ с manifest
        for key, expected in (("bin_id", str(bid)),
                              ("source_filename", row["source_filename"]),
                              ("obs_id", row["obs_id"])):
            if key not in obs:
                raise ProfileShapeError(
                    f"{row['output_file']}: нет метаданного '{key}' в NPZ")
            if str(obs[key]) != expected:
                raise ProfileShapeError(
                    f"{row['output_file']}: метаданное '{key}'={obs[key]!r} "
                    f"не совпадает с manifest ({expected!r})")
        expected_mean = float(row["mean_rate_trimmed_count_per_s"])
        actual_mean = float(np.mean(obs["rate"]))
        if not math.isclose(actual_mean, expected_mean, rel_tol=1e-9):
            raise ProfileShapeError(
                f"{row['output_file']}: средний RATE {actual_mean} != "
                f"{expected_mean}")
        obs_by_id[bid] = obs
    return [obs_by_id[i] for i in range(1, 11)]


def mean_profile(rate: np.ndarray) -> np.ndarray:
    """Средний профиль по периодам: mean(rate, axis=0), вектор из 100."""
    if rate.ndim != 2 or rate.shape != (N_PERIODS, N_BINS):
        raise ProfileShapeError(
            f"rate.shape={rate.shape}, ожидается ({N_PERIODS},{N_BINS})")
    if not np.all(np.isfinite(rate)):
        raise ProfileShapeError("rate содержит неконечные значения")
    return np.mean(rate, axis=0)


def normalize(profile: np.ndarray) -> tuple[np.ndarray, float]:
    """Нормированный профиль p = profile / B, где B = mean(profile).

    Возвращает (p, B). Бросает ProfileShapeError, если B неположителен
    (не добавляется epsilon — см. METHOD §3 fail-fast).
    """
    if profile.ndim != 1 or profile.shape != (N_BINS,):
        raise ProfileShapeError(
            f"profile.shape={profile.shape}, ожидается ({N_BINS},)")
    if not np.all(np.isfinite(profile)):
        raise ProfileShapeError("profile содержит неконечные значения")
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
    if phase.ndim != 1 or phase.shape != (N_BINS,):
        raise ProfileShapeError(
            f"phase.shape={phase.shape}, ожидается ({N_BINS},)")
    if not np.all(np.isfinite(phase)):
        raise ProfileShapeError("phase содержит неконечные значения")
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
    if rh.ndim != 1 or rl.ndim != 1:
        raise ProfileShapeError("группы для контраста E должны быть одномерными")
    if rh.size == 0 or rl.size == 0:
        raise ProfileShapeError("пустая группа для контраста E")
    if not np.all(np.isfinite(rh)) or not np.all(np.isfinite(rl)):
        raise ProfileShapeError("R содержит неконечные значения")
    if not np.all(rh > 0):
        raise ProfileShapeError("R верхней группы должен быть строго положителен")
    if not np.all(rl > 0):
        raise ProfileShapeError("R нижней группы должен быть строго положителен")
    return float(np.mean(rh)) / float(np.mean(rl)) - 1.0