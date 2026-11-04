import numpy as np
import glob

def find_significant_peaks(filepath, threshold=0.3):
    """Find significant peaks above threshold."""
    data = np.loadtxt(filepath, skiprows=1)
    wl = data[:, 0]
    intensity = data[:, 1]
    
    # Smooth slightly to reduce noise
    from scipy.ndimage import uniform_filter1d
    smoothed = uniform_filter1d(intensity, size=3)
    
    # Find local maxima in smoothed data
    peaks = []
    for i in range(1, len(smoothed) - 1):
        if smoothed[i] > smoothed[i-1] and smoothed[i] > smoothed[i+1] and smoothed[i] > threshold:
            # FWHM via interpolation
            half_max = smoothed[i] / 2.0
            pk = i
            
            # Left
            left_idx = pk
            for j in range(pk, -1, -1):
                if smoothed[j] < half_max:
                    left_idx = j
                    break
            if left_idx < pk:
                wl_left = wl[left_idx] + (wl[left_idx+1] - wl[left_idx]) * \
                          (half_max - smoothed[left_idx]) / (smoothed[left_idx+1] - smoothed[left_idx])
            else:
                wl_left = wl[pk]
            
            # Right
            right_idx = pk
            for j in range(pk, len(smoothed)):
                if smoothed[j] < half_max:
                    right_idx = j
                    break
            if right_idx > pk:
                wl_right = wl[right_idx-1] + (wl[right_idx] - wl[right_idx-1]) * \
                           (half_max - smoothed[right_idx-1]) / (smoothed[right_idx] - smoothed[right_idx-1])
            else:
                wl_right = wl[pk]
            
            fwhm = wl_right - wl_left
            peaks.append({
                'wavelength': wl[pk],
                'intensity': smoothed[pk],
                'fwhm': fwhm
            })
    
    return peaks

files = sorted(glob.glob('/home/artem/ai4science/week_2/runs/run_without/data/spectrum_*.txt'))

print(f"{'Spectrum':<16} {'#':>3} {'λ (nm)':>10} {'Intensity':>12} {'FWHM (nm)':>10}")
print("-" * 60)

for fpath in files:
    fname = fpath.split('/')[-1]
    peaks = find_significant_peaks(fpath)
    for i, p in enumerate(peaks, 1):
        print(f"{fname:<16} {i:>3} {p['wavelength']:>10.1f} {p['intensity']:>12.4f} {p['fwhm']:>10.3f}")