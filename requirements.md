# SmartSignal RF Analysis Platform - Requirements Document

## Project Overview
**SmartSignal AI Platform (SmartSignal SIGINT v4.2)** - An AI-powered RF signal intelligence platform for automated modulation classification, DSP analysis, demodulation, and bitstream decoding from raw RF recordings.

## System Requirements

### Functional Requirements

#### Phase 1: File Ingestion
- **FR-1.1**: Accept `.iq` and `.wav` files (case-insensitive extensions)
- **FR-1.2**: Support IQ formats: float32, float64, int16, int8, uint8 (interleaved I/Q)
- **FR-1.3**: Support WAV formats: 8/16/24/32-bit PCM, mono (real-only) and stereo (I=ch0, Q=ch1)
- **FR-1.4**: Extract metadata: sample rate, duration, channel count, sample format, file size
- **FR-1.5**: Never fabricate sampling rate - mark as "unavailable" if not in file header
- **FR-1.6**: Convert all input to complex64 (x[n] = I[n] + jQ[n])
- **FR-1.7**: Maximum upload size: 200 MB

#### Phase 2: Classical DSP Branch
- **FR-2.1**: DC removal: μ = (1/N) Σ x[n], x_dc[n] = x[n] - μ
- **FR-2.2**: RMS normalization: P = (1/N) Σ |x[n]|², x_norm[n] = x_dc[n] / √P (guard against zero power)
- **FR-2.3**: PSD estimation via Welch method (scipy.signal.welch, onesided=False, fftshift)
  - Configurable: nperseg=1024, noverlap=512, Hann window
- **FR-2.4**: Waterfall/Spectrogram via STFT (scipy.signal.stft, onesided=False, fftshift)
  - Configurable: nperseg=256, noverlap=192
- **FR-2.5**: Noise floor estimation: 10th percentile of linear PSD
- **FR-2.6**: Signal detection: Contiguous regions > noise_floor + 6dB, minimum 3-bin width
  - Returns: detected flag, peak value, peak index, lower/upper frequency edges
- **FR-2.7**: Adaptive bandpass filtering: frequency shift → SOS lowpass (filtfilt) → shift back
  - 10% guard bands on each side of detected region

#### Phase 3: Parameter Extraction
- **FR-3.1**: Bandwidth from detected region edges (preferred) or 99% energy containment
- **FR-3.2**: SNR: band-integrated (signal_power = band_power - noise_in_band) / noise_in_band
- **FR-3.3**: Symbol rate estimation:
  - Envelope power FFT for QAM/ASK
  - M-th power FFT (M=2,4,8) for PSK/FSK
  - Harmonic discrimination to find fundamental
  - Confidence scoring (prominence, harmonic count)
  - Returns: symbol_rate_hz, status (estimated/low_confidence/unavailable), confidence
- **FR-3.4**: CFO estimation: Coarse-to-fine M-th power (M=2,4,8)
  - Coarse: peak of |FFT(x^M)| / M
  - Fine: correct coarse, re-estimate residual within ±1% Fs
  - Returns: cfo_hz, coarse_cfo_hz, fine_cfo_hz, status, confidence
- **FR-3.5**: Phase offset: M-th power angle mean with concentration metric
- **FR-3.6**: Timing offset: Gardner TED with autocorrelation-based SPS estimation
- **FR-3.7**: All parameters include: value, unit, status, confidence, method

#### Phase 4: AI Modulation Classification
- **FR-4.1**: Load pre-trained MHA model (`mha_best.pt`) once at startup
- **FR-4.2**: Model architecture: Residual CNN + Multi-Head Attention
  - SignalCNN: stem(2→64) → RB(64→128) → RB(128→256) → RB(256→256) → output (B,256,128)
  - Positional encoding: (1,128,256) * 0.02
  - MHA: 8 heads, dropout=0.1, LayerNorm, FFN(256→1024→256)
  - Classifier: Linear(256→256) → LayerNorm → GELU → Dropout(0.35) → Linear(256→4)
- **FR-4.3**: Model-specific preprocessing (exact RadioMLDataset match):
  - Select 1024-sample window (max energy)
  - Per-channel normalization: (x - mean) / (std + 1e-6)
  - Transpose to (2, 1024), float32 tensor
- **FR-4.4**: Classes: FSK(0), QAM(1), QPSK(2), PSK(3)
- **FR-4.5**: Output: top-1 prediction, confidence, all class probabilities

#### Phase 5: Adaptive Demodulation
- **FR-5.1**: Router maps AI family → receiver (FSK→FSK, QAM→QAM, QPSK/PSK→PSK)
- **FR-5.2**: PSK demodulator: CFO corr → Gardner timing → Costas loop → constellation decision → Gray bits
- **FR-5.3**: FSK demodulator: Frequency discriminator → smoothing → symbol timing → freq clustering → Gray bits
- **FR-5.4**: QAM demodulator: CFO corr → Gardner timing → Costas (decision-directed) → constellation decision → Gray bits
- **FR-5.5**: Synchronization loops:
  - Gardner TED (2 samples/symbol)
  - Costas loop (BPSK: I×Q, QPSK: sign(I)Q - sign(Q)I, M-PSK: arg(x^M)/M)
  - FSK discriminator: angle(x[n]·conj(x[n-1])) × Fs/(2π)
- **FR-5.6**: EVM calculation for PSK/QAM: RMS(|received - decision|² / |decision|²) × 100%
- **FR-5.7**: Bitstream output: binary string, hex string, bit count, symbol count

#### API Endpoints
- **FR-API-1**: POST `/api/upload` - File upload, returns job_id
- **FR-API-2**: POST `/api/analyze` - Start analysis with iq_dtype, sample_rate
- **FR-API-3**: GET `/api/analysis/{job_id}` - Complete AnalysisResult
- **FR-API-4**: GET `/api/analysis/{job_id}/status` - JobStatus (progress, message)
- **FR-API-5**: GET `/api/analysis/{job_id}/waveform` - WaveformData
- **FR-API-6**: GET `/api/analysis/{job_id}/spectrum` - SpectrumData
- **FR-API-7**: GET `/api/analysis/{job_id}/waterfall` - WaterfallData
- **FR-API-8**: GET `/api/analysis/{job_id}/constellation` - ConstellationData
- **FR-API-9**: GET `/api/analysis/{job_id}/bitstream` - BitstreamData
- **FR-API-10**: GET `/api/health` - Health check

#### Frontend (React + Vite)
- **FR-FE-1**: Dashboard with live pipeline status (5 phases)
- **FR-FE-2**: Interactive visualizations (canvas-based):
  - Waveform: I/Q channels, amplitude
  - Spectrum: PSD with noise floor line, peak marker
  - Waterfall: STFT spectrogram with color mapping
  - Constellation: Recovered symbols with grid/axes
- **FR-FE-3**: AI predictions panel with probability bars
- **FR-FE-4**: Bitstream terminal with binary/hex/ASCII views
- **FR-FE-5**: File upload drag-and-drop with progress polling

### Non-Functional Requirements
- **NFR-1**: Model loads once at startup, not per request
- **NFR-2**: All DSP uses mathematically established techniques (scipy.signal)
- **NFR-3**: No fabricated parameters - return "unavailable" or "low_confidence"
- **NFR-4**: AI branch uses raw IQ + notebook preprocessing ONLY (no DSP preprocessing)
- **NFR-5**: DSP branch uses DC removal + RMS normalization (separate from AI)
- **NFR-6**: Visualization data downsampled (waveform 4096 pts, spectrum 2048 bins, waterfall 256×128, constellation 2000 pts)
- **NFR-7**: Error handling: graceful degradation, no crashes on parameter failure
- **NFR-8**: CORS enabled for Vite dev servers (5173, 5174)

## Technical Constraints
- **Python**: 3.10+ (tested on 3.13)
- **PyTorch**: 2.0+ (CPU version)
- **Key dependencies**: fastapi, uvicorn, numpy, scipy, pydantic, torch
- **Frontend**: React 19, Vite 8, React Router 7
- **OS**: Cross-platform (Windows/Linux/macOS)

## Data Models (Pydantic)
All API contracts defined in `backend/schemas/analysis.py`:
- `MeasuredValue`: value, unit, status
- `AnalysisResult`: Complete result with all phases
- Visualization payloads: WaveformData, SpectrumData, WaterfallData, ConstellationData, BitstreamData

## Acceptance Criteria
1. Upload 10-second QPSK .iq file → get modulation=QPSK, demod=completed, bits>0, constellation displayed
2. Upload 16QAM .wav → modulation=QAM, EVM displayed, bitstream in terminal
3. Upload 2FSK .iq → modulation=FSK, frequency separation displayed
4. All visualization endpoints return valid data for PSK/QAM
5. Constellation endpoint returns 404 for FSK (expected - no traditional constellation)
6. Pipeline status updates in real-time during processing
7. Build succeeds for both backend (tests pass) and frontend (npm run build)