#!/usr/bin/env python3
"""Independent check of E_a via pairwise two-point Arrhenius ratios.

For each pair of points within the same series, E_a = R * ln(k2/k1) / (1/T1 - 1/T2).
Average over all pairs in series 2024-01, 2024-02, 2024-04.
"""
import numpy as np
import csv
from itertools import combinations

R = 8.314
SERIES = {'2024-01', '2024-02', '2024-04'}

rows = []
with open('data/raw/rates.csv') as f:
    for r in csv.DictReader(f):
        rows.append((r['series'], float(r['T_C']), float(r['k_s'])))

by_series = {}
for s, T, k in rows:
    if s in SERIES:
        by_series.setdefault(s, []).append((T + 273.15, k))

Ea_pairs = []
for s, pts in by_series.items():
    for (T1, k1), (T2, k2) in combinations(pts, 2):
        if T1 == T2:
            continue
        Ea = R * np.log(k2 / k1) / (1.0 / T1 - 1.0 / T2)
        Ea_pairs.append(Ea)

Ea_pairs = np.array(Ea_pairs)
Ea_mean = Ea_pairs.mean() / 1000.0  # kJ/mol
Ea_std = Ea_pairs.std(ddof=1) / 1000.0
Ea_med = np.median(Ea_pairs) / 1000.0

with open('results/verify_pairwise.txt', 'w') as f:
    f.write(f"method: pairwise two-point Arrhenius ratios within each series\n")
    f.write(f"series: {sorted(SERIES)}\n")
    f.write(f"n pairs: {len(Ea_pairs)}\n")
    f.write(f"E_a mean = {Ea_mean:.3f} kJ/mol (std {Ea_std:.3f})\n")
    f.write(f"E_a median = {Ea_med:.3f} kJ/mol\n")

print(f"n pairs = {len(Ea_pairs)}")
print(f"E_a mean = {Ea_mean:.3f} kJ/mol (std {Ea_std:.3f})")
print(f"E_a median = {Ea_med:.3f} kJ/mol")