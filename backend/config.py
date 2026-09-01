"""
SmartSignal Backend — Configuration
====================================
Central configuration. All paths, constants, and tuneable parameters
live here so they can be changed without touching business logic.
"""

import os
from pathlib import Path

# ============================================================
# PATHS
# ============================================================

# Root of the Project_2 repository
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Model weights — stays at project_root/model/mha_best.pt
MODEL_PATH = PROJECT_ROOT / "model" / "mha_best.pt"

# Upload staging area
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Results cache directory
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# API
# ============================================================

API_PREFIX = "/api"
API_TITLE = "SmartSignal RF Analysis API"
API_VERSION = "1.0.0"
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_PORT_FALLBACK_COUNT = int(os.getenv("API_PORT_FALLBACK_COUNT", "10"))

# CORS — Vite dev server runs on 5173, production on 5174
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
]

# Maximum upload size (200 MB)
MAX_UPLOAD_BYTES = 200 * 1024 * 1024

# ============================================================
# MODEL
# ============================================================

# Exact class names as saved in the checkpoint
MODEL_CLASS_NAMES = ["FSK", "QAM", "QPSK", "PSK"]

# Window length used during training (MUST NOT change)
MODEL_INPUT_LENGTH = 1024

# Number of output classes
MODEL_NUM_CLASSES = 4

# Epsilon for per-channel normalization (matches training)
MODEL_NORM_EPS = 1e-6

# ============================================================
# IQ FILE FORMATS
# ============================================================

# Supported raw IQ sample types (interleaved IQIQIQ...)
SUPPORTED_IQ_DTYPES = {
    "float32": "float32",   # 4 bytes per sample (most common)
    "float64": "float64",   # 8 bytes per sample
    "int16":   "int16",     # 2 bytes per sample (SDR default)
    "int8":    "int8",      # 1 byte per sample (RTL-SDR 8-bit)
    "uint8":   "uint8",     # 1 byte (offset binary)
}

# Default assumed format when none is specified
DEFAULT_IQ_DTYPE = "float32"

# ============================================================
# DSP PARAMETERS
# ============================================================

# Welch PSD
WELCH_NPERSEG = 1024        # Segment length for Welch PSD
WELCH_NOVERLAP = 512        # 50% overlap
WELCH_WINDOW = "hann"       # Hann window (good sidelobe rejection)

# STFT (spectrogram / waterfall)
STFT_NPERSEG = 256          # Short-time segment length
STFT_NOVERLAP = 192         # 75% overlap for good time resolution

# Noise floor estimation
NOISE_FLOOR_PERCENTILE = 10  # Use 10th percentile of PSD as noise floor

# Signal detection threshold above noise floor (dB)
DETECTION_THRESHOLD_DB = 6.0  # Signal must exceed noise by this margin

# Bandpass filter guard band (fraction of estimated bandwidth)
FILTER_GUARD_BAND = 0.1     # 10% guard on each side

# ============================================================
# VISUALIZATION DOWNSAMPLING
# ============================================================

# Maximum number of waveform samples sent to frontend
WAVEFORM_MAX_POINTS = 4096

# Maximum number of PSD frequency bins sent to frontend
SPECTRUM_MAX_POINTS = 2048

# Maximum waterfall time bins
WATERFALL_MAX_TIME_BINS = 256

# Maximum constellation points sent to frontend
CONSTELLATION_MAX_POINTS = 2000

# ============================================================
# DEMODULATION DEFAULTS
# ============================================================

# Matched filter rolloff (root raised cosine)
RRC_ROLLOFF = 0.35
RRC_SPAN = 11  # Spans ± 11 symbols

# Costas loop bandwidth for carrier recovery
COSTAS_LOOP_BW = 0.01

# Gardner timing error threshold
GARDNER_LOOP_BW = 0.01

# Maximum CFO for coarse estimation (fraction of sample rate)
MAX_CFO_FRACTION = 0.3

# ============================================================
# LOGGING
# ============================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
