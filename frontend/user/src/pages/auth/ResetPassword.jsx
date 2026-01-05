import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { API_ENDPOINTS } from '../../config/api.config';
import useMutation from '../../hooks/useMutation';
import '/src/style/style.css';

const ResetPassword = () => {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const token = searchParams.get('token');

    const [formData, setFormData] = useState({
        newPassword: '',
        confirmPassword: ''
    });
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);

    const { mutate, loading } = useMutation();

    useEffect(() => {
        if (!token) {
            setError('Link đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.');
        }
    }, [token]);

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

        if (!token) {
            setError('Link đặt lại mật khẩu không hợp lệ!');
            return;
        }

        if (!formData.newPassword || !formData.confirmPassword) {
            setError('Vui lòng nhập đầy đủ thông tin!');
            return;
        }

        if (formData.newPassword.length < 8) {
            setError('Mật khẩu phải có ít nhất 8 ký tự!');
            return;
        }

        if (formData.newPassword !== formData.confirmPassword) {
            setError('Mật khẩu xác nhận không khớp!');
            return;
        }

        setError('');

        const result = await mutate(API_ENDPOINTS.AUTH.PASSWORD_RESET_CONFIRM, {
            method: 'POST',
            body: {
                token: token,
                new_password: formData.newPassword
            },
            auth: false
        });

        if (result.success) {
            setSuccess(true);
            setTimeout(() => {
                navigate('/login');
            }, 3000);
        } else {
            setError(result.error || 'Không thể đặt lại mật khẩu. Vui lòng thử lại!');
        }
    };

    return (
        <div className="login-page">
            <h1 className="login-brand-title">STYLEX</h1>

            <div className="login-glass-container">

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
                            Mật khẩu đã được đặt lại thành công!
                            <br />
                            Đang chuyển hướng đến trang đăng nhập...
                        </div>
                    </div>
                ) : !token ? (
                    <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '60px', marginBottom: '20px' }}>
                            ⚠️
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
                            {error}
                        </div>
                        <Link to="/forgot-password" className="login-btn" style={{
                            display: 'inline-block',
                            textDecoration: 'none',
                            textAlign: 'center'
                        }}>
                            Yêu cầu link mới
                        </Link>
                    </div>
                ) : (
                    <>

                        <form onSubmit={handleSubmit}>
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
                                <label>Xác nhận mật khẩu</label>
                            </div>

                            <p style={{
                                color: '#888',
                                fontSize: '12px',
                                marginBottom: '15px',
                                marginTop: '-10px'
                            }}>
                                Mật khẩu phải có ít nhất 8 ký tự
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
                                {loading ? 'Đang xử lý...' : 'Đặt lại mật khẩu'}
                            </button>
                        </form>
                    </>
                )}

                <div className="login-sign-up" style={{ marginTop: '25px' }}>
                    <p>
                        <Link to="/login" style={{ color: '#666' }}>
                            ← Quay lại đăng nhập
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default ResetPassword;
