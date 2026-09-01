"""
Phase 1 — WAV File Reader
===========================
Reads WAV files containing IQ data.

Stereo WAV (2 channels):
    channel 0 → I (in-phase)
    channel 1 → Q (quadrature)
    → complex64: x[n] = ch0[n] + j*ch1[n]

Mono WAV (1 channel):
    Treated as REAL-valued RF data.
    Q = 0 for all samples.
    Returned as complex64 with Im=0.
    Flag real_only=True is set in metadata.

The WAV header provides:
    - sample_rate (always known from header)
    - bit depth / dtype
    - channel count
    - sample count

DO NOT apply DSP preprocessing here.
"""

import logging
import wave
import numpy as np
from pathlib import Path
from typing import Tuple

logger = logging.getLogger(__name__)


# Mapping from WAV sample width (bytes) to numpy dtype
_WAVE_DTYPE_MAP = {
    1: np.int8,    # rarely used
    2: np.int16,   # most common (CD quality, SDR default)
    3: None,       # 24-bit — handled specially
    4: np.int32,   # 32-bit integer
}

# Scale factors to convert integer WAV samples to float [-1, +1]
_WAVE_SCALE = {
    np.int8:  128.0,
    np.int16: 32768.0,
    np.int32: 2147483648.0,
}


def _read_24bit(data_bytes: bytes, n_samples: int) -> np.ndarray:
    """Decode 24-bit (3-byte) little-endian WAV samples."""
    result = np.zeros(n_samples, dtype=np.int32)
    for i in range(n_samples):
        b = data_bytes[i*3:(i+1)*3]
        # Sign-extend from 24-bit to 32-bit
        val = int.from_bytes(b, byteorder="little", signed=True)
        result[i] = val
    return result.astype(np.float32) / 8388608.0  # 2^23


def read_wav_file(path: Path) -> Tuple[np.ndarray, dict]:
    """
    Read a WAV file and return (signal_complex64, metadata_dict).

    Parameters
    ----------
    path : Path
        Absolute path to the .wav file.

    Returns
    -------
    signal : np.ndarray, dtype=complex64
        x[n] = I[n] + j*Q[n]
        For mono WAV: Q[n] = 0 for all n.
    metadata : dict
        Acquisition metadata extracted from the WAV header.

    Raises
    ------
    FileNotFoundError, ValueError, wave.Error
    """
    logger.info("[PHASE 1] Reading WAV file: %s", path.name)

    if not path.exists():
        raise FileNotFoundError(f"WAV file not found: {path}")

    with wave.open(str(path), "rb") as wf:
        n_channels   = wf.getnchannels()
        sample_width = wf.getsampwidth()   # bytes per sample per channel
        frame_rate   = wf.getframerate()   # samples per second
        n_frames     = wf.getnframes()
        raw_bytes    = wf.readframes(n_frames)

    logger.info(
        "[PHASE 1] WAV header: channels=%d  sample_width=%d  rate=%d  frames=%d",
        n_channels, sample_width, frame_rate, n_frames,
    )

    # ----------------------------------------------------------
    # Decode raw bytes → float32 samples
    # ----------------------------------------------------------
    total_samples = n_frames * n_channels

    if sample_width == 3:
        # Special 24-bit path
        samples_float = _read_24bit(raw_bytes, total_samples)
    else:
        np_dtype = _WAVE_DTYPE_MAP.get(sample_width)
        if np_dtype is None:
            raise ValueError(
                f"Unsupported WAV sample width: {sample_width} bytes"
            )
        raw_array = np.frombuffer(raw_bytes, dtype=np_dtype)
        samples_float = raw_array.astype(np.float32) / _WAVE_SCALE[np_dtype]

    # ----------------------------------------------------------
    # Shape into (n_frames, n_channels) then build complex64
    # ----------------------------------------------------------
    samples_float = samples_float.reshape(n_frames, n_channels)

    real_only = False
    if n_channels == 2:
        i_ch = samples_float[:, 0]
        q_ch = samples_float[:, 1]
    elif n_channels == 1:
        logger.warning(
            "[PHASE 1] Mono WAV — treating as real RF (Q=0). "
            "Analysis quality may be limited."
        )
        i_ch = samples_float[:, 0]
        q_ch = np.zeros_like(i_ch)
        real_only = True
    else:
        raise ValueError(
            f"WAV has {n_channels} channels. Expected 1 (mono) or 2 (stereo IQ)."
        )

    signal = (i_ch + 1j * q_ch).astype(np.complex64)

    duration_val  = n_frames / frame_rate if frame_rate > 0 else None
    iq_dtype_name = {
        1: "int8",
        2: "int16",
        3: "int24",
        4: "int32",
    }.get(sample_width, f"unknown_{sample_width*8}bit")

    metadata = {
        "format": "WAV",
        "iq_dtype": iq_dtype_name,
        "size_bytes": path.stat().st_size,
        "channels": n_channels,
        "real_only": real_only,
        "sample_count": n_frames,
        "sampling_rate": {
            "value": float(frame_rate),
            "unit": "Hz",
            "status": "measured",  # Always known from WAV header
        },
        "duration": {
            "value": duration_val,
            "unit": "s",
            "status": "measured",
        },
    }

    logger.info(
        "[PHASE 1] WAV read complete. samples=%d  rate=%d Hz  duration=%.4f s",
        n_frames, frame_rate, duration_val or 0,
    )
    return signal, metadata
