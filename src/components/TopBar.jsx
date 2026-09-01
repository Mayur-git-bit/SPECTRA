export default function TopBar({ title, subtitle, showUpload = true, onUpload }) {
  return (
    <header style={{
      position: 'fixed',
      top: 0,
      right: 0,
      width: 'calc(100% - 260px)',
      zIndex: 40,
      backgroundColor: 'rgba(15, 19, 28, 0.85)',
      backdropFilter: 'blur(12px)',
      borderBottom: '1px solid var(--color-outline-variant)',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '0 var(--spacing-margin-page)',
      height: '80px',
    }}>
      <div>
        <h2 className="font-headline-md" style={{ color: 'var(--color-on-surface)' }}>{title}</h2>
        {subtitle && (
          <p style={{ color: 'var(--color-on-surface-variant)', fontSize: '13px', marginTop: '2px' }}>{subtitle}</p>
        )}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
        {/* Theme Toggle */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: '8px',
          backgroundColor: 'var(--color-surface-container)',
          padding: '4px',
          borderRadius: '999px',
          border: '1px solid var(--color-outline-variant)',
        }}>
          <span className="material-symbols-outlined" style={{ color: 'var(--color-on-surface-variant)', fontSize: '14px', paddingLeft: '8px' }}>
            light_mode
          </span>
          <div style={{
            width: '32px', height: '16px',
            backgroundColor: 'var(--color-primary-container)',
            borderRadius: '999px',
            position: 'relative',
          }}>
            <div style={{
              position: 'absolute', right: 0, top: 0,
              width: '16px', height: '16px',
              backgroundColor: 'var(--color-on-primary-container)',
              borderRadius: '50%',
              transform: 'scale(1.2)',
              border: '2px solid var(--color-primary-container)',
            }} />
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button style={{
            width: '40px', height: '40px', borderRadius: '50%',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'var(--color-on-surface-variant)',
            backgroundColor: 'transparent',
            border: '1px solid transparent',
          }}
            onMouseEnter={e => {
              e.currentTarget.style.backgroundColor = 'var(--color-surface-container-high)';
              e.currentTarget.style.borderColor = 'var(--color-outline-variant)';
            }}
            onMouseLeave={e => {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.borderColor = 'transparent';
            }}>
            <span className="material-symbols-outlined">dark_mode</span>
          </button>
          <button style={{
            width: '40px', height: '40px', borderRadius: '50%',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'var(--color-on-surface-variant)',
            backgroundColor: 'transparent',
            border: '1px solid transparent',
            position: 'relative',
          }}
            onMouseEnter={e => {
              e.currentTarget.style.backgroundColor = 'var(--color-surface-container-high)';
            }}
            onMouseLeave={e => {
              e.currentTarget.style.backgroundColor = 'transparent';
            }}>
            <span className="material-symbols-outlined">notifications</span>
            <span style={{
              position: 'absolute', top: '8px', right: '8px',
              width: '8px', height: '8px',
              backgroundColor: 'var(--color-error)',
              borderRadius: '50%',
            }} />
          </button>
        </div>

        {showUpload && (
          <button style={{
            backgroundColor: 'var(--color-primary-container)',
            color: 'var(--color-on-primary-container)',
            border: '1px solid rgba(210, 187, 255, 0.3)',
            borderRadius: 'var(--radius-default)',
            padding: '10px 24px',
            fontFamily: 'Inter, sans-serif',
            fontWeight: 500,
            fontSize: '14px',
            display: 'flex', alignItems: 'center', gap: '8px',
            boxShadow: '0 0 15px rgba(124, 58, 237, 0.3)',
            transition: 'all 0.2s ease',
          }}
            onMouseEnter={e => {
              e.currentTarget.style.backgroundColor = 'var(--color-inverse-primary)';
              e.currentTarget.style.boxShadow = '0 0 20px rgba(124, 58, 237, 0.5)';
            }}
            onMouseLeave={e => {
              e.currentTarget.style.backgroundColor = 'var(--color-primary-container)';
              e.currentTarget.style.boxShadow = '0 0 15px rgba(124, 58, 237, 0.3)';
            }}
            onClick={onUpload}>
            <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>upload</span>
            Upload New Signal
          </button>
        )}
      </div>
    </header>
  );
}
