import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useCart } from '../context/useCart';
import '/src/style/main.css';

const Header = ({
  topLinks = [],
  menuLinks = [],
  user,
  onLogout,
}) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const userMenuRef = useRef(null);
  const { itemCount } = useCart();

  const toggleMenu = () => setIsMenuOpen((prev) => !prev);
  const closeMenu = useCallback(() => setIsMenuOpen(false), []);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        closeMenu();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);

    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [closeMenu]);

  return (
    <header className="header">
      {user && (
        <div className="top-links">
          {topLinks.map(({ to, label }) => (
            <Link key={to} to={to}>
              {label}
            </Link>
          ))}
        </div>
      )}

      <nav className="navbar">
        <div className="logo">
          <Link to="/">
            <svg className="logo-icon" viewBox="0 0 24 24" fill="none">
              <path d="M3 3L10 12L3 21" stroke="black" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M8 3L15 12L8 21" stroke="black" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M13 3L20 12L13 21" stroke="black" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span>STYLEX</span>
          </Link>
        </div>

        <div className="menu">
          {menuLinks.map(({ to, label, className }) => (
            <Link key={to} to={to} className={className}>
              {label}
            </Link>
          ))}
        </div>

        <div className="icons">
          <div className="search">
            <input type="text" placeholder="Tìm kiếm" />
            <svg className="search-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>

          {user ? (
            <div className="user-menu" ref={userMenuRef}>
              <button className="icon user-icon" onClick={toggleMenu}>
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </button>
              {isMenuOpen && (
                <div className="user-dropdown">
                  <div className="user-info">
                    <span className="user-name">👋 Hi, {user.username}</span>
                  </div>
                  <div className="dropdown-divider"></div>
                  <Link to="/profile" className="dropdown-item">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                      <circle cx="12" cy="7" r="4" />
                    </svg>
                    Tài khoản của tôi
                  </Link>
                  <Link to="/orders" className="dropdown-item">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
                      <rect x="8" y="2" width="8" height="4" rx="1" ry="1" />
                    </svg>
                    Đơn hàng
                  </Link>
                  <div className="dropdown-divider"></div>
                  <button onClick={onLogout} className="dropdown-item logout-btn">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                      <polyline points="16 17 21 12 16 7" />
                      <line x1="21" y1="12" x2="9" y2="12" />
                    </svg>
                    Đăng xuất
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="auth-buttons">
              <Link to="/login" className="login-link">
                Login
              </Link>
              <span className="auth-divider" aria-hidden="true"></span>
              <Link to="/signup" className="signup-link">
                Sign up
              </Link>
            </div>
          )}

          {user && (
            <>
              <Link to="#" className="icon" title="Yêu thích">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4.318 6.318a4.5 4.5 0 016.364 0L12 7.636l1.318-1.318a4.5 4.5 0 116.364 6.364L12 20.364l-7.682-7.682a4.5 4.5 0 010-6.364z" />
                </svg>
              </Link>

              <Link to="/cart" className="icon cart" title="Giỏ hàng">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
                {itemCount > 0 && <span className="cart-badge">{itemCount}</span>}
              </Link>
            </>
          )}
        </div>
      </nav>

      <div className="mobile-menu">
        {menuLinks.map(({ to, label, className }) => (
          <Link key={to} to={to} className={className}>
            {label}
          </Link>
        ))}
      </div>
    </header>
  );
};

export default Header;