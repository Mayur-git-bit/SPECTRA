"""
Phase 5 — Synchronization Loops
================================
Implements carrier recovery, timing recovery, and phase correction
for PSK, FSK, and QAM demodulation.
"""

import logging
import numpy as np
from scipy import signal
from typing import Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    """Result of synchronization."""
    synced_signal: np.ndarray
    constellation: np.ndarray          # Recovered symbols (complex)
    symbol_indices: np.ndarray         # Sample indices of symbol decisions
    timing_offset: float               # Final timing offset (fractional samples)
    carrier_phase: float               # Final carrier phase (radians)
    cfo_hz: float                      # Final CFO estimate (Hz)
    evm_rms: Optional[float] = None    # Error Vector Magnitude (if reference available)
    status: str = "completed"


def apply_cfo_correction(iq_signal: np.ndarray, cfo_hz: float, fs: float) -> np.ndarray:
    """Apply coarse CFO correction."""
    if cfo_hz == 0.0:
        return iq_signal
    t = np.arange(len(iq_signal)) / fs
    correction = np.exp(-1j * 2 * np.pi * cfo_hz * t)
    return iq_signal * correction


def apply_phase_correction(iq_signal: np.ndarray, phase_rad: float) -> np.ndarray:
    """Apply static phase correction."""
    if phase_rad == 0.0:
        return iq_signal
    return iq_signal * np.exp(-1j * phase_rad)


# ============================================================
# TIMING RECOVERY - Gardner TED
# ============================================================

def gardner_ted(samples: np.ndarray, sps: float) -> np.ndarray:
    """
    Gardner Timing Error Detector.
    Works for BPSK, QPSK, OQPSK, and other real/imag symmetric constellations.
    
    TED output: e[n] = Re{(x[n] - x[n-2]) * conj(x[n-1])}
    where samples are at 2 samples per symbol.
    
    Returns timing error per symbol period.
    """
    if len(samples) < 4:
        return np.array([])
    
    # Gardner operates at 2 samples per symbol
    # If we have SPS samples/symbol, we need to interpolate or decimate
    # For simplicity, assume we operate at the actual sample rate with SPS
    
    step = max(1, int(round(sps / 2)))  # step to get ~2 samples per symbol
    if step < 1:
        step = 1
    
    errors = []
    # Need at least 3 samples (n, n-1, n-2) at the 2x rate
    for i in range(2 * step, len(samples) - step, step):
        x_n = samples[i]
        x_n1 = samples[i - step]
        x_n2 = samples[i - 2 * step]
        
        error = np.real((x_n - x_n2) * np.conj(x_n1))
        errors.append(error)
    
    return np.array(errors)


def gardner_loop(
    iq_signal: np.ndarray,
    sps: float,
    loop_bw: float = 0.01,
    damping: float = 0.707,
) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Gardner timing recovery loop.
    Operates at 2 samples per symbol (Gardner TED requirement).
    
    Returns:
        symbol_indices: Sample indices of symbol decisions
        timing_errors: Timing error history
        final_timing_offset: Final fractional timing offset
    """
    if len(iq_signal) < 100 or sps < 1.5:
        return np.array([]), np.array([]), 0.0
    
    # Loop filter coefficients (2nd order)
    K1 = -4 * damping * loop_bw
    K2 = -4 * loop_bw**2
    
    N = len(iq_signal)
    
    # Gardner TED operates at 2 samples per symbol
    # So we need spacing of sps/2 between TED samples
    ted_spacing = max(1, int(round(sps / 2)))
    
    # Generate initial symbol indices (one per symbol)
    num_symbols = int(N / sps)
    symbol_indices = np.arange(0, num_symbols * sps, sps).astype(float)
    
    timing_errors = []
    phase_acc = 0.0
    freq_acc = 0.0
    
    # Start from first symbol that has enough room for TED
    # Need: idx - 2*ted_spacing >= 0 and idx + ted_spacing < N
    start_idx = 2 * ted_spacing
    
    for i in range(num_symbols):
        idx = int(round(symbol_indices[i]))
        if idx < start_idx:
            continue
        if idx + ted_spacing >= N:
            break
            
        # Gardner TED at 2 samples per symbol
        x_n = iq_signal[idx + ted_spacing]
        x_n1 = iq_signal[idx]
        x_n2 = iq_signal[idx - ted_spacing]
        
        error = np.real((x_n - x_n2) * np.conj(x_n1))
        timing_errors.append(error)
        
        # Loop filter
        freq_acc += K2 * error
        phase_acc += freq_acc + K1 * error
        
        # Update next symbol index
        if i + 1 < num_symbols:
            symbol_indices[i + 1] = symbol_indices[i] + sps + phase_acc
    
    final_offset = phase_acc / max(1, len(timing_errors))
    
    return symbol_indices[:len(timing_errors)], np.array(timing_errors), float(final_offset)


# ============================================================
# CARRIER RECOVERY - Costas Loop (for PSK/QAM)
# ============================================================

def costas_loop(
    iq_signal: np.ndarray,
    modulation_order: int,
    loop_bw: float = 0.01,
    damping: float = 0.707,
) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Costas Loop for carrier recovery.
    Works for M-PSK (BPSK, QPSK, 8PSK, etc.) and QAM.
    
    For QPSK: phase_error = sign(I) * Q - sign(Q) * I
    For BPSK: phase_error = I * Q
    For M-PSK: phase_error = arg(x[n]^M) / M
    """
    if len(iq_signal) < 100:
        return iq_signal, np.array([]), 0.0
    
    # Loop filter coefficients
    K1 = -4 * damping * loop_bw
    K2 = -4 * loop_bw**2
    
    phase_acc = 0.0
    freq_acc = 0.0
    phase_errors = []
    
    corrected = iq_signal.copy()
    
    for i in range(len(iq_signal)):
        x = corrected[i]
        
        # Phase detector
        if modulation_order == 2:  # BPSK
            error = np.real(x) * np.imag(x)
        elif modulation_order == 4:  # QPSK
            error = np.sign(np.real(x)) * np.imag(x) - np.sign(np.imag(x)) * np.real(x)
        else:  # M-PSK / QAM - use decision-directed
            # Make hard decision to nearest constellation point
            decision = slice_decision(x, modulation_order)
            error = np.imag(x * np.conj(decision))
        
        phase_errors.append(error)
        
        # Loop filter
        freq_acc += K2 * error
        phase_acc += freq_acc + K1 * error
        
        # Apply correction to next sample (or current for decision-directed)
        if i + 1 < len(corrected):
            corrected[i + 1] *= np.exp(-1j * phase_acc)
    
    final_phase = phase_acc
    return corrected, np.array(phase_errors), float(final_phase)


def slice_decision(sample: complex, modulation_order: int) -> complex:
    """Make hard decision to nearest PSK constellation point."""
    if modulation_order == 2:  # BPSK
        return 1.0 if np.real(sample) > 0 else -1.0
    elif modulation_order == 4:  # QPSK
        i = 1.0 if np.real(sample) > 0 else -1.0
        q = 1.0 if np.imag(sample) > 0 else -1.0
        return (i + 1j * q) / np.sqrt(2)
    else:  # M-PSK
        phase = np.angle(sample)
        nearest = round(phase / (2 * np.pi / modulation_order))
        return np.exp(1j * nearest * 2 * np.pi / modulation_order)


# ============================================================
# FSK DEMODULATION - Frequency Discriminator
# ============================================================

def fsk_discriminator(iq_signal: np.ndarray, fs: float) -> np.ndarray:
    """
    FM/Frequency Discriminator for FSK.
    y[n] = x[n] * conj(x[n-1])
    phase_diff = angle(y[n])
    freq = phase_diff * fs / (2*pi)
    """
    if len(iq_signal) < 2:
        return np.array([])
    
    # Differential phase
    prod = iq_signal[1:] * np.conj(iq_signal[:-1])
    phase_diff = np.angle(prod)
    
    # Instantaneous frequency
    freq = phase_diff * fs / (2 * np.pi)
    
    return freq


def fsk_symbol_decisions(
    inst_freq: np.ndarray,
    sps: float,
    modulation_order: int = 2,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Convert instantaneous frequency to symbol decisions.
    
    For binary FSK: compare to threshold between the two frequencies
    For M-FSK: cluster frequencies into M levels
    """
    if len(inst_freq) == 0:
        return np.array([]), np.array([])
    
    # Estimate frequency levels from histogram/clustering
    if modulation_order == 2:
        # Binary FSK: threshold at midpoint
        f_min, f_max = np.min(inst_freq), np.max(inst_freq)
        threshold = (f_min + f_max) / 2
        decisions = (inst_freq > threshold).astype(int)
    else:
        # M-FSK: k-means clustering on frequencies
        from scipy.cluster.vq import kmeans, vq
        centroids, _ = kmeans(inst_freq, modulation_order)
        centroids = np.sort(centroids)
        decisions, _ = vq(inst_freq, centroids)
    
    # Downsample to symbol rate (average over symbol period)
    step = int(round(sps))
    if step < 1:
        step = 1
    
    symbol_decisions = []
    for i in range(0, len(decisions) - step, step):
        symbol_decisions.append(decisions[i:i+step].mean())
    
    return np.array(symbol_decisions), decisions


# ============================================================
# QAM CONSTELLATION DECISION
# ============================================================

def qam_constellation(order: int) -> np.ndarray:
    """Generate normalized QAM constellation points."""
    if order == 4:
        # QPSK
        return np.array([1+1j, 1-1j, -1+1j, -1-1j]) / np.sqrt(2)
    elif order == 16:
        # 16-QAM normalized to unit average power
        levels = np.array([-3, -1, 1, 3])
        I, Q = np.meshgrid(levels, levels)
        const = (I + 1j * Q).flatten()
        # Normalize to unit average power
        const = const / np.sqrt(np.mean(np.abs(const)**2))
        return const
    elif order == 64:
        levels = np.array([-7, -5, -3, -1, 1, 3, 5, 7])
        I, Q = np.meshgrid(levels, levels)
        const = (I + 1j * Q).flatten()
        const = const / np.sqrt(np.mean(np.abs(const)**2))
        return const
    elif order == 256:
        levels = np.arange(-15, 16, 2)
        I, Q = np.meshgrid(levels, levels)
        const = (I + 1j * Q).flatten()
        const = const / np.sqrt(np.mean(np.abs(const)**2))
        return const
    else:
        # Default to QPSK
        return qam_constellation(4)


def qam_slice(sample: complex, constellation: np.ndarray) -> complex:
    """Find nearest constellation point."""
    distances = np.abs(constellation - sample)
    return constellation[np.argmin(distances)]


def calculate_evm(received: np.ndarray, constellation: np.ndarray) -> float:
    """Calculate RMS EVM in percent."""
    if len(received) == 0:
        return 0.0
    
    decisions = np.array([qam_slice(s, constellation) for s in received])
    errors = received - decisions
    evm_rms = np.sqrt(np.mean(np.abs(errors)**2) / np.mean(np.abs(decisions)**2))
    return float(evm_rms * 100)  # Percent