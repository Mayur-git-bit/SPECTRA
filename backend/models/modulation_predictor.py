"""
Phase 4 — Modulation Classification (AI Model Inference)
========================================================
Wrapper for the trained Multi-Head Attention (MHA) modulation classifier.

Model preprocessing (from notebook RadioMLDataset.__getitem__):
1. Raw IQ: complex64 array of shape (N,) where x[n] = I[n] + jQ[n]
2. Extract 1024-sample window (center or max energy)
3. Split into I/Q channels: shape (1024, 2) 
4. Per-channel normalization: (x - mean) / (std + 1e-6)
5. Transpose to (2, 1024)
6. Convert to float32 tensor, add batch dimension: (1, 2, 1024)

Classes: FSK (0), QAM (1), QPSK (2), PSK (3)
"""

import logging
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from config import (
    MODEL_PATH,
    MODEL_CLASS_NAMES,
    MODEL_INPUT_LENGTH,
    MODEL_NUM_CLASSES,
    MODEL_NORM_EPS,
)

logger = logging.getLogger(__name__)


# ============================================================
# MODEL ARCHITECTURE (must match notebook exactly)
# ============================================================

class ResidualBlock(nn.Module):
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int = 7,
        dropout: float = 0.10,
    ):
        super().__init__()
        padding = kernel_size // 2
        self.conv1 = nn.Conv1d(
            in_channels, out_channels, kernel_size, padding=padding, bias=False
        )
        self.bn1 = nn.BatchNorm1d(out_channels)
        self.conv2 = nn.Conv1d(
            out_channels, out_channels, kernel_size, padding=padding, bias=False
        )
        self.bn2 = nn.BatchNorm1d(out_channels)
        self.dropout = nn.Dropout(dropout)
        if in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv1d(in_channels, out_channels, kernel_size=1, bias=False),
                nn.BatchNorm1d(out_channels),
            )
        else:
            self.shortcut = nn.Identity()

    def forward(self, x):
        identity = self.shortcut(x)
        out = self.conv1(x)
        out = self.bn1(out)
        out = F.gelu(out)
        out = self.dropout(out)
        out = self.conv2(out)
        out = self.bn2(out)
        out = out + identity
        out = F.gelu(out)
        return out


class SignalCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.stem = nn.Sequential(
            nn.Conv1d(2, 64, kernel_size=7, padding=3, bias=False),
            nn.BatchNorm1d(64),
            nn.GELU(),
            nn.MaxPool1d(2),
        )
        self.block1 = ResidualBlock(64, 128, kernel_size=7)
        self.pool1 = nn.MaxPool1d(2)
        self.block2 = ResidualBlock(128, 256, kernel_size=5)
        self.pool2 = nn.MaxPool1d(2)
        self.block3 = ResidualBlock(256, 256, kernel_size=3)

    def forward(self, x):
        x = self.stem(x)          # 1024 -> 512
        x = self.block1(x)        # 512
        x = self.pool1(x)         # 512 -> 256
        x = self.block2(x)        # 256
        x = self.pool2(x)         # 256 -> 128
        x = self.block3(x)        # 128
        return x                  # (B, 256, 128)


class MultiHeadAttentionBlock(nn.Module):
    def __init__(
        self,
        feature_dim: int = 256,
        heads: int = 8,
        dropout: float = 0.10,
    ):
        super().__init__()
        self.attention = nn.MultiheadAttention(
            embed_dim=feature_dim,
            num_heads=heads,
            dropout=dropout,
            batch_first=True,
        )
        self.norm1 = nn.LayerNorm(feature_dim)
        self.ffn = nn.Sequential(
            nn.Linear(feature_dim, feature_dim * 4),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(feature_dim * 4, feature_dim),
        )
        self.norm2 = nn.LayerNorm(feature_dim)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        attended, weights = self.attention(x, x, x, need_weights=True)
        x = self.norm1(x + self.dropout(attended))
        feed_forward = self.ffn(x)
        x = self.norm2(x + self.dropout(feed_forward))
        context = x.mean(dim=1)  # Global average pooling
        return context, weights


class ModulationClassifier(nn.Module):
    def __init__(self, attention_type: str = "mha"):
        super().__init__()
        self.attention_type = attention_type
        self.cnn = SignalCNN()
        self.position = nn.Parameter(
            torch.randn(1, 128, 256) * 0.02
        )
        self.attention = MultiHeadAttentionBlock(256, heads=8)
        self.classifier = nn.Sequential(
            nn.Linear(256, 256),
            nn.LayerNorm(256),
            nn.GELU(),
            nn.Dropout(0.35),
            nn.Linear(256, MODEL_NUM_CLASSES),
        )

    def forward(self, x, return_attention: bool = False):
        x = self.cnn(x)                    # (B, 256, 128)
        x = x.transpose(1, 2)              # (B, 128, 256)
        x = x + self.position              # Add positional encoding
        context, attention_weights = self.attention(x)
        logits = self.classifier(context)
        if return_attention:
            return logits, attention_weights
        return logits


# ============================================================
# MODEL PREPROCESSING (exact match to notebook)
# ============================================================

def preprocess_iq_for_model(
    iq_signal: np.ndarray,
    window_length: int = MODEL_INPUT_LENGTH,
) -> torch.Tensor:
    """
    Apply notebook-exact preprocessing to raw IQ signal.
    
    Parameters:
        iq_signal: complex64 array of shape (N,)
        window_length: Number of samples for model input (default 1024)
        
    Returns:
        Tensor of shape (1, 2, 1024) ready for model inference
    """
    if len(iq_signal) < window_length:
        # Pad with zeros if signal is too short
        padded = np.zeros(window_length, dtype=np.complex64)
        padded[:len(iq_signal)] = iq_signal
        iq_signal = padded
    
    # Select window: use center of signal (or could use max energy window)
    start = (len(iq_signal) - window_length) // 2
    if start < 0:
        start = 0
    window = iq_signal[start:start + window_length]
    
    # Split into I/Q channels: shape (1024, 2)
    iq_real = np.stack([window.real, window.imag], axis=1).astype(np.float32)
    
    # Per-channel normalization: (x - mean) / (std + eps)
    # This matches RadioMLDataset.__getitem__ exactly
    mean = iq_real.mean(axis=0, keepdims=True)
    std = iq_real.std(axis=0, keepdims=True)
    iq_normalized = (iq_real - mean) / (std + MODEL_NORM_EPS)
    
    # Transpose to (2, 1024)
    iq_transposed = iq_normalized.T
    
    # Convert to tensor: (1, 2, 1024)
    tensor = torch.from_numpy(iq_transposed).float().unsqueeze(0)
    
    return tensor


def select_best_window(iq_signal: np.ndarray, window_length: int = MODEL_INPUT_LENGTH) -> np.ndarray:
    """
    Select the most energetic window from the signal.
    Returns window of length window_length.
    """
    if len(iq_signal) <= window_length:
        return iq_signal
    
    # Compute energy in sliding windows
    stride = window_length // 4  # 25% overlap
    num_windows = (len(iq_signal) - window_length) // stride + 1
    
    max_energy = -1
    best_start = 0
    
    for i in range(num_windows):
        start = i * stride
        end = start + window_length
        window = iq_signal[start:end]
        energy = np.sum(np.abs(window)**2)
        if energy > max_energy:
            max_energy = energy
            best_start = start
    
    return iq_signal[best_start:best_start + window_length]


# ============================================================
# MODULATION PREDICTOR
# ============================================================

class ModulationPredictor:
    """
    Loads the trained MHA model and provides modulation classification.
    
    Usage:
        predictor = ModulationPredictor()
        predictor.load_model()
        result = predictor.predict(iq_signal)
    """
    
    def __init__(self, device: Optional[str] = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model: Optional[ModulationClassifier] = None
        self.class_names = MODEL_CLASS_NAMES
        self.input_length = MODEL_INPUT_LENGTH
        self._loaded = False
        logger.info(f"[PHASE 4] ModulationPredictor initialized on device: {self.device}")
    
    def load_model(self) -> bool:
        """Load the model weights from checkpoint."""
        if self._loaded:
            return True
            
        try:
            logger.info(f"[PHASE 4] Loading model from {MODEL_PATH}")
            checkpoint = torch.load(MODEL_PATH, map_location=self.device, weights_only=False)
            
            # Verify checkpoint
            if "model_state_dict" not in checkpoint:
                logger.error("[PHASE 4] Invalid checkpoint: missing model_state_dict")
                return False
            
            if checkpoint.get("attention_type") != "mha":
                logger.warning(f"[PHASE 4] Checkpoint attention_type: {checkpoint.get('attention_type')}, expected 'mha'")
            
            # Build model
            self.model = ModulationClassifier(attention_type="mha").to(self.device)
            self.model.load_state_dict(checkpoint["model_state_dict"])
            self.model.eval()
            
            # Verify class names match
            ckpt_classes = checkpoint.get("class_names", [])
            if ckpt_classes != self.class_names:
                logger.warning(f"[PHASE 4] Class names mismatch: checkpoint={ckpt_classes}, config={self.class_names}")
            
            self._loaded = True
            logger.info(f"[PHASE 4] Model loaded successfully (epoch={checkpoint.get('epoch', 'unknown')}, val_acc={checkpoint.get('best_val_accuracy', 'unknown'):.4f})")
            return True
            
        except Exception as e:
            logger.error(f"[PHASE 4] Failed to load model: {e}")
            return False
    
    def predict(self, iq_signal: np.ndarray) -> Dict:
        """
        Run modulation classification on raw IQ signal.
        
        Parameters:
            iq_signal: complex64 array of raw IQ samples
            
        Returns:
            Dict with keys:
                - prediction: str (top-1 class name)
                - confidence: float (softmax probability of top-1)
                - probabilities: Dict[str, float] (all class probabilities)
                - status: str (model_predicted | unavailable | error)
        """
        result = {
            "prediction": None,
            "confidence": 0.0,
            "probabilities": {},
            "status": "unavailable"
        }
        
        if not self._loaded:
            if not self.load_model():
                result["status"] = "error"
                return result
        
        if len(iq_signal) < 100:
            logger.warning("[PHASE 4] Signal too short for classification")
            result["status"] = "unavailable"
            return result
        
        try:
            with torch.no_grad():
                # Preprocess: select best window and apply notebook-exact preprocessing
                window = select_best_window(iq_signal, self.input_length)
                x = preprocess_iq_for_model(window, self.input_length).to(self.device)
                
                # Inference
                logits = self.model(x)
                probs = F.softmax(logits, dim=1).squeeze(0).cpu().numpy()
                
                # Top-1 prediction
                top_idx = int(np.argmax(probs))
                top_prob = float(probs[top_idx])
                top_class = self.class_names[top_idx]
                
                # All probabilities
                prob_dict = {name: float(probs[i]) for i, name in enumerate(self.class_names)}
                
                result["prediction"] = top_class
                result["confidence"] = top_prob
                result["probabilities"] = prob_dict
                result["status"] = "model_predicted"
                
                logger.info(f"[PHASE 4] Modulation prediction: {top_class} ({top_prob:.4f})")
                logger.info(f"[PHASE 4] All probs: {prob_dict}")
                
        except Exception as e:
            logger.error(f"[PHASE 4] Inference error: {e}")
            result["status"] = "error"
        
        return result
    
    def predict_batch(self, iq_windows: List[np.ndarray]) -> List[Dict]:
        """Predict on multiple windows (for averaging)."""
        return [self.predict(w) for w in iq_windows]


# Singleton instance for reuse across requests
_predictor_instance: Optional[ModulationPredictor] = None

def get_modulation_predictor() -> ModulationPredictor:
    """Get or create the global ModulationPredictor instance."""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = ModulationPredictor()
    return _predictor_instance