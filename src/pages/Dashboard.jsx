import { useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import TopBar from '../components/TopBar';
import { useAnalysis } from '../context/AnalysisContext';
import { uploadAndAnalyzeSignal } from '../utils/signalUpload';

// Simple canvas-based waveform renderer
function WaveformCanvas({ i_samples: iSamples, q_samples: qSamples, amplitude, time }) {
  const canvasRef = useRef(null);
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !iSamples || !qSamples) return;
    
    const ctx = canvas.getContext('2d');
    const parent = canvas.parentElement;
    canvas.width = parent.clientWidth;
    canvas.height = parent.clientHeight;
    
    const width = canvas.width;
    const height = canvas.height;
    const centerY = height / 2;
    const scale = height * 0.4;
    
    // Clear
    ctx.clearRect(0, 0, width, height);
    
    // Grid
    ctx.strokeStyle = 'rgba(74, 68, 85, 0.1)';
    ctx.lineWidth = 1;
    for (let y = 0; y < height; y += 20) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke();
    }
    for (let x = 0; x < width; x += 20) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke();
    }
    
    // Draw I channel
    ctx.beginPath();
    ctx.strokeStyle = '#5de6ff';
    ctx.lineWidth = 1.5;
    ctx.shadowColor = '#5de6ff';
    ctx.shadowBlur = 4;
    
    const stepX = width / Math.max(1, iSamples.length - 1);
    iSamples.forEach((val, i) => {
      const x = i * stepX;
      const y = centerY - val * scale;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
    ctx.shadowBlur = 0;
    
    // Draw Q channel
    ctx.beginPath();
    ctx.strokeStyle = '#ffb4ab';
    ctx.lineWidth = 1;
    qSamples.forEach((val, i) => {
      const x = i * stepX;
      const y = centerY - val * scale;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }, [iSamples, qSamples]);
  
  return (
    <canvas ref={canvasRef} style={{ width: '100%', height: '100%', display: 'block' }} />
  );
}

// Spectrum canvas renderer
function SpectrumCanvas({
  frequency,
  power_db: powerDb,
  noise_floor_db: noiseFloorDb,
  peak_frequency_hz: peakFrequencyHz
}) {
  const canvasRef = useRef(null);
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !frequency || !powerDb) return;
    
    const ctx = canvas.getContext('2d');
    const parent = canvas.parentElement;
    canvas.width = parent.clientWidth;
    canvas.height = parent.clientHeight;
    
    const width = canvas.width;
    const height = canvas.height;
    const padding = 40;
    
    ctx.clearRect(0, 0, width, height);
    
    // Grid
    ctx.strokeStyle = 'rgba(74, 68, 85, 0.1)';
    ctx.lineWidth = 1;
    for (let y = padding; y < height - padding; y += 30) {
      ctx.beginPath(); ctx.moveTo(padding, y); ctx.lineTo(width - padding, y); ctx.stroke();
    }
    for (let x = padding; x < width - padding; x += 50) {
      ctx.beginPath(); ctx.moveTo(x, padding); ctx.lineTo(x, height - padding); ctx.stroke();
    }
    
    // Find min/max power for scaling
    const minDb = Math.min(...powerDb);
    const maxDb = Math.max(...powerDb);
    const dbRange = maxDb - minDb || 1;
    
    // Draw spectrum
    ctx.beginPath();
    ctx.strokeStyle = '#5de6ff';
    ctx.lineWidth = 2;
    ctx.shadowColor = '#5de6ff';
    ctx.shadowBlur = 4;
    
    const xScale = (width - 2 * padding) / (frequency.length - 1);
    const yScale = (height - 2 * padding) / dbRange;
    
    powerDb.forEach((db, i) => {
      const x = padding + i * xScale;
      const y = height - padding - (db - minDb) * yScale;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
    ctx.shadowBlur = 0;
    
    // Noise floor line
    if (noiseFloorDb !== undefined && noiseFloorDb !== null) {
      const y = height - padding - (noiseFloorDb - minDb) * yScale;
      ctx.beginPath();
      ctx.strokeStyle = 'rgba(255, 180, 171, 0.8)';
      ctx.lineWidth = 1;
      ctx.setLineDash([5, 5]);
      ctx.moveTo(padding, y);
      ctx.lineTo(width - padding, y);
      ctx.stroke();
      ctx.setLineDash([]);
    }
    
    // Peak marker
    if (peakFrequencyHz !== undefined && peakFrequencyHz !== null) {
      const peakIdx = powerDb.indexOf(Math.max(...powerDb));
      if (peakIdx >= 0) {
        const x = padding + peakIdx * xScale;
        const y = height - padding - (powerDb[peakIdx] - minDb) * yScale;
        ctx.beginPath();
        ctx.arc(x, y, 6, 0, Math.PI * 2);
        ctx.fillStyle = '#5de6ff';
        ctx.fill();
      }
    }
  }, [frequency, powerDb, noiseFloorDb, peakFrequencyHz]);
  
  return (
    <canvas ref={canvasRef} style={{ width: '100%', height: '100%', display: 'block' }} />
  );
}

// Waterfall canvas renderer
function WaterfallCanvas({ time, frequency, power_db: powerDb }) {
  const canvasRef = useRef(null);
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !powerDb || !powerDb.length) return;
    
    const ctx = canvas.getContext('2d');
    const parent = canvas.parentElement;
    canvas.width = parent.clientWidth;
    canvas.height = parent.clientHeight;
    
    const width = canvas.width;
    const height = canvas.height;
    
    const timeBins = powerDb[0]?.length || 0;
    const freqBins = powerDb.length;
    
    if (timeBins === 0 || freqBins === 0) return;
    
    // Create image data
    const imageData = ctx.createImageData(width, height);
    const data = imageData.data;
    
    // Find min/max for color mapping
    let minDb = Infinity, maxDb = -Infinity;
    for (let f = 0; f < freqBins; f++) {
      for (let t = 0; t < timeBins; t++) {
        const db = powerDb[f][t];
        if (db < minDb) minDb = db;
        if (db > maxDb) maxDb = db;
      }
    }
    const range = maxDb - minDb || 1;
    
    for (let y = 0; y < height; y++) {
      const fIdx = Math.floor((y / height) * freqBins);
      if (fIdx >= freqBins) continue;
      
      for (let x = 0; x < width; x++) {
        const tIdx = Math.floor((x / width) * timeBins);
        if (tIdx >= timeBins) continue;
        
        const db = powerDb[fIdx][tIdx];
        const norm = (db - minDb) / range;
        
        // Color map: dark blue -> cyan -> yellow -> magenta
        let r, g, b;
        if (norm < 0.25) {
          r = 0; g = norm * 4 * 255; b = 255;
        } else if (norm < 0.5) {
          r = 0; g = 255; b = (1 - (norm - 0.25) * 4) * 255;
        } else if (norm < 0.75) {
          r = (norm - 0.5) * 4 * 255; g = 255; b = 0;
        } else {
          r = 255; g = (1 - (norm - 0.75) * 4) * 255; b = (norm - 0.75) * 4 * 255;
        }
        
        const idx = (y * width + x) * 4;
        data[idx] = r;
        data[idx + 1] = g;
        data[idx + 2] = b;
        data[idx + 3] = 255;
      }
    }
    
    ctx.putImageData(imageData, 0, 0);
  }, [powerDb]);
  
  return (
    <canvas ref={canvasRef} style={{ width: '100%', height: '100%', display: 'block' }} />
  );
}

// Constellation canvas renderer
function ConstellationCanvas({ iValues, qValues }) {
  const canvasRef = useRef(null);
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !iValues || !qValues) return;
    
    const ctx = canvas.getContext('2d');
    const parent = canvas.parentElement;
    canvas.width = parent.clientWidth;
    canvas.height = parent.clientHeight;
    
    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;
    const scale = Math.min(width, height) * 0.35;
    
    ctx.clearRect(0, 0, width, height);
    
    // Grid
    ctx.strokeStyle = 'rgba(74, 68, 85, 0.1)';
    ctx.lineWidth = 1;
    for (let i = -2; i <= 2; i++) {
      const x = centerX + i * scale;
      const y = centerY + i * scale;
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke();
    }
    
    // Axes
    ctx.beginPath();
    ctx.strokeStyle = 'rgba(74, 68, 85, 0.3)';
    ctx.lineWidth = 1;
    ctx.moveTo(0, centerY); ctx.lineTo(width, centerY);
    ctx.moveTo(centerX, 0); ctx.lineTo(centerX, height);
    ctx.stroke();
    
    // Points
    ctx.fillStyle = '#5de6ff';
    for (let i = 0; i < iValues.length; i++) {
      const x = centerX + iValues[i] * scale;
      const y = centerY - qValues[i] * scale;
      ctx.beginPath();
      ctx.arc(x, y, 2, 0, Math.PI * 2);
      ctx.fill();
    }
  }, [iValues, qValues]);
  
  return (
    <canvas ref={canvasRef} style={{ width: '100%', height: '100%', display: 'block' }} />
  );
}

function PipelineNode({ icon, label, subtitle, number, status }) {
  const isComplete = status === 'complete';
  const isActive = status === 'active';

  const borderColor = isComplete
    ? 'var(--color-primary)'
    : isActive
      ? 'var(--color-secondary)'
      : 'var(--color-outline-variant)';

  const backgroundColor = isComplete
    ? 'rgba(124, 58, 237, 0.16)'
    : isActive
      ? 'rgba(93, 230, 255, 0.12)'
      : 'var(--color-surface-container-lowest)';

  const textColor = isComplete || isActive
    ? 'var(--color-on-surface)'
    : 'var(--color-on-surface-variant)';

  return (
    <div style={{ position: 'relative', zIndex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', minWidth: '96px' }}>
      <div style={{
        width: '48px',
        height: '48px',
        borderRadius: '50%',
        border: `2px solid ${borderColor}`,
        backgroundColor,
        color: textColor,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: isComplete ? '0 0 16px rgba(124, 58, 237, 0.35)' : 'none',
      }}>
        <span className="material-symbols-outlined" style={{ fontSize: '22px' }}>{icon}</span>
      </div>
      <div style={{ textAlign: 'center' }}>
        <div className="font-data-md" style={{ color: 'var(--color-primary)', fontSize: '11px', marginBottom: '2px' }}>{number}</div>
        <div style={{ color: 'var(--color-on-surface)', fontSize: '12px', fontWeight: 600 }}>{label}</div>
        <div style={{ color: 'var(--color-on-surface-variant)', fontSize: '11px', marginTop: '2px', maxWidth: '120px' }}>{subtitle}</div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const location = useLocation();
  const { analysisBundle, setAnalysisBundle } = useAnalysis();
  const fileInputRef = useRef(null);
  const [jobId, setJobId] = useState(() => analysisBundle?.jobId ?? null);
  const [status, setStatus] = useState(() => analysisBundle?.status ?? null);
  const [analysis, setAnalysis] = useState(() => analysisBundle?.analysis ?? null);
  const [waveform, setWaveform] = useState(() => analysisBundle?.waveform ?? null);
  const [spectrum, setSpectrum] = useState(() => analysisBundle?.spectrum ?? null);
  const [waterfall, setWaterfall] = useState(() => analysisBundle?.waterfall ?? null);
  const [constellation, setConstellation] = useState(() => analysisBundle?.constellation ?? null);
  const [bitstream, setBitstream] = useState(() => analysisBundle?.bitstream ?? null);
  const [error, setError] = useState(null);
  const [file, setFile] = useState(() => analysisBundle?.file ?? null);

  const openFilePicker = () => {
    fileInputRef.current?.click();
  };

  useEffect(() => {
    if (!analysisBundle) {
      return;
    }

    setJobId(analysisBundle.jobId ?? null);
    setStatus(analysisBundle.status ?? null);
    setAnalysis(analysisBundle.analysis ?? null);
    setWaveform(analysisBundle.waveform ?? null);
    setSpectrum(analysisBundle.spectrum ?? null);
    setWaterfall(analysisBundle.waterfall ?? null);
    setConstellation(analysisBundle.constellation ?? null);
    setBitstream(analysisBundle.bitstream ?? null);
    setFile(analysisBundle.file ?? null);
  }, [analysisBundle]);

  useEffect(() => {
    if (location.state?.openUpload) {
      fileInputRef.current?.click();
    }
  }, [location.state]);
  
  const uploadAndAnalyze = async (selectedFile) => {
    setError(null);
    setAnalysis(null);
    setFile(selectedFile);
    
    try {
      const bundle = await uploadAndAnalyzeSignal(selectedFile, setStatus);

      setJobId(bundle.jobId);
      setAnalysis(bundle.analysis);
      setWaveform(bundle.waveform);
      setSpectrum(bundle.spectrum);
      setWaterfall(bundle.waterfall);
      setConstellation(bundle.constellation);
      setBitstream(bundle.bitstream);

      setAnalysisBundle(bundle);
      
    } catch (err) {
      setError(err.message);
    }
  };
  
  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      uploadAndAnalyze(selectedFile);
    }
  };
  
  // Pipeline status from analysis
  const getPipelineStatus = () => {
    if (!analysis) return { phase1: 'pending', phase2: 'pending', phase3: 'pending', phase4: 'pending', phase5: 'pending' };
    return {
      phase1: 'completed',
      phase2: analysis.spectral ? 'completed' : 'pending',
      phase3: analysis.synchronization ? 'completed' : 'pending',
      phase4: analysis.modulation ? 'completed' : 'pending',
      phase5: analysis.demodulation ? 'completed' : 'pending',
    };
  };
  
  const pipelineStatus = getPipelineStatus();
  const overallProgress = Object.values(pipelineStatus).filter(s => s === 'completed').length / 5 * 100;
  
  return (
    <div className="page-layout">
      <Sidebar />
      <div className="main-content">
        <TopBar title="Dashboard" subtitle="Overview of signal analysis pipeline" onUpload={openFilePicker} />
        
        <main style={{ flex: 1, paddingTop: '96px', padding: '96px 24px 24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          {/* File Upload */}
          {!jobId && (
            <div style={{
              backgroundColor: 'var(--color-surface-container-low)',
              border: '2px dashed var(--color-outline-variant)',
              borderRadius: 'var(--radius-lg)',
              padding: '48px',
              textAlign: 'center',
            }}>
              <input ref={fileInputRef} type="file" id="file-upload" accept=".iq,.wav" onChange={handleFileSelect} style={{ display: 'none' }} />
              <label htmlFor="file-upload" style={{ cursor: 'pointer', display: 'inline-block' }}>
                <span className="material-symbols-outlined" style={{ fontSize: '48px', color: 'var(--color-primary)', marginBottom: '16px', display: 'block' }}>upload</span>
                <p style={{ fontSize: '18px', color: 'var(--color-on-surface)', marginBottom: '8px' }}>Drop IQ or WAV file here</p>
                <p style={{ color: 'var(--color-on-surface-variant)' }}>or click to browse</p>
              </label>
            </div>
          )}
          
          {jobId && !analysis && (
            <div style={{
              backgroundColor: 'var(--color-surface-container-low)',
              border: '1px solid var(--color-outline-variant)',
              borderRadius: 'var(--radius-lg)',
              padding: '24px',
            }}>
              <h3 className="font-label-caps" style={{ color: 'var(--color-on-surface-variant)' }}>PROCESSING...</h3>
              <div style={{ marginTop: '16px' }}>
                <div style={{ width: '100%', height: '8px', backgroundColor: 'var(--color-surface-container-high)', borderRadius: '999px', overflow: 'hidden' }}>
                  <div style={{
                    height: '100%', width: overallProgress + '%', borderRadius: '999px',
                    background: 'var(--color-primary-container)',
                    boxShadow: '0 0 10px rgba(124, 58, 237, 0.5)',
                    transition: 'width 0.5s ease',
                  }} />
                </div>
                <p style={{ marginTop: '8px', color: 'var(--color-on-surface-variant)' }}>
                  {status?.message || 'Processing...'} ({status?.progress || 0}%)
                </p>
              </div>
            </div>
          )}
          
          {analysis && (
            <>
              {/* Analysis Pipeline Status */}
              <div style={{
                backgroundColor: 'var(--color-surface-container-low)',
                border: '1px solid var(--color-outline-variant)',
                borderRadius: 'var(--radius-lg)',
                padding: 'var(--spacing-container-padding)',
                display: 'flex', flexDirection: 'column', gap: '24px',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3 className="font-label-caps" style={{ color: 'var(--color-on-surface-variant)' }}>ANALYSIS PIPELINE</h3>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <span className="font-data-md" style={{ color: 'var(--color-on-surface-variant)', fontSize: '13px' }}>
                      Status: <span style={{ color: 'var(--color-primary)' }}>{Math.round(overallProgress)}%</span>
                    </span>
                    <div style={{ width: '192px', height: '8px', backgroundColor: 'var(--color-surface-container-high)', borderRadius: '999px', overflow: 'hidden' }}>
                      <div style={{
height: '100%', width: overallProgress + '%', borderRadius: '999px',
                        background: 'var(--color-primary-container)',
                        boxShadow: '0 0 10px rgba(124, 58, 237, 0.5)',
                        transition: 'width 0.5s ease',
                      }} />
                    </div>
                  </div>
                </div>
                
                {/* Pipeline Nodes */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 32px', position: 'relative' }}>
                  <div style={{ position: 'absolute', top: '50%', left: '64px', right: '64px', height: '1px', backgroundColor: 'var(--color-outline-variant)', transform: 'translateY(-50%)', zIndex: 0 }} />
                  <div style={{ position: 'absolute', top: '50%', left: '64px', width: (overallProgress * 0.45) + '%', height: '1px', backgroundColor: 'var(--color-secondary)', transform: 'translateY(-50%)', zIndex: 0, boxShadow: '0 0 8px rgba(93, 230, 255, 0.5)' }} />
                  
                  {[
                    { icon: 'sensors', label: 'Signal Detection', subtitle: 'Detect & isolate', number: '1', phase: 'phase1' },
                    { icon: 'settings_applications', label: 'DSP Analysis', subtitle: 'Filtering, Sync', number: '2', phase: 'phase2' },
                    { icon: 'psychology', label: 'AI Classification', subtitle: 'Modulation', number: '3', phase: 'phase4' },
                    { icon: 'memory', label: 'Adaptive Demod', subtitle: 'PSK/FSK/QAM', number: '4', phase: 'phase5' },
                    { icon: 'insert_chart', label: 'Results Output', subtitle: 'Decoded bits', number: '5', phase: 'phase5' },
                  ].map(node => (
                    <PipelineNode 
                      key={node.phase}
                      icon={node.icon}
                      label={node.label}
                      subtitle={node.subtitle}
                      number={node.number}
                      status={pipelineStatus[node.phase] === 'completed' ? 'complete' : pipelineStatus[node.phase] === 'active' ? 'active' : 'pending'}
                    />
                  ))}
                </div>
              </div>
              
              {/* Row 2: Visualizations */}
              <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '16px', height: '400px' }}>
                {/* Signal Overview - Waveform */}
                <div style={{
                  backgroundColor: 'var(--color-surface-container-low)',
                  border: '1px solid var(--color-outline-variant)',
                  borderRadius: 'var(--radius-lg)',
                  padding: 'var(--spacing-container-padding)',
                  display: 'flex', flexDirection: 'column',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <h3 className="font-label-caps" style={{ color: 'var(--color-on-surface-variant)' }}>TIME DOMAIN</h3>
                  </div>
                  <div style={{ flex: 1, position: 'relative', backgroundColor: 'var(--color-surface-container-lowest)', border: '1px solid #4a4455', borderRadius: 'var(--radius-lg)' }}>
                    {waveform && <WaveformCanvas {...waveform} />}
                    {!waveform && <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-on-surface-variant)' }}>Loading...</div>}
                  </div>
                  {/* Stats */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '16px', paddingTop: '12px', borderTop: '1px solid var(--color-outline-variant)' }}>
                    {[
                      { icon: 'bolt', label: 'Power', value: analysis.spectral?.noise_floor_db?.value ? analysis.spectral.noise_floor_db.value.toFixed(1) + ' dB' : 'N/A', color: 'var(--color-secondary)' },
                      { icon: 'graphic_eq', label: 'SNR', value: analysis.spectral?.snr_db?.value ? analysis.spectral.snr_db.value.toFixed(1) + ' dB' : 'N/A', color: 'var(--color-secondary)' },
                      { icon: 'speed', label: 'Peak Freq', value: analysis.spectral?.peak_frequency?.value ? (analysis.spectral.peak_frequency.value/1e6).toFixed(2) + ' MHz' : 'N/A', color: 'var(--color-secondary)' },
                      { icon: 'check_circle', label: 'Signal', value: analysis.spectral?.peak_frequency?.value ? 'Detected' : 'None', color: analysis.spectral?.peak_frequency?.value ? '#4ade80' : '#ffb4ab' },
                    ].map(stat => (
                      <div key={stat.label} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span className="material-symbols-outlined" style={{ fontSize: '16px', color: stat.color }}>{stat.icon}</span>
                        <div>
                          <p style={{ fontSize: '10px', color: 'var(--color-on-surface-variant)', textTransform: 'uppercase' }}>{stat.label}</p>
                          <p className="font-data-md" style={{ fontSize: '13px', color: stat.color }}>{stat.value}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                
                {/* Spectrum + Waterfall */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {/* Spectrum FFT */}
                  <div style={{
                    flex: 1,
                    backgroundColor: 'var(--color-surface-container-low)',
                    border: '1px solid var(--color-outline-variant)',
                    borderRadius: 'var(--radius-lg)',
                    padding: 'var(--spacing-container-padding)',
                    display: 'flex', flexDirection: 'column',
                    overflow: 'hidden',
                  }}>
                    <h3 className="font-label-caps" style={{ color: 'var(--color-on-surface-variant)', marginBottom: '8px' }}>SPECTRUM</h3>
                    <div style={{ flex: 1, position: 'relative', backgroundColor: 'var(--color-surface-container-lowest)', border: '1px solid rgba(74,68,85,0.5)', borderRadius: 'var(--radius-lg)' }}>
                      {spectrum && <SpectrumCanvas {...spectrum} />}
                      {!spectrum && <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-on-surface-variant)' }}>Loading...</div>}
                    </div>
                  </div>
                  
                  {/* Waterfall */}
                  <div style={{
                    flex: 1,
                    backgroundColor: 'var(--color-surface-container-low)',
                    border: '1px solid var(--color-outline-variant)',
                    borderRadius: 'var(--radius-lg)',
                    padding: 'var(--spacing-container-padding)',
                    display: 'flex', flexDirection: 'column',
                    overflow: 'hidden',
                  }}>
                    <h3 className="font-label-caps" style={{ color: 'var(--color-on-surface-variant)', marginBottom: '8px' }}>WATERFALL</h3>
                    <div style={{
                      flex: 1, position: 'relative',
                      backgroundColor: '#000',
                      border: '1px solid rgba(74,68,85,0.5)', borderRadius: 'var(--radius-lg)',
                      overflow: 'hidden',
                    }}>
                      {waterfall && <WaterfallCanvas {...waterfall} />}
                      {!waterfall && <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-on-surface-variant)' }}>Loading...</div>}
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Row 3: AI Predictions & Bitstream */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '16px' }}>
                {/* AI Predictions */}
                <div style={{
                  backgroundColor: 'var(--color-surface-container-low)',
                  border: '1px solid var(--color-outline-variant)',
                  borderRadius: 'var(--radius-lg)',
                  padding: 'var(--spacing-container-padding)',
                  display: 'flex', flexDirection: 'column',
                }}>
                  <h3 className="font-label-caps" style={{ color: 'var(--color-on-surface-variant)', marginBottom: '16px' }}>AI PREDICTIONS</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', flex: 1 }}>
                    {analysis.modulation && [
                      { label: 'Modulation', value: analysis.modulation.prediction, conf: Math.round((analysis.modulation.confidence || 0) * 100) },
                      ...Object.entries(analysis.modulation.probabilities || {}).map(([k, v]) => ({ label: k, value: k, conf: Math.round(v * 100) })).filter(x => x.value !== analysis.modulation.prediction).slice(0, 3)
                    ].map(item => (
                      <div key={item.label}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', fontSize: '13px' }}>
                          <span style={{ color: 'var(--color-on-surface-variant)' }}>{item.label}</span>
                          <span className="font-data-md" style={{ fontWeight: 700 }}>{item.value}</span>
                          <span className="font-data-md" style={{ color: 'var(--color-primary)' }}>{item.conf}%</span>
                        </div>
                        <div style={{ height: '6px', backgroundColor: 'var(--color-surface-container-high)', borderRadius: '999px', overflow: 'hidden' }}>
                          <div style={{ height: '100%', width: item.conf + '%', backgroundColor: item.value === analysis.modulation.prediction ? 'var(--color-primary)' : 'var(--color-secondary)', borderRadius: '999px' }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                
                {/* Decoded Output */}
                <div style={{
                  backgroundColor: 'var(--color-surface-container-low)',
                  border: '1px solid var(--color-outline-variant)',
                  borderRadius: 'var(--radius-lg)',
                  padding: 'var(--spacing-container-padding)',
                  display: 'flex', flexDirection: 'column',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <h3 className="font-label-caps" style={{ color: 'var(--color-on-surface-variant)' }}>CONSTELLATION & BITSTREAM</h3>
                  </div>
                  <div style={{ flex: 1, display: 'flex', gap: '16px', overflow: 'hidden' }}>
                    {/* Constellation */}
                    <div style={{ flex: 1, backgroundColor: 'var(--color-surface-container-lowest)', border: '1px solid rgba(74,68,85,0.5)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
                      {constellation && <ConstellationCanvas iValues={constellation.i_values} qValues={constellation.q_values} />}
                      {!constellation && <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-on-surface-variant)' }}>No constellation</div>}
                    </div>
                    
                    {/* Bitstream Terminal */}
                    <div style={{ width: '320px', backgroundColor: 'var(--color-surface-container-lowest)', border: '1px solid rgba(74,68,85,0.5)', borderRadius: 'var(--radius-lg)', padding: '16px', fontFamily: 'JetBrains Mono, monospace', fontSize: '13px', color: '#00ff00', overflowY: 'auto' }}>
                      {bitstream && bitstream.binary ? (
                        <>
                          <div style={{ wordBreak: 'break-all', lineHeight: 1.8 }}>
                            {bitstream.binary}
                          </div>
                          <div style={{ marginTop: '8px', color: 'var(--color-on-surface-variant)', fontSize: '11px' }}>
                            {bitstream.length_bits} bits, {bitstream.symbol_count} symbols
                          </div>
                        </>
                      ) : (
                        <div style={{ color: 'var(--color-on-surface-variant)' }}>No bitstream available</div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
          
          {error && (
            <div style={{
              backgroundColor: 'rgba(255, 180, 171, 0.1)',
              border: '1px solid rgba(255, 180, 171, 0.3)',
              borderRadius: 'var(--radius-lg)',
              padding: '16px',
              color: 'var(--color-error)',
            }}>
              Error: {error}
            </div>
          )}
          
        </main>
      </div>
    </div>
  );
}