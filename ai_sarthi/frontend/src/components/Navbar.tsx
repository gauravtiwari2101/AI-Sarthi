import { Link, useLocation } from 'react-router-dom';
import { Sparkles } from 'lucide-react';

export default function Navbar() {
  const location = useLocation();
  const isActive = (path: string) => {
    if (path === '/' && location.pathname === '/') return 'nav-link active';
    if (path !== '/' && location.pathname.startsWith(path)) return 'nav-link active';
    return 'nav-link';
  };

  return (
    <nav className="navbar" id="main-navbar">
      <Link to="/" className="navbar-brand">
        <div className="navbar-logo">MH</div>
        <div className="navbar-title-group">
          <div className="navbar-title">
            AI SARTHI
            <span style={{ fontSize: 10, color: 'var(--warm-amber)', fontWeight: 700, marginLeft: 4 }}>
              MAHARASHTRA
            </span>
          </div>
          <div className="navbar-subtitle">Public Health Department • Policy Intelligence</div>
        </div>
      </Link>

      <ul className="navbar-nav">
        <li><Link to="/" className={isActive('/')}>Overview</Link></li>
        <li><Link to="/districts" className={isActive('/districts')}>District Intelligence</Link></li>
        <li><Link to="/allocations" className={isActive('/allocations')}>Allocation Studio</Link></li>
        <li><Link to="/analytics" className={isActive('/analytics')}>Financial Analytics</Link></li>
        <li><Link to="/sources" className={isActive('/sources')}>Sources & Audit</Link></li>
      </ul>

      <div className="nav-actions">
        <Link to="/chat" className="btn-ask-ai" id="nav-ask-ai">
          <Sparkles size={14} />
          Ask AI Sarthi
        </Link>
      </div>
    </nav>
  );
}
