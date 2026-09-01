"""
Phase 5 — PSK Demodulator
==========================
Demodulates BPSK, QPSK, 8PSK, and higher-order PSK signals.
"""

import logging
import numpy as np
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from dsp.synchronization import (
    apply_cfo_correction,
    apply_phase_correction,
    gardner_loop,
    costas_loop,
    slice_decision,
    qam_constellation,
    calculate_evm,
)
from dsp.router import ReceiverConfig

logger = logging.getLogger(__name__)


@dataclass
class PSKDemodResult:
    """Result of PSK demodulation."""
    bits: np.ndarray                 # Demodulated bits (0/1)
    symbols: np.ndarray              # Demodulated symbol indices
    constellation: np.ndarray        # Recovered constellation points
    symbol_indices: np.ndarray       # Sample indices of symbol decisions
    evm_rms_pct: Optional[float]     # EVM in percent
    ber: Optional[float]             # BER (if reference available)
    status: str                      # completed | failed | partial
    timing_offset: float
    carrier_phase: float
    cfo_hz: float


def psk_constellation(order: int) -> np.ndarray:
    """Generate PSK constellation points."""
    if order == 2:  # BPSK
        return np.array([1.0, -1.0])
    phases = np.arange(order) * 2 * np.pi / order
    return np.exp(1j * phases)


def psk_symbol_to_bits(symbol_idx: int, order: int) -> np.ndarray:
    """Convert PSK symbol index to bits (Gray coding)."""
    if order == 2:  # BPSK
        return np.array([symbol_idx], dtype=np.uint8)
    elif order == 4:  # QPSK - Gray coded
        # 0: 00, 1: 01, 2: 11, 3: 10 (Gray)
        gray = np.array([0, 1, 3, 2], dtype=np.uint8)
        val = gray[symbol_idx]
        return np.array([(val >> 1) & 1, val & 1], dtype=np.uint8)
    elif order == 8:  # 8PSK - Gray coded
        gray = np.array([0, 1, 3, 2, 6, 7, 5, 4], dtype=np.uint8)
        val = gray[symbol_idx]
        return np.array([(val >> 2) & 1, (val >> 1) & 1, val & 1], dtype=np.uint8)
    else:
        # Generic Gray coding for M-PSK
        bits_per_symbol = int(np.log2(order))
        gray = symbol_idx ^ (symbol_idx >> 1)
        return np.array([(gray >> i) & 1 for i in reversed(range(bits_per_symbol))], dtype=np.uint8)


def psk_demodulate(
    iq_signal: np.ndarray,
    config: ReceiverConfig,
) -> PSKDemodResult:
    """
    Complete PSK demodulation chain:
    1. Coarse CFO correction
    2. Matched filtering (optional)
    3. Timing recovery (Gardner TED)
    4. Carrier recovery (Costas loop)
    5. Symbol sampling and decision
    6. Symbol-to-bit mapping
    """
    M = config.modulation_order
    fs = config.sample_rate
    rs = config.symbol_rate
    sps = config.samples_per_symbol
    cfo_hz = config.cfo_hz
    phase_offset = config.phase_offset_rad
    
    logger.info(f"[PSK] Demodulating {config.modulation} (M={M}) with Fs={fs/1e6:.2f}MHz Rs={rs/1e3:.1f}k SPS={sps:.1f}")
    
    # 1. Coarse CFO correction
    signal = apply_cfo_correction(iq_signal, cfo_hz, fs)
    
    # 2. Static phase correction (from Phase 3 estimate)
    signal = apply_phase_correction(signal, phase_offset)
    
    # 3. Timing recovery (Gardner TED)
    symbol_indices, timing_errors, timing_offset = gardner_loop(signal, sps)
    
    if len(symbol_indices) == 0:
        logger.warning("[PSK] Timing recovery failed - insufficient samples")
        return PSKDemodResult(
            bits=np.array([], dtype=np.uint8),
            symbols=np.array([], dtype=int),
            constellation=np.array([], dtype=complex),
            symbol_indices=np.array([]),
            evm_rms_pct=None,
            ber=None,
            status="failed",
            timing_offset=0.0,
            carrier_phase=0.0,
            cfo_hz=cfo_hz,
        )
    
    # Sample symbols at recovered timing instants
    # Use linear interpolation for fractional indices
    symbols_recovered = np.zeros(len(symbol_indices), dtype=complex)
    for i, idx in enumerate(symbol_indices):
        idx_int = int(np.floor(idx))
        frac = idx - idx_int
        if idx_int + 1 < len(signal):
            symbols_recovered[i] = signal[idx_int] * (1 - frac) + signal[idx_int + 1] * frac
        else:
            symbols_recovered[i] = signal[idx_int]
    
    # 4. Carrier recovery (Costas loop) on symbol-rate samples
    symbols_corrected, phase_errors, carrier_phase = costas_loop(symbols_recovered, M)
    
    # 5. Symbol decision
    psk_const = psk_constellation(M)
    symbol_indices_decided = np.zeros(len(symbols_corrected), dtype=int)
    for i, sym in enumerate(symbols_corrected):
        # Find nearest constellation point
        distances = np.abs(psk_const - sym)
        symbol_indices_decided[i] = np.argmin(distances)
    
    # 6. Symbol-to-bit mapping
    bits_list = []
    for sym_idx in symbol_indices_decided:
        bits_list.extend(psk_symbol_to_bits(sym_idx, M))
    bits = np.array(bits_list, dtype=np.uint8)
    
    # Calculate EVM (if constellation is known)
    evm_rms = calculate_evm(symbols_corrected, psk_const)
    
    logger.info(f"[PSK] Demodulated {len(bits)} bits, {len(symbol_indices_decided)} symbols, EVM={evm_rms:.2f}%")
    
    return PSKDemodResult(
        bits=bits,
        symbols=symbol_indices_decided,
        constellation=symbols_corrected,
        symbol_indices=symbol_indices,
        evm_rms_pct=evm_rms,
        ber=None,  # No reference bits available
        status="completed",
        timing_offset=timing_offset,
        carrier_phase=carrier_phase,
        cfo_hz=cfo_hz,
    )