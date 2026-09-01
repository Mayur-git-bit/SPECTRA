# SmartSignal RF Analysis Platform - Setup Guide

## Prerequisites

### System Requirements
- **OS**: Windows 10/11, Linux (Ubuntu 20.04+), macOS 12+
- **Python**: 3.10 - 3.13 (tested on 3.13)
- **Node.js**: 18+ (for frontend)
- **RAM**: Minimum 4 GB, recommended 8 GB+
- **Disk**: 2 GB free space

### Required Tools
- Git
- Python package manager (pip)
- Node.js package manager (npm)

---

## Backend Setup

### 1. Create Virtual Environment
```bash
cd E:\SIH\Project_2\backend

# If `.venv` already exists, activate it instead of creating a new environment.

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate
```

### 2. Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**requirements.txt contents:**
```
fastapi==0.115.12
uvicorn[standard]==0.34.3
python-multipart==0.0.20
numpy>=1.26.0
scipy>=1.13.0
torch>=2.0.0
pydantic>=2.0.0
anyio>=4.0.0
python-json-logger>=2.0.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
httpx>=0.27.0
```

### 3. Verify Model File Exists
```bash
# Should exist at project root
ls ../model/mha_best.pt
# Output: ../model/mha_best.pt (8,007,127 bytes)
```

### 4. Run Backend Tests
```bash
pytest tests/ -v
```
Expected: 7 tests pass (4 Phase 1 + 3 Phase 2)

### 5. Start Backend Server
```bash
python main.py
```

**Verify:**
- Health check: use the port printed by `python main.py` (defaults to `8000`, falls back to `8001+` if needed)
- API docs: open `http://127.0.0.1:<port>/docs` in browser

---

## Frontend Setup

### 1. Install Node Dependencies
```bash
cd E:\SIH\Project_2
npm install
```

**package.json key dependencies:**
```json
{
  "dependencies": {
    "react": "^19.2.8",
    "react-dom": "^19.2.8",
    "react-router-dom": "^7.18.3"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^6.1.0",
    "vite": "^8.2.2",
    "oxlint": "^1.79.0"
  }
}
```

### 2. Build Frontend (Production)
```bash
npm run build
```
Output: `dist/` folder with optimized assets (~320 KB JS, 7 KB CSS)

### 3. Start Development Server
```bash
npm run dev
```
- Opens at `http://localhost:5173` (or 5174)
- Hot module replacement enabled
- Proxies API calls to the backend URL in `VITE_BACKEND_URL` (defaults to `http://127.0.0.1:8000`)
- If `python main.py` starts on a fallback port, set `VITE_BACKEND_URL` to match that port before starting Vite

---

## Running the Complete Application

### Option 1: Development Mode (Two Terminals)

**Terminal 1 - Backend:**
```bash
cd E:\SIH\Project_2\backend
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd E:\SIH\Project_2
npm run dev
```
- Frontend: `http://localhost:5173`
- Backend API: the port printed by `python main.py` (`8000` by default)
- CORS configured for both ports

### Option 2: Production Build
```bash
# Build frontend
cd E:\SIH\Project_2
npm run build

# Serve with backend (configure static files in main.py if needed)
cd E:\SIH\Project_2\backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## Testing the Pipeline

### 1. Quick Test with Synthetic Signal
```bash
cd E:\SIH\Project_2\backend
python -c "
import numpy as np
from pipeline.phase2 import run_phase2
from pipeline.phase3 import run_phase3
from pipeline.phase4 import run_phase4
from pipeline.phase5 import run_phase5

fs = 1e6
t = np.arange(0, 0.01, 1/fs)
symbols = np.random.randint(0, 4, int(len(t) / (fs/100e3)))
sig = np.repeat(np.exp(1j * (np.pi/4 + symbols * np.pi/2)), int(fs/100e3))[:len(t)]
sig = sig * np.exp(1j * 2 * np.pi * 5000 * t)
noise = (np.random.randn(len(t)) + 1j * np.random.randn(len(t))) * 0.1
raw = sig + noise

dsp, p2 = run_phase2(raw, fs)
p3 = run_phase3(dsp, p2, fs)
ai = run_phase4(raw)
d5 = run_phase5(raw, ai, p3, fs)
print(f'Modulation: {ai[\"prediction\"]} ({ai[\"confidence\"]:.2f})')
print(f'Demod: {d5[\"status\"]} | Bits: {d5[\"bit_count\"]} | EVM: {d5[\"evm_rms_pct\"]:.1f}%')
"
```

### 2. End-to-End API Test
```bash
cd E:\SIH\Project_2
python -c "
import requests
import numpy as np
import tempfile
import os

# Create test QPSK signal
fs = 1e6
t = np.arange(0, 0.01, 1/fs)
symbols = np.random.randint(0, 4, int(len(t) / (fs/100e3)))
sig = np.repeat(np.exp(1j * (np.pi/4 + symbols * np.pi/2)), int(fs/100e3))[:len(t)]
sig = sig * np.exp(1j * 2 * np.pi * 5000 * t)
noise = (np.random.randn(len(t)) + 1j * np.random.randn(len(t))) * 0.1
raw = sig + noise

with tempfile.NamedTemporaryFile(suffix='.iq', delete=False) as f:
    raw.astype(np.complex64).tofile(f.name)
    iq_file = f.name

# Upload
with open(iq_file, 'rb') as f:
    r = requests.post('http://127.0.0.1:8000/api/upload', files={'file': ('test.iq', f)}, data={'iq_dtype': 'float32', 'sample_rate': str(fs)})
    job_id = r.json()['job_id']

# Analyze
requests.post('http://127.0.0.1:8000/api/analyze', json={'job_id': job_id, 'iq_dtype': 'float32', 'sample_rate': fs})

# Poll
import time
for _ in range(60):
    r = requests.get(f'http://127.0.0.1:8000/api/analysis/{job_id}/status')
    if r.json()['status'] == 'completed':
        break
    time.sleep(1)

# Get results
r = requests.get(f'http://127.0.0.1:8000/api/analysis/{job_id}')
result = r.json()
print(f'Modulation: {result[\"modulation\"][\"prediction\"]} ({result[\"modulation\"][\"confidence\"]:.2f})')
print(f'Demod: {result[\"demodulation\"][\"status\"]} | Bits: {result[\"demodulation\"][\"bit_count\"]} | EVM: {result[\"demodulation\"][\"evm_rms_pct\"][\"value\"]:.1f}%')

os.unlink(iq_file)
"
```

---

## Project Structure

```
E:\SIH\Project_2\
├── backend/
│   ├── main.py                 # FastAPI app + all endpoints
│   ├── config.py               # Central configuration
│   ├── requirements.txt        # Python dependencies
│   ├── api/
│   │   └── upload.py           # POST /api/upload
│   ├── dsp/
│   │   ├── preprocessing.py    # DC removal, RMS normalize
│   │   ├── spectrum.py         # Welch PSD, STFT spectrogram
│   │   ├── noise.py            # Noise floor (10th percentile)
│   │   ├── detection.py        # Contiguous region detection
│   │   ├── filtering.py        # Adaptive bandpass (SOS filtfilt)
│   │   ├── bandwidth.py        # Region-based + energy BW
│   │   ├── snr.py              # Band-integrated SNR
│   │   ├── symbol_rate.py      # Multi-method symbol rate
│   │   ├── carrier.py          # CFO coarse→fine
│   │   ├── timing.py           # Phase offset, Gardner TED
│   │   ├── router.py           # AI family → receiver mapping
│   │   ├── synchronization.py  # Gardner, Costas, FSK disc.
│   │   ├── psk.py              # PSK demodulator
│   │   ├── fsk.py              # FSK demodulator
│   │   └── qam.py              # QAM demodulator
│   ├── file_io/
│   │   ├── iq_reader.py        # Raw IQ binary reader
│   │   ├── wav_reader.py       # WAV reader (mono/stereo)
│   │   └── metadata.py         # Basic file metadata
│   ├── models/
│   │   ├── __init__.py
│   │   └── modulation_predictor.py  # MHA model wrapper
│   ├── pipeline/
│   │   ├── phase2.py           # Classical DSP orchestrator
│   │   ├── phase3.py           # Parameter extraction
│   │   ├── phase4.py           # AI classification
│   │   └── phase5.py           # Adaptive demodulation
│   ├── schemas/
│   │   └── analysis.py         # All Pydantic models
│   ├── visualization/
│   │   └── __init__.py         # Downsampling for UI
│   ├── tests/
│   │   ├── test_phase1.py      # File I/O tests
│   │   └── test_phase2.py      # DSP tests
│   ├── uploads/                # Staging area (auto-created)
│   └── results/                # Analysis cache (auto-created)
├── model/
│   ├── mha_best.pt             # Pre-trained MHA weights (8 MB)
│   └── modulation-detection.ipynb  # Training notebook
├── src/                        # React frontend
│   ├── main.jsx                # Entry point
│   ├── App.jsx                 # Router + routes
│   ├── api.js                  # API client + polling
│   ├── components/
│   │   ├── Sidebar.jsx         # Navigation
│   │   └── TopBar.jsx          # Header with upload
│   ├── pages/
│   │   ├── Dashboard.jsx       # Main dashboard (live data)
│   │   ├── AIAnalysis.jsx      # AI predictions + constellation
│   │   ├── DSPPipeline.jsx     # DSP flow editor
│   │   ├── BitStreamAnalysis.jsx # Bitstream terminal
│   │   ├── SignalDetection.jsx # Spectrum monitor
│   │   └── Home.jsx            # Landing page
│   └── assets/
├── package.json
├── vite.config.js
└── index.html
```

---

## Configuration

### Key Config Options (`backend/config.py`)
```python
# Model
MODEL_PATH = PROJECT_ROOT / "model" / "mha_best.pt"
MODEL_CLASS_NAMES = ["FSK", "QAM", "QPSK", "PSK"]
MODEL_INPUT_LENGTH = 1024
MODEL_NORM_EPS = 1e-6

# DSP Parameters
WELCH_NPERSEG = 1024
WELCH_NOVERLAP = 512
NOISE_FLOOR_PERCENTILE = 10
DETECTION_THRESHOLD_DB = 6.0
FILTER_GUARD_BAND = 0.1

# Visualization Limits
WAVEFORM_MAX_POINTS = 4096
SPECTRUM_MAX_POINTS = 2048
WATERFALL_MAX_TIME_BINS = 256
CONSTELLATION_MAX_POINTS = 2000

# API
CORS_ORIGINS = ["http://localhost:5173", "http://localhost:5174"]
MAX_UPLOAD_BYTES = 200 * 1024 * 1024
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: torch` | `pip install torch --index-url https://download.pytorch.org/whl/cpu` |
| `ModuleNotFoundError: scipy` | `pip install scipy>=1.13.0` |
| Model not found | Verify `model/mha_best.pt` exists at project root |
| CORS errors | Backend `CORS_ORIGINS` must match frontend port (5173/5174) |
| Frontend build fails | Check for template literals in JSX style objects (use string concat) |
| `uvicorn` not found | `pip install uvicorn[standard]` |
| Port 8000 blocked or in use | Run `python main.py`; it falls back automatically, or set `API_PORT` to a free port |

### Backend Logs
```bash
# Set log level
$env:LOG_LEVEL="DEBUG"  # Windows
# export LOG_LEVEL=DEBUG  # Linux/macOS
python main.py
```

### Frontend DevTools
- Open browser DevTools → Console/Network tabs
- React DevTools extension recommended
- Check Network tab for API calls to `/api/analysis/{job_id}/*`

---

## Development Workflow

### Adding New DSP Module
1. Create `backend/dsp/new_module.py` with functions
2. Import in `backend/pipeline/phase3.py` or `phase2.py`
3. Add tests in `backend/tests/test_phaseX.py`
4. Run `pytest tests/ -v`

### Adding New Modulation Type
1. Update `MODEL_CLASS_NAMES` in `config.py`
2. Retrain model (see `model/modulation-detection.ipynb`)
3. Add demodulator in `backend/dsp/` (psk/fsk/qam pattern)
4. Register in `backend/dsp/router.py`
5. Add mapping in `backend/pipeline/phase5.py`

### Frontend Changes
- Components in `src/components/`
- Pages in `src/pages/` (auto-routed via App.jsx)
- API calls in `src/api.js`
- Styles: CSS variables in `src/index.css`

---

## Deployment Notes

### Docker (Optional)
```dockerfile
# Backend
FROM python:3.13-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ .
COPY model/mha_best.pt /app/model/
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Frontend (multi-stage)
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json .
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

### Environment Variables
```bash
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR
API_PORT=8000           # Backend port
FRONTEND_PORT=5173      # Vite dev server
```

---

## Support

For issues:
1. Check backend logs for `[PHASE X]` prefixed messages
2. Verify model loads: `[PHASE 4] Model loaded successfully (epoch=12, val_acc=0.7922)`
3. Check API docs at `http://127.0.0.1:8000/docs`
4. Frontend network tab for failed visualization endpoints