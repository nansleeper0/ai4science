#!/usr/bin/env python3
"""Find absorption peaks in spectrum files and output center_nm + fwhm_nm."""

import csv
import glob
import os
import numpy as np
from scipy.optimize import curve_fit
from scipy.signal import find_peaks

DATA_DIR = "data"
OUT_FILE = "results/peaks.csv"


def gaussian(x, amp, center, fwhm, offset):
    """Gaussian with baseline offset."""
    sigma = fwhm / (2 * np.sqrt(2 * np.log(2)))
    return amp * np.exp(-0.5 * ((x - center) / sigma) ** 2) + offset


def load_spectrum(path):
    wl = []
    inten = []
    with open(path) as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader)  # skip header
        for row in reader:
            wl.append(float(row[0]))
            inten.append(float(row[1]))
    return np.array(wl), np.array(inten)


def estimate_background(wl, inten):
    """Estimate background using rolling 10th percentile."""
    window_size = 150
    bg = np.zeros_like(inten)
    for i in range(len(inten)):
        lo = max(0, i - window_size // 2)
        hi = min(len(inten), i + window_size // 2)
        bg[i] = np.percentile(inten[lo:hi], 10)
    return bg


def find_peaks_in_spectrum(wl, inten):
    """Subtract background, find peaks, fit Gaussians."""
    n = len(wl)
    step = wl[1] - wl[0]  # 0.5 nm

    # Estimate background
    bg = estimate_background(wl, inten)
    inten_bg_sub = inten - bg
    inten_bg_sub = np.maximum(inten_bg_sub, 0)

    # Estimate noise from the lowest 10% of bg-subtracted values
    lower = inten_bg_sub[inten_bg_sub < np.percentile(inten_bg_sub, 10)]
    if len(lower) > 10:
        noise = np.median(np.abs(lower - np.median(lower)))
    else:
        noise = 0.01

    # Use prominence threshold = 5 * noise, but with a minimum of 0.2
    # to avoid detecting small bumps
    prominence_threshold = max(5 * max(noise, 1e-6), 0.2)

    # Find peaks using prominence
    min_dist_nm = 30
    min_idx = max(1, int(min_dist_nm / step))

    peak_indices, props = find_peaks(
        inten_bg_sub,
        distance=min_idx,
        prominence=prominence_threshold,
    )

    if len(peak_indices) == 0:
        return []

    results = []
    for idx in peak_indices:
        # Fit a Gaussian around this peak
        half_range = 50  # nm window
        lo = max(0, idx - int(half_range / step))
        hi = min(n, idx + int(half_range / step) + 1)

        x_fit = wl[lo:hi]
        y_fit = inten[lo:hi]

        # Initial guess from data
        amp_guess = inten[idx] - bg[idx]
        center_guess = wl[idx]
        fwhm_guess = 10.0
        offset_guess = bg[idx]

        try:
            popt, _ = curve_fit(
                gaussian,
                x_fit,
                y_fit,
                p0=[amp_guess, center_guess, fwhm_guess, offset_guess],
                bounds=(
                    [0, 400, 2.0, 0],
                    [np.inf, 700, 30.0, np.inf],
                ),
                maxfev=10000,
            )
            center = popt[1]
            fwhm = popt[2]
            # Filter: FWHM must be in reasonable range [3, 20] nm
            if 3.0 <= fwhm <= 20.0:
                results.append((center, fwhm))
        except Exception:
            pass

    return results


def main():
    os.makedirs("results", exist_ok=True)

    files = sorted(glob.glob(f"{DATA_DIR}/spectrum_*.txt"))
    rows = []
    for fpath in files:
        fname = os.path.basename(fpath)
        wl, inten = load_spectrum(fpath)
        peaks = find_peaks_in_spectrum(wl, inten)
        for center, fwhm in peaks:
            rows.append(
                {
                    "file": fname,
                    "center_nm": f"{center:.1f}",
                    "fwhm_nm": f"{fwhm:.1f}",
                }
            )

    with open(OUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "center_nm", "fwhm_nm"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} peaks to {OUT_FILE}")
    for r in rows:
        print(f"  {r['file']}: {r['center_nm']} nm, FWHM {r['fwhm_nm']} nm")


if __name__ == "__main__":
    main()