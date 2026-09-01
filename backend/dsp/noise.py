"""
Phase 2.5 — Noise Floor Estimation
===================================
Estimates the noise floor from a Power Spectral Density (PSD) array.
"""

import numpy as np
from config import NOISE_FLOOR_PERCENTILE

def estimate_noise_floor(psd_linear: np.ndarray) -> float:
    """
    Estimate the noise floor from a linear PSD array.
    Uses a percentile-based approach assuming that the majority
    of the spectrum (or at least the lowest N%) is noise.
    
    Returns:
        Noise floor power (linear scale).
    """
    if len(psd_linear) == 0:
        return 1e-12
        
    # Sort and take the Nth percentile
    noise_power = np.percentile(psd_linear, NOISE_FLOOR_PERCENTILE)
    
    # Safeguard against zero or negative (though PSD should be >= 0)
    if noise_power <= 0:
        noise_power = 1e-12
        
    return float(noise_power)


def to_db(linear_power: np.ndarray | float) -> np.ndarray | float:
    """Convert linear power to dB."""
    return 10 * np.log10(np.maximum(linear_power, 1e-12))
