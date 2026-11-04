#!/usr/bin/env python3
"""Fit Arrhenius law to rates.csv (series 2024-01, 2024-02, 2024-04).

Outputs E_a, ln A, R^2, and residual diagnostics to results/fit_arrhenius.txt.
"""
import numpy as np
import csv

R = 8.314  # J/(mol*K)
SERIES = {'2024-01', '2024-02', '2024-04'}

rows = []
with open('data/raw/rates.csv') as f:
    for r in csv.DictReader(f):
        rows.append((r['series'], float(r['T_C']), float(r['k_s'])))

# keep only valid series
pts = [(T + 273.15, k) for s, T, k in rows if s in SERIES]
T = np.array([p[0] for p in pts])
k = np.array([p[1] for p in pts])
x = 1.0 / T
y = np.log(k)

# linear regression y = a + b*x
n = len(x)
b, a = np.polyfit(x, y, 1)
yhat = a + b * x
resid = y - yhat
ss_res = np.sum(resid**2)
ss_tot = np.sum((y - np.mean(y))**2)
r2 = 1 - ss_res / ss_tot
Ea = -b * R  # J/mol
Ea_kJ = Ea / 1000.0
lnA = a

# standard error of slope
s2 = ss_res / (n - 2)
sxx = np.sum((x - np.mean(x))**2)
se_b = np.sqrt(s2 / sxx)
se_Ea = se_b * R / 1000.0  # kJ/mol

# temperature range actually used
Tmin, Tmax = T.min(), T.max()

with open('results/fit_arrhenius.txt', 'w') as f:
    f.write(f"series used: {sorted(SERIES)}\n")
    f.write(f"n points: {n}\n")
    f.write(f"T range used: {Tmin:.2f}-{Tmax:.2f} K ({Tmin-273.15:.1f}-{Tmax-273.15:.1f} C)\n")
    f.write(f"slope b = {b:.6f} K\n")
    f.write(f"intercept ln A = {lnA:.6f}\n")
    f.write(f"E_a = {Ea_kJ:.3f} kJ/mol (se {se_Ea:.3f} kJ/mol)\n")
    f.write(f"R^2 = {r2:.6f}\n")
    f.write(f"max |resid| = {np.max(np.abs(resid)):.6f}\n")

print(f"n={n}")
print(f"T range: {Tmin-273.15:.1f}-{Tmax-273.15:.1f} C")
print(f"slope b = {b:.6f} K")
print(f"ln A = {lnA:.6f}")
print(f"E_a = {Ea_kJ:.3f} kJ/mol (se {se_Ea:.3f})")
print(f"R^2 = {r2:.6f}")
print(f"max |resid| = {np.max(np.abs(resid)):.6f}")
