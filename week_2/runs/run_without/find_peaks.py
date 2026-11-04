import numpy as np
import glob
from scipy.signal import find_peaks
from scipy.interpolate import interp1d

def find_peaks_fwhm(filepath):
    """Find peaks and their FWHM in a spectrum file."""
    data = np.loadtxt(filepath, skiprows=1)
    wl = data[:, 0]
    intensity = data[:, 1]
    
    # Find peaks using scipy
    peaks, props = find_peaks(intensity, height=0, distance=10)
    
    results = []
    for pk in peaks:
        peak_height = intensity[pk]
        peak_wl = wl[pk]
        
        # Find FWHM by interpolation
        half_max = peak_height / 2.0
        
        # Search left side
        left_idx = pk
        for i in range(pk, -1, -1):
            if intensity[i] < half_max:
                left_idx = i
                break
        
        # Search right side
        right_idx = pk
        for i in range(pk, len(intensity)):
            if intensity[i] < half_max:
                right_idx = i
                break
        
        # Linear interpolation for more precise FWHM
        if left_idx < pk:
            # Interpolate between left_idx and left_idx+1
            wl_left = wl[left_idx] + (wl[left_idx+1] - wl[left_idx]) * \
                      (half_max - intensity[left_idx]) / (intensity[left_idx+1] - intensity[left_idx])
        else:
            wl_left = wl[pk]
        
        if right_idx > pk:
            wl_right = wl[right_idx-1] + (wl[right_idx] - wl[right_idx-1]) * \
                       (half_max - intensity[right_idx-1]) / (intensity[right_idx] - intensity[right_idx-1])
        else:
            wl_right = wl[pk]
        
        fwhm = wl_right - wl_left
        
        results.append({
            'wavelength': peak_wl,
            'intensity': peak_height,
            'fwhm': fwhm,
            'half_max': half_max
        })
    
    return results

# Process all spectra
files = sorted(glob.glob('/home/artem/ai4science/week_2/runs/run_without/data/spectrum_*.txt'))

for fpath in files:
    fname = fpath.split('/')[-1]
    print(f"\n{'='*60}")
    print(f"  {fname}")
    print(f"{'='*60}")
    
    peaks = find_peaks_fwhm(fpath)
    
    if not peaks:
        print("  No peaks found.")
        continue
    
    print(f"  {'#':>3}  {'λ (nm)':>10}  {'Intensity':>12}  {'FWHM (nm)':>10}")
    print(f"  {'-'*3}  {'-'*10}  {'-'*12}  {'-'*10}")
    for i, p in enumerate(peaks, 1):
        print(f"  {i:>3}  {p['wavelength']:>10.2f}  {p['intensity']:>12.5f}  {p['fwhm']:>10.3f}")
    
    print(f"\n  Total peaks: {len(peaks)}")