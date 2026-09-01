"""
Phase 3.4 — Carrier Frequency Offset Estimation
===============================================
Estimates CFO (Carrier Frequency Offset) using coarse-to-fine strategy.
"""

import numpy as np
from typing import Dict, Any, List


def _mth_power_cfo(iq_signal: np.ndarray, fs: float, M: int) -> float:
    """Helper: M-th power CFO estimation."""
    if len(iq_signal) < 1024:
        return 0.0
        
    N = min(len(iq_signal), 16384)
    sig = iq_signal[:N]
    
    # M-th power
    sig_m = sig ** M
    
    # FFT
    fft_m = np.fft.fft(sig_m)
    freqs = np.fft.fftfreq(N, 1/fs)
    
    # Find peak (exclude DC region)
    dc_guard = int(0.01 * N)
    if dc_guard < 1:
        dc_guard = 1
    mag = np.abs(fft_m)
    mag[:dc_guard] = 0
    mag[-dc_guard:] = 0
    
    peak_idx = np.argmax(mag)
    peak_freq = freqs[peak_idx]
    
    # CFO is peak_freq / M
    cfo = peak_freq / M
    
    return float(cfo)


def _mth_power_cfo_bounded(iq_signal: np.ndarray, fs: float, M: int, max_hz: float) -> float:
    """M-th power CFO estimation with bounded search range."""
    if len(iq_signal) < 1024:
        return 0.0
        
    N = min(len(iq_signal), 16384)
    sig = iq_signal[:N]
    
    sig_m = sig ** M
    fft_m = np.fft.fft(sig_m)
    freqs = np.fft.fftfreq(N, 1/fs)
    mag = np.abs(fft_m)
    
    # Create mask for frequency range [-max_hz, max_hz]
    freq_mask = (freqs >= -max_hz) & (freqs <= max_hz)
    if not np.any(freq_mask):
        return 0.0
    
    # Zero out everything outside the range
    mag[~freq_mask] = 0
    
    peak_idx = np.argmax(mag)
    if mag[peak_idx] == 0:
        return 0.0
    peak_freq = freqs[peak_idx]
    
    return float(peak_freq / M)


def estimate_cfo_coarse(iq_signal: np.ndarray, fs: float, modulation_order: int = 4) -> float:
    """
    Coarse CFO estimation using the M-th power method.
    Works for M-PSK (M=2 for BPSK, 4 for QPSK, etc).
    For M-QAM, this method is less effective but gives a rough estimate.
    """
    return _mth_power_cfo(iq_signal, fs, modulation_order)


def estimate_cfo(iq_signal: np.ndarray, fs: float) -> Dict[str, Any]:
    """
    Coarse-to-fine CFO estimation.
    
    Tries multiple modulation orders (2, 4, 8) and selects the most consistent estimate.
    Then applies fine estimation on the corrected signal.
    
    Returns:
        Dict with cfo_hz, status, confidence, method
    """
    result = {
        "cfo_hz": 0.0,
        "status": "unavailable",
        "confidence": 0.0,
        "method": "mth_power_multi"
    }
    
    if len(iq_signal) < 1024 or fs <= 0:
        return result
    
    # Try multiple modulation orders
    orders = [2, 4, 8]  # BPSK, QPSK, 8PSK
    estimates = []
    
    for M in orders:
        cfo = _mth_power_cfo(iq_signal, fs, M)
        if abs(cfo) < fs * 0.4:  # Reject aliases beyond reasonable range
            estimates.append({"M": M, "cfo": cfo})
    
    if not estimates:
        return result
    
    # Check consistency: estimates should be similar if they're correct
    # (M*CFO gives the same tone frequency)
    # We can't directly compare because they're scaled by 1/M
    # Instead, evaluate the peak prominence for each M
    
    best_estimate = estimates[0]  # Default to M=2
    best_prominence = 0.0
    
    for est in estimates:
        M = est["M"]
        cfo = est["cfo"]
        # Recompute to get prominence
        N = min(len(iq_signal), 16384)
        sig = iq_signal[:N]
        sig_m = sig ** M
        fft_m = np.fft.fft(sig_m)
        mag = np.abs(fft_m)
        dc_guard = int(0.01 * N)
        mag[:dc_guard] = 0
        mag[-dc_guard:] = 0
        peak_idx = np.argmax(mag)
        peak_val = mag[peak_idx]
        median_val = np.median(mag)
        prominence = peak_val / median_val if median_val > 0 else 1.0
        
        if prominence > best_prominence:
            best_prominence = prominence
            best_estimate = est
    
    coarse_cfo = best_estimate["cfo"]
    
    # Fine estimation: apply coarse correction and re-estimate residual
    # Search only in narrow range around 0 to avoid symbol-rate harmonics
    corrected = correct_cfo(iq_signal, coarse_cfo, fs)
    # Use M=4 for fine estimation, but restrict search to ±max_residual
    max_residual = fs * 0.01  # ±1% of fs
    fine_cfo = _mth_power_cfo_bounded(corrected, fs, 4, max_residual)
    
    final_cfo = coarse_cfo + fine_cfo
    
    # Confidence based on peak prominence
    confidence = min(1.0, best_prominence / 20.0)
    
    result["cfo_hz"] = float(final_cfo)
    result["coarse_cfo_hz"] = float(coarse_cfo)
    result["fine_cfo_hz"] = float(fine_cfo)
    result["status"] = "estimated" if confidence > 0.4 else "low_confidence"
    result["confidence"] = float(confidence)
    
    return result


def correct_cfo(iq_signal: np.ndarray, cfo_hz: float, fs: float) -> np.ndarray:
    """
    Apply CFO correction by multiplying with complex exponential.
    """
    if cfo_hz == 0.0:
        return iq_signal
    t = np.arange(len(iq_signal)) / fs
    correction = np.exp(-1j * 2 * np.pi * cfo_hz * t)
    return iq_signal * correction