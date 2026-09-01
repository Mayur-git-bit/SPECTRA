"""
Phase 2.1 & 2.2 — DC Removal and Normalization
==============================================
General DSP preprocessing applied ONLY to the classical DSP branch.
(Must not be applied to the AI model branch).
"""

import numpy as np
from typing import Tuple

def remove_dc(signal: np.ndarray) -> Tuple[np.ndarray, complex]:
    """
    Remove DC offset from a complex signal.
    
    mu = (1/N) * sum(x[n])
    x_dc[n] = x[n] - mu
    
    Returns:
        dc_corrected_signal, estimated_dc_value
    """
    mu = np.mean(signal)
    return signal - mu, mu


def rms_normalize(signal: np.ndarray) -> np.ndarray:
    """
    Normalize signal by its RMS power.
    
    P = (1/N) * sum(|x[n]|^2)
    x_norm[n] = x[n] / sqrt(P)
    
    Returns:
        Normalized complex signal
    """
    # Calculate power using squared magnitude
    power = np.mean(np.abs(signal)**2)
    
    if power < 1e-12:
        return signal.copy()  # Avoid division by zero for empty signals
        
    return signal / np.sqrt(power)


def process_dsp_branch(raw_signal: np.ndarray) -> Tuple[np.ndarray, complex]:
    """
    Complete Phase 2 preprocessing pipeline for the DSP branch.
    
    Pipeline: raw IQ -> DC removal -> RMS normalization
    """
    sig_no_dc, dc_val = remove_dc(raw_signal)
    sig_norm = rms_normalize(sig_no_dc)
    return sig_norm, dc_val
