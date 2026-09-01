"""
Phase 3.1 — Bandwidth Estimation
=================================
Estimates occupied bandwidth from the PSD.
Supports region-based (from detection) and energy-threshold methods.
"""

import numpy as np
from typing import Tuple, Optional


def estimate_bandwidth_from_region(
    lower_edge_hz: Optional[float],
    upper_edge_hz: Optional[float]
) -> Tuple[float, float, float]:
    """
    Compute bandwidth from pre-detected region edges.
    
    Returns:
        bandwidth, lower_edge, upper_edge
    """
    if lower_edge_hz is None or upper_edge_hz is None:
        return 0.0, 0.0, 0.0
    if upper_edge_hz <= lower_edge_hz:
        return 0.0, float(lower_edge_hz), float(upper_edge_hz)
    
    bandwidth = upper_edge_hz - lower_edge_hz
    return float(bandwidth), float(lower_edge_hz), float(upper_edge_hz)


def estimate_bandwidth_energy(
    freqs: np.ndarray,
    psd_linear: np.ndarray,
    energy_threshold: float = 0.99
) -> Tuple[float, float, float]:
    """
    Estimate occupied bandwidth containing a percentage of total energy.
    This method includes noise energy and may overestimate in noisy conditions.
    
    Returns:
        bandwidth, lower_edge, upper_edge
    """
    if len(psd_linear) == 0:
        return 0.0, 0.0, 0.0
        
    total_energy = np.sum(psd_linear)
    if total_energy <= 0:
        return 0.0, 0.0, 0.0
        
    # Calculate cumulative sum of energy
    cumulative_energy = np.cumsum(psd_linear) / total_energy
    
    # Find edges containing the central X% of energy
    lower_percentile = (1.0 - energy_threshold) / 2.0
    upper_percentile = 1.0 - lower_percentile
    
    lower_idx = np.searchsorted(cumulative_energy, lower_percentile)
    upper_idx = np.searchsorted(cumulative_energy, upper_percentile)
    
    # Bound indices
    lower_idx = min(len(freqs) - 1, max(0, lower_idx))
    upper_idx = min(len(freqs) - 1, max(0, upper_idx))
    
    lower_edge = freqs[lower_idx]
    upper_edge = freqs[upper_idx]
    bandwidth = upper_edge - lower_edge
    
    return float(bandwidth), float(lower_edge), float(upper_edge)


def estimate_bandwidth(
    freqs: np.ndarray,
    psd_linear: np.ndarray,
    energy_threshold: float = 0.99,
    lower_edge_hz: Optional[float] = None,
    upper_edge_hz: Optional[float] = None,
) -> Tuple[float, float, float]:
    """
    Main bandwidth estimation function.
    Prefers region-based edges from signal detection if available,
    falls back to energy-threshold method.
    
    Returns:
        bandwidth, lower_edge, upper_edge
    """
    # Try region-based first (from Phase 2 detection)
    if lower_edge_hz is not None and upper_edge_hz is not None:
        bw, low, high = estimate_bandwidth_from_region(lower_edge_hz, upper_edge_hz)
        if bw > 0:
            return bw, low, high
    
    # Fallback to energy method
    return estimate_bandwidth_energy(freqs, psd_linear, energy_threshold)