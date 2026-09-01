"""
Phase 5 — DSP Router
====================
Routes the signal to the appropriate demodulator based on AI prediction
and extracted DSP parameters.
"""

import logging
from typing import Dict, Any, Optional, Literal
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# Modulation family to demodulator mapping
MODULATION_TO_RECEIVER = {
    "BPSK": "PSK",
    "QPSK": "PSK", 
    "8PSK": "PSK",
    "16PSK": "PSK",
    "32PSK": "PSK",
    "FSK": "FSK",
    "GFSK": "FSK",
    "GMSK": "FSK",
    "2FSK": "FSK",
    "4FSK": "FSK",
    "QAM": "QAM",
    "16QAM": "QAM",
    "32QAM": "QAM",
    "64QAM": "QAM",
    "128QAM": "QAM",
    "256QAM": "QAM",
}

# Modulation order mapping (for PSK/QAM)
MODULATION_ORDER = {
    "BPSK": 2,
    "QPSK": 4,
    "8PSK": 8,
    "16PSK": 16,
    "32PSK": 32,
    "16QAM": 16,
    "32QAM": 32,
    "64QAM": 64,
    "128QAM": 128,
    "256QAM": 256,
}


@dataclass
class ReceiverConfig:
    """Configuration for the demodulator."""
    receiver_type: Literal["PSK", "FSK", "QAM"]
    modulation: str                    # Specific modulation (e.g., "QPSK", "16QAM")
    modulation_order: int              # M for M-PSK or M-QAM
    sample_rate: float                 # Hz
    symbol_rate: float                 # symbols/sec
    samples_per_symbol: float          # SPS
    cfo_hz: float                      # Carrier frequency offset (Hz)
    phase_offset_rad: float            # Phase offset (radians)
    timing_offset: float               # Timing offset (fractional samples)
    bandwidth_hz: float                # Signal bandwidth (Hz)
    snr_db: float                      # Signal-to-noise ratio (dB)
    snr_status: str                    # SNR reliability status
    symbol_rate_status: str            # Symbol rate reliability status
    cfo_status: str                    # CFO reliability status


def determine_receiver_type(modulation_prediction: str) -> str:
    """
    Map AI modulation prediction to receiver type.
    
    AI predicts families: FSK, QAM, QPSK, PSK
    Router maps to: FSK, QAM, PSK receivers
    """
    # Direct family mapping
    if modulation_prediction in ["FSK", "QAM"]:
        return modulation_prediction
    elif modulation_prediction in ["QPSK", "PSK"]:
        return "PSK"
    else:
        # Default to PSK for unknown
        logger.warning(f"[ROUTER] Unknown modulation prediction: {modulation_prediction}, defaulting to PSK")
        return "PSK"


def get_modulation_order(modulation: str, receiver_type: str) -> int:
    """
    Get modulation order M for M-PSK or M-QAM.
    For FSK, returns 2 (binary) as default.
    """
    if modulation in MODULATION_ORDER:
        return MODULATION_ORDER[modulation]
    
    # For family-level predictions, we need to infer order
    if receiver_type == "PSK":
        # Default to QPSK (4) for PSK family
        return 4
    elif receiver_type == "QAM":
        # Default to 16QAM for QAM family
        return 16
    elif receiver_type == "FSK":
        return 2  # Binary FSK default
    
    return 4


def build_receiver_config(
    ai_result: Dict[str, Any],
    phase3_results: Dict[str, Any],
    sample_rate: float,
) -> ReceiverConfig:
    """
    Build receiver configuration from AI prediction and DSP parameters.
    """
    # Get AI prediction
    ai_modulation = ai_result.get("prediction", "PSK")
    ai_confidence = ai_result.get("confidence", 0.0)
    ai_probabilities = ai_result.get("probabilities", {})
    
    # Determine receiver type
    receiver_type = determine_receiver_type(ai_modulation)
    
    # Get modulation order
    mod_order = get_modulation_order(ai_modulation, receiver_type)
    
    # Extract DSP parameters with fallbacks
    symbol_rate = phase3_results.get("symbol_rate_hz", 0.0)
    sps = phase3_results.get("samples_per_symbol", 0.0)
    cfo_hz = phase3_results.get("cfo_hz", 0.0)
    phase_offset = phase3_results.get("phase_offset_rad", 0.0)
    timing_offset = phase3_results.get("timing_offset", 0.0)
    bandwidth = phase3_results.get("bandwidth_hz", 0.0)
    snr_db = phase3_results.get("snr_db", 0.0)
    
    # If symbol rate unavailable, estimate from bandwidth
    if symbol_rate <= 0 and bandwidth > 0:
        # Rough estimate: BW ≈ symbol_rate * (1 + rolloff), assume rolloff=0.35
        symbol_rate = bandwidth / 1.35
        sps = sample_rate / symbol_rate if symbol_rate > 0 else 0.0
    
    # If still no SPS, use a reasonable default
    if sps <= 0:
        sps = 4.0  # Default 4 samples per symbol
        symbol_rate = sample_rate / sps if sample_rate > 0 else 0.0
    
    # Status fields
    snr_status = phase3_results.get("snr_status", "estimated")
    symbol_rate_status = phase3_results.get("symbol_rate_status", "unavailable")
    cfo_status = phase3_results.get("cfo_status", "unavailable")
    
    logger.info(f"[ROUTER] Receiver: {receiver_type} | Modulation: {ai_modulation} (order={mod_order}) | "
                f"Fs={sample_rate/1e6:.2f}MHz Rs={symbol_rate/1e3:.1f}k SPS={sps:.1f} | "
                f"CFO={cfo_hz:.0f}Hz SNR={snr_db:.1f}dB")
    
    return ReceiverConfig(
        receiver_type=receiver_type,
        modulation=ai_modulation,
        modulation_order=mod_order,
        sample_rate=sample_rate,
        symbol_rate=symbol_rate,
        samples_per_symbol=sps,
        cfo_hz=cfo_hz,
        phase_offset_rad=phase_offset,
        timing_offset=timing_offset,
        bandwidth_hz=bandwidth,
        snr_db=snr_db,
        snr_status=snr_status,
        symbol_rate_status=symbol_rate_status,
        cfo_status=cfo_status,
    )


def log_config(config: ReceiverConfig):
    """Log receiver configuration for debugging."""
    logger.info(f"[ROUTER] Config: type={config.receiver_type} mod={config.modulation} "
                f"M={config.modulation_order} Fs={config.sample_rate/1e6:.2f}MHz "
                f"Rs={config.symbol_rate/1e3:.1f}k SPS={config.samples_per_symbol:.1f} "
                f"CFO={config.cfo_hz:.0f}Hz BW={config.bandwidth_hz/1e3:.1f}kHz "
                f"SNR={config.snr_db:.1f}dB")