"""
SmartSignal Backend — Pydantic Schemas
========================================
All request/response data models. These define the API contract
between the backend and React frontend.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ============================================================
# SHARED PRIMITIVES
# ============================================================

class MeasuredValue(BaseModel):
    """
    A numeric value with a reliability status label.
    status: measured | estimated | model_predicted |
            user_provided | unavailable | low_confidence
    """
    value: Optional[float] = None
    unit: Optional[str] = None
    status: str = "unavailable"


# ============================================================
# UPLOAD
# ============================================================

class UploadResponse(BaseModel):
    job_id: str
    filename: str
    size_bytes: int
    message: str


# ============================================================
# JOB STATUS
# ============================================================

class JobStatus(BaseModel):
    job_id: str
    status: str  # uploaded | reading | dsp_analysis | feature_extraction |
                 # modulation_classification | demodulation | completed | failed
    progress: int = Field(0, ge=0, le=100)
    message: str = ""
    error: Optional[str] = None


# ============================================================
# FILE INFO
# ============================================================

class FileInfo(BaseModel):
    name: str
    format: str               # "IQ" or "WAV"
    size_bytes: int
    iq_dtype: Optional[str]   # float32 / int16 / etc.
    channels: Optional[int]   # 1 (mono) or 2 (stereo IQ)


# ============================================================
# ACQUISITION
# ============================================================

class AcquisitionInfo(BaseModel):
    sampling_rate: MeasuredValue
    sample_count: int
    duration: MeasuredValue   # seconds


# ============================================================
# SPECTRAL
# ============================================================

class SpectralInfo(BaseModel):
    peak_frequency: MeasuredValue      # Hz
    bandwidth: MeasuredValue           # Hz
    lower_edge: MeasuredValue          # Hz
    upper_edge: MeasuredValue          # Hz
    noise_floor_db: MeasuredValue      # dBm or relative dB
    snr_db: MeasuredValue


# ============================================================
# MODULATION AI
# ============================================================

class ModulationInfo(BaseModel):
    prediction: Optional[str] = None  # "FSK" | "QAM" | "QPSK" | "PSK"
    confidence: Optional[float] = None
    probabilities: Dict[str, float] = {}
    status: str = "unavailable"       # model_predicted | unavailable | low_confidence


# ============================================================
# SYNCHRONIZATION
# ============================================================

class SyncInfo(BaseModel):
    symbol_rate: MeasuredValue           # symbols/second
    samples_per_symbol: MeasuredValue
    frequency_offset_hz: MeasuredValue   # Hz
    phase_offset_rad: MeasuredValue      # radians
    timing_offset: MeasuredValue         # fractional sample


# ============================================================
# DEMODULATION
# ============================================================

class DemodInfo(BaseModel):
    receiver: Optional[str] = None    # "PSK" | "FSK" | "QAM"
    status: str = "not_started"       # completed | failed | not_started
    symbol_count: Optional[int] = None
    bit_count: Optional[int] = None
    evm_rms_pct: MeasuredValue = MeasuredValue()
    ber: MeasuredValue = MeasuredValue()
    constellation_i: Optional[List[float]] = None
    constellation_q: Optional[List[float]] = None


# ============================================================
# BITSTREAM
# ============================================================

class BitstreamInfo(BaseModel):
    length_bits: Optional[int] = None
    binary_preview: Optional[str] = None   # first 512 chars
    hex_preview: Optional[str] = None      # first 128 chars hex
    status: str = "unavailable"


# ============================================================
# COMPLETE RESULT
# ============================================================

class AnalysisResult(BaseModel):
    job_id: str
    status: str

    file: FileInfo
    acquisition: AcquisitionInfo
    spectral: SpectralInfo
    modulation: ModulationInfo
    synchronization: SyncInfo
    demodulation: DemodInfo
    bitstream: BitstreamInfo


# ============================================================
# VISUALIZATION PAYLOADS
# ============================================================

class WaveformData(BaseModel):
    """Time-domain waveform (downsampled for display)."""
    time: List[float]          # seconds
    i_samples: List[float]     # real part
    q_samples: List[float]     # imaginary part
    amplitude: List[float]     # |I + jQ|
    sample_rate: Optional[float]


class SpectrumData(BaseModel):
    """Power Spectral Density (Welch)."""
    frequency: List[float]     # Hz (relative to center or absolute)
    power_db: List[float]      # dBFS or relative dB
    noise_floor_db: Optional[float]
    peak_frequency_hz: Optional[float]


class WaterfallData(BaseModel):
    """STFT spectrogram matrix."""
    time: List[float]          # seconds
    frequency: List[float]     # Hz
    power_db: List[List[float]]  # [time_bins][freq_bins] in dB


class ConstellationData(BaseModel):
    """Recovered symbol constellation."""
    i_values: List[float]
    q_values: List[float]
    point_count: int
    modulation: Optional[str]


class BitstreamData(BaseModel):
    """Full bitstream payload."""
    binary: str
    hex: str
    length_bits: int
    symbol_count: int
