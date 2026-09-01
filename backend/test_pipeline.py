import numpy as np
from pipeline.phase2 import run_phase2
from pipeline.phase3 import run_phase3
from pipeline.phase4 import run_phase4
from pipeline.phase5 import run_phase5

fs = 1e6
t = np.arange(0, 0.01, 1/fs)
symbol_rate = 100e3
sps = fs / symbol_rate

def test_bpsk():
    symbols = np.random.randint(0, 2, int(len(t) / sps))
    sig = np.repeat(np.exp(1j * symbols * np.pi), int(sps))[:len(t)]
    cfo = 5000
    sig = sig * np.exp(1j * 2 * np.pi * cfo * t)
    noise = (np.random.randn(len(t)) + 1j * np.random.randn(len(t))) * 0.1
    raw = sig + noise
    return raw

def test_qpsk():
    symbols = np.random.randint(0, 4, int(len(t) / sps))
    sig = np.repeat(np.exp(1j * (np.pi/4 + symbols * np.pi/2)), int(sps))[:len(t)]
    cfo = 5000
    sig = sig * np.exp(1j * 2 * np.pi * cfo * t)
    noise = (np.random.randn(len(t)) + 1j * np.random.randn(len(t))) * 0.1
    raw = sig + noise
    return raw

def test_8psk():
    symbols = np.random.randint(0, 8, int(len(t) / sps))
    sig = np.repeat(np.exp(1j * symbols * 2*np.pi/8), int(sps))[:len(t)]
    cfo = 5000
    sig = sig * np.exp(1j * 2 * np.pi * cfo * t)
    noise = (np.random.randn(len(t)) + 1j * np.random.randn(len(t))) * 0.1
    raw = sig + noise
    return raw

def test_16qam():
    qam16 = np.array([-3-3j, -3-1j, -3+1j, -3+3j, -1-3j, -1-1j, -1+1j, -1+3j, 1-3j, 1-1j, 1+1j, 1+3j, 3-3j, 3-1j, 3+1j, 3+3j]) / np.sqrt(10)
    symbols = np.random.randint(0, 16, int(len(t) / sps))
    sig = np.repeat(qam16[symbols], int(sps))[:len(t)]
    cfo = 5000
    sig = sig * np.exp(1j * 2 * np.pi * cfo * t)
    noise = (np.random.randn(len(t)) + 1j * np.random.randn(len(t))) * 0.1
    raw = sig + noise
    return raw

def test_2fsk():
    f1, f2 = 10000, 20000
    symbols = np.random.randint(0, 2, len(t))
    freqs = np.where(symbols == 0, f1, f2)
    phase = np.cumsum(2 * np.pi * freqs / fs)
    sig = np.exp(1j * phase)
    noise = (np.random.randn(len(t)) + 1j * np.random.randn(len(t))) * 0.1
    raw = sig + noise
    return raw

def run_test(name, raw):
    dsp_sig, p2 = run_phase2(raw, fs)
    p3 = run_phase3(dsp_sig, p2, fs)
    ai = run_phase4(raw)
    d5 = run_phase5(raw, ai, p3, fs)
    evm = d5['evm_rms_pct'] if d5['evm_rms_pct'] else 'N/A'
    freq_sep = d5['frequency_separation_hz'] if d5['frequency_separation_hz'] else 'N/A'
    print(f'{name}: AI={ai["prediction"]}({ai["confidence"]:.2f}) Rx={d5["receiver"]} status={d5["status"]} bits={d5["bit_count"]} evm={evm} freq_sep={freq_sep}')

print('Testing modulation types...')
run_test('BPSK', test_bpsk())
run_test('QPSK', test_qpsk())
run_test('8PSK', test_8psk())
run_test('16QAM', test_16qam())
run_test('2FSK', test_2fsk())
print('All tests done!')