import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { saveAuthTokens, saveUser } from '../../utils/auth.utils';
import { API_ENDPOINTS } from '../../config/api.config';
import logger from '../../utils/logger';
import '/src/style/style.css';

const Login = ({ onLoginSuccess }) => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    if (errorMessage) setErrorMessage('');
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();

    if (!formData.email || !formData.password) {
      setErrorMessage('Vui lòng nhập đầy đủ thông tin!');
      return;
    }

    setLoading(true);
    setErrorMessage('');

    try {
      // Gọi API Login
      logger.log('Logging in to:', API_ENDPOINTS.AUTH.LOGIN);
      const response = await fetch(API_ENDPOINTS.AUTH.LOGIN, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          grant_type: 'password',
          username: formData.email,
          password: formData.password
        })
      });

      const result = await response.json();
      logger.log('Login API response:', result);
      logger.log('access_token:', result.access_token);

      if (response.ok && result.access_token) {
        // 1. Lưu token - ALWAYS save to localStorage first
        logger.log('Saving authToken to localStorage...');
        localStorage.setItem('authToken', result.access_token);
        localStorage.setItem('refreshToken', result.refresh_token || '');
        logger.log('authToken saved:', localStorage.getItem('authToken'));

        // Also call saveAuthTokens if available
        if (typeof saveAuthTokens === 'function') {
          saveAuthTokens(result.access_token, result.refresh_token || '');
        }

        // 2. Lấy thông tin User
        try {
          const userResponse = await fetch(API_ENDPOINTS.USERS.ME, {
            headers: {
              'Authorization': `Bearer ${result.access_token}`
            }
          });

          if (userResponse.ok) {
            const userData = await userResponse.json();
            if (typeof saveUser === 'function') saveUser(userData);
            if (onLoginSuccess) onLoginSuccess(userData);
          } else {
            // Nếu không lấy được info thì dùng tạm email
            const basicUser = { email: formData.email };
            if (typeof saveUser === 'function') saveUser(basicUser);
            if (onLoginSuccess) onLoginSuccess(basicUser);
          }
        } catch (err) {
          logger.warn('Could not fetch user info', err);
        }

        // 3. Chuyển hướng
        navigate('/');
      } else {
        setErrorMessage(result.detail || result.message || 'Email hoặc mật khẩu không đúng!');
      }
    } catch (error) {
      logger.error('Login error:', error);
      setErrorMessage('Không thể kết nối đến server. Vui lòng kiểm tra mạng!');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <h1 className="login-brand-title">STYLEX</h1>

      <div className="login-glass-container">
        <h2>ĐĂNG NHẬP</h2>

        <form onSubmit={handleSubmit}>
          <div className="login-input-group">
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              placeholder=" "
            />
            <label>Email</label>
          </div>

          <div className="login-input-group">
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
            />
            <label>Mật khẩu</label>
          </div>

          <div className="login-remember-forget">
            <label className="login-remember-label">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
              />
              Ghi nhớ đăng nhập
            </label>
            <Link to="/forgot-password">Quên mật khẩu?</Link>
          </div>

          {errorMessage && (
            <div style={{
              color: '#ff4444',
              backgroundColor: '#ffebee',
              padding: '10px',
              borderRadius: '5px',
              marginBottom: '15px',
              fontSize: '14px',
              textAlign: 'center',
              border: '1px solid #ffcdd2'
            }}>
              {errorMessage}
            </div>
          )}

          <button
            type="submit"
            className="login-btn"
            disabled={loading}
            style={{
              opacity: loading ? 0.7 : 1,
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Đang đăng nhập...' : 'Đăng nhập'}
          </button>
        </form>

        <div className="login-sign-up">
          <p>
            Chưa có tài khoản?{' '}
            <Link to="/signup">
              Đăng ký ngay
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;