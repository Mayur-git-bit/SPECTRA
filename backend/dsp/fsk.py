"""
Phase 5 — FSK Demodulator
==========================
Demodulates FSK (2FSK, 4FSK, GFSK, GMSK) signals using frequency discriminator.
"""

import logging
import numpy as np
from typing import Dict, Any, Optional
from dataclasses import dataclass

from dsp.synchronization import (
    apply_cfo_correction,
    apply_phase_correction,
    fsk_discriminator,
    fsk_symbol_decisions,
    gardner_loop,
)
from dsp.router import ReceiverConfig

logger = logging.getLogger(__name__)


@dataclass
class FSKDemodResult:
    """Result of FSK demodulation."""
    bits: np.ndarray                 # Demodulated bits (0/1)
    symbols: np.ndarray              # Demodulated symbol indices
    instantaneous_freq: np.ndarray   # Instantaneous frequency trace
    symbol_indices: np.ndarray       # Sample indices of symbol decisions
    evm_rms_pct: Optional[float]     # Not applicable for FSK
    ber: Optional[float]             # BER (if reference available)
    status: str                      # completed | failed | partial
    timing_offset: float
    carrier_phase: float
    cfo_hz: float
    frequency_separation_hz: float   # Estimated tone separation


def fsk_demodulate(
    iq_signal: np.ndarray,
    config: ReceiverConfig,
) -> FSKDemodResult:
    """
    Complete FSK demodulation chain:
    1. Coarse CFO correction
    2. Frequency discriminator (differential phase)
    3. Timing recovery on frequency trajectory
    4. Symbol decisions via frequency clustering/thresholding
    5. Symbol-to-bit mapping
    """
    M = config.modulation_order  # 2 for 2FSK, 4 for 4FSK, etc.
    fs = config.sample_rate
    rs = config.symbol_rate
    sps = config.samples_per_symbol
    cfo_hz = config.cfo_hz
    phase_offset = config.phase_offset_rad
    
    logger.info(f"[FSK] Demodulating {config.modulation} (M={M}) with Fs={fs/1e6:.2f}MHz Rs={rs/1e3:.1f}k SPS={sps:.1f}")
    
    # 1. Coarse CFO correction
    signal = apply_cfo_correction(iq_signal, cfo_hz, fs)
    
    # 2. Static phase correction
    signal = apply_phase_correction(signal, phase_offset)
    
    # 3. Frequency discriminator
    # y[n] = x[n] * conj(x[n-1]), phase_diff = angle(y[n])
    # inst_freq = phase_diff * fs / (2*pi)
    inst_freq = fsk_discriminator(signal, fs)
    
    if len(inst_freq) == 0:
        logger.warning("[FSK] Frequency discriminator failed")
        return FSKDemodResult(
            bits=np.array([], dtype=np.uint8),
            symbols=np.array([], dtype=int),
            instantaneous_freq=np.array([]),
            symbol_indices=np.array([]),
            evm_rms_pct=None,
            ber=None,
            status="failed",
            timing_offset=0.0,
            carrier_phase=0.0,
            cfo_hz=cfo_hz,
            frequency_separation_hz=0.0,
        )
    
    # Smooth the instantaneous frequency (differentiation amplifies noise)
    # Use a simple moving average
    smooth_window = max(1, int(sps / 4))
    if smooth_window > 1:
        kernel = np.ones(smooth_window) / smooth_window
        inst_freq_smooth = np.convolve(inst_freq, kernel, mode='same')
    else:
        inst_freq_smooth = inst_freq
    
    # 4. Timing recovery on frequency trajectory
    # Use Gardner TED on the complex signal, not the frequency
    # But we can also use the frequency signal for timing
    symbol_indices, timing_errors, timing_offset = gardner_loop(signal, sps)
    
    if len(symbol_indices) == 0:
        # Fallback: use uniform sampling at symbol rate
        num_symbols = int(len(inst_freq_smooth) / sps)
        symbol_indices = np.arange(0, num_symbols * sps, sps)
        timing_offset = 0.0
    
    # 5. Symbol decisions from instantaneous frequency
    # Sample frequency at symbol timing instants
    freq_at_symbols = []
    for idx in symbol_indices:
        idx_int = int(round(idx))
        if idx_int < len(inst_freq_smooth):
            freq_at_symbols.append(inst_freq_smooth[idx_int])
        else:
            freq_at_symbols.append(inst_freq_smooth[-1])
    
    freq_at_symbols = np.array(freq_at_symbols)
    
    # Cluster frequencies into M levels
    symbol_decisions, _ = fsk_symbol_decisions(
        freq_at_symbols, 
        sps, 
        modulation_order=M
    )
    
    if len(symbol_decisions) == 0:
        logger.warning("[FSK] No symbol decisions")
        return FSKDemodResult(
            bits=np.array([], dtype=np.uint8),
            symbols=np.array([], dtype=int),
            instantaneous_freq=inst_freq_smooth,
            symbol_indices=symbol_indices,
            evm_rms_pct=None,
            ber=None,
            status="failed",
            timing_offset=timing_offset,
            carrier_phase=0.0,
            cfo_hz=cfo_hz,
            frequency_separation_hz=0.0,
        )
    
    # Round to nearest integer symbol
    symbol_indices_decided = np.round(symbol_decisions).astype(int)
    symbol_indices_decided = np.clip(symbol_indices_decided, 0, M - 1)
    
    # 6. Symbol-to-bit mapping
    bits_list = []
    bits_per_symbol = int(np.log2(M)) if M > 1 else 1
    for sym_idx in symbol_indices_decided:
        if bits_per_symbol == 1:
            bits_list.append(sym_idx)
        else:
            # Gray coding for M-FSK
            gray = sym_idx ^ (sym_idx >> 1)
            for i in reversed(range(bits_per_symbol)):
                bits_list.append((gray >> i) & 1)
    bits = np.array(bits_list, dtype=np.uint8)
    
    # Estimate frequency separation
    unique_freqs = np.unique(freq_at_symbols)
    if len(unique_freqs) >= 2:
        freq_separation = np.max(unique_freqs) - np.min(unique_freqs)
    else:
        freq_separation = 0.0
    
    logger.info(f"[FSK] Demodulated {len(bits)} bits, {len(symbol_indices_decided)} symbols, freq_sep={freq_separation:.1f}Hz")
    
    return FSKDemodResult(
        bits=bits,
        symbols=symbol_indices_decided,
        instantaneous_freq=inst_freq_smooth,
        symbol_indices=symbol_indices,
        evm_rms_pct=None,
        ber=None,
        status="completed",
        timing_offset=timing_offset,
        carrier_phase=0.0,
        cfo_hz=cfo_hz,
        frequency_separation_hz=freq_separation,
    )