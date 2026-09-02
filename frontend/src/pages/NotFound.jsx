import { Link } from 'react-router-dom';
export default function NotFound() {
  return (
    <div style={{minHeight:'100vh',display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',background:'var(--bg-primary)',gap:'var(--space-6)'}}>
      <div style={{fontSize:'5rem'}}>🔭</div>
      <h1 style={{fontSize:'var(--font-size-4xl)',fontWeight:700,background:'var(--gradient-accent)',WebkitBackgroundClip:'text',WebkitTextFillColor:'transparent',backgroundClip:'text'}}>404</h1>
      <p style={{color:'var(--text-muted)'}}>Page not found</p>
      <Link to="/" className="btn btn-primary">Go home</Link>
    </div>
  );
}
