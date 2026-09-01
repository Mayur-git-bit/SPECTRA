import numpy as np
import pytest
from dsp.preprocessing import remove_dc, rms_normalize
from dsp.spectrum import estimate_psd, generate_spectrogram
from pipeline.phase2 import run_phase2

def test_remove_dc():
    # Signal with DC offset of 2.0 + 1.0j
    t = np.linspace(0, 1, 1000)
    sig = np.sin(2 * np.pi * 10 * t) + 1j * np.cos(2 * np.pi * 10 * t)
    sig_with_dc = sig + (2.0 + 1.0j)
    
    sig_no_dc, dc_val = remove_dc(sig_with_dc)
    
    assert np.isclose(dc_val.real, 2.0, atol=1e-2)
    assert np.isclose(dc_val.imag, 1.0, atol=1e-2)
    assert np.isclose(np.mean(sig_no_dc), 0.0, atol=1e-10)

def test_rms_normalize():
    sig = np.array([2.0, 2.0, -2.0, -2.0], dtype=np.complex64)
    sig_norm = rms_normalize(sig)
    
    # Power = mean(|x|^2) = mean(4) = 4
    # RMS = 2
    # Normalized = [1, 1, -1, -1]
    
    assert np.isclose(np.mean(np.abs(sig_norm)**2), 1.0)
    assert np.allclose(sig_norm.real, [1, 1, -1, -1])

def test_pipeline_phase2():
    # Generate a noisy signal with a clear tone at 100 Hz
    fs = 1000
    t = np.linspace(0, 1, fs, endpoint=False)
    tone = np.exp(1j * 2 * np.pi * 100 * t)
    noise = (np.random.randn(fs) + 1j * np.random.randn(fs)) * 0.1
    raw_sig = tone + noise + (3.0 - 2.0j)  # Add DC
    
    dsp_sig, results = run_phase2(raw_sig, sample_rate=fs)
    
    assert results["is_detected"]
    assert np.isclose(results["peak_frequency_hz"], 100.0, atol=(fs/1024)*2)
    assert results["peak_snr_db"] > 10.0
    assert np.isclose(results["dc_offset"].real, 3.0, atol=0.1)
