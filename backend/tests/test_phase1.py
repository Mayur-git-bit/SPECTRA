import os
import wave
import numpy as np
import pytest
from pathlib import Path

from file_io.iq_reader import read_iq_file
from file_io.wav_reader import read_wav_file

TEST_DIR = Path(__file__).parent / "test_data"
TEST_DIR.mkdir(exist_ok=True)

def create_dummy_wav(path: Path, channels: int, sample_width: int, framerate: int, num_frames: int):
    # Generate some dummy data
    t = np.linspace(0, num_frames / framerate, num_frames, endpoint=False)
    # 1 kHz tone for I
    i_sig = np.sin(2 * np.pi * 1000 * t)
    
    if channels == 2:
        # Cosine for Q
        q_sig = np.cos(2 * np.pi * 1000 * t)
        data = np.zeros(num_frames * 2)
        data[0::2] = i_sig
        data[1::2] = q_sig
    else:
        data = i_sig
        
    # Scale to int16
    if sample_width == 2:
        data = (data * 32767).astype(np.int16)
    
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(framerate)
        wf.writeframes(data.tobytes())

def create_dummy_iq(path: Path, num_samples: int):
    t = np.linspace(0, num_samples / 1e6, num_samples, endpoint=False)
    i_sig = np.sin(2 * np.pi * 1000 * t)
    q_sig = np.cos(2 * np.pi * 1000 * t)
    
    data = np.zeros(num_samples * 2, dtype=np.float32)
    data[0::2] = i_sig
    data[1::2] = q_sig
    data.tofile(str(path))

def test_read_wav_stereo():
    wav_path = TEST_DIR / "stereo.wav"
    create_dummy_wav(wav_path, channels=2, sample_width=2, framerate=48000, num_frames=4800)
    
    signal, meta = read_wav_file(wav_path)
    
    assert signal.dtype == np.complex64
    assert len(signal) == 4800
    assert meta["channels"] == 2
    assert meta["sampling_rate"]["value"] == 48000
    assert meta["real_only"] is False
    assert abs(signal[0].real) < 0.1  # Sin start at 0
    assert signal[0].imag > 0.9       # Cos starts at 1
    
    wav_path.unlink()

def test_read_wav_mono():
    wav_path = TEST_DIR / "mono.wav"
    create_dummy_wav(wav_path, channels=1, sample_width=2, framerate=48000, num_frames=4800)
    
    signal, meta = read_wav_file(wav_path)
    
    assert len(signal) == 4800
    assert meta["channels"] == 1
    assert meta["real_only"] is True
    # All imaginary components should be 0
    assert np.all(signal.imag == 0)
    
    wav_path.unlink()

def test_read_iq_float32():
    iq_path = TEST_DIR / "test.iq"
    create_dummy_iq(iq_path, num_samples=10000)
    
    signal, meta = read_iq_file(iq_path, dtype_name="float32", sample_rate=1e6)
    
    assert signal.dtype == np.complex64
    assert len(signal) == 10000
    assert meta["iq_dtype"] == "float32"
    assert meta["channels"] == 2
    assert meta["sample_count"] == 10000
    assert meta["sampling_rate"]["value"] == 1e6
    assert meta["duration"]["value"] == 0.01  # 10k / 1M
    
    iq_path.unlink()

def test_read_iq_invalid_size():
    iq_path = TEST_DIR / "invalid.iq"
    with open(iq_path, "wb") as f:
        f.write(b"123") # 3 bytes, not divisible by 8 (float32 pair)
        
    with pytest.raises(ValueError):
        read_iq_file(iq_path, dtype_name="float32")
        
    iq_path.unlink()
