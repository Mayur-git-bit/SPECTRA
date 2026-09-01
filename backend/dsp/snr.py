"""
Phase 3.2 — SNR Estimation
===========================
Rigorous SNR estimation integrated over the detected bandwidth.
"""

import numpy as np
from typing import Tuple

from dsp.noise import to_db

def estimate_snr(
    freqs: np.ndarray,
    psd_linear: np.ndarray,
    noise_floor_linear: float,
    lower_edge: float,
    upper_edge: float
) -> float:
    """
    Estimate SNR by integrating signal power over the detected bandwidth.
    
    SNR = (Total Band Power - Noise Power in Band) / (Total Noise Power)
    This is an approximation suitable for unknown signals.
    """
    if len(freqs) == 0 or upper_edge <= lower_edge:
        return 0.0
        
    # Find indices within the signal band
    band_mask = (freqs >= lower_edge) & (freqs <= upper_edge)
    
    if not np.any(band_mask):
        return 0.0
        
    band_psd = psd_linear[band_mask]
    
    # Total power in the band
    total_band_power = np.sum(band_psd)
    
    # Noise power expected in the band
    noise_in_band = noise_floor_linear * np.sum(band_mask)
    
    # Signal power is total minus noise (bounded to 0)
    signal_power = max(1e-12, total_band_power - noise_in_band)
    
    # We compare signal power to the noise power in the same band
    # (SNR in-band) or across the whole spectrum. Usually, SNR is quoted
    # relative to the band of interest.
    noise_power = max(1e-12, noise_in_band)
    
    return float(to_db(signal_power / noise_power))
