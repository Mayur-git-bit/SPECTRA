import { Link, useLocation } from 'react-router-dom';

const navItems = [
  { path: '/dashboard', icon: 'dashboard', label: 'Dashboard', filled: true },
  { path: '/upload', icon: 'upload_file', label: 'Upload Signal' },
  { path: '/signal-detection', icon: 'sensors', label: 'Signal Detection' },
  { path: '/ai-analysis', icon: 'psychology', label: 'AI Analysis' },
  { path: '/dsp-pipeline', icon: 'account_tree', label: 'DSP Pipeline' },
  { path: '/bit-stream', icon: 'save_as', label: 'Bit Stream Analysis' },
  { path: '/results', icon: 'analytics', label: 'Results' },
  { path: '/dataset', icon: 'database', label: 'Dataset Generator' },
  { path: '/model-training', icon: 'model_training', label: 'Model Training' },
  { path: '/settings', icon: 'settings', label: 'Settings' },
];

export default function Sidebar() {
  const location = useLocation();

  return (
    <nav style={{
      width: 'var(--sidebar-width)',
      height: '100vh',
      position: 'fixed',
      left: 0,
      top: 0,
      backgroundColor: 'var(--color-surface-container-lowest)',
      borderRight: '1px solid var(--color-outline-variant)',
      display: 'flex',
      flexDirection: 'column',
      padding: 'var(--spacing-gutter) var(--spacing-container-padding)',
      zIndex: 50,
    }}>
      {/* Brand */}
      <Link to="/" style={{ marginBottom: '32px', padding: '0 16px', display: 'flex', alignItems: 'center', gap: '12px', textDecoration: 'none' }}>
        <span className="material-symbols-outlined" style={{ color: 'var(--color-primary)', fontSize: '32px' }}>
          multiline_chart
        </span>
        <div>
          <h1 className="font-headline-md" style={{ color: 'var(--color-primary)', fontWeight: 700, letterSpacing: '-0.02em', margin: 0 }}>
            SmartSignal
          </h1>
          <p className="font-label-caps" style={{ color: 'var(--color-on-surface-variant)', textTransform: 'uppercase', margin: 0 }}>
            SIGINT v4.2
          </p>
        </div>
      </Link>

      {/* Nav Items */}
      <div style={{ flex: 1, overflowY: 'auto' }}>
        <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '2px' }}>
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <li key={item.path}>
                <Link
                  to={item.path}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '10px 16px',
                    borderRadius: 'var(--radius-default)',
                    borderLeft: isActive ? '2px solid var(--color-secondary-fixed)' : '2px solid transparent',
                    backgroundColor: isActive ? 'rgba(0, 203, 230, 0.1)' : 'transparent',
                    color: isActive ? 'var(--color-secondary-fixed)' : 'var(--color-on-surface-variant)',
                    textDecoration: 'none',
                    fontFamily: 'Inter, sans-serif',
                    fontSize: '14px',
                    fontWeight: isActive ? 600 : 400,
                    transition: 'all 0.2s ease',
                  }}
                  onMouseEnter={e => {
                    if (!isActive) {
                      e.currentTarget.style.color = 'var(--color-secondary-fixed)';
                      e.currentTarget.style.backgroundColor = 'var(--color-surface-container-high)';
                    }
                  }}
                  onMouseLeave={e => {
                    if (!isActive) {
                      e.currentTarget.style.color = 'var(--color-on-surface-variant)';
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }
                  }}
                >
                  <span
                    className="material-symbols-outlined"
                    style={{ fontVariationSettings: isActive ? "'FILL' 1" : "'FILL' 0" }}
                  >
                    {item.icon}
                  </span>
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </div>

      {/* Footer */}
      <div style={{ marginTop: 'auto', paddingTop: '24px', borderTop: '1px solid var(--color-outline-variant)' }}>
        <div style={{ marginBottom: '16px', padding: '0 16px' }}>
          <p className="font-label-caps" style={{ color: 'var(--color-on-surface-variant)', marginBottom: '8px' }}>
            SYSTEM STATUS
          </p>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-secondary)' }}>
            <span style={{
              width: '8px', height: '8px', borderRadius: '50%',
              backgroundColor: 'var(--color-secondary)',
              display: 'inline-block',
            }} className="anim-pulse-slow" />
            <span className="font-data-md" style={{ fontSize: '11px' }}>All Systems Operational</span>
          </div>
        </div>
        <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '2px' }}>
          {[
            { icon: 'memory', label: 'System Info' },
            { icon: 'account_circle', label: 'User Profile' },
          ].map(item => (
            <li key={item.label}>
              <a href="#" style={{
                display: 'flex', alignItems: 'center', gap: '12px',
                padding: '10px 16px',
                color: 'var(--color-on-surface-variant)',
                textDecoration: 'none', fontSize: '14px',
                borderRadius: 'var(--radius-default)',
                transition: 'all 0.2s ease',
              }}
                onMouseEnter={e => {
                  e.currentTarget.style.color = 'var(--color-secondary-fixed)';
                  e.currentTarget.style.backgroundColor = 'var(--color-surface-container-high)';
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.color = 'var(--color-on-surface-variant)';
                  e.currentTarget.style.backgroundColor = 'transparent';
                }}
              >
                <span className="material-symbols-outlined">{item.icon}</span>
                {item.label}
              </a>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
}
