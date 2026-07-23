// src/components/Header.jsx
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import logo from '../assets/ZaibHunt.png';

function Header() {
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="app-header">
      <div className="header-container">
        <Link to={isAuthenticated ? '/dashboard' : '/'} className="header-logo">
          <img src={logo} alt="ZaibHunt Logo" className="header-logo-img" />
          <span className="header-logo-text">ZaibHunt</span>
        </Link>

        <nav className="header-nav">
          {isAuthenticated ? (
            <>
              <Link to="/dashboard" className="header-nav-link">Dashboard</Link>
              <Link to="/resume" className="header-nav-link">Resume</Link>
              <Link to="/jobs" className="header-nav-link">Jobs</Link>
              <Link to="/matches" className="header-nav-link">Matches</Link>
              <div className="header-user-section">
                <span className="header-user-email">{user?.email}</span>
                <button onClick={handleLogout} className="btn btn-secondary btn-sm">
                  Logout
                </button>
              </div>
            </>
          ) : (
            <>
              <Link to="/login" className="header-nav-link">Login</Link>
              <Link to="/signup" className="btn btn-primary btn-sm">Sign Up</Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}

export default Header;