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
      const response = await fetch('http://localhost:8000/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (response.ok) {
        alert("Đăng ký thành công! Vui lòng kiểm tra email.");
        navigate('/login');
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


          {error && <div style={{ color: 'red', marginBottom: '10px', textAlign: 'center' }}>{error}</div>}

          <button type="submit" className="login-btn" disabled={loading}>
            {loading ? 'Đang xử lý...' : 'Đăng ký'}
          </button>
        </form>

        <div className="login-sign-up">
          <Link to="/login">Bạn đã có tài khoản? Đăng nhập ngay</Link>
        </div>
      </div>
    </div>
  );
};

export default SignUp;