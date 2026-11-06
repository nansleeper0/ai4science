"""Детерминированные проверки измерителя формы (ДЗ2, METHOD §3, §5, §6).

Проверяют формулы на известных искусственных примерах и отрицательные
случаи. На реальном наборе — только договор и контрольные суммы.
"""
import csv
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from profile_shape import (  # noqa: E402
    N_BINS, N_PERIODS, W1, W2, ProfileShapeError,
    group_contrast_E, load_dataset, load_npz, mean_profile,
    metric_R, normalize,
)

DATA = Path(__file__).resolve().parents[2] / "data" / "profile_luminosity_10bins"


def _phase():
    return (np.arange(N_BINS) + 0.5) / N_BINS


def _window_mask(phase, lo, hi):
    return (phase >= lo) & (phase < hi)


def _make_obs(profile, n_periods=N_PERIODS, bin_id="1",
              source_filename="bin_01_obs1_n1.lc", obs_id="obs1"):
    """Собирает валидный NPZ-совместимый словарь из профиля (100,)."""
    rate = np.tile(profile, (n_periods, 1))
    error = np.ones_like(rate)
    time = np.arange(rate.size).reshape(rate.shape).astype(float)
    return {"rate": rate, "error": error, "time": time, "phase": _phase(),
            "bin_id": bin_id, "source_filename": source_filename,
            "obs_id": obs_id}


def _write_npz(path, obs):
    np.savez(path, **obs)


def _make_manifest_dir(tmp_path, rows, files):
    """Создаёт временный каталог с manifest.csv и NPZ-файлами."""
    folder = tmp_path / "data"
    folder.mkdir(parents=True)
    with open(folder / "manifest.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    for name, obs in files.items():
        _write_npz(folder / name, obs)
    return folder


def _manifest_row(bid, name, obs, mean=None):
    if mean is None:
        mean = float(np.mean(obs["rate"]))
    return {
        "bin_id": str(bid),
        "bin_low_count_per_s": "0",
        "bin_high_count_per_s": "1",
        "bin_candidates": "1",
        "output_file": name,
        "source_filename": str(obs["source_filename"]),
        "obs_id": str(obs["obs_id"]),
        "source_index": "0",
        "source_n_periods": str(N_PERIODS),
        "retained_n_periods": str(N_PERIODS),
        "n_phase_bins": str(N_BINS),
        "mean_rate_full_count_per_s": str(mean),
        "mean_rate_trimmed_count_per_s": str(mean),
        "pulse_period_s": "1",
        "retained_time_gaps": "0",
        "source_fits_sha256": "0" * 64,
        "output_sha256": "0" * 64,
    }


def _make_10obs():
    """Десять наблюдений с разными профилями и корректными SHA."""
    rng = np.random.default_rng(7)
    obs = {}
    for bid in range(1, 11):
        prof = rng.uniform(1, 4, size=N_BINS)
        name = f"bin_{bid:02d}_obs{bid}_n1.npz"
        o = _make_obs(prof, bin_id=str(bid),
                      source_filename=name.replace(".npz", ".lc"),
                      obs_id=f"obs{bid}")
        obs[name] = o
    return obs


def _finalize_manifest(folder, rows, files):
    """Записывает реальные SHA256 в manifest."""
    import hashlib
    for r in rows:
        p = folder / r["output_file"]
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        r["output_sha256"] = h
    with open(folder / "manifest.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


# ---------------------------------------------------------------- договор
def test_dataset_contract():
    """Десять NPZ, ключи, формы, конечность, error>0, phase монотонна."""
    obs = load_dataset(DATA)
    assert len(obs) == 10
    for o in obs:
        assert o["rate"].shape == (N_PERIODS, N_BINS)
        assert o["error"].shape == (N_PERIODS, N_BINS)
        assert o["time"].shape == (N_PERIODS, N_BINS)
        assert o["phase"].shape == (N_BINS,)
        assert np.all(np.isfinite(o["rate"]))
        assert np.all(np.isfinite(o["error"]))
        assert np.all(o["error"] > 0)
        assert np.all((o["phase"] >= 0) & (o["phase"] < 1))
        assert np.all(np.diff(o["phase"]) > 0)


def test_rate_allows_negative():
    """Отрицательные RATE допустимы и не обрезаются (договор §3)."""
    obs = load_dataset(DATA)
    neg = sum(int(np.sum(o["rate"] < 0)) for o in obs)
    assert neg >= 2  # в наборе есть два отрицательных значения


def test_mean_rate_consistency():
    """mean_rate_trimmed согласуется со средним по сохранённому участку."""
    with open(DATA / "manifest.csv") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 10
    for row, o in zip(rows, load_dataset(DATA)):
        expected = float(row["mean_rate_trimmed_count_per_s"])
        actual = float(np.mean(o["rate"]))
        assert actual == pytest.approx(expected, rel=1e-9)


# ------------------------------------------------- manifest / контрольные суммы
def test_manifest_sha_rejects_tampered(tmp_path):
    """Изменённый NPZ со старым SHA отклоняется, даже если средний RATE сохранён."""
    files = _make_10obs()
    rows = [_manifest_row(b, n, o) for b, (n, o) in enumerate(files.items(), 1)]
    folder = _make_manifest_dir(tmp_path, rows, files)
    _finalize_manifest(folder, rows, files)
    # корректный набор загружается
    assert len(load_dataset(folder)) == 10
    # подменяем содержимое одного NPZ, сохраняя средний RATE
    name = rows[0]["output_file"]
    o = files[name]
    prof = o["rate"][0].copy()
    prof[0] += 1.0  # меняем данные
    prof[1] -= 1.0  # компенсируем, чтобы средний RATE сохранился
    new_obs = _make_obs(prof, bin_id=o["bin_id"],
                        source_filename=o["source_filename"],
                        obs_id=o["obs_id"])
    assert float(np.mean(new_obs["rate"])) == pytest.approx(
        float(np.mean(o["rate"])), rel=1e-12)
    _write_npz(folder / name, new_obs)
    with pytest.raises(ProfileShapeError, match="SHA256"):
        load_dataset(folder)


def test_manifest_meta_mismatch_rejects(tmp_path):
    """Внутренний bin_id изменён, SHA пересчитан, но метаданные расходятся."""
    files = _make_10obs()
    rows = [_manifest_row(b, n, o) for b, (n, o) in enumerate(files.items(), 1)]
    folder = _make_manifest_dir(tmp_path, rows, files)
    _finalize_manifest(folder, rows, files)
    assert len(load_dataset(folder)) == 10
    # меняем внутренний bin_id, не трогая данные; SHA пересчитываем
    name = rows[0]["output_file"]
    o = files[name]
    bad = dict(o)
    bad["bin_id"] = "99"
    _write_npz(folder / name, bad)
    _finalize_manifest(folder, rows, files)  # пересчёт SHA в manifest
    with pytest.raises(ProfileShapeError, match="bin_id"):
        load_dataset(folder)


def test_manifest_missing_extra_duplicate(tmp_path):
    """Отсутствующий/лишний файл или дублированный bin_id отклоняется."""
    files = _make_10obs()
    rows = [_manifest_row(b, n, o) for b, (n, o) in enumerate(files.items(), 1)]
    folder = _make_manifest_dir(tmp_path, rows, files)
    _finalize_manifest(folder, rows, files)
    # отсутствующий файл
    (folder / rows[0]["output_file"]).unlink()
    with pytest.raises(ProfileShapeError):
        load_dataset(folder)
    # лишний файл (не в manifest)
    folder_extra = _make_manifest_dir(tmp_path / "extra", rows, files)
    _finalize_manifest(folder_extra, rows, files)
    _write_npz(folder_extra / "bin_99_extra_n1.npz",
               _make_obs(np.full(N_BINS, 1.0)))
    with pytest.raises(ProfileShapeError):
        load_dataset(folder_extra)
    # дублированный bin_id
    rows2 = [_manifest_row(b, n, o) for b, (n, o) in enumerate(files.items(), 1)]
    rows2[0]["bin_id"] = "2"
    folder2 = _make_manifest_dir(tmp_path / "dup", rows2, files)
    _finalize_manifest(folder2, rows2, files)
    with pytest.raises(ProfileShapeError):
        load_dataset(folder2)


def test_manifest_row_order_does_not_change_order(tmp_path):
    """Перестановка строк manifest не меняет порядок загруженных наблюдений."""
    files = _make_10obs()
    rows = [_manifest_row(b, n, o) for b, (n, o) in enumerate(files.items(), 1)]
    folder = _make_manifest_dir(tmp_path, rows, files)
    _finalize_manifest(folder, rows, files)
    ordered = load_dataset(folder)
    # перемешиваем строки manifest
    shuffled = rows[::-1]
    with open(folder / "manifest.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(shuffled[0].keys()))
        w.writeheader()
        w.writerows(shuffled)
    reordered = load_dataset(folder)
    for a, b in zip(ordered, reordered):
        assert np.array_equal(a["rate"], b["rate"])


# ---------------------------------------------------------------- формулы
def test_normalized_area_is_one():
    """Площадь нормированного профиля sum(p)*Δφ = 1."""
    rng = np.random.default_rng(0)
    for _ in range(5):
        profile = rng.uniform(1, 5, size=N_BINS)
        p, B = normalize(profile)
        assert p == pytest.approx(profile / B)
        assert np.sum(p) * (1.0 / N_BINS) == pytest.approx(1.0)


def test_R_scale_and_permutation_invariant():
    """R инвариантен к положительному масштабу и перестановке периодов."""
    phase = _phase()
    m1 = _window_mask(phase, *W1)
    m2 = _window_mask(phase, *W2)
    base = np.full(N_BINS, 1.0)
    type_a = base.copy(); type_a[m1] = 2.0; type_a[m2] = 2.0
    type_b = base.copy(); type_b[m1] = 8.0; type_b[m2] = 4.0
    rate = np.vstack([np.tile(type_a, (17, 1)), np.tile(type_b, (17, 1))])
    R0 = metric_R(mean_profile(rate), phase)
    # масштаб
    assert metric_R(mean_profile(rate * 7.3), phase) == pytest.approx(R0)
    # перестановка, меняющая первый период (тип A -> тип B)
    perm = np.arange(N_PERIODS)
    perm[0] = 17  # первый период становится типом B
    perm[17] = 0
    rate_perm = rate[perm]
    assert not np.array_equal(rate_perm[0], rate[0])  # периоды различаются
    assert metric_R(mean_profile(rate_perm), phase) == pytest.approx(R0)


def test_R_is_ratio_of_integrals_not_mean_of_ratios():
    """Независимый пример против ошибки «среднее отношений» (задание).

    Два типа периодов с потоками в W1/W2: (2,2) и (8,4), каждый по 17 раз.
    Правильное R = 0.6; ошибочное среднее отношений = 0.75.
    """
    phase = _phase()
    m1 = _window_mask(phase, *W1)
    m2 = _window_mask(phase, *W2)
    base = np.full(N_BINS, 1.0)  # положительная константа вне окон
    type_a = base.copy(); type_a[m1] = 2.0; type_a[m2] = 2.0
    type_b = base.copy(); type_b[m1] = 8.0; type_b[m2] = 4.0
    rate = np.vstack([np.tile(type_a, (17, 1)), np.tile(type_b, (17, 1))])
    assert rate.shape == (34, 100)
    prof = mean_profile(rate)
    R = metric_R(prof, phase)
    assert R == pytest.approx(0.6, rel=1e-9)
    # ошибочное среднее отношений периодов
    per_period = [metric_R(r, phase) for r in rate]
    assert float(np.mean(per_period)) == pytest.approx(0.75, rel=1e-9)
    assert R != pytest.approx(0.75)


def test_negative_rate_inside_W2_no_clipping():
    """Отрицательный отсчёт ВНУТРИ W2 сохраняется, без clipping.

    Все 100 бинов = 1, один бин внутри W2 = -0.5.
    W1: 25 единиц, W2: 24 единицы и -0.5.
    Правильное R = 23.5/25 = 0.94; ошибочный clipping дал бы 0.96.
    """
    phase = _phase()
    m1 = _window_mask(phase, *W1)
    m2 = _window_mask(phase, *W2)
    assert m1.sum() == 25
    assert m2.sum() == 25
    profile = np.full(N_BINS, 1.0)
    # один бин внутри W2 делаем -0.5
    idx = np.where(m2)[0][0]
    profile[idx] = -0.5
    R = metric_R(profile, phase)
    assert R == pytest.approx(23.5 / 25.0, rel=1e-9)
    assert R != pytest.approx(0.96)


# ---------------------------------------------------------------- отказы
def test_rejects_nan_via_public_load(tmp_path):
    """NaN в rate вызывает явный отказ через публичную загрузку NPZ."""
    obs = _make_obs(np.full(N_BINS, 1.0))
    obs["rate"][0, 0] = np.nan
    path = tmp_path / "bad.npz"
    _write_npz(path, obs)
    with pytest.raises(ProfileShapeError):
        load_npz(path)


def test_rejects_wrong_shape(tmp_path):
    """Неправильная форма rate отклоняется."""
    obs = _make_obs(np.full(N_BINS, 1.0))
    obs["rate"] = obs["rate"][:, :50]
    path = tmp_path / "bad_shape.npz"
    _write_npz(path, obs)
    with pytest.raises(ProfileShapeError):
        load_npz(path)


def test_rejects_error_nonpositive(tmp_path):
    """error <= 0 отклоняется."""
    obs = _make_obs(np.full(N_BINS, 1.0))
    obs["error"][0, 0] = 0.0
    path = tmp_path / "bad_error.npz"
    _write_npz(path, obs)
    with pytest.raises(ProfileShapeError):
        load_npz(path)


def test_rejects_nonpositive_integral():
    """Неположительный интеграл W1/W2 → отказ, без epsilon."""
    phase = _phase()
    m1 = _window_mask(phase, *W1)
    m2 = _window_mask(phase, *W2)
    profile = np.full(N_BINS, 1.0)
    profile[m1] = 0.0
    profile[m2] = 2.0
    with pytest.raises(ProfileShapeError):
        metric_R(profile, phase)
    profile2 = np.full(N_BINS, 1.0)
    profile2[m2] = 0.0
    profile2[m1] = 2.0
    with pytest.raises(ProfileShapeError):
        metric_R(profile2, phase)


def test_rejects_nonpositive_mean():
    """Неположительное среднее профиля → отказ."""
    with pytest.raises(ProfileShapeError):
        normalize(np.full(N_BINS, -1.0))


def test_rejects_bad_public_shapes():
    """Некорректные размеры публичных функций отклоняются."""
    with pytest.raises(ProfileShapeError):
        mean_profile(np.ones((10, 10)))
    with pytest.raises(ProfileShapeError):
        normalize(np.ones((5, 5)))
    with pytest.raises(ProfileShapeError):
        metric_R(np.ones(N_BINS), np.ones(50))


def test_group_contrast_E():
    """E = mean(high)/mean(low) - 1, равные веса; отказы на неконечных R."""
    assert group_contrast_E([1.2, 1.2], [1.0, 1.0]) == pytest.approx(0.2)
    assert group_contrast_E([1.0, 1.0], [1.0, 1.0]) == pytest.approx(0.0)
    with pytest.raises(ProfileShapeError):
        group_contrast_E([], [1.0])
    with pytest.raises(ProfileShapeError):
        group_contrast_E([1.0], [0.0])
    with pytest.raises(ProfileShapeError):
        group_contrast_E([np.nan], [1.0])
    with pytest.raises(ProfileShapeError):
        group_contrast_E([1.0], [np.inf])
    # двумерные группы отклоняются
    with pytest.raises(ProfileShapeError):
        group_contrast_E([[1.0, 1.0]], [1.0, 1.0])
    with pytest.raises(ProfileShapeError):
        group_contrast_E([1.0, 1.0], [[1.0, 1.0]])
    # неположительный R в любой группе отклоняется, даже если среднее > 0
    with pytest.raises(ProfileShapeError):
        group_contrast_E([1.0, -0.5], [1.0, 1.0])  # среднее high = 0.25 > 0
    with pytest.raises(ProfileShapeError):
        group_contrast_E([1.0, 1.0], [1.0, -0.5])  # среднее low = 0.25 > 0
    with pytest.raises(ProfileShapeError):
        group_contrast_E([1.0, 0.0], [1.0, 1.0])  # нулевой R в high