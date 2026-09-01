"""
Phase 2.3 & 2.4 — Power Spectral Density and Spectrogram
========================================================
Generates PSD (Welch) and Spectrogram (STFT) for the DSP branch.
"""

import numpy as np
from scipy import signal
from typing import Tuple

from config import (
    WELCH_NPERSEG, WELCH_NOVERLAP, WELCH_WINDOW,
    STFT_NPERSEG, STFT_NOVERLAP
)

def estimate_psd(
    iq_signal: np.ndarray,
    fs: float = 1.0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Estimate Power Spectral Density using Welch's method.
    
    Parameters:
        iq_signal: complex numpy array
        fs: sampling rate (defaults to 1.0 for normalized freq)
        
    Returns:
        freqs (Hz or normalized)
        psd (linear power)
    """
    # Ensure segment length isn't longer than the signal
    nperseg = min(WELCH_NPERSEG, len(iq_signal))
    noverlap = min(WELCH_NOVERLAP, nperseg // 2)
    
    freqs, psd = signal.welch(
        iq_signal,
        fs=fs,
        window=WELCH_WINDOW,
        nperseg=nperseg,
        noverlap=noverlap,
        return_onesided=False,
        scaling='density'
    )
    
    # fftshift to center 0 Hz
    freqs = np.fft.fftshift(freqs)
    psd = np.fft.fftshift(psd)
    
    return freqs, psd


def generate_spectrogram(
    iq_signal: np.ndarray,
    fs: float = 1.0
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate STFT spectrogram (waterfall).
    
    Returns:
        f (frequencies)
        t (time bins)
        Sxx (spectrogram power matrix)
    """
    nperseg = min(STFT_NPERSEG, len(iq_signal))
    noverlap = min(STFT_NOVERLAP, nperseg - 1)
    
    f, t, Zxx = signal.stft(
        iq_signal,
        fs=fs,
        window='hann',
        nperseg=nperseg,
        noverlap=noverlap,
        return_onesided=False
    )
    
    # fftshift frequencies
    f = np.fft.fftshift(f)
    Zxx = np.fft.fftshift(Zxx, axes=0)
    
    # Convert to power
    Sxx = np.abs(Zxx)**2
    
    return f, t, Sxx
