import React, { useState, useRef, useEffect, useCallback } from 'react';
import logger from '../../../utils/logger';
import { Link, useNavigate } from 'react-router-dom';
import { useCart } from '../../../pages/home/CartContext';
import NotificationBell from '../../notifications/NotificationBell/NotificationBell';
import ChangePasswordModal from '../../modals/ChangePasswordModal/ChangePasswordModal';
import { API_ENDPOINTS } from '../../../config/api.config';
import { authFetch } from '../../../utils/authInterceptor';
import '/src/style/main.css';

const Header = ({
  topLinks = [],
  menuLinks = [],
  user,
  onLogout,
}) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isPasswordModalOpen, setIsPasswordModalOpen] = useState(false);
  const [isEmailVerified, setIsEmailVerified] = useState(false);
  const [showSearchDropdown, setShowSearchDropdown] = useState(false);
  const [searchHistory, setSearchHistory] = useState([]);
  const [recentlyViewed, setRecentlyViewed] = useState([]);
  const [loadingSearchData, setLoadingSearchData] = useState(false);
  const userMenuRef = useRef(null);
  const searchRef = useRef(null);
  const { itemCount } = useCart();
  const navigate = useNavigate();

  const toggleMenu = () => setIsMenuOpen((prev) => !prev);
  const closeMenu = useCallback(() => setIsMenuOpen(false), []);

  // Fetch user verification status
  useEffect(() => {
    const fetchUserProfile = async () => {
      const token = localStorage.getItem('authToken');
      if (!token || !user) return;

      try {
        const response = await fetch(API_ENDPOINTS.AUTH.ME, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (response.ok) {
          const data = await response.json();
          setIsEmailVerified(data.is_email_verified || false);
        }
      } catch (error) {
        logger.error('Error fetching user profile:', error);
      }
    };

    fetchUserProfile();
  }, [user]);

  // Fetch search suggestions when dropdown opens
  const fetchSearchSuggestions = async () => {
    setLoadingSearchData(true);
    const token = localStorage.getItem('authToken');

    try {
      // Fetch search history (authenticated users only)
      if (token) {
        const historyRes = await fetch(`${API_ENDPOINTS.ANALYTICS.SEARCH_HISTORY}?limit=5`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (historyRes.ok) {
          const data = await historyRes.json();
          // console.log('Search History Data:', data);
          setSearchHistory(data);
        }

        // Fetch recently viewed products
        const recentRes = await fetch(`${API_ENDPOINTS.ANALYTICS.RECENTLY_VIEWED}?limit=3`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (recentRes.ok) {
          const data = await recentRes.json();
          // console.log('Recently Viewed Data:', data);
          setRecentlyViewed(data);
        }
      }
    } catch (error) {
      logger.error('Error fetching search suggestions:', error);
    }
    setLoadingSearchData(false);
  };

  // Handle search input focus
  const handleSearchFocus = () => {
    setShowSearchDropdown(true);
    fetchSearchSuggestions();
  };

  // Track search query
  const trackSearch = async (query) => {
    try {
      const token = localStorage.getItem('authToken');
      await fetch(API_ENDPOINTS.ANALYTICS.TRACK_SEARCH, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          query: query,
          results_count: 0
        })
      });
    } catch (error) {
      logger.error('Error tracking search:', error);
    }
  };

  // Search handlers
  const handleSearchKeyDown = (e) => {
    if (e.key === 'Enter' && searchQuery.trim()) {
      const query = searchQuery.trim();
      trackSearch(query);
      navigate(`/product?search=${encodeURIComponent(query)}`);
      setSearchQuery('');
      setShowSearchDropdown(false);
    }
  };

  const handleSearchClick = () => {
    if (searchQuery.trim()) {
      const query = searchQuery.trim();
      trackSearch(query);
      navigate(`/product?search=${encodeURIComponent(query)}`);
      setSearchQuery('');
      setShowSearchDropdown(false);
    }
  };

  // Handle suggestion click
  const handleSuggestionClick = (query) => {
    trackSearch(query);
    navigate(`/product?search=${encodeURIComponent(query)}`);
    setSearchQuery('');
    setShowSearchDropdown(false);
  };

  // Get dynamic label for loyalty link
  const getLoyaltyLabel = (originalLabel, to) => {
    if (to === '/loyalty') {
      return isEmailVerified ? 'HỘI VIÊN' : 'ĐĂNG KÝ HỘI VIÊN';
    }
    return originalLabel;
  };

  // Close search dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        closeMenu();
      }
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setShowSearchDropdown(false);
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
              {getLoyaltyLabel(label, to)}
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
          {menuLinks.map(({ to, label, className = '' }) => (
            <Link key={to} to={to} className={className}>
              {label}
            </Link>
          ))}
        </div>

        <div className="icons">
          <div className="search" ref={searchRef}>
            <input
              type="text"
              placeholder="Tìm kiếm"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={handleSearchKeyDown}
              onFocus={handleSearchFocus}
            />
            <svg
              className="search-icon"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              onClick={handleSearchClick}
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>

            {/* Search Dropdown */}
            {showSearchDropdown && (
              <div className="search-dropdown">
                {loadingSearchData ? (
                  <div className="search-loading">Đang tải...</div>
                ) : (
                  <>
                    {/* Search History */}
                    {searchHistory.length > 0 && (
                      <div className="search-section">
                        <div className="search-section-title">
                          <span>Tìm kiếm gần đây</span>
                        </div>
                        {searchHistory.map((item, index) => {
                          const displayText = typeof item === 'string' ? item : (item.search_query || item.query || item.search_term || item.keyword || item.text || '');
                          if (!displayText) return null;
                          return (
                            <div
                              key={index}
                              className="search-suggestion-item history-item"
                              onClick={() => handleSuggestionClick(displayText)}
                            >
                              <span className="suggestion-text">{displayText}</span>
                            </div>
                          );
                        })}
                      </div>
                    )}

                    {/* Recently Viewed Products */}
                    {recentlyViewed.length > 0 && (
                      <div className="search-section">
                        <div className="search-section-title">
                          <span>Sản phẩm đã xem</span>
                        </div>
                        {recentlyViewed.map((item, index) => {
                          // Handle both flat product object and nested { product: ... } structure
                          const product = item.product || item;
                          const productName = product.name || product.product_name || '';
                          const productSlug = product.slug || product.product_id || product.id;

                          if (!productName) return null;

                          return (
                            <div
                              key={product.id || index}
                              className="search-suggestion-item recent-item"
                              onClick={() => {
                                navigate(`/products/${productSlug}`);
                                setShowSearchDropdown(false);
                              }}
                            >
                              <span className="suggestion-text">{productName}</span>
                            </div>
                          );
                        })}
                      </div>
                    )}

                    {/* No suggestions */}
                    {searchHistory.length === 0 && recentlyViewed.length === 0 && (
                      <div className="no-suggestions">Nhập từ khóa để tìm kiếm</div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>

          {user ? (
            <div className="user-menu" ref={userMenuRef}>
              <button className="icon user-icon" onClick={toggleMenu}>
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                {itemCount > 0 && <span className="user-icon-badge">{itemCount}</span>}
              </button>
              {isMenuOpen && (
                <div className="user-dropdown">
                  <div className="user-info">
                    <span className="user-name">Hi, {user.first_name && user.last_name ? `${user.first_name} ${user.last_name}` : user.username}</span>
                  </div>
                  <div className="dropdown-divider"></div>
                  <Link to="/profile" className="dropdown-item" onClick={closeMenu}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                      <circle cx="12" cy="7" r="4" />
                    </svg>
                    Tài khoản của tôi
                  </Link>
                  <Link to="/orders" className="dropdown-item" onClick={closeMenu}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
                      <rect x="8" y="2" width="8" height="4" rx="1" ry="1" />
                    </svg>
                    Đơn hàng
                  </Link>
                  <Link to="/returns" className="dropdown-item" onClick={closeMenu}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                      <polyline points="9 22 9 12 15 12 15 22" />
                    </svg>
                    Đơn trả hàng
                  </Link>
                  <Link to="/wishlist" className="dropdown-item" onClick={closeMenu}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
                    </svg>
                    Yêu thích
                  </Link>
                  {isEmailVerified && (
                    <>
                      <Link to="/loyalty" className="dropdown-item" onClick={closeMenu}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                        </svg>
                        Hội viên
                      </Link>
                      <Link to="/vouchers" className="dropdown-item" onClick={closeMenu}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <rect x="3" y="4" width="18" height="16" rx="2" />
                          <path d="M7 10h10M7 14h10" />
                        </svg>
                        Voucher của tôi
                      </Link>
                    </>
                  )}
                  <Link to="/cart" className="dropdown-item" onClick={closeMenu}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="9" cy="21" r="1" />
                      <circle cx="20" cy="21" r="1" />
                      <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6" />
                    </svg>
                    Giỏ hàng
                    {itemCount > 0 && <span className="dropdown-badge">{itemCount}</span>}
                  </Link>
                  <button
                    className="dropdown-item"
                    onClick={() => {
                      setIsPasswordModalOpen(true);
                      closeMenu();
                    }}
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4" />
                    </svg>
                    Đổi mật khẩu
                  </button>
                  <div className="dropdown-divider"></div>
                  <button onClick={() => { onLogout(); navigate('/'); }} className="dropdown-item logout-btn">
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

          {user && <NotificationBell />}
        </div>
      </nav>

      <div className="mobile-menu">
        {menuLinks.map(({ to, label, className = '' }) => (
          <Link key={to} to={to} className={className}>
            {label}
          </Link>
        ))}
      </div>

      <ChangePasswordModal
        isOpen={isPasswordModalOpen}
        onClose={() => setIsPasswordModalOpen(false)}
      />
    </header>
  );
};

export default Header;