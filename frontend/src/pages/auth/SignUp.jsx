import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { API_ENDPOINTS } from '../../config/api.config';
import ScrollDatePicker from '../../components/forms/ScrollDatePicker/ScrollDatePicker';
import logger from '../../utils/logger';
import '/src/style/style.css';
import '/src/style/Loyalty.css';

const SignUp = () => {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    day: '',
    month: '',
    year: '',
    email: '',
    password: ''
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Data ngày tháng năm
  const days = Array.from({ length: 31 }, (_, i) => i + 1);
  const months = [
    'Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6',
    'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12'
  ];
  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: currentYear - 1940 }, (_, i) => currentYear - i);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    // Payload gửi lên server
    const payload = {
      email: formData.email,
      password: formData.password,
      first_name: formData.firstName,
      last_name: formData.lastName,
    };

    // Thêm date_of_birth nếu đã nhập đầy đủ
    if (formData.day && formData.month && formData.year) {
      const dateOfBirth = `${formData.year}-${String(formData.month).padStart(2, '0')}-${String(formData.day).padStart(2, '0')}`;
      payload.date_of_birth = dateOfBirth;
    }

    try {
      logger.log('Registering with:', API_ENDPOINTS.AUTH.REGISTER);
      const response = await fetch(API_ENDPOINTS.AUTH.REGISTER, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess("Đăng ký thành công! Vui lòng kiểm tra email.");
        setTimeout(() => {
          navigate('/login');
        }, 2000);
      } else {
        setError(data.detail || 'Đăng ký thất bại.');
      }
    } catch (err) {
      logger.error(err);
      setError('Lỗi kết nối server.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <h1 className="login-brand-title">STYLEX</h1>
      <div className="login-glass-container" style={{ maxWidth: '500px' }}>
        <h2>ĐĂNG KÝ</h2>
        <form onSubmit={handleSubmit}>

          <div style={{ display: 'flex', gap: '10px' }}>
            <div className="input__group">
              <input type="text" name="firstName" value={formData.firstName} onChange={handleChange} required />
              <label>Họ</label>
            </div>
            <div className="input__group">
              <input type="text" name="lastName" value={formData.lastName} onChange={handleChange} required />
              <label>Tên</label>
            </div>
          </div>

          <div className="signup-container">
            <label style={{ display: 'block', marginBottom: '10px', color: 'black', fontSize: '14px' }}>
              Ngày sinh
            </label>
            <ScrollDatePicker
              day={formData.day}
              month={formData.month}
              year={formData.year}
              onDayChange={(value) => setFormData(prev => ({ ...prev, day: value }))}
              onMonthChange={(value) => setFormData(prev => ({ ...prev, month: value }))}
              onYearChange={(value) => setFormData(prev => ({ ...prev, year: value }))}
            />
          </div>

          <div className="input__group">
            <input type="email" name="email" value={formData.email} onChange={handleChange} required />
            <label>Email</label>
          </div>

          <div className="input__group">
            <input type="password" name="password" value={formData.password} onChange={handleChange} required />
            <label>Mật khẩu</label>
          </div>


          {error && <div style={{ color: 'red', marginTop: '20px', marginBottom: '20px', padding: '12px', textAlign: 'center', fontSize: '16px', backgroundColor: 'rgba(255, 0, 0, 0.1)', borderRadius: '8px', fontWeight: '500' }}>{error}</div>}

          <button type="submit" className="login-btn" disabled={loading}>
            {loading ? 'Đang xử lý...' : 'Đăng ký'}
          </button>
        </form>

        <div className="login-sign-up" style={{ fontSize: '16px' }}>
          <Link to="/login">Bạn đã có tài khoản? Đăng nhập ngay</Link>
        </div>
      </div>

      {/* Success Modal */}
      {success && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '30px',
            borderRadius: '12px',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.2)',
            minWidth: '400px',
            textAlign: 'center'
          }}>
            <h3 style={{ margin: '0 0 20px 0', fontSize: '20px', fontWeight: '600', color: '#000' }}>Thông báo</h3>
            <p style={{ margin: '0 0 20px 0', fontSize: '16px', color: '#333' }}>{success}</p>
            <button
              onClick={() => navigate('/login')}
              style={{
                padding: '12px 30px',
                backgroundColor: '#000',
                color: 'white',
                border: 'none',
                borderRadius: '25px',
                fontSize: '16px',
                fontWeight: '600',
                cursor: 'pointer'
              }}
            >
              OK
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default SignUp;