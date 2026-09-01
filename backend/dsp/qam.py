"""
Phase 5 — QAM Demodulator
==========================
Demodulates QAM (16QAM, 64QAM, 256QAM) signals.
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
    qam_constellation,
    qam_slice,
    calculate_evm,
)
from dsp.router import ReceiverConfig

logger = logging.getLogger(__name__)


@dataclass
class QAMDemodResult:
    """Result of QAM demodulation."""
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


def qam_symbol_to_bits(symbol_idx: int, order: int) -> np.ndarray:
    """Convert QAM symbol index to bits (Gray coding)."""
    # For square QAM, we can derive bits from I/Q components
    if order == 4:  # QPSK (same as 4QAM)
        gray = np.array([0, 1, 3, 2], dtype=np.uint8)
        val = gray[symbol_idx]
        return np.array([(val >> 1) & 1, val & 1], dtype=np.uint8)
    elif order == 16:
        # 16-QAM Gray mapping (standard)
        # I and Q each use 2-bit Gray code: 00, 01, 11, 10 for -3, -1, 1, 3
        # Symbol index maps to I/Q levels
        i_levels = np.array([-3, -1, 1, 3])
        q_levels = np.array([-3, -1, 1, 3])
        # Standard 16-QAM mapping
        i_idx = symbol_idx // 4
        q_idx = symbol_idx % 4
        # Gray decode I and Q separately
        i_gray = np.array([0, 1, 3, 2], dtype=np.uint8)
        q_gray = np.array([0, 1, 3, 2], dtype=np.uint8)
        i_val = i_gray[i_idx]
        q_val = q_gray[q_idx]
        return np.array([(i_val >> 1) & 1, i_val & 1, (q_val >> 1) & 1, q_val & 1], dtype=np.uint8)
    elif order == 64:
        # 64-QAM: 6 bits per symbol (3 bits I, 3 bits Q)
        # Gray coding for 8 levels: 000, 001, 011, 010, 110, 111, 101, 100
        gray8 = np.array([0, 1, 3, 2, 6, 7, 5, 4], dtype=np.uint8)
        i_idx = symbol_idx // 8
        q_idx = symbol_idx % 8
        i_val = gray8[i_idx]
        q_val = gray8[q_idx]
        bits = []
        for i in reversed(range(3)):
            bits.append((i_val >> i) & 1)
        for i in reversed(range(3)):
            bits.append((q_val >> i) & 1)
        return np.array(bits, dtype=np.uint8)
    elif order == 256:
        # 256-QAM: 8 bits per symbol (4 bits I, 4 bits Q)
        gray16 = np.array([0, 1, 3, 2, 6, 7, 5, 4, 12, 13, 15, 14, 10, 11, 9, 8], dtype=np.uint8)
        i_idx = symbol_idx // 16
        q_idx = symbol_idx % 16
        i_val = gray16[i_idx]
        q_val = gray16[q_idx]
        bits = []
        for i in reversed(range(4)):
            bits.append((i_val >> i) & 1)
        for i in reversed(range(4)):
            bits.append((q_val >> i) & 1)
        return np.array(bits, dtype=np.uint8)
    else:
        # Fallback: binary representation
        bits_per_symbol = int(np.log2(order))
        return np.array([(symbol_idx >> i) & 1 for i in reversed(range(bits_per_symbol))], dtype=np.uint8)


def qam_demodulate(
    iq_signal: np.ndarray,
    config: ReceiverConfig,
) -> QAMDemodResult:
    """
    Complete QAM demodulation chain:
    1. Coarse CFO correction
    2. Matched filtering (optional)
    3. Timing recovery (Gardner TED)
    4. Carrier recovery (Costas loop / decision-directed)
    5. Symbol sampling and decision
    6. Symbol-to-bit mapping (Gray coded)
    """
    M = config.modulation_order
    fs = config.sample_rate
    rs = config.symbol_rate
    sps = config.samples_per_symbol
    cfo_hz = config.cfo_hz
    phase_offset = config.phase_offset_rad
    
    logger.info(f"[QAM] Demodulating {config.modulation} (M={M}) with Fs={fs/1e6:.2f}MHz Rs={rs/1e3:.1f}k SPS={sps:.1f}")
    
    # 1. Coarse CFO correction
    signal = apply_cfo_correction(iq_signal, cfo_hz, fs)
    
    # 2. Static phase correction
    signal = apply_phase_correction(signal, phase_offset)
    
    # 3. Timing recovery (Gardner TED)
    symbol_indices, timing_errors, timing_offset = gardner_loop(signal, sps)
    
    if len(symbol_indices) == 0:
        logger.warning("[QAM] Timing recovery failed - insufficient samples")
        return QAMDemodResult(
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
    symbols_recovered = np.zeros(len(symbol_indices), dtype=complex)
    for i, idx in enumerate(symbol_indices):
        idx_int = int(np.floor(idx))
        frac = idx - idx_int
        if idx_int + 1 < len(signal):
            symbols_recovered[i] = signal[idx_int] * (1 - frac) + signal[idx_int + 1] * frac
        else:
            symbols_recovered[i] = signal[idx_int]
    
    # 4. Carrier recovery (Costas loop - decision-directed for QAM)
    symbols_corrected, phase_errors, carrier_phase = costas_loop(symbols_recovered, M)
    
    # 5. Symbol decision
    qam_const = qam_constellation(M)
    symbol_indices_decided = np.zeros(len(symbols_corrected), dtype=int)
    for i, sym in enumerate(symbols_corrected):
        # Find nearest constellation point
        distances = np.abs(qam_const - sym)
        symbol_indices_decided[i] = np.argmin(distances)
    
    # 6. Symbol-to-bit mapping
    bits_list = []
    for sym_idx in symbol_indices_decided:
        bits_list.extend(qam_symbol_to_bits(sym_idx, M))
    bits = np.array(bits_list, dtype=np.uint8)
    
    # Calculate EVM
    evm_rms = calculate_evm(symbols_corrected, qam_const)
    
    logger.info(f"[QAM] Demodulated {len(bits)} bits, {len(symbol_indices_decided)} symbols, EVM={evm_rms:.2f}%")
    
    return QAMDemodResult(
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