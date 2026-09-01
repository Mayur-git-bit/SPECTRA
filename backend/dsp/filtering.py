"""
Phase 2.7 — Adaptive Bandpass Filtering
========================================
Filters out out-of-band noise using a zero-phase SOS Butterworth filter.
"""

import numpy as np
from scipy import signal

from config import FILTER_GUARD_BAND

def apply_bandpass(
    iq_signal: np.ndarray,
    low_cut: float,
    high_cut: float,
    fs: float = 1.0,
    order: int = 4
) -> np.ndarray:
    """
    Apply a zero-phase (filtfilt) bandpass filter to a complex signal.
    
    Parameters:
        iq_signal: Complex baseband signal.
        low_cut: Lower cutoff frequency (Hz or normalized [-0.5, 0.5]).
        high_cut: Upper cutoff frequency (Hz or normalized [-0.5, 0.5]).
        fs: Sampling rate.
        order: Filter order.
        
    Returns:
        Filtered complex signal.
    """
    # Normalize frequencies to Nyquist (fs/2)
    nyq = 0.5 * fs
    
    # Add guard bands
    bw = high_cut - low_cut
    safe_low = max(-nyq * 0.99, low_cut - bw * FILTER_GUARD_BAND)
    safe_high = min(nyq * 0.99, high_cut + bw * FILTER_GUARD_BAND)
    
    if safe_low >= safe_high:
        return iq_signal  # Invalid band, return original
        
    # Scipy expects frequencies in [0, fs/2] for real signals,
    # but for complex signals basebanded around 0, we can use a complex
    # bandpass or shift the signal, apply a lowpass, and shift back.
    # The most robust way for complex baseband is to frequency shift the 
    # signal so the center of the band is at DC, apply a lowpass, 
    # then shift back.
    
    center_freq = (safe_high + safe_low) / 2.0
    cutoff_bw = (safe_high - safe_low) / 2.0
    
    # 1. Frequency shift to DC
    t = np.arange(len(iq_signal)) / fs
    shift_phasor = np.exp(-1j * 2 * np.pi * center_freq * t)
    sig_shifted = iq_signal * shift_phasor
    
    # 2. Design lowpass filter
    # cutoff must be strictly between 0 and nyquist
    Wn = cutoff_bw / nyq
    if Wn >= 1.0:
        return iq_signal  # Covers whole band anyway
        
    sos = signal.butter(order, Wn, btype='low', output='sos')
    
    # 3. Apply zero-phase lowpass (filtfilt)
    # Apply to real and imaginary parts independently since filter is real
    filtered_real = signal.sosfiltfilt(sos, sig_shifted.real)
    filtered_imag = signal.sosfiltfilt(sos, sig_shifted.imag)
    sig_filtered = filtered_real + 1j * filtered_imag
    
    # 4. Shift back to original frequency
    shift_back = np.exp(1j * 2 * np.pi * center_freq * t)
    
    return sig_filtered * shift_back
