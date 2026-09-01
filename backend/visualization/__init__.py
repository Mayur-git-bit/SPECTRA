"""
Visualization Data Generation
=============================
Generates downsampled visualization data for the frontend.
"""

import numpy as np
from typing import Optional, List
from scipy import signal

from config import (
    WAVEFORM_MAX_POINTS,
    SPECTRUM_MAX_POINTS,
    WATERFALL_MAX_TIME_BINS,
    CONSTELLATION_MAX_POINTS,
    WELCH_NPERSEG,
    WELCH_NOVERLAP,
    WELCH_WINDOW,
    STFT_NPERSEG,
    STFT_NOVERLAP,
)


def downsample_signal(signal: np.ndarray, max_points: int) -> np.ndarray:
    """Downsample signal to max_points using decimation or averaging."""
    if len(signal) <= max_points:
        return signal
    
    # Use decimation (take every Nth sample)
    step = len(signal) // max_points
    return signal[::step][:max_points]


def downsample_complex(signal: np.ndarray, max_points: int) -> np.ndarray:
    """Downsample complex signal."""
    if len(signal) <= max_points:
        return signal
    step = len(signal) // max_points
    return signal[::step][:max_points]


def generate_waveform_data(iq_signal: np.ndarray) -> dict:
    """Generate time-domain waveform data for frontend."""
    max_points = WAVEFORM_MAX_POINTS
    
    # Downsample
    ds_signal = downsample_complex(iq_signal, max_points)
    
    # Time axis (normalized if Fs unknown)
    time = np.arange(len(ds_signal)) / max_points  # Normalized 0-1
    
    return {
        "time": time.tolist(),
        "i_samples": ds_signal.real.tolist(),
        "q_samples": ds_signal.imag.tolist(),
        "amplitude": np.abs(ds_signal).tolist(),
        "sample_rate": None,  # Unknown in normalized mode
    }


def generate_spectrum_data(iq_signal: np.ndarray, phase2_results: dict) -> dict:
    """Generate PSD spectrum data for frontend."""
    freqs = phase2_results.get("psd_freqs", np.array([]))
    psd_linear = phase2_results.get("psd_linear", np.array([]))
    noise_floor_db = phase2_results.get("noise_floor_db")
    peak_freq = phase2_results.get("peak_frequency_hz")
    
    if len(freqs) == 0 or len(psd_linear) == 0:
        return {
            "frequency": [],
            "power_db": [],
            "noise_floor_db": noise_floor_db,
            "peak_frequency_hz": peak_freq,
        }
    
    # Convert to dB
    psd_db = 10 * np.log10(np.maximum(psd_linear, 1e-12))
    
    # Downsample to max points
    max_points = SPECTRUM_MAX_POINTS
    if len(freqs) > max_points:
        step = len(freqs) // max_points
        freqs = freqs[::step]
        psd_db = psd_db[::step]
    
    return {
        "frequency": freqs.tolist(),
        "power_db": psd_db.tolist(),
        "noise_floor_db": noise_floor_db,
        "peak_frequency_hz": peak_freq,
    }


def generate_waterfall_data(iq_signal: np.ndarray) -> dict:
    """Generate STFT spectrogram (waterfall) data for frontend."""
    max_time_bins = WATERFALL_MAX_TIME_BINS

    # Keep the STFT input bounded so large uploads don't create
    # massive spectrograms that stall the browser.
    max_input_samples = max(
        STFT_NPERSEG * max_time_bins,
        STFT_NPERSEG * 8,
    )
    if len(iq_signal) > max_input_samples:
        step = len(iq_signal) // max_input_samples
        iq_signal = iq_signal[::step][:max_input_samples]
    
    # STFT parameters
    nperseg = min(STFT_NPERSEG, len(iq_signal))
    noverlap = min(STFT_NOVERLAP, nperseg - 1)
    
    f, t, Zxx = signal.stft(
        iq_signal,
        fs=1.0,  # Normalized
        window='hann',
        nperseg=nperseg,
        noverlap=noverlap,
        return_onesided=False,
    )
    
    # fftshift
    f = np.fft.fftshift(f)
    Zxx = np.fft.fftshift(Zxx, axes=0)
    
    # Power in dB
    Sxx = np.abs(Zxx)**2
    Sxx_db = 10 * np.log10(np.maximum(Sxx, 1e-12))
    
    # Downsample time bins
    if len(t) > max_time_bins:
        step = len(t) // max_time_bins
        t = t[::step]
        Sxx_db = Sxx_db[:, ::step]
    
    # Limit frequency bins too
    max_freq_bins = 512
    if len(f) > max_freq_bins:
        step = len(f) // max_freq_bins
        f = f[::step]
        Sxx_db = Sxx_db[::step, :]
    
    return {
        "time": t.tolist(),
        "frequency": f.tolist(),
        "power_db": Sxx_db.tolist(),
    }


def generate_constellation_data(i_values: List[float], q_values: List[float], modulation: Optional[str]) -> dict:
    """Generate constellation plot data."""
    max_points = CONSTELLATION_MAX_POINTS
    
    i_arr = np.array(i_values)
    q_arr = np.array(q_values)
    
    if len(i_arr) > max_points:
        step = len(i_arr) // max_points
        i_arr = i_arr[::step]
        q_arr = q_arr[::step]
    
    return {
        "i_values": i_arr.tolist(),
        "q_values": q_arr.tolist(),
        "point_count": len(i_arr),
        "modulation": modulation,
    }


def generate_bitstream_data(binary: str, hex_str: str, length_bits: int, symbol_count: int) -> dict:
    """Generate bitstream data."""
    # Compute hex from binary if not provided or invalid
    if not hex_str:
        # Pad binary to multiple of 4
        padding = (4 - len(binary) % 4) % 4
        binary_padded = binary + '0' * padding
        try:
            hex_str = hex(int(binary_padded, 2))[2:].upper()
            if padding:
                hex_str = hex_str[:-1]  # Remove last nibble if padded
        except ValueError:
            hex_str = ""
    
    return {
        "binary": binary,
        "hex": hex_str or "",
        "length_bits": length_bits,
        "symbol_count": symbol_count,
    }