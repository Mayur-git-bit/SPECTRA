"""
Phase 1 — Raw IQ File Reader
==============================
Reads binary IQ files (.iq / .IQ) with interleaved I and Q samples.

Format assumed: IQIQIQ... interleaved
Supported dtypes: float32, float64, int16, int8, uint8

The file reader:
  1. Detects file size
  2. Validates byte count is consistent with chosen dtype
  3. Reads raw bytes → numpy array
  4. De-interleaves I and Q → complex64 NumPy array
  5. Converts int types to float using standard scaling

DO NOT apply any filtering, normalization, or DC removal here.
That belongs to the DSP branch (phase2).
"""

import logging
import numpy as np
from pathlib import Path
from typing import Optional, Tuple

from config import DEFAULT_IQ_DTYPE, SUPPORTED_IQ_DTYPES

logger = logging.getLogger(__name__)


# ============================================================
# INT SCALING
# ============================================================
# Maps integer IQ types to their full-scale divisor so that
# the result is approximately in the range [-1, +1].

INT_SCALE = {
    "int16":  32768.0,
    "int8":   128.0,
    "uint8":  128.0,   # uint8: subtract 127.5, divide by 128
}


def _to_complex64(raw: np.ndarray, dtype_name: str) -> np.ndarray:
    """
    Convert a de-interleaved float array of shape (N, 2) where
    column 0 = I, column 1 = Q, to complex64.

    Handles integer types by normalising to [-1, +1].
    float32 / float64 are passed through directly.
    """
    if dtype_name == "uint8":
        # Offset binary → centre on 0 before scaling
        raw = raw.astype(np.float32)
        raw -= 127.5
        raw /= INT_SCALE["uint8"]
    elif dtype_name in INT_SCALE:
        raw = raw.astype(np.float32) / INT_SCALE[dtype_name]
    elif dtype_name == "float64":
        raw = raw.astype(np.float32)
    # float32 → already correct

    i_ch = raw[:, 0]
    q_ch = raw[:, 1]
    return (i_ch + 1j * q_ch).astype(np.complex64)


def read_iq_file(
    path: Path,
    dtype_name: str = DEFAULT_IQ_DTYPE,
    sample_rate: Optional[float] = None,
) -> Tuple[np.ndarray, dict]:
    """
    Read a raw IQ file and return (signal_complex64, metadata_dict).

    Parameters
    ----------
    path : Path
        Absolute path to the .iq file.
    dtype_name : str
        Sample format: float32 | float64 | int16 | int8 | uint8
    sample_rate : float or None
        Samples per second. If None, returned as "unavailable".

    Returns
    -------
    signal : np.ndarray, dtype=complex64
        Complex IQ signal: x[n] = I[n] + jQ[n]
    metadata : dict
        Acquisition metadata.

    Raises
    ------
    ValueError
        If the file size is not divisible by (bytes_per_sample × 2)
        or if the dtype is not supported.
    FileNotFoundError
        If the file does not exist.
    """
    logger.info("[PHASE 1] Reading IQ file: %s  dtype=%s", path.name, dtype_name)

    if not path.exists():
        raise FileNotFoundError(f"IQ file not found: {path}")

    if dtype_name not in SUPPORTED_IQ_DTYPES:
        raise ValueError(
            f"Unsupported IQ dtype '{dtype_name}'. "
            f"Supported: {list(SUPPORTED_IQ_DTYPES.keys())}"
        )

    np_dtype = np.dtype(SUPPORTED_IQ_DTYPES[dtype_name])
    bytes_per_sample = np_dtype.itemsize  # bytes for one I or Q value
    bytes_per_pair = bytes_per_sample * 2  # one IQ pair

    file_size = path.stat().st_size

    if file_size == 0:
        raise ValueError(f"IQ file is empty: {path}")

    if file_size % bytes_per_pair != 0:
        raise ValueError(
            f"File size {file_size} bytes is not divisible by "
            f"{bytes_per_pair} (dtype={dtype_name}). "
            f"Check the selected sample format."
        )

    num_samples = file_size // bytes_per_pair

    logger.info("[PHASE 1] Sample count: %d  File size: %d bytes", num_samples, file_size)

    # Read raw flat array, then reshape to (N, 2) — [I, Q] pairs
    raw_flat = np.fromfile(str(path), dtype=np_dtype)
    raw_pairs = raw_flat.reshape(num_samples, 2)

    signal = _to_complex64(raw_pairs, dtype_name)

    duration_status = "unavailable"
    duration_val = None
    if sample_rate is not None and sample_rate > 0:
        duration_val = num_samples / sample_rate
        duration_status = "measured"

    metadata = {
        "format": "IQ",
        "iq_dtype": dtype_name,
        "size_bytes": file_size,
        "channels": 2,
        "sample_count": num_samples,
        "sampling_rate": {
            "value": sample_rate,
            "unit": "Hz",
            "status": "user_provided" if sample_rate else "unavailable",
        },
        "duration": {
            "value": duration_val,
            "unit": "s",
            "status": duration_status,
        },
    }

    logger.info("[PHASE 1] IQ conversion complete. samples=%d", num_samples)
    return signal, metadata
