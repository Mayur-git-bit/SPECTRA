import { useState } from 'react';
import Sidebar from '../components/Sidebar';
import TopBar from '../components/TopBar';
import { useAnalysis } from '../context/AnalysisContext';
import { useNavigate } from 'react-router-dom';

// Constellation plot using canvas
function ConstellationPlot({ mode = 'iq', activeMode = 'iq', onModeChange }) {
  const points = Array.from({ length: 200 }, () => {
    const symbol = Math.floor(Math.random() * 16);
    const ix = (symbol % 4) - 1.5;
    const iy = Math.floor(symbol / 4) - 1.5;
    return {
      x: ix + (Math.random() - 0.5) * 0.15,
      y: iy + (Math.random() - 0.5) * 0.15,
    };
  });

  return (
    <div style={{
      flex: 1,
      position: 'relative',
      backgroundColor: '#060A12',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '16px',
    }}>
      {/* Grid */}
      <div style={{
        position: 'absolute', inset: 0,
        backgroundImage: 'linear-gradient(to right, #171c24 1px, transparent 1px), linear-gradient(to bottom, #171c24 1px, transparent 1px)',
        backgroundSize: '40px 40px',
      }} />
      {/* Axes */}
      <div style={{ position: 'absolute', top: '50%', left: 0, right: 0, height: '1px', backgroundColor: 'rgba(74,68,85,0.5)' }} />
      <div style={{ position: 'absolute', top: 0, bottom: 0, left: '50%', width: '1px', backgroundColor: 'rgba(74,68,85,0.5)' }} />

      {/* Constellation Points */}
      <div style={{ position: 'relative', width: '360px', height: '360px' }}>
        {points.map((pt, i) => {
          const px = ((pt.x / 3 + 0.5) * 100);
          const py = ((pt.y / 3 + 0.5) * 100);
          return (
            <div key={i} style={{
              position: 'absolute',
              width: mode === 'centroids' && i % 25 === 0 ? '8px' : '4px', height: mode === 'centroids' && i % 25 === 0 ? '8px' : '4px',
              borderRadius: '50%',
              backgroundColor: mode === 'decision' ? 'var(--color-tertiary)' : (i % 5 === 0 ? 'var(--color-primary)' : 'var(--color-secondary)'),
              left: `${px}%`, top: `${py}%`,
              transform: 'translate(-50%, -50%)',
              opacity: mode === 'iq' ? 0.8 : 0.55,
              boxShadow: `0 0 ${i % 7 === 0 ? 6 : 3}px ${mode === 'decision' ? 'var(--color-tertiary)' : (i % 5 === 0 ? 'var(--color-primary)' : 'var(--color-secondary)')}`,
            }} />
          );
        })}
        {mode === 'decision' && (
          <>
            <div style={{ position: 'absolute', left: '18%', top: '18%', width: '64%', height: '64%', border: '1px dashed rgba(255, 180, 171, 0.7)', borderRadius: '50%' }} />
            <div style={{ position: 'absolute', left: '12%', top: '12%', width: '76%', height: '76%', borderTop: '1px solid rgba(93, 230, 255, 0.5)', transform: 'rotate(35deg)' }} />
            <div style={{ position: 'absolute', left: '12%', top: '12%', width: '76%', height: '76%', borderTop: '1px solid rgba(93, 230, 255, 0.5)', transform: 'rotate(-35deg)' }} />
          </>
        )}
        {/* Crosshairs (AI centers) */}
        {[[-1.5, -1.5], [-0.5, -1.5], [0.5, -1.5], [1.5, -1.5],
          [-1.5, -0.5], [-0.5, -0.5], [0.5, -0.5], [1.5, -0.5],
          [-1.5, 0.5], [-0.5, 0.5], [0.5, 0.5], [1.5, 0.5],
          [-1.5, 1.5], [-0.5, 1.5], [0.5, 1.5], [1.5, 1.5]].map(([ix, iy], i) => {
          const px = ((ix / 3 + 0.5) * 100);
          const py = ((iy / 3 + 0.5) * 100);
          return (
            <div key={`center-${i}`} style={{
              position: 'absolute',
              width: '8px', height: '8px',
              borderRadius: '50%',
              border: '1px solid var(--color-error)',
              boxShadow: '0 0 8px rgba(255, 180, 171, 0.5)',
              left: `${px}%`, top: `${py}%`,
              transform: 'translate(-50%, -50%)',
            }} />
          );
        })}
      </div>

      {/* Controls */}
      <div style={{
        position: 'absolute', bottom: '16px', right: '16px',
        display: 'flex',
        backgroundColor: 'var(--color-surface-container)',
        border: '1px solid var(--color-surface-variant)',
        borderRadius: 'var(--radius-lg)',
        padding: '4px',
      }}>
        {[
          { label: 'IQ Data', value: 'iq' },
          { label: 'Centroids', value: 'centroids' },
          { label: 'Decision Bounds', value: 'decision' },
        ].map((btn) => (
          <button
            key={btn.value}
            onClick={() => onModeChange?.(btn.value)}
            style={{
              padding: '4px 12px',
              fontSize: '11px', fontFamily: 'JetBrains Mono, monospace',
              backgroundColor: activeMode === btn.value ? 'var(--color-surface-variant)' : 'transparent',
              color: activeMode === btn.value ? 'var(--color-secondary)' : 'var(--color-on-surface-variant)',
              border: 'none', borderRadius: 'var(--radius-default)',
              cursor: 'pointer',
            }}
          >
            {btn.label}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function AIAnalysis() {
  const navigate = useNavigate();
  const { analysisBundle } = useAnalysis();
  const analysis = analysisBundle?.analysis;
  const modulation = analysis?.modulation;
  const synchronization = analysis?.synchronization;
  const spectral = analysis?.spectral;
  const [plotMode, setPlotMode] = useState('iq');

  const predictions = modulation?.probabilities
    ? Object.entries(modulation.probabilities)
        .map(([name, conf]) => ({ name, conf: conf * 100, isPrimary: name === modulation.prediction }))
        .sort((a, b) => b.conf - a.conf)
    : [];

  const features = analysis
    ? [
        { name: 'File', value: analysisBundle?.file?.name || 'Uploaded file' },
        { name: 'Peak Frequency', value: spectral?.peak_frequency?.value != null ? `${(spectral.peak_frequency.value / 1e6).toFixed(3)} MHz` : 'N/A' },
        { name: 'Bandwidth', value: spectral?.bandwidth?.value != null ? `${(spectral.bandwidth.value / 1e6).toFixed(3)} MHz` : 'N/A' },
        { name: 'SNR', value: spectral?.snr_db?.value != null ? `${spectral.snr_db.value.toFixed(1)} dB` : 'N/A', highlight: 'primary' },
        { name: 'Symbol Rate', value: synchronization?.symbol_rate?.value != null ? `${(synchronization.symbol_rate.value / 1000).toFixed(1)} kSym/s` : 'N/A' },
        { name: 'CFO', value: synchronization?.frequency_offset_hz?.value != null ? `${synchronization.frequency_offset_hz.value.toFixed(1)} Hz` : 'N/A' },
      ]
    : [];

  return (
    <div className="page-layout">
      <Sidebar />
      <main className="main-content" style={{ height: '100vh', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {/* Custom TopBar for this page */}
        <header style={{
          height: '64px', borderBottom: '1px solid var(--color-outline-variant)',
          backgroundColor: 'rgba(15, 19, 28, 0.8)', backdropFilter: 'blur(12px)',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '0 var(--spacing-gutter)',
          flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <h2 className="font-headline-md" style={{ color: 'var(--color-on-surface)', fontWeight: 700, letterSpacing: '-0.02em' }}>
              AI Analysis
            </h2>
            <span className="font-data-md" style={{
              color: 'var(--color-on-surface-variant)', fontSize: '13px',
              borderLeft: '1px solid var(--color-surface-variant)',
              paddingLeft: '16px', paddingTop: '4px', paddingBottom: '4px',
            }}>
              SIG_ID: <span style={{ color: 'var(--color-secondary)' }}>4920-Alpha</span>
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{
              display: 'flex', alignItems: 'center',
              backgroundColor: 'var(--color-surface-container)',
              borderRadius: '999px', padding: '4px',
              border: '1px solid var(--color-surface-variant)',
            }}>
              {['light_mode', 'dark_mode'].map((icon, i) => (
                <button key={icon} style={{
                  padding: '4px', borderRadius: '50%',
                  backgroundColor: i === 1 ? 'var(--color-surface-variant)' : 'transparent',
                  color: i === 1 ? 'var(--color-primary)' : 'var(--color-on-surface-variant)',
                  border: 'none', cursor: 'pointer',
                }}>
                  <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>{icon}</span>
                </button>
              ))}
            </div>
            <div style={{ display: 'flex', gap: '8px', color: 'var(--color-on-surface-variant)' }}>
              {['notifications', 'settings'].map(icon => (
                <button key={icon} style={{
                  padding: '8px', borderRadius: 'var(--radius-lg)',
                  backgroundColor: 'transparent', border: 'none', cursor: 'pointer',
                  color: 'var(--color-on-surface-variant)',
                  transition: 'all 0.2s',
                }}
                  onMouseEnter={e => e.currentTarget.style.backgroundColor = 'var(--color-surface-variant)'}
                  onMouseLeave={e => e.currentTarget.style.backgroundColor = 'transparent'}
                >
                  <span className="material-symbols-outlined">{icon}</span>
                </button>
              ))}
            </div>
            <button style={{
              backgroundColor: 'var(--color-primary)',
              color: 'white', border: 'none',
              padding: '8px 16px', borderRadius: 'var(--radius-lg)',
              fontFamily: 'Inter, sans-serif', fontSize: '13px', fontWeight: 500,
              display: 'flex', alignItems: 'center', gap: '8px',
              cursor: 'pointer', transition: 'all 0.2s',
            }} onClick={() => navigate('/dashboard', { state: { openUpload: true } })}>
              <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>upload</span>
              Upload New Signal
            </button>
          </div>
        </header>

        {/* Content */}
        <div style={{ flex: 1, overflowY: 'auto', padding: 'var(--spacing-gutter)' }}>
          {analysis && (
            <div className="glass-panel" style={{ marginBottom: '16px', borderRadius: '12px', padding: '16px', border: '1px solid rgba(93, 230, 255, 0.25)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: '16px', flexWrap: 'wrap' }}>
                <div>
                  <div className="font-label-caps" style={{ color: 'var(--color-secondary)', marginBottom: '4px' }}>Current Analysis</div>
                  <div style={{ color: 'var(--color-on-surface)', fontWeight: 700 }}>{analysisBundle?.file?.name || 'Uploaded IQ file'}</div>
                  <div style={{ color: 'var(--color-on-surface-variant)', fontSize: '12px' }}>{analysisBundle?.jobId ? `Job ${analysisBundle.jobId}` : 'Live analysis bundle'}</div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(120px, 1fr))', gap: '12px', flex: 1 }}>
                  <div><div className="font-label-caps" style={{ fontSize: '10px', color: 'var(--color-outline)' }}>Prediction</div><div style={{ color: 'var(--color-primary)', fontWeight: 700 }}>{modulation?.prediction || 'N/A'}</div></div>
                  <div><div className="font-label-caps" style={{ fontSize: '10px', color: 'var(--color-outline)' }}>Confidence</div><div style={{ color: 'var(--color-secondary)', fontWeight: 700 }}>{modulation?.confidence != null ? `${(modulation.confidence * 100).toFixed(1)}%` : 'N/A'}</div></div>
                  <div><div className="font-label-caps" style={{ fontSize: '10px', color: 'var(--color-outline)' }}>SNR</div><div style={{ color: 'var(--color-secondary)', fontWeight: 700 }}>{spectral?.snr_db?.value != null ? `${spectral.snr_db.value.toFixed(1)} dB` : 'N/A'}</div></div>
                  <div><div className="font-label-caps" style={{ fontSize: '10px', color: 'var(--color-outline)' }}>CFO</div><div style={{ color: 'var(--color-secondary)', fontWeight: 700 }}>{synchronization?.frequency_offset_hz?.value != null ? `${synchronization.frequency_offset_hz.value.toFixed(1)} Hz` : 'N/A'}</div></div>
                </div>
              </div>
              {modulation?.probabilities && (
                <div style={{ marginTop: '12px', display: 'grid', gap: '8px' }}>
                  {Object.entries(modulation.probabilities).map(([name, value]) => (
                    <div key={name}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                        <span style={{ color: 'var(--color-on-surface-variant)' }}>{name}</span>
                        <span style={{ color: 'var(--color-on-surface)' }}>{(value * 100).toFixed(1)}%</span>
                      </div>
                      <div style={{ height: '6px', backgroundColor: 'var(--color-surface-container-high)', borderRadius: '999px', overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: `${value * 100}%`, backgroundColor: name === modulation.prediction ? 'var(--color-primary)' : 'var(--color-secondary)', borderRadius: '999px' }} />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 'var(--spacing-gutter)', minHeight: '700px' }}>
            {/* Left: Constellation + Pipeline */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-gutter)' }}>
              {/* Constellation Card */}
              <div style={{
                backgroundColor: 'var(--color-surface-container-low)',
                border: '1px solid var(--color-surface-variant)',
                borderRadius: 'var(--radius-lg)',
                flex: 1, display: 'flex', flexDirection: 'column',
                overflow: 'hidden',
              }}>
                <div style={{
                  padding: 'var(--spacing-container-padding)',
                  borderBottom: '1px solid var(--color-surface-variant)',
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  backgroundColor: 'rgba(23, 28, 36, 0.5)',
                }}>
                  <h3 className="font-label-caps" style={{ color: 'var(--color-on-surface)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className="material-symbols-outlined" style={{ fontSize: '14px', color: 'var(--color-secondary)' }}>scatter_plot</span>
                    AI Constellation Analysis
                  </h3>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    {[
                      { label: '16-QAM Predicted', bg: 'rgba(210, 187, 255, 0.1)', color: 'var(--color-primary)', border: 'rgba(210, 187, 255, 0.3)' },
                      { label: 'EVM: 4.2%', bg: 'var(--color-surface-variant)', color: 'var(--color-on-surface-variant)', border: 'var(--color-outline-variant)' },
                    ].map(badge => (
                      <span key={badge.label} className="font-data-md" style={{
                        padding: '2px 8px', borderRadius: 'var(--radius-default)',
                        fontSize: '10px',
                        backgroundColor: badge.bg, color: badge.color,
                        border: `1px solid ${badge.border}`,
                      }}>{badge.label}</span>
                    ))}
                  </div>
                </div>
                <ConstellationPlot mode={plotMode} activeMode={plotMode} onModeChange={setPlotMode} />
              </div>

              {/* Inference Pipeline Status */}
              <div style={{
                backgroundColor: 'var(--color-surface-container-low)',
                border: '1px solid var(--color-surface-variant)',
                borderRadius: 'var(--radius-lg)',
                height: '180px', display: 'flex', flexDirection: 'column',
                overflow: 'hidden',
              }}>
                <div style={{
                  padding: 'var(--spacing-container-padding)',
                  borderBottom: '1px solid var(--color-surface-variant)',
                  backgroundColor: 'rgba(23, 28, 36, 0.5)',
                }}>
                  <h3 className="font-label-caps" style={{ color: 'var(--color-on-surface)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className="material-symbols-outlined" style={{ fontSize: '14px', color: 'var(--color-tertiary)' }}>memory</span>
                    Inference Pipeline Status
                  </h3>
                </div>
                <div style={{ flex: 1, padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '16px' }}>
                  {[
                    { icon: 'filter_alt', label: 'Denoising\nAutoencoder', active: false },
                    null,
                    { icon: 'query_stats', label: 'Feature\nExtraction', active: true },
                    null,
                    { icon: 'network_node', label: 'CNN\nClassifier', active: false },
                  ].map((node, i) => {
                    if (node === null) return <div key={i} style={{ height: '1px', backgroundColor: 'var(--color-outline-variant)', width: '32px', flexShrink: 0 }} />;
                    return (
                      <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1 }}>
                        <div style={{
                          width: '40px', height: '40px', borderRadius: 'var(--radius-lg)',
                          backgroundColor: node.active ? 'rgba(210, 187, 255, 0.2)' : 'var(--color-surface-variant)',
                          border: `1px solid ${node.active ? 'rgba(210, 187, 255, 0.5)' : 'var(--color-surface-variant)'}`,
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          marginBottom: '8px',
                          boxShadow: node.active ? '0 0 15px rgba(210, 187, 255, 0.1)' : 'none',
                        }}>
                          <span className="material-symbols-outlined" style={{ fontSize: '16px', color: node.active ? 'var(--color-primary)' : 'var(--color-on-surface-variant)' }}>
                            {node.icon}
                          </span>
                        </div>
                        <span className="font-data-md" style={{ fontSize: '10px', color: node.active ? 'var(--color-primary)' : 'var(--color-on-surface-variant)', textAlign: 'center', whiteSpace: 'pre-line' }}>
                          {node.label}
                        </span>
                        {node.active && (
                          <div style={{ marginTop: '4px' }}>
                            <div style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--color-primary)' }} className="anim-pulse-fast" />
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Right: Classification + Features */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-gutter)' }}>
              {/* Modulation Classification */}
              <div style={{
                backgroundColor: 'var(--color-surface-container-low)',
                border: '1px solid var(--color-surface-variant)',
                borderRadius: 'var(--radius-lg)',
                flex: 1, display: 'flex', flexDirection: 'column',
                overflow: 'hidden',
              }}>
                <div style={{
                  padding: 'var(--spacing-container-padding)',
                  borderBottom: '1px solid var(--color-surface-variant)',
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  backgroundColor: 'rgba(23, 28, 36, 0.5)',
                }}>
                  <h3 className="font-label-caps" style={{ color: 'var(--color-on-surface)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className="material-symbols-outlined" style={{ fontSize: '14px', color: 'var(--color-primary)' }}>stacked_bar_chart</span>
                    Modulation Classification
                  </h3>
                  <span className="font-data-md" style={{ fontSize: '10px', color: 'var(--color-secondary)' }}>Model: VGG16_RF</span>
                </div>
                <div style={{ padding: '16px', flex: 1, display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {predictions.length === 0 && (
                    <div style={{ color: 'var(--color-on-surface-variant)', fontSize: '13px' }}>Upload a signal to view model probabilities.</div>
                  )}
                  {/* Primary prediction */}
                  {predictions.length > 0 && (
                  <div style={{
                    backgroundColor: 'rgba(48, 53, 62, 0.3)',
                    border: '1px solid rgba(210, 187, 255, 0.3)',
                    borderRadius: 'var(--radius-lg)',
                    padding: '12px',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '8px' }}>
                      <span className="font-data-md" style={{ fontWeight: 700, color: 'var(--color-on-surface)' }}>{predictions[0]?.name || 'N/A'}</span>
                      <span className="font-data-lg" style={{ fontSize: '18px', color: 'var(--color-primary)' }}>{predictions[0] ? `${predictions[0].conf.toFixed(1)}%` : 'N/A'}</span>
                    </div>
                    <div className="progress-bar-bg" style={{ height: '8px', borderRadius: '999px', overflow: 'hidden' }}>
                      <div className="progress-bar-fill" style={{ height: '100%', width: predictions[0] ? `${predictions[0].conf}%` : '0%' }} />
                    </div>
                  </div>
                  )}

                  {/* Other predictions */}
                  {predictions.length > 1 && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {predictions.slice(1).map(p => (
                      <div key={p.name}>
                        <div className="font-data-md" style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '4px' }}>
                          <span style={{ color: 'var(--color-on-surface-variant)' }}>{p.name}</span>
                          <span style={{ color: 'var(--color-on-surface-variant)' }}>{p.conf}%</span>
                        </div>
                        <div className="progress-bar-bg" style={{ height: '4px', borderRadius: '999px', overflow: 'hidden' }}>
                          <div style={{ height: '100%', width: `${p.conf}%`, backgroundColor: 'rgba(93, 230, 255, 0.7)', borderRadius: '999px' }} />
                        </div>
                      </div>
                    ))}
                  </div>
                  )}

                  <div style={{ marginTop: 'auto', paddingTop: '16px', borderTop: '1px solid var(--color-surface-variant)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '11px' }}>
                      <span className="font-data-md" style={{ color: 'var(--color-on-surface-variant)' }}>Confidence Score:</span>
                      <span className="font-data-md" style={{
                        color: 'var(--color-secondary)',
                        padding: '2px 8px',
                        backgroundColor: 'rgba(93, 230, 255, 0.1)',
                        borderRadius: 'var(--radius-default)',
                      }}>HIGH</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Extracted Features */}
              <div style={{
                backgroundColor: 'var(--color-surface-container-low)',
                border: '1px solid var(--color-surface-variant)',
                borderRadius: 'var(--radius-lg)',
                flex: 1, display: 'flex', flexDirection: 'column',
                overflow: 'hidden',
              }}>
                <div style={{
                  padding: 'var(--spacing-container-padding)',
                  borderBottom: '1px solid var(--color-surface-variant)',
                  backgroundColor: 'rgba(23, 28, 36, 0.5)',
                }}>
                  <h3 className="font-label-caps" style={{ color: 'var(--color-on-surface)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className="material-symbols-outlined" style={{ fontSize: '14px', color: 'var(--color-tertiary)' }}>data_object</span>
                    Extracted Features
                  </h3>
                </div>
                <div style={{ overflowY: 'auto' }}>
                  {features.length === 0 ? (
                    <div style={{ padding: '16px', color: 'var(--color-on-surface-variant)', fontSize: '13px' }}>Upload a signal to view extracted features.</div>
                  ) : (
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ backgroundColor: 'rgba(48, 53, 62, 0.2)', borderBottom: '1px solid var(--color-surface-variant)' }}>
                        <th className="font-label-caps" style={{ padding: '8px 16px', fontSize: '10px', color: 'var(--color-on-surface-variant)', textAlign: 'left' }}>Metric</th>
                        <th className="font-label-caps" style={{ padding: '8px 16px', fontSize: '10px', color: 'var(--color-on-surface-variant)', textAlign: 'right' }}>Value</th>
                      </tr>
                    </thead>
                    <tbody>
                      {features.map(f => (
                        <tr key={f.name} style={{ borderBottom: '1px solid var(--color-surface-variant)' }}
                          onMouseEnter={e => e.currentTarget.style.backgroundColor = 'rgba(48, 53, 62, 0.3)'}
                          onMouseLeave={e => e.currentTarget.style.backgroundColor = 'transparent'}
                        >
                          <td className="font-data-md" style={{ padding: '10px 16px', color: 'var(--color-on-surface-variant)', fontSize: '13px' }}>{f.name}</td>
                          <td className="font-data-md" style={{
                            padding: '10px 16px', textAlign: 'right', fontSize: '13px',
                            color: f.highlight === 'secondary' ? 'var(--color-secondary)' : f.highlight === 'primary' ? 'var(--color-primary)' : 'var(--color-on-surface)',
                          }}>{f.value}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
