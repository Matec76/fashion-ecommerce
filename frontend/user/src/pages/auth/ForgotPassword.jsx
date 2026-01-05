import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { API_ENDPOINTS } from '../../config/api.config';
import useMutation from '../../hooks/useMutation';
import '/src/style/style.css';

const ForgotPassword = () => {
    const [email, setEmail] = useState('');
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [submitted, setSubmitted] = useState(false);

    const { mutate, loading } = useMutation();

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!email) {
            setError('Vui lòng nhập email của bạn!');
            return;
        }

        setError('');
        setMessage('');

        const result = await mutate(API_ENDPOINTS.AUTH.PASSWORD_RESET_REQUEST, {
            method: 'POST',
            body: { email },
            auth: false // Không cần auth token cho forgot password
        });

        if (result.success) {
            setSubmitted(true);
            setMessage('Email đặt lại mật khẩu đã được gửi! Vui lòng kiểm tra hộp thư của bạn.');
        } else {
            setError(result.error || 'Không thể gửi email. Vui lòng thử lại!');
        }
    };

    return (
        <div className="login-page">
            <h1 className="login-brand-title">STYLEX</h1>

            <div className="login-glass-container">
                <h2>QUÊN MẬT KHẨU</h2>

                {!submitted ? (
                    <>
                        <p style={{
                            color: '#666',
                            fontSize: '14px',
                            textAlign: 'center',
                            marginBottom: '25px'
                        }}>
                            Nhập email đăng ký của bạn. Chúng tôi sẽ gửi link đặt lại mật khẩu.
                        </p>

                        <form onSubmit={handleSubmit}>
                            <div className="login-input-group">
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => {
                                        setEmail(e.target.value);
                                        if (error) setError('');
                                    }}
                                    required
                                    placeholder=" "
                                />
                                <label>Email</label>
                            </div>

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
                                {loading ? 'Đang gửi...' : 'Gửi email đặt lại'}
                            </button>
                        </form>
                    </>
                ) : (
                    <div style={{ textAlign: 'center' }}>
                        <div style={{
                            fontSize: '60px',
                            marginBottom: '20px'
                        }}>
                            ✉️
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
                            {message}
                        </div>
                        <p style={{ color: '#666', fontSize: '13px' }}>
                            Không nhận được email?{' '}
                            <button
                                onClick={() => {
                                    setSubmitted(false);
                                    setMessage('');
                                }}
                                style={{
                                    background: 'none',
                                    border: 'none',
                                    color: '#2196f3',
                                    cursor: 'pointer',
                                    textDecoration: 'underline',
                                    fontSize: '13px'
                                }}
                            >
                                Gửi lại
                            </button>
                        </p>
                    </div>
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

export default ForgotPassword;
