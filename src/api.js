// API Client for SmartSignal Backend
const API_BASE = '/api';

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function handleResponse(response) {
  if (!response.ok) {
    const contentType = response.headers.get('content-type') || '';
    let message = `HTTP ${response.status}`;

    if (contentType.includes('application/json')) {
      const error = await response.json().catch(() => null);
      message = error?.detail || error?.message || message;
    } else {
      const text = await response.text().catch(() => '');
      message = text.trim() || message;
    }

    throw new ApiError(message, response.status);
  }
  return response.json();
}

export async function uploadFile(file, iqDtype = null, sampleRate = null) {
  const formData = new FormData();
  formData.append('file', file);
  if (iqDtype) formData.append('iq_dtype', iqDtype);
  if (sampleRate) formData.append('sample_rate', sampleRate.toString());
  
  const response = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse(response);
}

export async function analyzeSignal(jobId, iqDtype = null, sampleRate = null) {
  const response = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ job_id: jobId, iq_dtype: iqDtype, sample_rate: sampleRate }),
  });
  return handleResponse(response);
}

export async function getAnalysis(jobId) {
  const response = await fetch(`${API_BASE}/analysis/${jobId}`);
  return handleResponse(response);
}

export async function getAnalysisStatus(jobId) {
  const response = await fetch(`${API_BASE}/analysis/${jobId}/status`);
  return handleResponse(response);
}

export async function getWaveform(jobId) {
  const response = await fetch(`${API_BASE}/analysis/${jobId}/waveform`);
  return handleResponse(response);
}

export async function getSpectrum(jobId) {
  const response = await fetch(`${API_BASE}/analysis/${jobId}/spectrum`);
  return handleResponse(response);
}

export async function getWaterfall(jobId) {
  const response = await fetch(`${API_BASE}/analysis/${jobId}/waterfall`);
  return handleResponse(response);
}

export async function getConstellation(jobId) {
  const response = await fetch(`${API_BASE}/analysis/${jobId}/constellation`);
  return handleResponse(response);
}

export async function getBitstream(jobId) {
  const response = await fetch(`${API_BASE}/analysis/${jobId}/bitstream`);
  return handleResponse(response);
}

export async function healthCheck() {
  const response = await fetch(`${API_BASE}/health`);
  return handleResponse(response);
}

// Polling helper
export async function pollAnalysis(jobId, onProgress, interval = 1000, maxAttempts = 300) {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const status = await getAnalysisStatus(jobId);
    onProgress(status);
    
    if (status.status === 'completed') {
      const result = await getAnalysis(jobId);
      return result;
    }
    if (status.status === 'failed') {
      throw new Error(status.error || 'Analysis failed');
    }
    
    await new Promise(resolve => setTimeout(resolve, interval));
  }
  throw new Error('Analysis timeout');
}