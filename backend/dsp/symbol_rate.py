"""
Phase 3.3 — Symbol Rate Estimation
===================================
Estimates symbol rate using multiple methods:
1. Envelope power FFT (works for QAM, ASK - amplitude modulated)
2. M-th power FFT (works for PSK, FSK - constant envelope)
"""

import numpy as np
from scipy.signal import find_peaks
from typing import Dict, Any, List


def _estimate_symbol_rate_mth_power(iq_signal: np.ndarray, fs: float, M: int) -> Dict[str, Any]:
    """
    Estimate symbol rate using M-th power method.
    For M-PSK, x(t)^M strips modulation and reveals cyclostationarity at symbol rate.
    """
    result = {
        "symbol_rate_hz": 0.0,
        "status": "unavailable",
        "confidence": 0.0,
        "method": f"mth_power_M{M}"
    }
    
    if len(iq_signal) < 1024 or fs <= 0:
        return result
        
    N = min(len(iq_signal), 65536)
    sig = iq_signal[:N]
    
    # M-th power
    sig_m = sig ** M
    
    # Remove mean
    sig_m = sig_m - np.mean(sig_m)
    
    if np.std(sig_m) < 1e-12:
        return result
    
    # FFT
    P_f = np.abs(np.fft.fft(sig_m))
    P_f = P_f[:N//2]
    freqs = np.fft.fftfreq(N, 1/fs)[:N//2]
    
    # Ignore DC
    min_freq_hz = max(100.0, fs * 0.001)
    min_idx = int(min_freq_hz * N / fs)
    min_idx = max(min_idx, 1)
    
    if min_idx >= len(P_f):
        return result
    
    # Find peaks
    noise_floor = np.median(P_f[min_idx:])
    threshold = max(noise_floor * 5, np.mean(P_f) * 3)
    min_distance = max(10, int(0.01 * N / 2))
    
    peaks, properties = find_peaks(P_f[min_idx:], height=threshold, distance=min_distance)
    
    if len(peaks) == 0:
        return result
    
    peak_indices = peaks + min_idx
    peak_heights = properties['peak_heights']
    peak_freqs = freqs[peak_indices]
    
    # Sort by height
    sort_idx = np.argsort(peak_heights)[::-1]
    peak_freqs = peak_freqs[sort_idx]
    peak_heights = peak_heights[sort_idx]
    
    # For M-th power, the symbol rate appears as peaks at n * Rs
    # We look for the fundamental by finding the lowest peak that explains others
    candidate_rates = []
    for i, (freq, height) in enumerate(zip(peak_freqs, peak_heights)):
        is_harmonic = False
        for j in range(i):
            lower_freq = peak_freqs[j]
            ratio = freq / lower_freq
            n = round(ratio)
            if n >= 2 and abs(ratio - n) < 0.05:
                is_harmonic = True
                break
        if not is_harmonic:
            candidate_rates.append({
                "freq": float(freq),
                "height": float(height),
                "prominence": float(height / noise_floor) if noise_floor > 0 else 1.0
            })
    
    if not candidate_rates:
        result["symbol_rate_hz"] = float(peak_freqs[0])
        result["status"] = "low_confidence"
        result["confidence"] = 0.3
        return result
    
    candidate_rates.sort(key=lambda c: (c["prominence"] < 3.0, c["freq"]))
    best = candidate_rates[0]
    symbol_rate = best["freq"]
    prominence = best["prominence"]
    
    confidence = min(1.0, prominence / 10.0)
    
    # Check harmonics
    harmonic_count = 0
    for freq in peak_freqs:
        ratio = freq / symbol_rate
        n = round(ratio)
        if n >= 2 and abs(ratio - n) < 0.05:
            harmonic_count += 1
    
    if harmonic_count >= 1:
        confidence = min(1.0, confidence + 0.2 * harmonic_count)
    
    result["symbol_rate_hz"] = symbol_rate
    result["status"] = "estimated" if confidence > 0.5 else "low_confidence"
    result["confidence"] = float(confidence)
    
    return result


def _estimate_symbol_rate_envelope(iq_signal: np.ndarray, fs: float) -> Dict[str, Any]:
    """Estimate symbol rate using envelope power FFT (for QAM/ASK)."""
    result = {
        "symbol_rate_hz": 0.0,
        "status": "unavailable",
        "confidence": 0.0,
        "method": "envelope_fft"
    }
    
    if len(iq_signal) < 1024 or fs <= 0:
        return result
        
    N = min(len(iq_signal), 65536)
    sig = iq_signal[:N]
    
    # Envelope power
    p = np.abs(sig)**2
    p = p - np.mean(p)
    
    if np.std(p) < 1e-12:
        return result
    
    P_f = np.abs(np.fft.fft(p))
    P_f = P_f[:N//2]
    freqs = np.fft.fftfreq(N, 1/fs)[:N//2]
    
    min_freq_hz = max(100.0, fs * 0.001)
    min_idx = int(min_freq_hz * N / fs)
    min_idx = max(min_idx, 1)
    
    if min_idx >= len(P_f):
        return result
    
    noise_floor = np.median(P_f[min_idx:])
    threshold = max(noise_floor * 5, np.mean(P_f) * 3)
    min_distance = max(10, int(0.01 * N / 2))
    
    peaks, properties = find_peaks(P_f[min_idx:], height=threshold, distance=min_distance)
    
    if len(peaks) == 0:
        return result
    
    peak_indices = peaks + min_idx
    peak_heights = properties['peak_heights']
    peak_freqs = freqs[peak_indices]
    
    sort_idx = np.argsort(peak_heights)[::-1]
    peak_freqs = peak_freqs[sort_idx]
    peak_heights = peak_heights[sort_idx]
    
    candidate_rates = []
    for i, (freq, height) in enumerate(zip(peak_freqs, peak_heights)):
        is_harmonic = False
        for j in range(i):
            lower_freq = peak_freqs[j]
            ratio = freq / lower_freq
            n = round(ratio)
            if n >= 2 and abs(ratio - n) < 0.05:
                is_harmonic = True
                break
        if not is_harmonic:
            candidate_rates.append({
                "freq": float(freq),
                "height": float(height),
                "prominence": float(height / noise_floor) if noise_floor > 0 else 1.0
            })
    
    if not candidate_rates:
        result["symbol_rate_hz"] = float(peak_freqs[0])
        result["status"] = "low_confidence"
        result["confidence"] = 0.3
        return result
    
    candidate_rates.sort(key=lambda c: (c["prominence"] < 3.0, c["freq"]))
    best = candidate_rates[0]
    symbol_rate = best["freq"]
    prominence = best["prominence"]
    
    confidence = min(1.0, prominence / 10.0)
    
    harmonic_count = 0
    for freq in peak_freqs:
        ratio = freq / symbol_rate
        n = round(ratio)
        if n >= 2 and abs(ratio - n) < 0.05:
            harmonic_count += 1
    
    if harmonic_count >= 1:
        confidence = min(1.0, confidence + 0.2 * harmonic_count)
    
    result["symbol_rate_hz"] = symbol_rate
    result["status"] = "estimated" if confidence > 0.5 else "low_confidence"
    result["confidence"] = float(confidence)
    
    return result


def estimate_symbol_rate(iq_signal: np.ndarray, fs: float) -> Dict[str, Any]:
    """
    Multi-method symbol rate estimation.
    Tries envelope method first (QAM/ASK), then M-th power methods for PSK/FSK.
    Returns the most confident estimate.
    """
    # Try envelope method (works for amplitude-modulated signals)
    results: List[Dict[str, Any]] = []
    
    env_result = _estimate_symbol_rate_envelope(iq_signal, fs)
    if env_result["symbol_rate_hz"] > 0:
        results.append(env_result)
    
    # Try M-th power methods (works for constant-envelope PSK/FSK)
    # M=2 for BPSK/2-FSK, M=4 for QPSK/4-FSK, M=8 for 8PSK
    for M in [2, 4, 8]:
        mth_result = _estimate_symbol_rate_mth_power(iq_signal, fs, M)
        if mth_result["symbol_rate_hz"] > 0:
            results.append(mth_result)
    
    if not results:
        return {
            "symbol_rate_hz": 0.0,
            "status": "unavailable",
            "confidence": 0.0,
            "method": "none"
        }
    
    # Select best by confidence, then by method priority (prefer envelope for QAM, M=4 for QPSK)
    # For now, just pick highest confidence
    best = max(results, key=lambda r: r["confidence"])
    
    # If we have multiple with similar confidence, prefer lower symbol rate (more fundamental)
    max_conf = best["confidence"]
    candidates = [r for r in results if abs(r["confidence"] - max_conf) < 0.1]
    if len(candidates) > 1:
        best = min(candidates, key=lambda r: r["symbol_rate_hz"])
    
    return best