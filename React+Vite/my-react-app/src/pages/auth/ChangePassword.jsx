import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { API_ENDPOINTS } from '../../config/api.config';
import useMutation from '../../components/useMutation';
import '/src/style/style.css';

const ChangePassword = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
    });
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);

    const { mutate, loading } = useMutation();

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
        if (error) setError('');
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        const token = localStorage.getItem('authToken');
        if (!token) {
            setError('Vui lòng đăng nhập để đổi mật khẩu!');
            return;
        }

        if (!formData.currentPassword || !formData.newPassword || !formData.confirmPassword) {
            setError('Vui lòng nhập đầy đủ thông tin!');
            return;
        }

        if (formData.newPassword.length < 8) {
            setError('Mật khẩu mới phải có ít nhất 8 ký tự!');
            return;
        }

        if (formData.newPassword !== formData.confirmPassword) {
            setError('Mật khẩu xác nhận không khớp!');
            return;
        }

        if (formData.currentPassword === formData.newPassword) {
            setError('Mật khẩu mới phải khác mật khẩu hiện tại!');
            return;
        }

        setError('');

        const result = await mutate(API_ENDPOINTS.AUTH.PASSWORD_CHANGE, {
            method: 'POST',
            body: {
                current_password: formData.currentPassword,
                new_password: formData.newPassword
            }
        });

        if (result.success) {
            setSuccess(true);
            setFormData({
                currentPassword: '',
                newPassword: '',
                confirmPassword: ''
            });
            setTimeout(() => {
                navigate('/profile');
            }, 3000);
        } else {
            setError(result.error || 'Không thể đổi mật khẩu. Vui lòng thử lại!');
        }
    };

    if (!token) {
        return (
            <div className="login-page">
                <h1 className="login-brand-title">STYLEX</h1>
                <div className="login-glass-container">
                    <h2>ĐỔI MẬT KHẨU</h2>
                    <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '60px', marginBottom: '20px' }}>
                            🔒
                        </div>
                        <div style={{
                            color: '#f44336',
                            backgroundColor: '#ffebee',
                            padding: '15px',
                            borderRadius: '8px',
                            marginBottom: '20px',
                            fontSize: '14px',
                            border: '1px solid #ffcdd2'
                        }}>
                            Bạn cần đăng nhập để đổi mật khẩu!
                        </div>
                        <Link to="/login" className="login-btn" style={{
                            display: 'inline-block',
                            textDecoration: 'none',
                            textAlign: 'center'
                        }}>
                            Đăng nhập
                        </Link>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="login-page">
            <h1 className="login-brand-title">STYLEX</h1>

            <div className="login-glass-container">
                <h2>ĐỔI MẬT KHẨU</h2>

                {success ? (
                    <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '60px', marginBottom: '20px' }}>
                            ✅
                        </div>
                        <div style={{
                            color: '#4caf50',
                            backgroundColor: '#e8f5e9',
                            padding: '15px',
                            borderRadius: '8px',
                            marginBottom: '20px',
                            fontSize: '14px',
                            border: '1px solid #c8e6c9'
                        }}>
                            Mật khẩu đã được thay đổi thành công!
                            <br />
                            Đang chuyển hướng...
                        </div>
                    </div>
                ) : (
                    <form onSubmit={handleSubmit}>
                        <div className="login-input-group">
                            <input
                                type="password"
                                name="currentPassword"
                                value={formData.currentPassword}
                                onChange={handleChange}
                                required
                                placeholder=" "
                            />
                            <label>Mật khẩu hiện tại</label>
                        </div>

                        <div className="login-input-group">
                            <input
                                type="password"
                                name="newPassword"
                                value={formData.newPassword}
                                onChange={handleChange}
                                required
                                placeholder=" "
                            />
                            <label>Mật khẩu mới</label>
                        </div>

                        <div className="login-input-group">
                            <input
                                type="password"
                                name="confirmPassword"
                                value={formData.confirmPassword}
                                onChange={handleChange}
                                required
                                placeholder=" "
                            />
                            <label>Xác nhận mật khẩu mới</label>
                        </div>

                        <p style={{
                            color: '#888',
                            fontSize: '12px',
                            marginBottom: '15px',
                            marginTop: '-10px'
                        }}>
                            Mật khẩu mới phải có ít nhất 8 ký tự
                        </p>

                        {error && (
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
                                {error}
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
                            {loading ? 'Đang xử lý...' : 'Đổi mật khẩu'}
                        </button>
                    </form>
                )}

                <div className="login-sign-up" style={{ marginTop: '25px' }}>
                    <p>
                        <Link to="/profile" style={{ color: '#666' }}>
                            ← Quay lại hồ sơ
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default ChangePassword;
