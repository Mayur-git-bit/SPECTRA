import { useEffect, useRef, useState } from 'react';
import Sidebar from '../components/Sidebar';
import TopBar from '../components/TopBar';

// Interactive Canvas for DSP Nodes
function DSPCanvas() {
  const canvasRef = useRef(null);
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    function resize() {
      const parent = canvas.parentElement;
      canvas.width = parent.clientWidth;
      canvas.height = parent.clientHeight;
      draw();
    }
    
    window.addEventListener('resize', resize);
    
    const nodes = [
      { id: 'n1', x: 100, y: 150, label: 'ADC Input', status: 'active', type: 'source' },
      { id: 'n2', x: 300, y: 150, label: 'DDC (Digital Down Conv)', status: 'active', type: 'process' },
      { id: 'n3', x: 500, y: 80, label: 'Low Pass Filter', status: 'active', type: 'filter' },
      { id: 'n4', x: 500, y: 220, label: 'High Pass Filter', status: 'inactive', type: 'filter' },
      { id: 'n5', x: 700, y: 80, label: 'Decimation (x4)', status: 'active', type: 'process' },
      { id: 'n6', x: 900, y: 150, label: 'Symbol Sync', status: 'active', type: 'sync' },
      { id: 'n7', x: 1100, y: 150, label: 'Carrier Recovery', status: 'warning', type: 'sync' },
    ];
    
    const edges = [
      { from: 'n1', to: 'n2', active: true },
      { from: 'n2', to: 'n3', active: true },
      { from: 'n2', to: 'n4', active: false },
      { from: 'n3', to: 'n5', active: true },
      { from: 'n5', to: 'n6', active: true },
      { from: 'n6', to: 'n7', active: true },
    ];
    
    let time = 0;
    let animationFrameId;
    
    function drawNode(node) {
      const isAct = node.status === 'active';
      const isWarn = node.status === 'warning';
      
      const borderColor = isAct ? '#5de6ff' : (isWarn ? '#ffb4ab' : '#4a4455');
      const bgColor = isAct ? 'rgba(13, 20, 34, 0.9)' : 'rgba(13, 20, 34, 0.7)';
      
      ctx.beginPath();
      ctx.roundRect(node.x - 75, node.y - 30, 150, 60, 8);
      ctx.fillStyle = bgColor;
      ctx.fill();
      ctx.lineWidth = 2;
      ctx.strokeStyle = borderColor;
      ctx.stroke();
      
      if (isAct || isWarn) {
        ctx.shadowColor = borderColor;
        ctx.shadowBlur = 10;
        ctx.stroke();
        ctx.shadowBlur = 0;
      }
      
      ctx.fillStyle = '#dfe2ee';
      ctx.font = '12px "JetBrains Mono"';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      
      // Wrap text simply
      const words = node.label.split(' ');
      if (words.length > 2) {
        ctx.fillText(words.slice(0,2).join(' '), node.x, node.y - 8);
        ctx.fillText(words.slice(2).join(' '), node.x, node.y + 8);
      } else {
        ctx.fillText(node.label, node.x, node.y);
      }
      
      // Status indicator
      if (isAct) {
        ctx.beginPath();
        ctx.arc(node.x - 60, node.y - 15, 4, 0, Math.PI*2);
        ctx.fillStyle = '#5de6ff';
        ctx.fill();
      } else if (isWarn) {
        ctx.beginPath();
        ctx.arc(node.x - 60, node.y - 15, 4, 0, Math.PI*2);
        ctx.fillStyle = '#ffb4ab';
        ctx.fill();
      }
    }
    
    function drawEdge(edge) {
      const fromNode = nodes.find(n => n.id === edge.from);
      const toNode = nodes.find(n => n.id === edge.to);
      if (!fromNode || !toNode) return;
      
      ctx.beginPath();
      ctx.moveTo(fromNode.x + 75, fromNode.y);
      
      // Bezier curve
      const cp1x = fromNode.x + 75 + 50;
      const cp1y = fromNode.y;
      const cp2x = toNode.x - 75 - 50;
      const cp2y = toNode.y;
      
      ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, toNode.x - 75, toNode.y);
      
      ctx.lineWidth = 2;
      ctx.strokeStyle = edge.active ? '#d2bbff' : '#4a4455';
      
      if (edge.active) {
        ctx.setLineDash([8, 8]);
        ctx.lineDashOffset = -time;
        ctx.shadowColor = '#d2bbff';
        ctx.shadowBlur = 8;
        ctx.stroke();
        ctx.shadowBlur = 0;
        ctx.setLineDash([]);
      } else {
        ctx.stroke();
      }
      
      // Arrowhead
      ctx.beginPath();
      ctx.moveTo(toNode.x - 75, toNode.y);
      ctx.lineTo(toNode.x - 85, toNode.y - 5);
      ctx.lineTo(toNode.x - 85, toNode.y + 5);
      ctx.fillStyle = edge.active ? '#d2bbff' : '#4a4455';
      ctx.fill();
    }
    
    function draw() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // Grid
      ctx.strokeStyle = 'rgba(74, 68, 85, 0.2)';
      ctx.lineWidth = 1;
      for (let x = 0; x < canvas.width; x += 40) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
      }
      for (let y = 0; y < canvas.height; y += 40) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
      }
      
      edges.forEach(drawEdge);
      nodes.forEach(drawNode);
      
      time += 1;
      animationFrameId = requestAnimationFrame(draw);
    }
    
    resize();
    
    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);
  
  return (
    <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }} className="canvas-bg">
      <canvas ref={canvasRef} style={{ display: 'block', width: '100%', height: '100%' }} />
      
      {/* Overlay Toolbar */}
      <div style={{
        position: 'absolute', top: '16px', left: '16px',
        backgroundColor: 'rgba(27, 32, 40, 0.8)',
        backdropFilter: 'blur(8px)',
        border: '1px solid var(--color-surface-variant)',
        borderRadius: 'var(--radius-lg)',
        padding: '4px',
        display: 'flex', gap: '4px',
      }}>
        {['add', 'remove', 'pan_tool', 'ads_click'].map((icon, i) => (
          <button key={icon} style={{
            padding: '6px',
            backgroundColor: i === 3 ? 'var(--color-surface-variant)' : 'transparent',
            color: i === 3 ? 'var(--color-secondary)' : 'var(--color-on-surface-variant)',
            border: 'none', borderRadius: 'var(--radius-default)',
            cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>{icon}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

export default function DSPPipeline() {
  const [activeTab, setActiveTab] = useState('parameters');
  
  return (
    <div className="page-layout">
      <Sidebar />
      <div className="main-content">
        <TopBar title="DSP Pipeline Configuration" subtitle="Visual flow-graph editor for signal processing chain" />
        
        <main style={{
          flex: 1, paddingTop: '80px',
          display: 'flex', flexDirection: 'column',
          height: '100vh', overflow: 'hidden',
        }}>
          {/* Main Area: Toolbar + Canvas */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', position: 'relative' }}>
            <DSPCanvas />
          </div>
          
          {/* Bottom Panel: Inspector/Parameters */}
          <div style={{
            height: '320px',
            backgroundColor: 'var(--color-surface-container-lowest)',
            borderTop: '1px solid var(--color-outline-variant)',
            display: 'flex',
          }}>
            {/* Left: Component Library */}
            <div style={{
              width: '260px',
              borderRight: '1px solid var(--color-outline-variant)',
              display: 'flex', flexDirection: 'column',
              backgroundColor: 'var(--color-surface-container-low)',
            }}>
              <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--color-surface-variant)' }}>
                <h3 className="font-label-caps" style={{ color: 'var(--color-on-surface-variant)' }}>COMPONENTS</h3>
              </div>
              <div style={{ flex: 1, overflowY: 'auto', padding: '12px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {[
                  { category: 'Sources', items: ['File Source', 'RTL-SDR', 'USRP Source'] },
                  { category: 'Filters', items: ['Low Pass', 'High Pass', 'Band Pass', 'FIR Filter'] },
                  { category: 'Math', items: ['Multiply', 'Add', 'Complex Conjugate'] },
                ].map(group => (
                  <div key={group.category}>
                    <div className="font-label-caps" style={{ color: 'var(--color-outline)', fontSize: '10px', marginBottom: '8px' }}>{group.category}</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      {group.items.map(item => (
                        <div key={item} className="font-data-md" style={{
                          padding: '6px 12px',
                          backgroundColor: 'var(--color-surface-container)',
                          border: '1px solid var(--color-surface-variant)',
                          borderRadius: 'var(--radius-default)',
                          fontSize: '11px', color: 'var(--color-on-surface)',
                          cursor: 'grab', display: 'flex', alignItems: 'center', gap: '8px',
                        }}>
                          <span className="material-symbols-outlined" style={{ fontSize: '14px', color: 'var(--color-on-surface-variant)' }}>drag_indicator</span>
                          {item}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Center & Right: Node Inspector */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
              <div style={{
                display: 'flex', borderBottom: '1px solid var(--color-surface-variant)',
                backgroundColor: 'var(--color-surface-container-low)',
              }}>
                {['Parameters', 'Metrics', 'Live Plot'].map((tab) => (
                  <button key={tab} 
                    onClick={() => setActiveTab(tab.toLowerCase())}
                    style={{
                      padding: '12px 24px',
                      backgroundColor: activeTab === tab.toLowerCase() ? 'var(--color-surface-container-lowest)' : 'transparent',
                      color: activeTab === tab.toLowerCase() ? 'var(--color-secondary)' : 'var(--color-on-surface-variant)',
                      border: 'none',
                      borderBottom: activeTab === tab.toLowerCase() ? '2px solid var(--color-secondary)' : '2px solid transparent',
                      borderRight: '1px solid var(--color-surface-variant)',
                      fontFamily: 'JetBrains Mono, monospace', fontSize: '11px', fontWeight: 700, letterSpacing: '0.05em', textTransform: 'uppercase',
                      cursor: 'pointer',
                  }}>
                    {tab}
                  </button>
                ))}
              </div>
              
              <div style={{ flex: 1, padding: '24px', display: 'flex', gap: '32px', overflowY: 'auto' }}>
                <div style={{ flex: 1, maxWidth: '500px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
                    <div style={{ width: '40px', height: '40px', borderRadius: 'var(--radius-lg)', backgroundColor: 'rgba(93, 230, 255, 0.1)', border: '1px solid var(--color-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-secondary)' }}>
                      <span className="material-symbols-outlined">filter_alt</span>
                    </div>
                    <div>
                      <h4 className="font-headline-md" style={{ fontSize: '18px', margin: 0, color: 'var(--color-on-surface)' }}>Low Pass Filter</h4>
                      <div className="font-data-md" style={{ fontSize: '11px', color: 'var(--color-secondary)' }}>ID: filter_lpf_01</div>
                    </div>
                  </div>
                  
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', alignItems: 'center', gap: '16px' }}>
                      <label className="font-data-md" style={{ fontSize: '12px', color: 'var(--color-on-surface-variant)' }}>Decimation</label>
                      <input type="number" defaultValue="1" style={{ width: '100%' }} />
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', alignItems: 'center', gap: '16px' }}>
                      <label className="font-data-md" style={{ fontSize: '12px', color: 'var(--color-on-surface-variant)' }}>Gain</label>
                      <input type="number" defaultValue="1.0" step="0.1" style={{ width: '100%' }} />
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', alignItems: 'center', gap: '16px' }}>
                      <label className="font-data-md" style={{ fontSize: '12px', color: 'var(--color-on-surface-variant)' }}>Sample Rate (Hz)</label>
                      <input type="number" defaultValue="2000000" style={{ width: '100%' }} />
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', alignItems: 'center', gap: '16px' }}>
                      <label className="font-data-md" style={{ fontSize: '12px', color: 'var(--color-on-surface-variant)' }}>Cutoff Freq (Hz)</label>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <input type="range" min="0" max="1000000" defaultValue="100000" style={{ flex: 1 }} />
                        <span className="font-data-md" style={{ fontSize: '12px', color: 'var(--color-secondary)', width: '60px', textAlign: 'right' }}>100k</span>
                      </div>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', alignItems: 'center', gap: '16px' }}>
                      <label className="font-data-md" style={{ fontSize: '12px', color: 'var(--color-on-surface-variant)' }}>Transition Width</label>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <input type="range" min="0" max="50000" defaultValue="10000" style={{ flex: 1 }} />
                        <span className="font-data-md" style={{ fontSize: '12px', color: 'var(--color-secondary)', width: '60px', textAlign: 'right' }}>10k</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div style={{ flex: 1, borderLeft: '1px solid var(--color-surface-variant)', paddingLeft: '32px' }}>
                  <h4 className="font-label-caps" style={{ color: 'var(--color-on-surface-variant)', marginBottom: '16px' }}>Filter Response Preview</h4>
                  <div style={{
                    height: '180px',
                    backgroundColor: 'var(--color-surface-container)',
                    border: '1px solid var(--color-outline-variant)',
                    borderRadius: 'var(--radius-lg)',
                    position: 'relative',
                    overflow: 'hidden',
                  }}>
                    <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }} viewBox="0 0 400 180" preserveAspectRatio="none">
                      <defs>
                        <linearGradient id="fillGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#d2bbff" stopOpacity="0.3" />
                          <stop offset="100%" stopColor="#d2bbff" stopOpacity="0" />
                        </linearGradient>
                      </defs>
                      {/* Ideal vs Actual filter response */}
                      <path d="M0 40 L150 40 L160 160 L400 160" fill="none" stroke="#4a4455" strokeWidth="1" strokeDasharray="4 4" />
                      <path d="M0 40 Q75 40 140 45 T170 150 Q200 160 400 160" fill="url(#fillGrad)" stroke="#d2bbff" strokeWidth="2" style={{ filter: 'drop-shadow(0 0 4px #d2bbff)' }} />
                    </svg>
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
