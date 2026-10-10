// src/components/Header.jsx
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import logo from '../assets/ZaibHunt.png';

function Header() {
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const closeMenu = () => setMenuOpen(false);

  const handleLogout = () => {
    closeMenu();
    logout();
    navigate('/login');
  };

  return (
    <header className="app-header">
      <div className="header-container">
        <Link
          to={isAuthenticated ? '/dashboard' : '/'}
          className="header-logo"
          onClick={closeMenu}
        >
          <img src={logo} alt="ZaibHunt Logo" className="header-logo-img" />
          <span className="header-logo-text">ZaibHunt</span>
        </Link>

        {/* Hamburger — only visible on mobile via CSS */}
        <button
          className="header-hamburger"
          onClick={() => setMenuOpen((open) => !open)}
          aria-label="Toggle navigation menu"
          aria-expanded={menuOpen}
        >
          {menuOpen ? '✕' : '☰'}
        </button>

        <nav className={`header-nav${menuOpen ? ' open' : ''}`}>
          {isAuthenticated ? (
            <>
              <Link to="/dashboard" className="header-nav-link" onClick={closeMenu}>
                Dashboard
              </Link>
              <Link to="/resume" className="header-nav-link" onClick={closeMenu}>
                Resume
              </Link>
              <Link to="/jobs" className="header-nav-link" onClick={closeMenu}>
                Jobs
              </Link>
              <Link to="/matches" className="header-nav-link" onClick={closeMenu}>
                Matches
              </Link>
              <div className="header-user-section">
                <span className="header-user-email">{user?.email}</span>
                <button onClick={handleLogout} className="btn btn-secondary btn-sm">
                  Logout
                </button>
              </div>
            </>
          ) : (
            <>
              <Link to="/login" className="header-nav-link" onClick={closeMenu}>
                Login
              </Link>
              <Link to="/signup" className="btn btn-primary btn-sm" onClick={closeMenu}>
                Sign Up
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}

export default Header;