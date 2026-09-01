"""
Phase 3.5 — Timing & Phase Offset Estimation
=============================================
Estimates phase offset and timing offset (Gardner TED).
"""

import numpy as np
from typing import Dict, Any, Tuple


def estimate_phase_offset(iq_signal: np.ndarray, modulation_order: int = 4) -> Dict[str, Any]:
    """
    Estimate constant phase offset using M-th power method.
    
    Returns:
        Dict with phase_offset_rad, status, confidence
    """
    result = {
        "phase_offset_rad": 0.0,
        "status": "unavailable",
        "confidence": 0.0,
        "method": "mth_power"
    }
    
    if len(iq_signal) < 1024:
        return result
        
    N = min(len(iq_signal), 16384)
    sig = iq_signal[:N]
    
    # M-th power
    sig_m = sig ** modulation_order
    
    # The angle of the mean of sig^M gives M * phase_offset
    mean_val = np.mean(sig_m)
    
    if np.abs(mean_val) < 1e-12:
        return result
    
    phase = np.angle(mean_val) / modulation_order
    
    # Confidence based on how concentrated the constellation is after M-th power
    # Higher |mean| = tighter clustering = more reliable
    magnitude = np.abs(mean_val)
    rms = np.sqrt(np.mean(np.abs(sig_m)**2))
    concentration = magnitude / rms if rms > 0 else 0.0
    
    confidence = min(1.0, concentration * 2.0)  # Scale factor
    
    result["phase_offset_rad"] = float(phase)
    result["status"] = "estimated" if confidence > 0.3 else "low_confidence"
    result["confidence"] = float(confidence)
    
    return result


def correct_phase(iq_signal: np.ndarray, phase_rad: float) -> np.ndarray:
    """Correct phase offset."""
    if phase_rad == 0.0:
        return iq_signal
    return iq_signal * np.exp(-1j * phase_rad)


def gardner_ted(samples: np.ndarray, sps: float) -> np.ndarray:
    """
    Gardner Timing Error Detector.
    Works for BPSK, QPSK, and other PSK modulations.
    Requires at least 2 samples per symbol.
    
    TED output: e[n] = Re{(x[n] - x[n-2]) * conj(x[n-1])}
    where samples are at 2x oversampling (sps >= 2).
    
    Returns timing error per symbol.
    """
    if len(samples) < 4:
        return np.array([])
    
    # Gardner TED operates at 2 samples per symbol
    # If sps > 2, we can decimate or interpolate
    # For simplicity, assume we have at least 2 sps
    
    errors = []
    # Process at symbol rate: need 3 samples per error (n, n-1, n-2)
    # at 2x oversampling, each symbol has 2 samples
    step = max(1, int(round(sps / 2)))  # step in samples per symbol
    
    for i in range(2 * step, len(samples) - step, step):
        x_n = samples[i]
        x_n1 = samples[i - step]
        x_n2 = samples[i - 2 * step]
        
        error = np.real((x_n - x_n2) * np.conj(x_n1))
        errors.append(error)
    
    return np.array(errors)


def mueller_muller_ted(samples: np.ndarray, sps: float) -> np.ndarray:
    """
    Mueller-Muller Timing Error Detector.
    Decision-directed, works for QAM/PSK.
    Requires symbol decisions (not available here, so simplified).
    """
    # Placeholder - requires decisions
    return np.array([])


def estimate_timing_offset(iq_signal: np.ndarray, fs: float) -> Dict[str, Any]:
    """
    Estimate timing offset (fractional sample delay) using Gardner TED.
    Requires symbol rate estimate to know SPS.
    
    Returns:
        Dict with timing_offset (fractional samples), status, confidence
    """
    result = {
        "timing_offset": 0.0,
        "status": "unavailable",
        "confidence": 0.0,
        "method": "gardner_ted"
    }
    
    if len(iq_signal) < 2048 or fs <= 0:
        return result
    
    # We need a rough symbol rate estimate to compute SPS
    # For now, use a simple approach: assume we're looking for symbol-rate periodicity
    # in the signal envelope
    
    # Use autocorrelation of envelope to find symbol period
    env = np.abs(iq_signal)
    env = env - np.mean(env)
    
    # Compute autocorrelation
    max_lag = min(len(env) // 4, 1000)
    acf = np.correlate(env, env, mode='full')
    acf = acf[len(env)-1:len(env)-1+max_lag]
    
    # Find peaks in ACF (excluding lag 0)
    from scipy.signal import find_peaks
    peaks, properties = find_peaks(acf[1:], height=np.max(acf)*0.3, distance=10)
    
    if len(peaks) == 0:
        return result
    
    # First peak after 0 is candidate symbol period
    peak_lag = peaks[0] + 1  # +1 because we skipped lag 0
    
    if peak_lag < 2:
        return result
    
    # Symbol period in samples = peak_lag
    sps_est = peak_lag
    
    # Now run Gardner TED at this SPS
    errors = gardner_ted(iq_signal, sps_est)
    
    if len(errors) < 10:
        return result
    
    # Average timing error (normalized to [-0.5, 0.5] samples)
    mean_error = np.mean(errors)
    std_error = np.std(errors)
    
    # Normalize by signal amplitude
    sig_rms = np.sqrt(np.mean(np.abs(iq_signal)**2))
    normalized_error = mean_error / (sig_rms**2 + 1e-12)
    
    # Timing offset in fractional samples (Gardner output is in volts^2, need calibration)
    # For normalized signal, error roughly proportional to timing offset
    timing_offset = normalized_error * 0.5  # Rough scaling
    
    # Clamp to reasonable range
    timing_offset = np.clip(timing_offset, -0.5, 0.5)
    
    # Confidence based on error consistency
    if std_error > 0:
        confidence = min(1.0, abs(mean_error) / (std_error + 1e-12) / 5.0)
    else:
        confidence = 0.5
    
    result["timing_offset"] = float(timing_offset)
    result["sps_estimate"] = float(sps_est)
    result["status"] = "estimated" if confidence > 0.3 else "low_confidence"
    result["confidence"] = float(confidence)
    
    return result