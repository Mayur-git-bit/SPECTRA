"""
Phase 5 Pipeline — Adaptive DSP Controller / Demodulation
==========================================================
Combines AI modulation prediction with DSP parameters to configure
and run the appropriate demodulator (PSK, FSK, or QAM).
"""

import logging
import numpy as np
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

from dsp.router import build_receiver_config, ReceiverConfig
from dsp.psk import psk_demodulate, PSKDemodResult
from dsp.fsk import fsk_demodulate, FSKDemodResult
from dsp.qam import qam_demodulate, QAMDemodResult

logger = logging.getLogger(__name__)


@dataclass
class DemodResult:
    """Unified demodulation result."""
    receiver: str                     # "PSK" | "FSK" | "QAM"
    modulation: str                   # Specific modulation (e.g., "QPSK", "16QAM")
    modulation_order: int
    status: str                       # completed | failed | not_started
    symbol_count: Optional[int]
    bit_count: Optional[int]
    evm_rms_pct: Optional[float]
    ber: Optional[float]
    constellation_i: Optional[list]
    constellation_q: Optional[list]
    timing_offset: Optional[float]
    carrier_phase: Optional[float]
    cfo_hz: Optional[float]
    frequency_separation_hz: Optional[float]  # For FSK
    bits_binary: Optional[str]        # Binary string
    bits_hex: Optional[str]           # Hex string


def run_phase5(
    raw_signal: np.ndarray,
    ai_result: Dict[str, Any],
    phase3_results: Dict[str, Any],
    sample_rate: float,
) -> Dict[str, Any]:
    """
    Run Phase 5 Adaptive Demodulation.
    
    Parameters:
        raw_signal: Raw complex64 IQ signal
        ai_result: Output from Phase 4 (modulation prediction)
        phase3_results: Output from Phase 3 (DSP parameters)
        sample_rate: Sampling rate in Hz
        
    Returns:
        Unified demodulation result dictionary
    """
    logger.info("[PHASE 5] Starting Adaptive Demodulation")
    
    # Build receiver configuration
    config = build_receiver_config(ai_result, phase3_results, sample_rate)
    
    # Route to appropriate demodulator
    if config.receiver_type == "PSK":
        result = psk_demodulate(raw_signal, config)
        demod_result = _psk_result_to_dict(result, config)
    elif config.receiver_type == "FSK":
        result = fsk_demodulate(raw_signal, config)
        demod_result = _fsk_result_to_dict(result, config)
    elif config.receiver_type == "QAM":
        result = qam_demodulate(raw_signal, config)
        demod_result = _qam_result_to_dict(result, config)
    else:
        logger.error(f"[PHASE 5] Unknown receiver type: {config.receiver_type}")
        demod_result = _empty_result(config)
    
    logger.info(f"[PHASE 5] Demodulation {demod_result['status']}: {demod_result['bit_count']} bits")
    
    return demod_result


def _psk_result_to_dict(result: PSKDemodResult, config: ReceiverConfig) -> Dict[str, Any]:
    """Convert PSK result to unified dict."""
    bits_binary = ""
    bits_hex = ""
    if len(result.bits) > 0:
        bits_binary = ''.join(str(b) for b in result.bits)
        # Convert to hex
        n = len(bits_binary)
        padding = (4 - n % 4) % 4
        bits_padded = bits_binary + '0' * padding
        bits_hex = hex(int(bits_padded, 2))[2:].upper()
        if padding:
            bits_hex = bits_hex[:-1]  # Remove last nibble if padded
    
    return {
        "receiver": "PSK",
        "modulation": config.modulation,
        "modulation_order": config.modulation_order,
        "status": result.status,
        "symbol_count": len(result.symbols) if len(result.symbols) > 0 else None,
        "bit_count": len(result.bits) if len(result.bits) > 0 else None,
        "evm_rms_pct": result.evm_rms_pct,
        "ber": result.ber,
        "constellation_i": result.constellation.real.tolist() if len(result.constellation) > 0 else None,
        "constellation_q": result.constellation.imag.tolist() if len(result.constellation) > 0 else None,
        "timing_offset": result.timing_offset,
        "carrier_phase": result.carrier_phase,
        "cfo_hz": result.cfo_hz,
        "frequency_separation_hz": None,
        "bits_binary": bits_binary if bits_binary else None,
        "bits_hex": bits_hex if bits_hex else None,
    }


def _fsk_result_to_dict(result: FSKDemodResult, config: ReceiverConfig) -> Dict[str, Any]:
    """Convert FSK result to unified dict."""
    bits_binary = ""
    bits_hex = ""
    if len(result.bits) > 0:
        bits_binary = ''.join(str(b) for b in result.bits)
        n = len(bits_binary)
        padding = (4 - n % 4) % 4
        bits_padded = bits_binary + '0' * padding
        bits_hex = hex(int(bits_padded, 2))[2:].upper()
        if padding:
            bits_hex = bits_hex[:-1]
    
    return {
        "receiver": "FSK",
        "modulation": config.modulation,
        "modulation_order": config.modulation_order,
        "status": result.status,
        "symbol_count": len(result.symbols) if len(result.symbols) > 0 else None,
        "bit_count": len(result.bits) if len(result.bits) > 0 else None,
        "evm_rms_pct": result.evm_rms_pct,
        "ber": result.ber,
        "constellation_i": None,  # FSK doesn't have traditional constellation
        "constellation_q": None,
        "timing_offset": result.timing_offset,
        "carrier_phase": result.carrier_phase,
        "cfo_hz": result.cfo_hz,
        "frequency_separation_hz": result.frequency_separation_hz,
        "bits_binary": bits_binary if bits_binary else None,
        "bits_hex": bits_hex if bits_hex else None,
    }


def _qam_result_to_dict(result: QAMDemodResult, config: ReceiverConfig) -> Dict[str, Any]:
    """Convert QAM result to unified dict."""
    bits_binary = ""
    bits_hex = ""
    if len(result.bits) > 0:
        bits_binary = ''.join(str(b) for b in result.bits)
        n = len(bits_binary)
        padding = (4 - n % 4) % 4
        bits_padded = bits_binary + '0' * padding
        bits_hex = hex(int(bits_padded, 2))[2:].upper()
        if padding:
            bits_hex = bits_hex[:-1]
    
    return {
        "receiver": "QAM",
        "modulation": config.modulation,
        "modulation_order": config.modulation_order,
        "status": result.status,
        "symbol_count": len(result.symbols) if len(result.symbols) > 0 else None,
        "bit_count": len(result.bits) if len(result.bits) > 0 else None,
        "evm_rms_pct": result.evm_rms_pct,
        "ber": result.ber,
        "constellation_i": result.constellation.real.tolist() if len(result.constellation) > 0 else None,
        "constellation_q": result.constellation.imag.tolist() if len(result.constellation) > 0 else None,
        "timing_offset": result.timing_offset,
        "carrier_phase": result.carrier_phase,
        "cfo_hz": result.cfo_hz,
        "frequency_separation_hz": None,
        "bits_binary": bits_binary if bits_binary else None,
        "bits_hex": bits_hex if bits_hex else None,
    }


def _empty_result(config: ReceiverConfig) -> Dict[str, Any]:
    """Return empty result for unknown receiver type."""
    return {
        "receiver": config.receiver_type,
        "modulation": config.modulation,
        "modulation_order": config.modulation_order,
        "status": "failed",
        "symbol_count": None,
        "bit_count": None,
        "evm_rms_pct": None,
        "ber": None,
        "constellation_i": None,
        "constellation_q": None,
        "timing_offset": None,
        "carrier_phase": None,
        "cfo_hz": None,
        "frequency_separation_hz": None,
        "bits_binary": None,
        "bits_hex": None,
    }