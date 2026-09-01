"""
Phase 3 Pipeline — Parameter Extraction
=======================================
Aggregates DSP-derived features for synchronization and spectral analysis.
"""

import logging
import numpy as np
from typing import Dict, Any

from dsp.bandwidth import estimate_bandwidth
from dsp.snr import estimate_snr
from dsp.symbol_rate import estimate_symbol_rate
from dsp.carrier import estimate_cfo
from dsp.timing import estimate_phase_offset, estimate_timing_offset

logger = logging.getLogger(__name__)

def run_phase3(
    dsp_signal: np.ndarray,
    phase2_results: Dict[str, Any],
    sample_rate: float
) -> Dict[str, Any]:
    """
    Run Phase 3 Parameter Extraction.
    """
    logger.info("[PHASE 3] Starting Parameter Extraction Pipeline")
    
    psd_freqs = phase2_results["psd_freqs"]
    psd_linear = phase2_results["psd_linear"]
    noise_db = phase2_results["noise_floor_db"]
    noise_linear = 10 ** (noise_db / 10.0)
    
    # Get detected region edges from Phase 2
    lower_edge_hz = phase2_results.get("lower_edge_hz")
    upper_edge_hz = phase2_results.get("upper_edge_hz")
    
    # 1. Bandwidth (prefer region-based)
    bw, low_edge, high_edge = estimate_bandwidth(
        psd_freqs, psd_linear, lower_edge_hz=lower_edge_hz, upper_edge_hz=upper_edge_hz
    )
    
    # 2. SNR
    snr_db = estimate_snr(psd_freqs, psd_linear, noise_linear, low_edge, high_edge)
    
    # 3. Symbol Rate
    sym_rate_result = estimate_symbol_rate(dsp_signal, sample_rate)
    sym_rate = sym_rate_result["symbol_rate_hz"]
    sym_rate_status = sym_rate_result["status"]
    sym_rate_confidence = sym_rate_result.get("confidence", 0.0)
    
    # 4. CFO (coarse + fine)
    cfo_result = estimate_cfo(dsp_signal, sample_rate)
    cfo_hz = cfo_result["cfo_hz"]
    cfo_status = cfo_result["status"]
    cfo_confidence = cfo_result.get("confidence", 0.0)
    
    # 5. Phase offset
    phase_result = estimate_phase_offset(dsp_signal)
    phase_rad = phase_result["phase_offset_rad"]
    phase_status = phase_result["status"]
    
    # 6. Timing offset
    timing_result = estimate_timing_offset(dsp_signal, sample_rate)
    timing_offset = timing_result["timing_offset"]
    timing_status = timing_result["status"]
    
    # Calculate samples per symbol if symbol rate is found
    sps = 0.0
    sps_status = "unavailable"
    if sym_rate > 0 and sample_rate > 0:
        sps = sample_rate / sym_rate
        sps_status = "calculated" if sym_rate_status != "low_confidence" else "low_confidence"
        
    logger.info(f"[PHASE 3] Bandwidth: {bw:.2f} Hz | SNR: {snr_db:.2f} dB | "
                f"Symbol Rate: {sym_rate:.2f} Hz ({sym_rate_status}) | CFO: {cfo_hz:.2f} Hz ({cfo_status})")
                
    return {
        "bandwidth_hz": bw,
        "lower_edge_hz": low_edge,
        "upper_edge_hz": high_edge,
        "snr_db": snr_db,
        "symbol_rate_hz": sym_rate,
        "symbol_rate_status": sym_rate_status,
        "symbol_rate_confidence": sym_rate_confidence,
        "samples_per_symbol": sps,
        "samples_per_symbol_status": sps_status,
        "cfo_hz": cfo_hz,
        "cfo_status": cfo_status,
        "cfo_confidence": cfo_confidence,
        "phase_offset_rad": phase_rad,
        "phase_offset_status": phase_status,
        "timing_offset": timing_offset,
        "timing_offset_status": timing_status,
    }
