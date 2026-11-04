#!/usr/bin/env python3
"""Plot Arrhenius fit: used measurements (series 2024-01/02/04) in ln k vs 1/T
plus the fitted line. Outputs results/arrhenius_plot.png.
"""
import numpy as np
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

R = 8.314  # J/(mol*K)
SERIES = {'2024-01', '2024-02', '2024-04'}

rows = []
with open('data/raw/rates.csv') as f:
    for r in csv.DictReader(f):
        rows.append((r['series'], float(r['T_C']), float(r['k_s'])))

pts = [(T + 273.15, k) for s, T, k in rows if s in SERIES]
T = np.array([p[0] for p in pts])
k = np.array([p[1] for p in pts])
x = 1.0 / T
y = np.log(k)

b, a = np.polyfit(x, y, 1)

# fitted line over the used x-range
xs = np.linspace(x.min(), x.max(), 100)
ys = a + b * xs

fig, ax = plt.subplots(figsize=(7, 5))
for s in sorted(SERIES):
    spts = [(T + 273.15, k) for ss, T, k in rows if ss == s]
    sT = np.array([p[0] for p in spts])
    sk = np.array([p[1] for p in spts])
    ax.scatter(1.0 / sT, np.log(sk), label=s, s=40)

ax.plot(xs, ys, 'k-', label='fit (E_a = 51.66 kJ/mol)')
ax.set_xlabel('1/T  (K$^{-1}$)')
ax.set_ylabel('ln k')
ax.set_title('Arrhenius plot: ln k vs 1/T (series 2024-01/02/04)')
ax.legend()
ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig('results/arrhenius_plot.png', dpi=150)
print('saved results/arrhenius_plot.png')
print(f'slope b = {b:.6f}, ln A = {a:.6f}')