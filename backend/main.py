"""
FastAPI application entry point.
"""

import logging
import socket
import uuid
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import (
    API_TITLE,
    API_VERSION,
    API_PREFIX,
    API_HOST,
    API_PORT,
    API_PORT_FALLBACK_COUNT,
    CORS_ORIGINS,
    UPLOAD_DIR,
    RESULTS_DIR,
)
from api import upload

# Job storage (in-memory for now)
job_store = {}

# Setup basic logging for backend
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting SmartSignal Backend...")
    # Initialize models or heavy resources here if needed globally
    from models.modulation_predictor import get_modulation_predictor
    predictor = get_modulation_predictor()
    predictor.load_model()
    logger.info("Model loaded and ready")
    yield
    logger.info("Shutting down SmartSignal Backend...")


app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(upload.router, prefix=API_PREFIX)


@app.get("/api/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}


@app.get("/")
async def root():
    """Backend landing page for direct browser access."""
    return {
        "message": "SmartSignal RF Analysis API is running.",
        "health": "/api/health",
        "docs": "/docs",
    }


# ============================================================
# ANALYSIS ENDPOINTS
# ============================================================

from fastapi import BackgroundTasks, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import numpy as np

from file_io.iq_reader import read_iq_file
from file_io.wav_reader import read_wav_file
from pipeline.phase2 import run_phase2
from pipeline.phase3 import run_phase3
from pipeline.phase4 import run_phase4
from pipeline.phase5 import run_phase5
from schemas.analysis import (
    AnalysisResult, FileInfo, AcquisitionInfo, SpectralInfo,
    ModulationInfo, SyncInfo, DemodInfo, BitstreamInfo, JobStatus,
    WaveformData, SpectrumData, WaterfallData, ConstellationData, BitstreamData
)


class AnalyzeRequest(BaseModel):
    job_id: str
    iq_dtype: Optional[str] = None
    sample_rate: Optional[float] = None


def update_job(job_id: str, status: str, progress: int = 0, message: str = "", error: Optional[str] = None):
    """Update job status in store."""
    job_store[job_id] = JobStatus(
        job_id=job_id,
        status=status,
        progress=progress,
        message=message,
        error=error
    )


async def process_analysis(job_id: str, file_path: str, iq_dtype: Optional[str], sample_rate: Optional[float]):
    """Background task to process the signal analysis."""
    try:
        update_job(job_id, "reading", 5, "Reading file...")
        
        # Phase 1: Read file
        ext = file_path.suffix.lower()
        if ext == ".iq":
            signal, metadata = read_iq_file(file_path, dtype_name=iq_dtype or "float32", sample_rate=sample_rate)
        elif ext == ".wav":
            signal, metadata = read_wav_file(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
        
        fs = metadata.get("sampling_rate", {}).get("value")
        if fs is None:
            fs = 1.0  # Normalized frequency
        
        update_job(job_id, "phase1", 10, "File read complete")
        
        # Phase 2: Classical DSP
        update_job(job_id, "phase2", 20, "Running DSP analysis...")
        dsp_signal, phase2_results = run_phase2(signal, fs)
        update_job(job_id, "phase2", 40, "DSP analysis complete")
        
        # Phase 3: Parameter extraction
        update_job(job_id, "phase3", 50, "Extracting signal parameters...")
        phase3_results = run_phase3(dsp_signal, phase2_results, fs)
        update_job(job_id, "phase3", 60, "Parameter extraction complete")
        
        # Phase 4: AI Modulation Classification
        update_job(job_id, "phase4", 70, "Running AI classification...")
        ai_result = run_phase4(signal)  # Use RAW signal for AI branch
        update_job(job_id, "phase4", 80, "AI classification complete")
        
        # Phase 5: Adaptive Demodulation
        update_job(job_id, "phase5", 90, "Running adaptive demodulation...")
        demod_result = run_phase5(signal, ai_result, phase3_results, fs)
        update_job(job_id, "phase5", 95, "Demodulation complete")
        
        # Build final result
        result = build_analysis_result(
            job_id=job_id,
            file_path=file_path,
            metadata=metadata,
            phase2_results=phase2_results,
            phase3_results=phase3_results,
            ai_result=ai_result,
            demod_result=demod_result,
            fs=fs
        )
        
        # Save result
        import json
        result_file = RESULTS_DIR / f"{job_id}.json"
        with open(result_file, "w") as f:
            json.dump(result.model_dump(), f, indent=2)
        
        update_job(job_id, "completed", 100, "Analysis complete")
        logger.info(f"[JOB {job_id}] Analysis completed successfully")
        
    except Exception as e:
        logger.error(f"[JOB {job_id}] Analysis failed: {e}")
        update_job(job_id, "failed", 0, "Analysis failed", str(e))


def build_analysis_result(
    job_id: str,
    file_path,
    metadata: dict,
    phase2_results: dict,
    phase3_results: dict,
    ai_result: dict,
    demod_result: dict,
    fs: float
) -> AnalysisResult:
    """Build the complete AnalysisResult from all phase outputs."""
    
    # File info
    file_info = FileInfo(
        name=file_path.name,
        format=metadata.get("format", "UNKNOWN"),
        size_bytes=metadata.get("size_bytes", 0),
        iq_dtype=metadata.get("iq_dtype"),
        channels=metadata.get("channels"),
    )
    
    # Acquisition info
    sample_count = metadata.get("sample_count", 0)
    duration_val = metadata.get("duration", {}).get("value")
    duration_status = metadata.get("duration", {}).get("status", "unavailable")
    sr_val = metadata.get("sampling_rate", {}).get("value")
    sr_status = metadata.get("sampling_rate", {}).get("status", "unavailable")
    
    acquisition = AcquisitionInfo(
        sampling_rate={"value": sr_val, "unit": "Hz", "status": sr_status},
        sample_count=sample_count,
        duration={"value": duration_val, "unit": "s", "status": duration_status},
    )
    
    # Spectral info
    spectral = SpectralInfo(
        peak_frequency={"value": phase2_results.get("peak_frequency_hz"), "unit": "Hz", "status": "estimated"},
        bandwidth={"value": phase3_results.get("bandwidth_hz"), "unit": "Hz", "status": "estimated"},
        lower_edge={"value": phase3_results.get("lower_edge_hz"), "unit": "Hz", "status": "estimated"},
        upper_edge={"value": phase3_results.get("upper_edge_hz"), "unit": "Hz", "status": "estimated"},
        noise_floor_db={"value": phase2_results.get("noise_floor_db"), "unit": "dB", "status": "estimated"},
        snr_db={"value": phase3_results.get("snr_db"), "unit": "dB", "status": phase3_results.get("snr_status", "estimated")},
    )
    
    # Modulation info
    modulation = ModulationInfo(
        prediction=ai_result.get("prediction"),
        confidence=ai_result.get("confidence"),
        probabilities=ai_result.get("probabilities", {}),
        status=ai_result.get("status", "unavailable"),
    )
    
    # Synchronization info
    sync = SyncInfo(
        symbol_rate={"value": phase3_results.get("symbol_rate_hz"), "unit": "symbols/s", "status": phase3_results.get("symbol_rate_status", "unavailable")},
        samples_per_symbol={"value": phase3_results.get("samples_per_symbol"), "unit": "samples/symbol", "status": phase3_results.get("samples_per_symbol_status", "unavailable")},
        frequency_offset_hz={"value": phase3_results.get("cfo_hz"), "unit": "Hz", "status": phase3_results.get("cfo_status", "unavailable")},
        phase_offset_rad={"value": phase3_results.get("phase_offset_rad"), "unit": "rad", "status": phase3_results.get("phase_offset_status", "unavailable")},
        timing_offset={"value": phase3_results.get("timing_offset"), "unit": "samples", "status": phase3_results.get("timing_offset_status", "unavailable")},
    )
    
    # Demodulation info
    demod = DemodInfo(
        receiver=demod_result.get("receiver"),
        status=demod_result.get("status", "not_started"),
        symbol_count=demod_result.get("symbol_count"),
        bit_count=demod_result.get("bit_count"),
        evm_rms_pct={"value": demod_result.get("evm_rms_pct"), "unit": "%", "status": "estimated" if demod_result.get("evm_rms_pct") else "unavailable"},
        ber={"value": demod_result.get("ber"), "unit": "", "status": "unavailable"},
        constellation_i=demod_result.get("constellation_i"),
        constellation_q=demod_result.get("constellation_q"),
    )
    
    # Bitstream info
    bitstream = BitstreamInfo(
        length_bits=demod_result.get("bit_count"),
        binary_preview=demod_result.get("bits_binary")[:512] if demod_result.get("bits_binary") else None,
        hex_preview=demod_result.get("bits_hex")[:128] if demod_result.get("bits_hex") else None,
        status=demod_result.get("status", "unavailable"),
    )
    
    return AnalysisResult(
        job_id=job_id,
        status="completed",
        file=file_info,
        acquisition=acquisition,
        spectral=spectral,
        modulation=modulation,
        synchronization=sync,
        demodulation=demod,
        bitstream=bitstream,
    )


@app.post("/api/analyze")
async def analyze_signal(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """Start signal analysis for an uploaded file."""
    job_id = request.job_id
    
    # Find the uploaded file
    file_path = None
    for ext in [".iq", ".wav"]:
        p = UPLOAD_DIR / f"{job_id}{ext}"
        if p.exists():
            file_path = p
            break
    
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found for job_id")
    
    # Initialize job status
    update_job(job_id, "queued", 0, "Job queued for analysis")
    
    # Start background processing
    background_tasks.add_task(process_analysis, job_id, file_path, request.iq_dtype, request.sample_rate)
    
    return {"job_id": job_id, "status": "queued", "message": "Analysis started"}


@app.get("/api/analysis/{job_id}")
async def get_analysis(job_id: str):
    """Get analysis results for a job."""
    # Check job status first
    if job_id in job_store:
        job = job_store[job_id]
        if job.status != "completed":
            return job
    
    # Try to load saved result
    result_file = RESULTS_DIR / f"{job_id}.json"
    if not result_file.exists():
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    import json
    with open(result_file, "r") as f:
        data = json.load(f)
    
    return data


@app.get("/api/analysis/{job_id}/status")
async def get_analysis_status(job_id: str):
    """Get job status."""
    if job_id in job_store:
        return job_store[job_id]
    
    result_file = RESULTS_DIR / f"{job_id}.json"
    if result_file.exists():
        return JobStatus(job_id=job_id, status="completed", progress=100, message="Analysis complete")
    
    raise HTTPException(status_code=404, detail="Job not found")


# ============================================================
# VISUALIZATION ENDPOINTS
# ============================================================

from visualization import (
    generate_waveform_data,
    generate_spectrum_data,
    generate_waterfall_data,
    generate_constellation_data,
    generate_bitstream_data,
)


@app.get("/api/analysis/{job_id}/waveform", response_model=WaveformData)
async def get_waveform(job_id: str):
    """Get waveform visualization data."""
    # Load the original signal
    file_path = None
    for ext in [".iq", ".wav"]:
        p = UPLOAD_DIR / f"{job_id}{ext}"
        if p.exists():
            file_path = p
            break
    
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
    
    ext = file_path.suffix.lower()
    if ext == ".iq":
        signal, _ = read_iq_file(file_path, dtype_name="float32")
    else:
        signal, _ = read_wav_file(file_path)
    
    return generate_waveform_data(signal)


@app.get("/api/analysis/{job_id}/spectrum", response_model=SpectrumData)
async def get_spectrum(job_id: str):
    """Get spectrum (PSD) visualization data."""
    file_path = None
    for ext in [".iq", ".wav"]:
        p = UPLOAD_DIR / f"{job_id}{ext}"
        if p.exists():
            file_path = p
            break
    
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
    
    ext = file_path.suffix.lower()
    if ext == ".iq":
        signal, _ = read_iq_file(file_path, dtype_name="float32")
    else:
        signal, _ = read_wav_file(file_path)
    
    # Use DSP branch signal for spectrum
    from pipeline.phase2 import run_phase2
    dsp_signal, p2 = run_phase2(signal, 1.0)
    return generate_spectrum_data(dsp_signal, p2)


@app.get("/api/analysis/{job_id}/waterfall", response_model=WaterfallData)
async def get_waterfall(job_id: str):
    """Get waterfall (spectrogram) visualization data."""
    file_path = None
    for ext in [".iq", ".wav"]:
        p = UPLOAD_DIR / f"{job_id}{ext}"
        if p.exists():
            file_path = p
            break
    
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
    
    ext = file_path.suffix.lower()
    if ext == ".iq":
        signal, _ = read_iq_file(file_path, dtype_name="float32")
    else:
        signal, _ = read_wav_file(file_path)
    
    return generate_waterfall_data(signal)


@app.get("/api/analysis/{job_id}/constellation", response_model=ConstellationData)
async def get_constellation(job_id: str):
    """Get constellation visualization data from demodulation result."""
    result_file = RESULTS_DIR / f"{job_id}.json"
    if not result_file.exists():
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    import json
    with open(result_file, "r") as f:
        data = json.load(f)
    
    constellation_i = data.get("demodulation", {}).get("constellation_i")
    constellation_q = data.get("demodulation", {}).get("constellation_q")
    modulation = data.get("modulation", {}).get("prediction")
    
    if constellation_i is None or constellation_q is None:
        raise HTTPException(status_code=404, detail="Constellation data not available")
    
    return generate_constellation_data(constellation_i, constellation_q, modulation)


@app.get("/api/analysis/{job_id}/bitstream", response_model=BitstreamData)
async def get_bitstream(job_id: str):
    """Get full bitstream data."""
    result_file = RESULTS_DIR / f"{job_id}.json"
    if not result_file.exists():
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    import json
    import traceback
    with open(result_file, "r") as f:
        data = json.load(f)
    
    bitstream = data.get("bitstream", {})
    binary = bitstream.get("binary_preview", "")
    hex_str = bitstream.get("hex_preview", "")
    length = bitstream.get("length_bits", 0)
    
    # Calculate symbol count
    demod = data.get("demodulation", {})
    symbol_count = demod.get("symbol_count", 0)
    
    try:
        return generate_bitstream_data(binary, hex_str, length, symbol_count)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Bitstream generation failed: {str(e)}")


def _port_is_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True


def _select_startup_port(host: str, preferred_port: int, fallback_count: int) -> int:
    for offset in range(max(1, fallback_count)):
        candidate_port = preferred_port + offset
        if _port_is_available(host, candidate_port):
            return candidate_port
    raise RuntimeError(
        f"No available port found starting at {preferred_port}. "
        f"Set API_PORT to a free port or raise API_PORT_FALLBACK_COUNT."
    )


if __name__ == "__main__":
    import uvicorn

    selected_port = _select_startup_port(API_HOST, API_PORT, API_PORT_FALLBACK_COUNT)
    if selected_port != API_PORT:
        logger.warning(
            "Port %s is unavailable on %s; starting on fallback port %s instead.",
            API_PORT,
            API_HOST,
            selected_port,
        )

    uvicorn.run("main:app", host=API_HOST, port=selected_port, reload=True)