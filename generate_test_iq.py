"""
Generate Test IQ Files for SmartSignal Testing
===============================================
Creates various modulation test signals saved as .iq files (float32, interleaved I/Q)
"""

import numpy as np
from pathlib import Path

def save_iq(signal: np.ndarray, filepath: str):
    """Save complex64 signal as interleaved IQ float32 binary file."""
    # Ensure complex64
    signal = signal.astype(np.complex64)
    # Interleave I/Q: [I0, Q0, I1, Q1, ...]
    iq_interleaved = np.empty(len(signal) * 2, dtype=np.float32)
    iq_interleaved[0::2] = signal.real
    iq_interleaved[1::2] = signal.imag
    iq_interleaved.tofile(filepath)
    print(f"Saved: {filepath} ({len(signal)} samples, {len(signal)*8} bytes)")

def generate_qpsk(fs=1e6, duration=0.01, symbol_rate=100e3, cfo=5000, snr_db=10):
    """Generate QPSK signal with optional CFO and noise."""
    n_samples = int(fs * duration)
    t = np.arange(n_samples) / fs
    sps = fs / symbol_rate
    num_symbols = int(n_samples / sps)
    
    # Random QPSK symbols (0, 1, 2, 3) -> phases (pi/4, 3pi/4, 5pi/4, 7pi/4)
    symbols = np.random.randint(0, 4, num_symbols)
    phases = np.pi/4 + symbols * np.pi/2
    
    # Pulse shape (rectangular for simplicity)
    sig = np.repeat(np.exp(1j * phases), int(sps))[:n_samples]
    
    # Apply CFO
    sig = sig * np.exp(1j * 2 * np.pi * cfo * t)
    
    # Add AWGN
    signal_power = np.mean(np.abs(sig)**2)
    noise_power = signal_power / (10**(snr_db/10))
    noise = np.sqrt(noise_power/2) * (np.random.randn(n_samples) + 1j * np.random.randn(n_samples))
    
    return sig + noise

def generate_bpsk(fs=1e6, duration=0.01, symbol_rate=100e3, cfo=5000, snr_db=10):
    """Generate BPSK signal."""
    n_samples = int(fs * duration)
    t = np.arange(n_samples) / fs
    sps = fs / symbol_rate
    num_symbols = int(n_samples / sps)
    
    symbols = np.random.randint(0, 2, num_symbols)
    phases = symbols * np.pi  # 0 or pi
    
    sig = np.repeat(np.exp(1j * phases), int(sps))[:n_samples]
    sig = sig * np.exp(1j * 2 * np.pi * cfo * t)
    
    signal_power = np.mean(np.abs(sig)**2)
    noise_power = signal_power / (10**(snr_db/10))
    noise = np.sqrt(noise_power/2) * (np.random.randn(n_samples) + 1j * np.random.randn(n_samples))
    
    return sig + noise

def generate_8psk(fs=1e6, duration=0.01, symbol_rate=100e3, cfo=5000, snr_db=10):
    """Generate 8PSK signal."""
    n_samples = int(fs * duration)
    t = np.arange(n_samples) / fs
    sps = fs / symbol_rate
    num_symbols = int(n_samples / sps)
    
    symbols = np.random.randint(0, 8, num_symbols)
    phases = symbols * 2*np.pi/8
    
    sig = np.repeat(np.exp(1j * phases), int(sps))[:n_samples]
    sig = sig * np.exp(1j * 2 * np.pi * cfo * t)
    
    signal_power = np.mean(np.abs(sig)**2)
    noise_power = signal_power / (10**(snr_db/10))
    noise = np.sqrt(noise_power/2) * (np.random.randn(n_samples) + 1j * np.random.randn(n_samples))
    
    return sig + noise

def generate_16qam(fs=1e6, duration=0.01, symbol_rate=100e3, cfo=5000, snr_db=10):
    """Generate 16QAM signal."""
    n_samples = int(fs * duration)
    t = np.arange(n_samples) / fs
    sps = fs / symbol_rate
    num_symbols = int(n_samples / sps)
    
    # 16QAM constellation (normalized to unit average power)
    qam16 = np.array([
        -3-3j, -3-1j, -3+1j, -3+3j,
        -1-3j, -1-1j, -1+1j, -1+3j,
         1-3j,  1-1j,  1+1j,  1+3j,
         3-3j,  3-1j,  3+1j,  3+3j
    ]) / np.sqrt(10)
    
    symbols = np.random.randint(0, 16, num_symbols)
    sig = np.repeat(qam16[symbols], int(sps))[:n_samples]
    sig = sig * np.exp(1j * 2 * np.pi * cfo * t)
    
    signal_power = np.mean(np.abs(sig)**2)
    noise_power = signal_power / (10**(snr_db/10))
    noise = np.sqrt(noise_power/2) * (np.random.randn(n_samples) + 1j * np.random.randn(n_samples))
    
    return sig + noise

def generate_2fsk(fs=1e6, duration=0.01, symbol_rate=100e3, freq_sep=10000, snr_db=10):
    """Generate 2FSK signal (continuous phase)."""
    n_samples = int(fs * duration)
    t = np.arange(n_samples) / fs
    sps = fs / symbol_rate
    num_symbols = int(n_samples / sps)
    
    symbols = np.random.randint(0, 2, num_symbols)
    # Frequency for each symbol period
    freqs = np.where(symbols == 0, -freq_sep/2, freq_sep/2)
    # Repeat for each sample in symbol
    freq_per_sample = np.repeat(freqs, int(sps))[:n_samples]
    # Continuous phase
    phase = np.cumsum(2 * np.pi * freq_per_sample / fs)
    
    sig = np.exp(1j * phase)
    
    signal_power = np.mean(np.abs(sig)**2)
    noise_power = signal_power / (10**(snr_db/10))
    noise = np.sqrt(noise_power/2) * (np.random.randn(n_samples) + 1j * np.random.randn(n_samples))
    
    return sig + noise

def generate_clean_qpsk(fs=1e6, duration=0.01, symbol_rate=100e3):
    """Clean QPSK without CFO or noise (for reference)."""
    n_samples = int(fs * duration)
    sps = fs / symbol_rate
    num_symbols = int(n_samples / sps)
    
    symbols = np.random.randint(0, 4, num_symbols)
    phases = np.pi/4 + symbols * np.pi/2
    
    return np.repeat(np.exp(1j * phases), int(sps))[:n_samples]

def main():
    output_dir = Path("test_iq_files")
    output_dir.mkdir(exist_ok=True)
    
    np.random.seed(42)  # Reproducible
    
    print("Generating test IQ files...")
    print(f"Output directory: {output_dir.absolute()}")
    print()
    
    # 1. QPSK @ 10 dB SNR, 5 kHz CFO
    sig = generate_qpsk(snr_db=10, cfo=5000)
    save_iq(sig, output_dir / "qpsk_10db_5khz_cfo.iq")
    
    # 2. QPSK @ 0 dB SNR (noisy)
    sig = generate_qpsk(snr_db=0, cfo=5000)
    save_iq(sig, output_dir / "qpsk_0db_5khz_cfo.iq")
    
    # 3. QPSK @ 20 dB SNR (clean)
    sig = generate_qpsk(snr_db=20, cfo=5000)
    save_iq(sig, output_dir / "qpsk_20db_5khz_cfo.iq")
    
    # 4. BPSK
    sig = generate_bpsk(snr_db=10, cfo=5000)
    save_iq(sig, output_dir / "bpsk_10db_5khz_cfo.iq")
    
    # 5. 8PSK
    sig = generate_8psk(snr_db=10, cfo=5000)
    save_iq(sig, output_dir / "8psk_10db_5khz_cfo.iq")
    
    # 6. 16QAM
    sig = generate_16qam(snr_db=10, cfo=5000)
    save_iq(sig, output_dir / "16qam_10db_5khz_cfo.iq")
    
    # 7. 2FSK
    sig = generate_2fsk(snr_db=10, freq_sep=10000)
    save_iq(sig, output_dir / "2fsk_10db_10khz_sep.iq")
    
    # 8. Clean QPSK (no noise, no CFO) - for testing DSP chain
    sig = generate_clean_qpsk()
    save_iq(sig, output_dir / "qpsk_clean_no_cfo_no_noise.iq")
    
    # 9. QPSK with different CFO values
    for cfo in [1000, 10000, 50000]:
        sig = generate_qpsk(snr_db=10, cfo=cfo)
        save_iq(sig, output_dir / f"qpsk_10db_{cfo//1000}khz_cfo.iq")
    
    # 10. Longer duration (0.1s = 100k samples)
    sig = generate_qpsk(duration=0.1, snr_db=10, cfo=5000)
    save_iq(sig, output_dir / "qpsk_10db_5khz_cfo_long.iq")
    
    print("\nAll test files generated!")
    print(f"Files in {output_dir}:")
    for f in sorted(output_dir.glob("*.iq")):
        size = f.stat().st_size
        samples = size // 8  # 8 bytes per complex64 sample (4+4)
        print(f"  {f.name}: {size} bytes ({samples} samples)")

if __name__ == "__main__":
    main()