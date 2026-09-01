import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import TopBar from '../components/TopBar';
import { useAnalysis } from '../context/AnalysisContext';
import { uploadAndAnalyzeSignal } from '../utils/signalUpload';

// WebGL Shader Background
function ShaderCanvas() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    function syncSize() {
      const w = canvas.clientWidth || 1280;
      const h = canvas.clientHeight || 720;
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w;
        canvas.height = h;
      }
    }

    const resizeObserver = new ResizeObserver(syncSize);
    resizeObserver.observe(canvas);
    syncSize();

    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    if (!gl) return;

    const vs = `attribute vec2 a_position;
varying vec2 v_texCoord;
void main() {
  v_texCoord = a_position * 0.5 + 0.5;
  gl_Position = vec4(a_position, 0.0, 1.0);
}`;
    const fs = `precision highp float;
uniform float u_time;
uniform vec2 u_resolution;
varying vec2 v_texCoord;

void main() {
    vec2 uv = v_texCoord;
    vec3 bg = vec3(0.02, 0.04, 0.07);
    float pulseSpeed = 1.2;
    float waveDist = 0.25;
    vec3 finalColor = bg;
    
    for (float i = 0.0; i < 4.0; i++) {
        float timeOffset = i * waveDist;
        float progress = fract(u_time * pulseSpeed * 0.2 - timeOffset);
        float dist = distance(uv, vec2(-0.1, 0.5));
        float waveIntensity = smoothstep(0.01, 0.0, abs(dist - progress * 1.5));
        waveIntensity *= (1.0 - progress);
        vec3 cyan = vec3(0.13, 0.83, 0.93);
        vec3 purple = vec3(0.48, 0.22, 0.93);
        vec3 waveColor = mix(cyan, purple, progress);
        finalColor += waveIntensity * waveColor * 0.8;
    }
    float noise = fract(sin(dot(uv, vec2(12.9898, 78.233))) * 43758.5453);
    finalColor += noise * 0.02;
    gl_FragColor = vec4(finalColor, 1.0);
}`;

    function createShader(type, src) {
      const s = gl.createShader(type);
      gl.shaderSource(s, src);
      gl.compileShader(s);
      return s;
    }

    const prog = gl.createProgram();
    gl.attachShader(prog, createShader(gl.VERTEX_SHADER, vs));
    gl.attachShader(prog, createShader(gl.FRAGMENT_SHADER, fs));
    gl.linkProgram(prog);
    gl.useProgram(prog);

    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    const pos = gl.getAttribLocation(prog, 'a_position');
    gl.enableVertexAttribArray(pos);
    gl.vertexAttribPointer(pos, 2, gl.FLOAT, false, 0, 0);

    const uTime = gl.getUniformLocation(prog, 'u_time');
    const uRes = gl.getUniformLocation(prog, 'u_resolution');

    let rafId;
    function render(t) {
      syncSize();
      gl.viewport(0, 0, canvas.width, canvas.height);
      if (uTime) gl.uniform1f(uTime, t * 0.001);
      if (uRes) gl.uniform2f(uRes, canvas.width, canvas.height);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      rafId = requestAnimationFrame(render);
    }
    rafId = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(rafId);
      resizeObserver.disconnect();
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{ display: 'block', width: '100%', height: '100%' }}
    />
  );
}

// Pipeline Node animation
function PipelineSection() {
  const nodeRef = useRef(null);

  useEffect(() => {
    const nodes = nodeRef.current?.querySelectorAll('.pipeline-node');
    const connectors = nodeRef.current?.querySelectorAll('.pipeline-connector .mat-icon');
    if (!nodes) return;

    let currentIndex = 0;
    const interval = setInterval(() => {
      nodes.forEach(n => {
        n.classList.remove('active');
        n.style.color = 'var(--color-on-surface-variant)';
      });
      nodes[currentIndex].classList.add('active');
      currentIndex = (currentIndex + 1) % nodes.length;
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div ref={nodeRef} className="glass-panel" style={{ borderRadius: '12px', padding: '32px', maxWidth: '800px', margin: '0 auto' }}>
      <div className="font-label-caps" style={{
        color: 'var(--color-on-surface-variant)',
        marginBottom: '32px',
        textAlign: 'center',
        letterSpacing: '0.15em',
      }}>
        AUTOMATED ANALYSIS PIPELINE
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '48px' }}>
        {[
          { icon: 'input', label: 'INPUT' },
          { icon: 'radar', label: 'DETECT' },
          { icon: 'psychology', label: 'AI CLASSIFY' },
          { icon: 'memory', label: 'DSP' },
          { icon: 'lock_open', label: 'DECODE' },
        ].map((item, i) => (
          <div key={i} style={{ display: 'contents' }}>
            <div className="pipeline-node" style={{ textAlign: 'center' }}>
              <span className="material-symbols-outlined" style={{ fontSize: '24px', display: 'block', marginBottom: '4px' }}>
                {item.icon}
              </span>
              <div className="font-data-md" style={{ fontSize: '10px' }}>{item.label}</div>
            </div>
            {i < 4 && (
              <div className="pipeline-connector">
                <span className="material-symbols-outlined mat-icon" style={{
                  position: 'relative', zIndex: 10,
                  backgroundColor: 'var(--color-background)',
                  fontSize: '14px',
                  color: 'var(--color-outline)',
                }}>arrow_forward</span>
              </div>
            )}
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px', paddingTop: '32px', borderTop: '1px solid var(--color-outline-variant)' }}>
        <div style={{ textAlign: 'center' }}>
          <div className="font-data-md" style={{ color: 'var(--color-secondary)', marginBottom: '8px' }}>SUPPORTED FORMATS</div>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '12px', flexWrap: 'wrap' }}>
            {['IQ', 'WAV', 'HF', 'VHF', 'UHF'].map(f => (
              <span key={f} className="font-data-lg" style={{
                backgroundColor: 'var(--color-surface-container-high)',
                padding: '4px 8px',
                borderRadius: 'var(--radius-lg)',
                fontSize: '13px',
                color: 'var(--color-on-surface-variant)',
              }}>{f}</span>
            ))}
          </div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div className="font-data-md" style={{ color: 'var(--color-primary)', marginBottom: '8px' }}>ANALYSIS CAPABILITIES</div>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '12px', flexWrap: 'wrap' }}>
            {['Modulation', 'FEC', 'Interleaving', 'Spectrum'].map(f => (
              <span key={f} className="font-data-lg" style={{
                backgroundColor: 'var(--color-surface-container-high)',
                padding: '4px 8px',
                borderRadius: 'var(--radius-lg)',
                fontSize: '13px',
                color: 'var(--color-on-surface-variant)',
              }}>{f}</span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  const navigate = useNavigate();
  const { setAnalysisBundle } = useAnalysis();
  const fileInputRef = useRef(null);
  const [isUploading, setIsUploading] = useState(false);

  const openUploader = () => {
    fileInputRef.current?.click();
  };

  const handleFileSelect = async (event) => {
    const selectedFile = event.target.files?.[0];
    event.target.value = '';

    if (!selectedFile) {
      return;
    }

    setIsUploading(true);
    try {
      const bundle = await uploadAndAnalyzeSignal(selectedFile);
      setAnalysisBundle(bundle);
      navigate('/dashboard');
    } catch (error) {
      console.error(error);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="page-layout">
      <Sidebar />
      <main className="main-content" style={{ position: 'relative', backgroundColor: '#060A12' }}>
        <TopBar title="Mission Control" showUpload={true} onUpload={openUploader} />
        <input ref={fileInputRef} type="file" accept=".iq,.wav" onChange={handleFileSelect} style={{ display: 'none' }} />

        {/* Hero Section */}
        <section style={{
          position: 'relative',
          paddingTop: '160px',
          paddingBottom: '96px',
          padding: '160px 96px 96px',
          minHeight: '70vh',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
        }}>
          {/* Shader BG */}
          <div style={{
            position: 'absolute', inset: 0, zIndex: 0, overflow: 'hidden', opacity: 0.4,
          }}>
            <ShaderCanvas />
          </div>

          <div style={{
            position: 'relative', zIndex: 10,
            maxWidth: '800px', margin: '0 auto',
            textAlign: 'center',
          }}>
            <h1 className="tech-gradient-text" style={{
              fontFamily: 'Manrope, sans-serif',
              fontSize: 'clamp(48px, 6vw, 72px)',
              fontWeight: 700,
              letterSpacing: '-0.02em',
              lineHeight: 1.1,
              marginBottom: '24px',
              marginTop: '80px',
            }}>
              Decode the Unknown.
            </h1>
            <p className="font-body-lg" style={{
              color: 'var(--color-on-surface-variant)',
              fontSize: '18px',
              maxWidth: '600px',
              margin: '0 auto 40px',
              lineHeight: 1.7,
            }}>
              AI-powered RF signal intelligence for automated modulation, FEC, interleaver and waveform analysis.
            </p>

            <div style={{ display: 'flex', justifyContent: 'center', gap: '24px' }}>
              <button disabled={isUploading} style={{
                backgroundColor: 'var(--color-primary-container)',
                color: 'var(--color-on-primary-container)',
                padding: '12px 32px',
                borderRadius: 'var(--radius-xl)',
                fontFamily: 'JetBrains Mono, monospace',
                fontWeight: 700,
                fontSize: '14px',
                display: 'flex', alignItems: 'center', gap: '8px',
                border: 'none',
                boxShadow: '0 0 20px rgba(124, 58, 237, 0.4)',
                transition: 'all 0.2s ease',
              }}
                onClick={openUploader}
                onMouseEnter={e => e.currentTarget.style.boxShadow = '0 0 30px rgba(124, 58, 237, 0.7)'}
                onMouseLeave={e => e.currentTarget.style.boxShadow = '0 0 20px rgba(124, 58, 237, 0.4)'}
              >
                <span className="material-symbols-outlined">query_stats</span>
                {isUploading ? 'Uploading...' : 'Analyze a Signal'}
              </button>
              <button style={{
                backgroundColor: 'transparent',
                color: 'var(--color-on-surface)',
                padding: '12px 32px',
                borderRadius: 'var(--radius-xl)',
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '14px',
                display: 'flex', alignItems: 'center', gap: '8px',
                border: '1px solid var(--color-outline)',
                transition: 'all 0.2s ease',
              }}
                onMouseEnter={e => {
                  e.currentTarget.style.borderColor = 'var(--color-secondary)';
                  e.currentTarget.style.color = 'var(--color-secondary)';
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.borderColor = 'var(--color-outline)';
                  e.currentTarget.style.color = 'var(--color-on-surface)';
                }}
              >
                <span className="material-symbols-outlined">account_tree</span>
                Explore Pipeline
              </button>
            </div>

            {/* Floating Labels */}
            <div className="font-data-md" style={{
              position: 'absolute', top: '25%', left: '40px',
              color: 'var(--color-secondary)', fontSize: '12px', opacity: 0.6,
              display: 'flex', alignItems: 'center', gap: '4px',
            }}>
              <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>timeline</span>
              QPSK
            </div>
            <div className="font-data-md" style={{
              position: 'absolute', bottom: '33%', right: '48px',
              color: 'var(--color-primary)', fontSize: '12px', opacity: 0.6,
              display: 'flex', alignItems: 'center', gap: '4px',
            }}>
              <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>memory</span>
              FEC Detected
            </div>
          </div>
        </section>

        {/* Pipeline Preview */}
        <section style={{
          position: 'relative', zIndex: 10,
          padding: '0 96px 96px',
        }}>
          <PipelineSection />
        </section>

        {/* Footer Status Bar */}
        <footer style={{
          backgroundColor: 'var(--color-surface-container-lowest)',
          borderTop: '1px solid var(--color-outline-variant)',
          height: '48px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 24px',
          marginTop: 'auto',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
            {[
              { icon: 'memory', label: 'GPU: NVIDIA RTX 3060' },
              { icon: 'code', label: 'Core v1.0.0' },
            ].map(item => (
              <div key={item.label} className="font-data-md" style={{
                display: 'flex', alignItems: 'center', gap: '8px',
                color: 'var(--color-on-surface-variant)', fontSize: '11px',
              }}>
                <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>{item.icon}</span>
                {item.label}
              </div>
            ))}
          </div>
          <div className="font-data-md" style={{
            display: 'flex', alignItems: 'center', gap: '8px',
            color: 'var(--color-secondary)', fontSize: '11px',
          }}>
            <span style={{
              width: '8px', height: '8px', borderRadius: '50%',
              backgroundColor: 'var(--color-secondary)',
              display: 'inline-block',
            }} className="anim-pulse-slow" />
            All Systems Operational
          </div>
        </footer>
      </main>
    </div>
  );
}
