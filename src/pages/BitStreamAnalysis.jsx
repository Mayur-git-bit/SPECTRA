import { useEffect, useState } from 'react';
import Sidebar from '../components/Sidebar';
import TopBar from '../components/TopBar';

export default function BitStreamAnalysis() {
  const [streamData, setStreamData] = useState([]);
  
  useEffect(() => {
    // Generate simulated infinite hex stream data
    const rows = 60;
    const data = [];
    for(let i=0; i<rows; i++) {
      let offset = (0x001000 + (i*16)).toString(16).padStart(8, '0').toUpperCase();
      let hex1 = [], hex2 = [], ascii = [];
      
      for(let j=0; j<8; j++) {
        let val = Math.floor(Math.random() * 256);
        let hex = val.toString(16).padStart(2, '0').toUpperCase();
        let char = (val > 32 && val < 127) ? String.fromCharCode(val) : '.';
        let isSync = (i % 15 === 0 && j < 4);
        hex1.push({ val: hex, char, type: isSync ? 'sync' : 'normal' });
      }
      for(let j=0; j<8; j++) {
        let val = Math.floor(Math.random() * 256);
        let hex = val.toString(16).padStart(2, '0').toUpperCase();
        let char = (val > 32 && val < 127) ? String.fromCharCode(val) : '.';
        let isPayload = (i % 15 !== 0);
        hex2.push({ val: hex, char, type: isPayload ? 'payload' : 'normal' });
      }
      data.push({ offset, hex1, hex2 });
    }
    setStreamData(data);
  }, []);

  return (
    <div className="page-layout">
      <Sidebar />
      <div className="main-content">
        <TopBar title="Mission Control" subtitle="Bit Stream Analysis" />
        
        <main style={{
          flex: 1, paddingTop: '96px', padding: '96px 24px 32px',
          display: 'flex', flexDirection: 'column', gap: '24px',
          maxWidth: '1600px', margin: '0 auto', width: '100%',
        }}>
          {/* Controls & Summary */}
          <div style={{ display: 'grid', gridTemplateColumns: '8fr 4fr', gap: '24px' }}>
            {/* Stream Controls */}
            <div className="glass-panel" style={{ borderRadius: '12px', padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <span className="font-label-caps" style={{ color: 'var(--color-on-surface-variant)', fontSize: '10px', textTransform: 'uppercase' }}>Stream Source</span>
                  <span className="font-data-md" style={{ color: 'var(--color-secondary)' }}>CH1_QPSK_14.4Mbaud</span>
                </div>
                <div style={{ height: '32px', width: '1px', backgroundColor: 'var(--color-outline-variant)' }} />
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <span className="font-label-caps" style={{ color: 'var(--color-on-surface-variant)', fontSize: '10px', textTransform: 'uppercase' }}>Format</span>
                  <select>
                    <option>Hexadecimal</option>
                    <option>Binary (Base2)</option>
                    <option>ASCII</option>
                  </select>
                </div>
                <div style={{ height: '32px', width: '1px', backgroundColor: 'var(--color-outline-variant)' }} />
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {['play_arrow', 'pause', 'skip_next'].map(icon => (
                    <button key={icon} style={{
                      padding: '6px',
                      backgroundColor: 'transparent',
                      border: '1px solid var(--color-outline-variant)',
                      borderRadius: 'var(--radius-default)',
                      color: 'var(--color-on-surface-variant)',
                      cursor: 'pointer',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}
                      onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--color-secondary)'; e.currentTarget.style.color = 'var(--color-secondary)'; }}
                      onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--color-outline-variant)'; e.currentTarget.style.color = 'var(--color-on-surface-variant)'; }}
                    >
                      <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>{icon}</span>
                    </button>
                  ))}
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                  display: 'flex', alignItems: 'center', gap: '8px',
                  padding: '4px 12px',
                  backgroundColor: 'var(--color-surface-container)',
                  border: '1px solid rgba(93, 230, 255, 0.3)',
                  borderRadius: '999px',
                }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--color-secondary)' }} className="anim-pulse-fast" />
                  <span className="font-label-caps" style={{ fontSize: '12px', color: 'var(--color-secondary)' }}>Sync Lock</span>
                </div>
                <button style={{
                  padding: '6px 12px',
                  backgroundColor: 'transparent',
                  border: '1px solid var(--color-outline-variant)',
                  borderRadius: 'var(--radius-default)',
                  color: 'var(--color-on-surface)',
                  fontFamily: 'Inter, sans-serif', fontSize: '12px', fontWeight: 500,
                  display: 'flex', alignItems: 'center', gap: '4px',
                  cursor: 'pointer',
                }}>
                  <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>download</span> Export
                </button>
              </div>
            </div>

            {/* Stream Stats */}
            <div className="glass-panel" style={{ borderRadius: '12px', padding: '16px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <span className="font-label-caps" style={{ color: 'var(--color-on-surface-variant)', fontSize: '10px', textTransform: 'uppercase', display: 'block', marginBottom: '4px' }}>Bitrate (Effective)</span>
                <div className="font-data-md" style={{ fontSize: '18px', color: 'var(--color-on-surface)' }}>28.8 <span style={{ fontSize: '12px', color: 'var(--color-on-surface-variant)' }}>Mbps</span></div>
              </div>
              <div>
                <span className="font-label-caps" style={{ color: 'var(--color-on-surface-variant)', fontSize: '10px', textTransform: 'uppercase', display: 'block', marginBottom: '4px' }}>BER (Post-FEC)</span>
                <div className="font-data-md" style={{ fontSize: '18px', color: 'var(--color-secondary)' }}>1.2e-7</div>
              </div>
            </div>
          </div>

          {/* Main Data Views */}
          <div style={{ display: 'grid', gridTemplateColumns: '8fr 4fr', gap: '24px', flex: 1, minHeight: '500px' }}>
            {/* Hex/Binary Viewer Panel */}
            <div className="glass-panel neon-glow-cyan" style={{ borderRadius: '12px', display: 'flex', flexDirection: 'column', overflow: 'hidden', borderColor: 'rgba(93, 230, 255, 0.3)' }}>
              <div style={{
                padding: '12px 16px', borderBottom: '1px solid rgba(74,68,85,0.5)',
                backgroundColor: 'rgba(15, 19, 28, 0.5)',
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              }}>
                <h3 className="font-label-caps" style={{ color: 'var(--color-secondary)', fontSize: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>data_object</span>
                  Raw Stream Viewer
                </h3>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <div className="font-data-md" style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '10px', color: 'var(--color-on-surface-variant)' }}>
                    <span style={{ width: '8px', height: '8px', backgroundColor: 'var(--color-error)', borderRadius: '2px' }} /> Header
                  </div>
                  <div className="font-data-md" style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '10px', color: 'var(--color-on-surface-variant)' }}>
                    <span style={{ width: '8px', height: '8px', backgroundColor: 'var(--color-secondary)', borderRadius: '2px' }} /> Payload
                  </div>
                </div>
              </div>
              
              <div style={{ flex: 1, backgroundColor: '#060A12', padding: '16px', fontFamily: 'JetBrains Mono, monospace', fontSize: '14px', overflow: 'hidden', position: 'relative' }}>
                {/* Headers */}
                <div style={{ display: 'flex', color: 'rgba(204, 195, 216, 0.5)', fontSize: '12px', marginBottom: '8px', paddingLeft: '48px', paddingBottom: '8px', borderBottom: '1px solid rgba(74,68,85,0.3)' }}>
                  <div style={{ width: '300px', display: 'flex', justifyContent: 'space-between', paddingRight: '16px' }}>
                    {['00','01','02','03','04','05','06','07'].map(v=><span key={v}>{v}</span>)}
                  </div>
                  <div style={{ width: '300px', display: 'flex', justifyContent: 'space-between', padding: '0 16px', borderLeft: '1px solid rgba(74,68,85,0.3)' }}>
                    {['08','09','0A','0B','0C','0D','0E','0F'].map(v=><span key={v}>{v}</span>)}
                  </div>
                  <div style={{ flex: 1, padding: '0 16px', borderLeft: '1px solid rgba(74,68,85,0.3)' }}>ASCII</div>
                </div>
                
                {/* Data stream (Animated) */}
                <div style={{ position: 'absolute', top: '48px', left: '0', right: '0', bottom: '0', padding: '0 16px', overflow: 'hidden' }}>
                  <div className="scrolling-data">
                    {[...streamData, ...streamData].map((row, i) => (
                      <div key={i} style={{ display: 'flex', padding: '4px 0', cursor: 'crosshair', transition: 'background-color 0.2s' }}
                        onMouseEnter={e => e.currentTarget.style.backgroundColor = 'rgba(48, 53, 62, 0.3)'}
                        onMouseLeave={e => e.currentTarget.style.backgroundColor = 'transparent'}
                      >
                        <div style={{ width: '80px', color: 'rgba(204, 195, 216, 0.5)', userSelect: 'none' }}>{row.offset}</div>
                        <div style={{ width: '300px', paddingRight: '16px', display: 'flex', justifyContent: 'space-between', letterSpacing: '0.1em' }}>
                          {row.hex1.map((h, j) => (
                            <span key={j} style={{
                              color: h.type === 'sync' ? 'var(--color-error)' : 'rgba(223, 226, 238, 0.8)',
                              fontWeight: h.type === 'sync' ? 'bold' : 'normal',
                            }}>{h.val}</span>
                          ))}
                        </div>
                        <div style={{ width: '300px', padding: '0 16px', borderLeft: '1px solid rgba(74,68,85,0.3)', display: 'flex', justifyContent: 'space-between', letterSpacing: '0.1em' }}>
                          {row.hex2.map((h, j) => (
                            <span key={j} style={{
                              color: h.type === 'payload' ? 'rgba(93, 230, 255, 0.9)' : 'rgba(223, 226, 238, 0.8)',
                            }}>{h.val}</span>
                          ))}
                        </div>
                        <div style={{ flex: 1, padding: '0 16px', borderLeft: '1px solid rgba(74,68,85,0.3)', color: 'var(--color-on-surface-variant)', letterSpacing: '0.2em', wordBreak: 'break-all' }}>
                          {row.hex1.map((h, j) => <span key={`a1-${j}`} style={{ color: h.type === 'sync' ? 'var(--color-error)' : 'inherit' }}>{h.char}</span>)}
                          {row.hex2.map((h, j) => <span key={`a2-${j}`} style={{ color: h.type === 'payload' ? 'rgba(93, 230, 255, 0.9)' : 'inherit' }}>{h.char}</span>)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Right Sidebar Modules */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              {/* Frame Sync Structure */}
              <div className="glass-panel" style={{ borderRadius: '12px', display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
                <div style={{
                  padding: '12px 16px', borderBottom: '1px solid rgba(74,68,85,0.5)',
                  backgroundColor: 'rgba(15, 19, 28, 0.5)',
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                }}>
                  <h3 className="font-label-caps" style={{ color: 'var(--color-on-surface)', fontSize: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>view_timeline</span>
                    Frame Structure
                  </h3>
                </div>
                <div style={{ padding: '16px', flex: 1, display: 'flex', flexDirection: 'column', gap: '16px', backgroundColor: '#060A12' }}>
                  {/* Visual Packet */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <div className="font-label-caps" style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--color-on-surface-variant)' }}>
                      <span>Detected Packet (Length: 1024b)</span>
                      <span>Confidence: 98.4%</span>
                    </div>
                    <div className="font-data-md" style={{
                      height: '24px', width: '100%', display: 'flex', borderRadius: '4px', overflow: 'hidden',
                      fontSize: '9px', fontWeight: 'bold', textAlign: 'center', lineHeight: '24px',
                    }}>
                      <div style={{ width: '10%', backgroundColor: 'rgba(255, 180, 171, 0.8)', color: 'var(--color-on-error-container)', borderRight: '1px solid rgba(0,0,0,0.5)' }}>SYNC</div>
                      <div style={{ width: '15%', backgroundColor: 'rgba(0, 98, 210, 0.8)', color: 'var(--color-on-tertiary-container)', borderRight: '1px solid rgba(0,0,0,0.5)' }}>HDR</div>
                      <div style={{ width: '65%', backgroundColor: 'rgba(93, 230, 255, 0.8)', color: 'var(--color-on-secondary)', borderRight: '1px solid rgba(0,0,0,0.5)' }}>PAYLOAD</div>
                      <div style={{ width: '10%', backgroundColor: 'rgba(124, 58, 237, 0.8)', color: 'var(--color-on-primary-container)' }}>CRC</div>
                    </div>
                    <div className="font-data-md" style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--color-on-surface-variant)' }}>
                      <span>0</span><span>32</span><span>128</span><span>960</span><span>1024</span>
                    </div>
                  </div>
                  
                  <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid rgba(74,68,85,0.3)', flex: 1 }}>
                    <h4 className="font-label-caps" style={{ fontSize: '10px', color: 'var(--color-on-surface-variant)', marginBottom: '12px' }}>Header Decode</h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {[
                        { label: 'Src_Addr', value: '0x4F2A', color: 'var(--color-secondary)' },
                        { label: 'Dst_Addr', value: '0xFFFF (Bcast)', color: 'var(--color-secondary)' },
                        { label: 'Pkt_Type', value: '0x03 (Data)', color: 'var(--color-secondary)' },
                        { label: 'Seq_Num', value: '14092', color: 'var(--color-primary-fixed)' },
                      ].map((item, i) => (
                        <div key={i} className="font-data-md" style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', borderBottom: i < 3 ? '1px solid rgba(74,68,85,0.2)' : 'none', paddingBottom: '4px' }}>
                          <span style={{ color: 'var(--color-on-surface-variant)' }}>{item.label}</span>
                          <span style={{ color: item.color }}>{item.value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Entropy Analysis */}
              <div className="glass-panel" style={{ borderRadius: '12px', display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
                <div style={{
                  padding: '12px 16px', borderBottom: '1px solid rgba(74,68,85,0.5)',
                  backgroundColor: 'rgba(15, 19, 28, 0.5)',
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                }}>
                  <h3 className="font-label-caps" style={{ color: 'var(--color-on-surface)', fontSize: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>bar_chart</span>
                    Bit Entropy
                  </h3>
                  <span className="font-data-md" style={{ fontSize: '12px', backgroundColor: 'var(--color-surface-variant)', padding: '2px 8px', borderRadius: '4px', color: 'var(--color-secondary)' }}>7.92 bits/byte</span>
                </div>
                <div style={{ padding: '16px', flex: 1, backgroundColor: '#060A12', position: 'relative', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                  {/* Histogram */}
                  <div style={{ position: 'absolute', inset: '16px 16px 32px 16px', borderBottom: '1px solid rgba(74,68,85,0.5)', borderLeft: '1px solid rgba(74,68,85,0.5)', display: 'flex', alignItems: 'flex-end' }}>
                    <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'flex-end', gap: '4px', padding: '0 4px' }}>
                      {Array.from({ length: 32 }).map((_, i) => (
                        <div key={i} style={{
                          flex: 1,
                          backgroundColor: 'rgba(93, 230, 255, 0.4)',
                          height: `${85 + Math.random() * 15}%`,
                          borderRadius: '2px 2px 0 0',
                          transition: 'background-color 0.2s',
                        }}
                          onMouseEnter={e => e.currentTarget.style.backgroundColor = 'var(--color-secondary)'}
                          onMouseLeave={e => e.currentTarget.style.backgroundColor = 'rgba(93, 230, 255, 0.4)'}
                        />
                      ))}
                    </div>
                  </div>
                  <div className="font-data-md" style={{ position: 'absolute', bottom: '8px', left: '16px', right: '16px', display: 'flex', justifyContent: 'space-between', fontSize: '9px', color: 'var(--color-on-surface-variant)' }}>
                    <span>0x00</span><span>0x7F</span><span>0xFF</span>
                  </div>
                  
                  {/* Analysis overlay */}
                  <div className="font-data-md" style={{
                    position: 'absolute', top: '16px', right: '16px',
                    backgroundColor: 'rgba(38, 42, 51, 0.9)',
                    border: '1px solid var(--color-outline-variant)',
                    padding: '8px', borderRadius: '4px', fontSize: '12px',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-error)' }}>
                      <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>lock</span>
                      Encrypted/Compressed
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
