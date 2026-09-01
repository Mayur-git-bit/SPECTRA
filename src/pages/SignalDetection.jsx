import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import TopBar from '../components/TopBar';
import { useAnalysis } from '../context/AnalysisContext';

function SignalPreview({ mode, spectral, currentSignal }) {
  if (mode === 'time') {
    return (
      <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }} viewBox="0 0 800 300" preserveAspectRatio="none">
        <defs>
          <linearGradient id="timeGrad" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#5de6ff" stopOpacity="0.2" />
            <stop offset="100%" stopColor="#ffb4ab" stopOpacity="0.2" />
          </linearGradient>
        </defs>
        <rect x="0" y="0" width="800" height="300" fill="rgba(10,14,22,0.6)" />
        <path d="M0 150 C40 130, 80 170, 120 150 S200 110, 240 150 S320 190, 360 150 S440 110, 480 150 S560 190, 600 150 S680 110, 720 150 S760 170, 800 150"
          fill="none" stroke="#5de6ff" strokeWidth="3" style={{ filter: 'drop-shadow(0 0 4px #5de6ff)' }} />
        <path d="M0 150 C40 130, 80 170, 120 150 S200 110, 240 150 S320 190, 360 150 S440 110, 480 150 S560 190, 600 150 S680 110, 720 150 S760 170, 800 150"
          fill="url(#timeGrad)" stroke="none" opacity="0.35" />
        {[120, 240, 360, 480, 600, 720].map((x, i) => (
          <line key={i} x1={x} y1="40" x2={x} y2="260" stroke="rgba(74,68,85,0.3)" strokeDasharray="6 8" />
        ))}
      </svg>
    );
  }

  if (mode === 'iq') {
    const points = Array.from({ length: 160 }, (_, i) => {
      const cluster = i % 4;
      const centers = [
        [-1.2, -1.2], [1.2, -1.2], [-1.2, 1.2], [1.2, 1.2],
      ];
      const [cx, cy] = centers[cluster];
      return {
        x: cx + (Math.random() - 0.5) * 0.7,
        y: cy + (Math.random() - 0.5) * 0.7,
      };
    });

    return (
      <div style={{ position: 'absolute', inset: 0 }}>
        <div style={{ position: 'absolute', inset: 0, backgroundImage: 'linear-gradient(to right, #171c24 1px, transparent 1px), linear-gradient(to bottom, #171c24 1px, transparent 1px)', backgroundSize: '40px 40px', opacity: 0.7 }} />
        <div style={{ position: 'absolute', top: '50%', left: 0, right: 0, height: '1px', backgroundColor: 'rgba(74,68,85,0.5)' }} />
        <div style={{ position: 'absolute', top: 0, bottom: 0, left: '50%', width: '1px', backgroundColor: 'rgba(74,68,85,0.5)' }} />
        {points.map((pt, i) => {
          const px = ((pt.x / 3 + 0.5) * 100);
          const py = ((pt.y / 3 + 0.5) * 100);
          return (
            <div key={i} style={{
              position: 'absolute', width: '5px', height: '5px', borderRadius: '50%',
              backgroundColor: i % 2 === 0 ? 'var(--color-secondary)' : 'var(--color-primary)',
              left: `${px}%`, top: `${py}%`, transform: 'translate(-50%, -50%)',
              opacity: 0.8, boxShadow: `0 0 5px ${i % 2 === 0 ? '#5de6ff' : '#d2bbff'}`,
            }} />
          );
        })}
      </div>
    );
  }

  return (
    <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }} viewBox="0 0 800 300" preserveAspectRatio="none">
      <defs>
        <linearGradient id="specGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#5de6ff" stopOpacity="0.4" />
          <stop offset="100%" stopColor="#5de6ff" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d="M0 280 L80 275 L160 270 L200 250 L240 220 L280 200 L320 180 L340 120 L360 50 L380 120 L400 200 L440 250 L480 260 L560 268 L640 272 L720 276 L800 280"
        fill="url(#specGrad)" />
      <path d="M0 280 L80 275 L160 270 L200 250 L240 220 L280 200 L320 180 L340 120 L360 50 L380 120 L400 200 L440 250 L480 260 L560 268 L640 272 L720 276 L800 280"
        fill="none" stroke="#5de6ff" strokeWidth="2" style={{ filter: 'drop-shadow(0 0 4px #5de6ff)' }} />
      {spectral?.peak_frequency?.value != null && (
        <line x1="360" y1="40" x2="360" y2="255" stroke="rgba(210,187,255,0.7)" strokeDasharray="6 6" />
      )}
      <text x="18" y="28" fill="#8f98ab" fontSize="14">{currentSignal?.freq || 'Spectrum view'}</text>
    </svg>
  );
}

export default function SignalDetection() {
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState('fft');
  const { analysisBundle } = useAnalysis();
  const analysis = analysisBundle?.analysis;
  const spectral = analysis?.spectral;
  const modulation = analysis?.modulation;
  const synchronization = analysis?.synchronization;

  const currentSignal = spectral ? {
    freq: spectral.peak_frequency?.value != null ? `${(spectral.peak_frequency.value / 1e6).toFixed(3)} MHz` : 'N/A',
    bw: spectral.bandwidth?.value != null ? `${(spectral.bandwidth.value / 1e6).toFixed(3)} MHz` : 'N/A',
    snr: spectral.snr_db?.value != null ? `${spectral.snr_db.value.toFixed(1)} dB` : 'N/A',
    mod: modulation?.prediction ? `${modulation.prediction} ${(modulation.confidence * 100).toFixed(1)}%` : 'Unknown',
    status: analysis?.modulation?.status === 'model_predicted' ? 'Current File' : 'Detected',
    statusColor: 'var(--color-primary)',
    dotColor: 'var(--color-primary)',
    pulse: true,
  } : null;

  const signals = [
    currentSignal,
    { freq: '2.445 GHz', bw: '20 MHz', snr: '24.5 dB', mod: 'QPSK (85%)', status: 'High Power', statusColor: 'var(--color-error)', dotColor: 'var(--color-error)', pulse: true },
    { freq: '2.412 GHz', bw: '5 MHz', snr: '12.1 dB', mod: 'BPSK (60%)', status: 'Stable', statusColor: 'var(--color-on-surface-variant)', dotColor: 'var(--color-secondary)', pulse: false },
    { freq: '2.480 GHz', bw: '~1 MHz', snr: '3.2 dB', mod: 'Unknown', status: 'Burst', statusColor: 'var(--color-outline)', dotColor: 'var(--color-outline-variant)', pulse: false, weak: true },
  ].filter(Boolean);

  const centerFreqLabel = spectral?.peak_frequency?.value != null ? `${(spectral.peak_frequency.value / 1e6).toFixed(3)} MHz` : '2.45 GHz';
  const spanLabel = spectral?.bandwidth?.value != null ? `${(spectral.bandwidth.value / 1e6).toFixed(3)} MHz` : '100 MHz';
  const rbwLabel = spectral?.bandwidth?.value != null ? `${Math.max(10, Math.round(spectral.bandwidth.value / 1000))} kHz` : '10 kHz';
  const signalsFoundLabel = currentSignal ? '1' : '3';
  const noiseFloorLabel = spectral?.noise_floor_db?.value != null ? `${spectral.noise_floor_db.value.toFixed(1)} dB` : '-102 dBm';

  return (
    <div className="page-layout">
      <Sidebar />
      <div className="main-content">
        <TopBar title="Signal Detection" subtitle="Live RF Spectrum Monitoring" />

        <main style={{
          flex: 1,
          paddingTop: '96px',
          padding: '96px 24px 24px',
          position: 'relative',
          display: 'flex',
          flexDirection: 'column',
          height: '100vh',
          overflow: 'hidden',
        }}>
          {/* Grid BG */}
          <div className="grid-bg" style={{ position: 'absolute', inset: 0, opacity: 0.05, pointerEvents: 'none', zIndex: 0 }} />

          {analysis && (
            <div className="glass-panel" style={{ position: 'relative', zIndex: 1, borderRadius: '12px', padding: '16px', marginBottom: '16px', border: '1px solid rgba(93, 230, 255, 0.25)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: '16px', flexWrap: 'wrap' }}>
                <div>
                  <div className="font-label-caps" style={{ color: 'var(--color-secondary)', marginBottom: '4px' }}>Current Analysis</div>
                  <div style={{ color: 'var(--color-on-surface)', fontWeight: 700 }}>{analysisBundle?.file?.name || 'Uploaded IQ file'}</div>
                  <div style={{ color: 'var(--color-on-surface-variant)', fontSize: '12px' }}>{analysisBundle?.jobId ? `Job ${analysisBundle.jobId}` : 'Live analysis bundle'}</div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(120px, 1fr))', gap: '12px', flex: 1 }}>
                  <div><div className="font-label-caps" style={{ fontSize: '10px', color: 'var(--color-outline)' }}>Peak Freq</div><div style={{ color: 'var(--color-secondary)', fontWeight: 700 }}>{spectral?.peak_frequency?.value ? `${(spectral.peak_frequency.value / 1e6).toFixed(3)} MHz` : 'N/A'}</div></div>
                  <div><div className="font-label-caps" style={{ fontSize: '10px', color: 'var(--color-outline)' }}>Bandwidth</div><div style={{ color: 'var(--color-secondary)', fontWeight: 700 }}>{spectral?.bandwidth?.value ? `${(spectral.bandwidth.value / 1e6).toFixed(3)} MHz` : 'N/A'}</div></div>
                  <div><div className="font-label-caps" style={{ fontSize: '10px', color: 'var(--color-outline)' }}>SNR</div><div style={{ color: 'var(--color-secondary)', fontWeight: 700 }}>{spectral?.snr_db?.value != null ? `${spectral.snr_db.value.toFixed(1)} dB` : 'N/A'}</div></div>
                  <div><div className="font-label-caps" style={{ fontSize: '10px', color: 'var(--color-outline)' }}>Modulation</div><div style={{ color: 'var(--color-primary)', fontWeight: 700 }}>{modulation?.prediction ? `${modulation.prediction} ${(modulation.confidence * 100).toFixed(1)}%` : 'N/A'}</div></div>
                </div>
              </div>
              {synchronization && (
                <div style={{ marginTop: '12px', display: 'flex', gap: '16px', flexWrap: 'wrap', color: 'var(--color-on-surface-variant)', fontSize: '12px' }}>
                  <span>Symbol Rate: {synchronization.symbol_rate?.value ? `${synchronization.symbol_rate.value.toFixed(0)} sym/s` : 'N/A'}</span>
                  <span>Samples/Symbol: {synchronization.samples_per_symbol?.value ? synchronization.samples_per_symbol.value.toFixed(2) : 'N/A'}</span>
                  <span>CFO: {synchronization.frequency_offset_hz?.value != null ? `${synchronization.frequency_offset_hz.value.toFixed(1)} Hz` : 'N/A'}</span>
                </div>
              )}
            </div>
          )}

          <div style={{ position: 'relative', zIndex: 1, display: 'flex', gap: '16px', flex: 1, overflow: 'hidden', paddingTop: '96px' }}>
            {/* Center: Visualizations */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '16px', minWidth: 0 }}>
              {/* Control Bar */}
              <div className="glass-panel" style={{
                borderRadius: '12px', padding: '12px',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                flexShrink: 0,
              }}>
                <div style={{ display: 'flex', gap: '8px' }}>
                  {[
                    { label: 'FFT View', value: 'fft' },
                    { label: 'Time Domain', value: 'time' },
                    { label: 'I/Q Plot', value: 'iq' },
                  ].map(btn => (
                    <button key={btn.value} onClick={() => setViewMode(btn.value)} style={{
                      padding: '6px 12px', borderRadius: 'var(--radius-default)',
                      fontSize: '11px', fontFamily: 'JetBrains Mono, monospace',
                      fontWeight: 700, letterSpacing: '0.08em',
                      backgroundColor: viewMode === btn.value ? 'rgba(210, 187, 255, 0.2)' : 'transparent',
                      color: viewMode === btn.value ? 'var(--color-primary)' : 'var(--color-on-surface-variant)',
                      border: viewMode === btn.value ? '1px solid rgba(210, 187, 255, 0.5)' : '1px solid transparent',
                      transition: 'all 0.2s ease',
                      cursor: 'pointer',
                    }}>
                      {btn.label}
                    </button>
                  ))}
                </div>
                <div className="font-data-md" style={{ display: 'flex', alignItems: 'center', gap: '24px', fontSize: '12px', color: 'var(--color-on-surface-variant)' }}>
                  <span>Center Freq: <strong style={{ color: 'var(--color-secondary)' }}>{centerFreqLabel}</strong></span>
                  <span>Span: <strong style={{ color: 'var(--color-secondary)' }}>{spanLabel}</strong></span>
                  <span>RBW: <strong style={{ color: 'var(--color-secondary)' }}>{rbwLabel}</strong></span>
                </div>
              </div>

              {/* Spectrum Analyzer */}
              <div className="glass-panel" style={{ borderRadius: '12px', padding: '12px', flex: 1, display: 'flex', flexDirection: 'column', position: 'relative', minHeight: '250px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexShrink: 0 }}>
                  <h3 className="font-label-caps" style={{ color: 'var(--color-on-surface)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className="material-symbols-outlined" style={{ fontSize: '16px', color: 'var(--color-secondary)' }}>show_chart</span>
                    Real-Time Spectrum
                  </h3>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--color-secondary)', display: 'inline-block' }} className="anim-pulse-fast" />
                    <span className="font-data-md" style={{ fontSize: '10px', color: 'var(--color-secondary)', textTransform: 'uppercase' }}>Live Data</span>
                  </div>
                </div>
                {/* Chart Area */}
                <div style={{
                  flex: 1,
                  position: 'relative',
                  border: '1px solid rgba(74,68,85,0.3)',
                  borderRadius: 'var(--radius-lg)',
                  backgroundColor: '#0a0e16',
                  overflow: 'hidden',
                }}>
                  {/* Grid lines overlay */}
                  <div style={{
                    position: 'absolute', inset: 0, opacity: 0.2, pointerEvents: 'none',
                    display: 'grid', gridTemplateColumns: 'repeat(10, 1fr)', gridTemplateRows: 'repeat(6, 1fr)',
                  }}>
                    {Array.from({ length: 60 }).map((_, i) => (
                      <div key={i} style={{ borderRight: '1px solid var(--color-outline-variant)', borderBottom: '1px solid var(--color-outline-variant)' }} />
                    ))}
                  </div>
                  {/* Y labels */}
                  <div style={{ position: 'absolute', left: '4px', top: '8px', bottom: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', pointerEvents: 'none' }}>
                    {['-20', '-40', '-60', '-80', '-100', '-120'].map(v => (
                      <span key={v} className="font-data-md" style={{ fontSize: '9px', color: 'var(--color-outline)' }}>{v}</span>
                    ))}
                  </div>
                  {/* X labels */}
                  <div style={{ position: 'absolute', bottom: '4px', left: '40px', right: 0, display: 'flex', justifyContent: 'space-between', pointerEvents: 'none' }}>
                    {['2.40', '2.42', '2.44', '2.46', '2.48', '2.50'].map(v => (
                      <span key={v} className="font-data-md" style={{ fontSize: '9px', color: 'var(--color-outline)' }}>{v}</span>
                    ))}
                  </div>
                  {/* SVG Spectrum */}
                  <SignalPreview mode={viewMode} spectral={spectral} currentSignal={currentSignal} />
                </div>
              </div>

              {/* Waterfall Plot */}
              <div className="glass-panel" style={{ borderRadius: '12px', padding: '12px', height: '160px', flexShrink: 0, display: 'flex', flexDirection: 'column' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', flexShrink: 0 }}>
                  <h3 className="font-label-caps" style={{ color: 'var(--color-on-surface)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className="material-symbols-outlined" style={{ fontSize: '16px', color: 'var(--color-tertiary)' }}>waterfall_chart</span>
                    Spectrogram (History)
                  </h3>
                  <div style={{ height: '6px', width: '128px', borderRadius: '999px', background: 'linear-gradient(to right, #000, #004395, #00cbe6, #ffb4ab)', border: '1px solid rgba(74,68,85,0.5)' }} />
                </div>
                <div style={{
                  flex: 1, borderRadius: 'var(--radius-lg)',
                  border: '1px solid rgba(74,68,85,0.3)',
                  overflow: 'hidden', position: 'relative',
                  background: 'linear-gradient(180deg, #0a0e16 0%, #001a2e 40%, #003366 70%, #005588 100%)',
                }}>
                  {/* Simulated waterfall bands */}
                  {Array.from({ length: 8 }).map((_, i) => (
                    <div key={i} style={{
                      position: 'absolute',
                      height: '1px',
                      left: `${20 + Math.random() * 10}%`,
                      right: `${20 + Math.random() * 10}%`,
                      top: `${10 + i * 12}%`,
                      background: 'linear-gradient(to right, transparent, var(--color-secondary), var(--color-primary), var(--color-secondary), transparent)',
                      opacity: 0.6 - i * 0.05,
                    }} />
                  ))}
                </div>
              </div>
            </div>

            {/* Right Sidebar: Detected Signals */}
            <div style={{ width: '280px', flexShrink: 0, display: 'flex', flexDirection: 'column', gap: '16px', overflow: 'hidden' }}>
              {/* Scanner Status */}
              <div className="glass-panel glass-panel-active" style={{ borderRadius: '12px', padding: '12px', backgroundColor: 'rgba(27, 32, 40, 0.5)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <h3 className="font-label-caps" style={{ color: 'var(--color-primary)' }}>Scanner Status</h3>
                  <span className="material-symbols-outlined" style={{ color: 'var(--color-primary)' }}>radar</span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                  <div>
                    <div className="font-label-caps" style={{ fontSize: '10px', color: 'var(--color-outline)', marginBottom: '4px' }}>Signals Found</div>
                    <div className="font-headline-md" style={{ color: 'var(--color-on-surface)' }}>{signalsFoundLabel}</div>
                  </div>
                  <div>
                    <div className="font-label-caps" style={{ fontSize: '10px', color: 'var(--color-outline)', marginBottom: '4px' }}>Noise Floor</div>
                    <div className="font-data-md" style={{ color: 'var(--color-on-surface-variant)' }}>{noiseFloorLabel}</div>
                  </div>
                </div>
                <button style={{
                  width: '100%', padding: '8px',
                  border: '1px solid rgba(93, 230, 255, 0.5)',
                  borderRadius: 'var(--radius-default)',
                  backgroundColor: 'var(--color-surface)',
                  color: 'var(--color-secondary)',
                  fontFamily: 'JetBrains Mono, monospace',
                  fontSize: '10px', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                  transition: 'all 0.2s',
                }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--color-secondary)'; e.currentTarget.style.backgroundColor = 'rgba(93, 230, 255, 0.1)'; }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = 'rgba(93, 230, 255, 0.5)'; e.currentTarget.style.backgroundColor = 'var(--color-surface)'; }}
                  onClick={() => navigate('/ai-analysis')}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>auto_awesome</span>
                  Run AI Classifier
                </button>
              </div>

              {/* Active Carriers */}
              <div className="glass-panel" style={{ borderRadius: '12px', flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                <div style={{
                  padding: '12px',
                  borderBottom: '1px solid rgba(74,68,85,0.5)',
                  backgroundColor: 'rgba(23, 28, 36, 0.5)',
                }}>
                  <h3 className="font-label-caps" style={{ color: 'var(--color-on-surface)' }}>Active Carriers</h3>
                </div>
                <div style={{ flex: 1, overflowY: 'auto', padding: '8px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {signals.map((sig, i) => (
                    <div key={i} style={{
                      padding: '12px',
                      borderRadius: 'var(--radius-lg)',
                      border: '1px solid var(--color-outline-variant)',
                      backgroundColor: 'var(--color-surface)',
                      opacity: sig.weak ? 0.7 : 1,
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                    }}
                      onMouseEnter={e => { e.currentTarget.style.borderColor = 'rgba(210, 187, 255, 0.5)'; e.currentTarget.style.opacity = '1'; }}
                      onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--color-outline-variant)'; e.currentTarget.style.opacity = sig.weak ? '0.7' : '1'; }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <div style={{
                            width: '8px', height: '8px', borderRadius: '50%',
                            backgroundColor: sig.dotColor,
                            boxShadow: `0 0 5px ${sig.dotColor}`,
                          }} className={sig.pulse ? 'anim-pulse-fast' : ''} />
                          <span className="font-data-md" style={{ fontSize: '13px', fontWeight: 700, color: 'var(--color-on-surface)' }}>{sig.freq}</span>
                        </div>
                        <span style={{
                          fontSize: '9px', fontFamily: 'JetBrains Mono, monospace', fontWeight: 700, letterSpacing: '0.08em',
                          backgroundColor: sig.pulse ? 'rgba(255, 180, 171, 0.2)' : 'rgba(48, 53, 62, 0.5)',
                          color: sig.statusColor,
                          padding: '2px 6px', borderRadius: 'var(--radius-default)',
                          border: sig.pulse ? '1px solid rgba(255, 180, 171, 0.3)' : '1px solid rgba(74,68,85,0.5)',
                        }}>
                          {sig.status}
                        </span>
                      </div>
                      <div className="font-data-md" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '11px', color: 'var(--color-on-surface-variant)', marginBottom: '12px' }}>
                        <div>BW: {sig.bw}</div>
                        <div>SNR: {sig.snr}</div>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid rgba(74,68,85,0.3)', paddingTop: '8px' }}>
                        <span className="font-label-caps" style={{ fontSize: '10px', color: 'var(--color-outline)' }}>Suspected Mod:</span>
                        <span className="font-data-md" style={{ fontSize: '11px', color: sig.weak ? 'var(--color-outline)' : 'var(--color-secondary)', fontStyle: sig.weak ? 'italic' : 'normal' }}>
                          {sig.mod}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
