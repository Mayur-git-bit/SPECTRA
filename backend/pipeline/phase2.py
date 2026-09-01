"""
Phase 2 Pipeline — Classical DSP
=================================
Orchestrates the classical DSP branch logic:
1. DC Removal & RMS Normalization
2. PSD estimation
3. Noise floor estimation
4. Signal detection
"""

import logging
import numpy as np
from typing import Tuple, Dict, Any

from dsp.preprocessing import process_dsp_branch
from dsp.spectrum import estimate_psd
from dsp.noise import estimate_noise_floor, to_db
from dsp.detection import detect_signal

logger = logging.getLogger(__name__)

def run_phase2(
    raw_signal: np.ndarray,
    sample_rate: float = 1.0
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Run Phase 2 Classical DSP preprocessing.
    
    Returns:
        dsp_signal: The preprocessed signal (DC removed, RMS normalized).
        results: Dictionary containing spectral measurements.
    """
    logger.info("[PHASE 2] Starting Classical DSP Pipeline")
    
    # 1. Preprocessing
    dsp_signal, dc_val = process_dsp_branch(raw_signal)
    logger.info(f"[PHASE 2] DC removed: {dc_val:.3e}, RMS normalized.")
    
    # 2. PSD Estimation
    freqs, psd_linear = estimate_psd(dsp_signal, fs=sample_rate)
    
    # 3. Noise Floor Estimation
    noise_linear = estimate_noise_floor(psd_linear)
    noise_db = to_db(noise_linear)
    logger.info(f"[PHASE 2] Noise floor estimated: {noise_db:.2f} dB")
    
    # 4. Signal Detection (with region edges)
    is_detected, peak_val_linear, peak_idx, lower_edge, upper_edge = detect_signal(
        psd_linear, noise_linear, freqs
    )
    peak_freq = freqs[peak_idx]
    
    # Calculate crude SNR (peak / noise)
    # A more rigorous SNR over bandwidth is done in Phase 3.
    snr_db = to_db(peak_val_linear) - noise_db
    
    logger.info(f"[PHASE 2] Detection: {'YES' if is_detected else 'NO'} | "
                f"Peak Freq: {peak_freq:.2f} Hz | Peak SNR: {snr_db:.2f} dB")
    if lower_edge is not None:
        logger.info(f"[PHASE 2] Signal region: {lower_edge:.2f} - {upper_edge:.2f} Hz")
                
    results = {
        "dc_offset": dc_val,
        "is_detected": is_detected,
        "peak_frequency_hz": peak_freq,
        "peak_snr_db": snr_db,
        "noise_floor_db": noise_db,
        "lower_edge_hz": lower_edge,
        "upper_edge_hz": upper_edge,
        "psd_freqs": freqs,
        "psd_linear": psd_linear
    }
    
    return dsp_signal, results
