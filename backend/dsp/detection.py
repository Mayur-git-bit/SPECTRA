"""
Phase 2.6 — Signal Detection
=============================
Detects contiguous spectral regions above noise floor with minimum-width filtering.
"""

import numpy as np
from typing import Tuple, Optional

from config import DETECTION_THRESHOLD_DB
from dsp.noise import to_db


def detect_signal_regions(
    psd_linear: np.ndarray,
    noise_floor_linear: float,
    freqs: np.ndarray,
    threshold_db: float = DETECTION_THRESHOLD_DB,
    min_width_bins: int = 3,
) -> Tuple[bool, float, int, Optional[float], Optional[float]]:
    """
    Detect contiguous signal regions in the PSD.
    
    Parameters:
        psd_linear: Array of linear PSD values.
        noise_floor_linear: Estimated noise floor (linear).
        freqs: Frequency axis corresponding to PSD bins.
        threshold_db: Detection margin above noise floor (dB).
        min_width_bins: Minimum number of contiguous bins to form a valid region.
        
    Returns:
        is_detected: True if any valid region found.
        peak_val_linear: Maximum PSD value in the strongest region.
        peak_idx: Index of the maximum value.
        lower_edge_hz: Lower frequency edge of strongest region (Hz), or None.
        upper_edge_hz: Upper frequency edge of strongest region (Hz), or None.
    """
    if len(psd_linear) == 0 or len(freqs) != len(psd_linear):
        return False, 0.0, 0, None, None
        
    noise_db = to_db(noise_floor_linear)
    threshold_linear = noise_floor_linear * (10 ** (threshold_db / 10.0))
    
    # Find bins above threshold
    above_threshold = psd_linear > threshold_linear
    
    if not np.any(above_threshold):
        # Fallback: check global peak margin
        peak_idx = int(np.argmax(psd_linear))
        peak_val_linear = psd_linear[peak_idx]
        peak_db = to_db(peak_val_linear)
        margin_db = peak_db - noise_db
        is_detected = margin_db >= threshold_db
        return is_detected, peak_val_linear, peak_idx, None, None
    
    # Find contiguous regions above threshold
    regions = []
    in_region = False
    region_start = 0
    
    for i, above in enumerate(above_threshold):
        if above and not in_region:
            in_region = True
            region_start = i
        elif not above and in_region:
            in_region = False
            region_end = i - 1
            region_width = region_end - region_start + 1
            if region_width >= min_width_bins:
                # Calculate region power and peak
                region_psd = psd_linear[region_start:region_end+1]
                region_peak_idx = region_start + int(np.argmax(region_psd))
                region_peak_val = psd_linear[region_peak_idx]
                regions.append({
                    'start': region_start,
                    'end': region_end,
                    'width': region_width,
                    'peak_idx': region_peak_idx,
                    'peak_val': region_peak_val,
                    'lower_edge': freqs[region_start],
                    'upper_edge': freqs[region_end],
                })
    
    # Check if we ended in a region
    if in_region:
        region_end = len(psd_linear) - 1
        region_width = region_end - region_start + 1
        if region_width >= min_width_bins:
            region_psd = psd_linear[region_start:region_end+1]
            region_peak_idx = region_start + int(np.argmax(region_psd))
            region_peak_val = psd_linear[region_peak_idx]
            regions.append({
                'start': region_start,
                'end': region_end,
                'width': region_width,
                'peak_idx': region_peak_idx,
                'peak_val': region_peak_val,
                'lower_edge': freqs[region_start],
                'upper_edge': freqs[region_end],
            })
    
    if not regions:
        # No region meets minimum width
        peak_idx = int(np.argmax(psd_linear))
        peak_val_linear = psd_linear[peak_idx]
        peak_db = to_db(peak_val_linear)
        margin_db = peak_db - noise_db
        is_detected = margin_db >= threshold_db
        return is_detected, peak_val_linear, peak_idx, None, None
    
    # Select strongest region by peak value
    strongest = max(regions, key=lambda r: r['peak_val'])
    
    return (
        True,
        strongest['peak_val'],
        strongest['peak_idx'],
        float(strongest['lower_edge']),
        float(strongest['upper_edge']),
    )


def detect_signal(
    psd_linear: np.ndarray,
    noise_floor_linear: float,
    freqs: Optional[np.ndarray] = None,
    threshold_db: float = DETECTION_THRESHOLD_DB,
    min_width_bins: int = 3,
) -> Tuple[bool, float, int, Optional[float], Optional[float]]:
    """
    Backward-compatible wrapper. If freqs provided, uses region detection.
    Otherwise falls back to simple peak detection.
    """
    if freqs is not None:
        return detect_signal_regions(psd_linear, noise_floor_linear, freqs, threshold_db, min_width_bins)
    
    # Legacy path for backward compatibility
    if len(psd_linear) == 0:
        return False, 0.0, 0, None, None
        
    peak_idx = int(np.argmax(psd_linear))
    peak_val_linear = psd_linear[peak_idx]
    peak_db = to_db(peak_val_linear)
    noise_db = to_db(noise_floor_linear)
    margin_db = peak_db - noise_db
    is_detected = margin_db >= threshold_db
    return is_detected, peak_val_linear, peak_idx, None, None