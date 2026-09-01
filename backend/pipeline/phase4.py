"""
Phase 4 Pipeline — AI Modulation Classification
================================================
Orchestrates the AI model branch for modulation classification.
"""

import logging
from typing import Dict, Any
import numpy as np

from models.modulation_predictor import get_modulation_predictor

logger = logging.getLogger(__name__)


def run_phase4(
    raw_signal: np.ndarray,
) -> Dict[str, Any]:
    """
    Run Phase 4 AI Modulation Classification.
    
    Parameters:
        raw_signal: Raw complex64 IQ signal (NOT preprocessed by DSP branch)
        
    Returns:
        Dict with modulation prediction, confidence, and all class probabilities
    """
    logger.info("[PHASE 4] Starting AI Modulation Classification")
    
    predictor = get_modulation_predictor()
    result = predictor.predict(raw_signal)
    
    logger.info(f"[PHASE 4] Prediction: {result['prediction']} (conf={result['confidence']:.4f})")
    
    return {
        "prediction": result["prediction"],
        "confidence": result["confidence"],
        "probabilities": result["probabilities"],
        "status": result["status"]
    }