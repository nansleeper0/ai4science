#!/usr/bin/env python3
"""[порождено: Codex] Export a deterministic selection from existing prepared arrays.

This is input-data preparation, not the HW2 shape/luminosity analysis.
Source notebooks and research data are read only; no notebook cells are executed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

import numpy as np

SOURCE_ROOT = Path('/home/artem/EXO2030/new_data/type_2_expand/code')
DEFAULT_CACHE = SOURCE_ROOT / 'data/30_10_26_all_prepared100.npz'
DEFAULT_NOTEBOOK = SOURCE_ROOT / '22_09_26.ipynb'
N_BINS = 10


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def cell_sources_sha256(path: Path) -> str:
    notebook = json.loads(path.read_text(encoding='utf-8'))
    content = [(cell['cell_type'], ''.join(cell.get('source', [])))
               for cell in notebook['cells']]
    serialized = json.dumps(content, ensure_ascii=False, separators=(',', ':'))
    return hashlib.sha256(serialized.encode()).hexdigest()


def export_dataset(cache: Path, notebook: Path, output: Path) -> dict:
    cache, notebook, output = cache.resolve(), notebook.resolve(), output.resolve()
    if output.exists():
        raise FileExistsError(f'Refusing to overwrite existing dataset: {output}')
    if not output.parent.is_dir():
        raise FileNotFoundError(output.parent)

    cache_hash = file_sha256(cache)
    notebook_hash = file_sha256(notebook)
    with np.load(cache, allow_pickle=False) as source:
        arrays = {name: source[name].copy() for name in source.files}
    metadata = json.loads(arrays['metadata_json'].item())
    expected_code_hash = str(arrays['source_cell_source_sha256'].item())
    if cell_sources_sha256(notebook) != expected_code_hash:
        raise ValueError('Prepared cache does not match current notebook cell sources')
    for name, expected in metadata['array_sha256'].items():
        if hashlib.sha256(arrays[name].tobytes()).hexdigest() != expected:
            raise ValueError(f'Source array checksum mismatch: {name}')

    # Existing canonical preparation also depends on the per-observation periods
    # and on the complete FITS collection used for the phase alignment.
    root = notebook.parent
    names = np.load(root / 'data/list_name.npy', allow_pickle=False)
    periods = np.load(root / 'data/list_period.npy', allow_pickle=False)
    if len(names) != len(periods):
        raise ValueError('Period/name tables have different lengths')
    period_by_name = {Path(str(name)).name: float(period)
                      for name, period in zip(names, periods, strict=True)}
    for name, period in zip(arrays['filenames'], arrays['periods'], strict=True):
        if period_by_name[str(name)] != float(period):
            raise ValueError(f'Changed period table: {name}')
    for row in metadata['input_fits_manifest']:
        path = root / 'data' / row['filename']
        if file_sha256(path) != row['sha256']:
            raise ValueError(f'Changed original FITS: {path}')
    manifest_by_name = {row['filename']: row for row in metadata['input_fits_manifest']}

    brightness = np.asarray(arrays['mean_rates'], dtype=float)
    offsets = np.asarray(arrays['offsets'], dtype=np.int64)
    ncycles = np.asarray(arrays['ncycles'], dtype=np.int64)
    nobs = len(brightness)
    if len(offsets) != nobs + 1 or not np.array_equal(np.diff(offsets), ncycles):
        raise ValueError('Invalid observation offsets')
    if not (np.isfinite(brightness).all() and (ncycles > 0).all()):
        raise ValueError('Invalid observation brightness or length')
    if not np.all(np.diff(brightness) >= 0):
        raise ValueError('Expected the canonical brightness-sorted input')
    for name in ('rate', 'error', 'time'):
        if arrays[name].shape != (int(offsets[-1]), 100):
            raise ValueError(f'Unexpected source matrix shape: {name}')

    edges = np.linspace(float(brightness.min()), float(brightness.max()), N_BINS + 1)
    if np.any(np.diff(edges) <= 0):
        raise ValueError('Cannot form ten nonzero-width bins')
    assignments = np.searchsorted(edges, brightness, side='right') - 1
    assignments[brightness == edges[-1]] = N_BINS - 1
    if not np.all((assignments >= 0) & (assignments < N_BINS)):
        raise ValueError('Brightness outside bin edges')
    selected, candidate_counts = [], []
    for bin_index in range(N_BINS):
        candidates = np.flatnonzero(assignments == bin_index)
        if not len(candidates):
            raise ValueError(f'Empty bin {bin_index + 1}; bin edges will not be changed silently')
        ranked = sorted(candidates,
                        key=lambda i: (-int(ncycles[i]), str(arrays['filenames'][i])))
        selected.append(int(ranked[0]))
        candidate_counts.append(len(candidates))
    common_length = int(ncycles[selected].min())
    stage = Path(tempfile.mkdtemp(prefix='.profile_dataset_', dir=output.parent))
    rows, output_hashes = [], {}
    try:
        for bin_index, index in enumerate(selected):
            start = int(offsets[index])
            stop = start + common_length
            rate, error, times = (arrays[key][start:stop].copy()
                                  for key in ('rate', 'error', 'time'))
            if not all(np.isfinite(a).all() for a in (rate, error, times)):
                raise ValueError('Nonfinite values in retained block')
            if np.any(error < 0):
                raise ValueError('Negative measurement uncertainty')
            if not np.all(np.diff(times, axis=1) > 0):
                raise ValueError('Non-monotonic times within pulse rows')
            period = float(arrays['periods'][index])
            row_dt = np.diff(times[:, 0])
            gap_after_rows = np.flatnonzero(row_dt > 1.25 * period)
            trimmed_brightness = float(np.mean(rate))
            filename = str(arrays['filenames'][index])
            obs_id = str(arrays['obs_ids'][index])
            destination_name = f'bin_{bin_index + 1:02d}_{filename.removesuffix(".lc")}.npz'
            np.savez_compressed(
                stage / destination_name,
                rate=rate, error=error, time=times,
                phase=(np.arange(100, dtype=float) + 0.5) / 100,
                pulse_period_s=np.asarray(period),
                source_filename=np.asarray(filename), obs_id=np.asarray(obs_id),
                bin_id=np.asarray(bin_index + 1, dtype=np.int64),
                bin_edges_count_per_s=edges[bin_index:bin_index + 2],
                mean_rate_full_count_per_s=np.asarray(brightness[index]),
                mean_rate_trimmed_count_per_s=np.asarray(trimmed_brightness),
                source_n_periods=np.asarray(ncycles[index], dtype=np.int64),
                source_row_indices=np.arange(common_length, dtype=np.int64),
                gap_after_row_indices=gap_after_rows.astype(np.int64),
            )
            output_hashes[destination_name] = file_sha256(stage / destination_name)
            rows.append({
                'bin_id': bin_index + 1,
                'bin_low_count_per_s': float(edges[bin_index]),
                'bin_high_count_per_s': float(edges[bin_index + 1]),
                'bin_candidates': candidate_counts[bin_index],
                'output_file': destination_name, 'source_filename': filename,
                'obs_id': obs_id, 'source_index': index,
                'source_n_periods': int(ncycles[index]),
                'retained_n_periods': common_length, 'n_phase_bins': 100,
                'mean_rate_full_count_per_s': float(brightness[index]),
                'mean_rate_trimmed_count_per_s': trimmed_brightness,
                'pulse_period_s': period,
                'retained_time_gaps': len(gap_after_rows),
                'source_fits_sha256': manifest_by_name[filename]['sha256'],
                'output_sha256': output_hashes[destination_name],
            })
        with (stage / 'manifest.csv').open('w', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        provenance = {
            'schema': 'exo2030.ten_brightness_bins.v1',
            'preparation_authoring_tool': 'Codex',
            'purpose': 'Input dataset preparation at the user request; no HW2 profile-shape inference performed',
            'source_notebook': str(notebook),
            'source_notebook_sha256': notebook_hash,
            'source_notebook_cell_sources_sha256': expected_code_hash,
            'cache_notebook': metadata['source_notebook'],
            'cache_notebook_sha256': metadata['source_notebook_sha256'],
            'cache_created_utc': metadata['created_utc'],
            'source_cache': str(cache), 'source_cache_sha256': cache_hash,
            'exporter_sha256': file_sha256(Path(__file__).resolve()),
            'input_fits_verified': len(metadata['input_fits_manifest']),
            'source_n_observations': nobs,
            'source_selection': 'Canonical post-peak observations prepared by the existing source notebook',
            'binning': 'Ten equal-width bins over the original full-observation mean RATE range; left closed/right open, final upper bound included',
            'bin_edges_count_per_s': edges.tolist(),
            'selection': 'Maximum complete pulse-row count within each bin; ties resolved by lexicographic source filename',
            'crop': 'Retain the first common_n_periods complete pulse rows of every selected observation; no random sampling, padding, rescaling or extra phase alignment',
            'common_n_periods': common_length, 'n_phase_bins': 100,
            'units': {'rate': 'count/s', 'error': 'count/s',
                      'time': 'Absolute BARYTIME seconds from the upstream preparation',
                      'phase': 'Cycle fraction, bin centres in the upstream aligned phase convention'},
            'brightness_note': 'Mean count rate is a brightness proxy, not calibrated physical luminosity',
            'phase_alignment': 'Already performed upstream in the source notebook; retained without changes',
            'rows': rows, 'output_file_sha256': output_hashes,
        }
        (stage / 'provenance.json').write_text(
            json.dumps(provenance, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        readme = f'''# EXO2030+375: десять кривых в десяти бинах яркости

[порождено: Codex] Техническое описание подготовки набора по поручению пользователя.

В каждом `bin_*.npz` одна кривая: массивы `rate`, `error`, `time` имеют форму
**({common_length}, 100)** — полные периоды × фазовые бины. Сохранены первые
{common_length} полных периодов каждого выбранного наблюдения. Поток и его
ошибки — count/s; время — абсолютные BARYTIME в секундах исходной подготовки.
`phase` — центры 100 фазовых бинов в общей фазовой системе исходного ноутбука.
Новая свёртка, нормировка амплитуды, сглаживание или фазовая привязка не делались.

Источник — канонические массивы `rate_arrs_sorted`, `error_arrs_sorted`,
`time_arrs_sorted` ноутбука `22_09_26.ipynb` исследовательского проекта.
Использован уже сохранённый полный набор299наблюдений; совпадение исходников
ячеек, контрольных сумм массивов, таблицы периодов и366входныхFITS проверено.
Исследовательский проект не изменялся. Пути/контрольные суммы — `provenance.json`.

## Отбор

1. Средний RATE каждого полного подготовленного наблюдения — исходная ось яркости.
2. Её диапазон разделён на десять равных по ширине бинов; последний включает
   правую границу. Это бины темпа счёта, не физической светимости.
3. В каждом бине взято наблюдение с наибольшим числом полных периодов.
   При равенстве используется имя исходного файла по алфавиту.
4. Общая длина — минимум числа периодов среди десяти выбранных наблюдений.
   Сохранено начало каждой кривой; время и ошибки обрезаны тем же срезом.

Бин и ранжирование определены ДО обрезки. Средние до/после и исходные длины
даны в `manifest.csv`. Одинаковое число периодов не означает строго одинаковую
длительность в секундах: индивидуальные периоды наблюдений различаются.
Временные разрывы, если имеются, отмечены в NPZ; здесь их число также есть
в таблице. Наличие соседних строк не следует считать доказательством непрерывности.

## Чтение

```python
from pathlib import Path
import numpy as np

folder = Path("data/profile_luminosity_10bins")
for path in sorted(folder.glob("bin_*.npz")):
    with np.load(path, allow_pickle=False) as lc:
        rate = lc["rate"]    # ({common_length}, 100)
        error = lc["error"]
        time = lc["time"]
```

Экспортёр: `src/prepare_profile_dataset.py`. Для повторной подготовки из
исследовательских источников укажите новый `--output`; существующий набор
не перезаписывается. Для дальнейшего задания агенту достаточно этой папки:
исходный FITS-архив и исследовательский notebook для чтения набора не нужны.
''' 
        (stage / 'README.md').write_text(readme, encoding='utf-8')
        # Verify that source files did not change during selection/export.
        if file_sha256(cache) != cache_hash or file_sha256(notebook) != notebook_hash:
            raise RuntimeError('Research source changed during export')
        stage.rename(output)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return {'output': str(output), 'n_curves': len(rows),
            'shape_each': [common_length, 100],
            'bin_candidate_counts': candidate_counts,
            'retained_time_gaps': [r['retained_time_gaps'] for r in rows]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-cache', type=Path, default=DEFAULT_CACHE)
    parser.add_argument('--source-notebook', type=Path, default=DEFAULT_NOTEBOOK)
    parser.add_argument('--output', type=Path,
                        default=Path(__file__).resolve().parents[1] / 'data/profile_luminosity_10bins')
    args = parser.parse_args()
    result = export_dataset(args.source_cache, args.source_notebook, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
