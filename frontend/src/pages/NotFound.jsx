import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--bg-primary)',
      gap: 16,
      transition: 'background-color 0.3s ease',
    }}>
      <div style={{
        fontSize: 'var(--font-size-4xl)',
        fontWeight: 700,
        color: 'var(--text-primary)',
        letterSpacing: '-0.04em',
      }}>
        404
      </div>
      <p style={{ color: 'var(--text-muted)', fontSize: 'var(--font-size-sm)' }}>
        This page doesn't exist or has been moved.
      </p>
      <Link to="/" className="btn btn-primary" style={{ marginTop: 8 }}>
        Back to home
      </Link>
    </div>
  );
}
