import React, { useEffect, useState } from 'react';
import logger from '../../utils/logger';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { API_ENDPOINTS } from '../../config/api.config';
import '/src/style/style.css';

const VerifyEmail = () => {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const [verificationStatus, setVerificationStatus] = useState('loading'); // loading, success, error
    const [message, setMessage] = useState('');

    useEffect(() => {
        const token = searchParams.get('token');

        if (!token) {
            setVerificationStatus('error');
            setMessage('Token xác thực không hợp lệ. Vui lòng kiểm tra lại email của bạn.');
            return;
        }

        // Gửi token lên backend để xác thực
        const verifyEmailToken = async () => {
            try {
                const response = await fetch(API_ENDPOINTS.AUTH.VERIFY_EMAIL, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ token: token })
                });

                if (response.ok) {
                    const data = await response.json();
                    setVerificationStatus('success');
                    setMessage(data.message || 'Email đã được xác thực thành công! Bạn có thể đăng nhập ngay bây giờ.');

                    // Redirect to login after 3 seconds
                    setTimeout(() => {
                        navigate('/login');
                    }, 3000);
                } else {
                    const error = await response.json();
                    setVerificationStatus('error');

                    // Handle validation error (422) or other errors
                    let errorMessage = 'Token không hợp lệ hoặc đã hết hạn. Vui lòng yêu cầu gửi lại email xác thực.';

                    if (error.detail) {
                        // Handle validation error format
                        if (Array.isArray(error.detail)) {
                            errorMessage = error.detail.map(err => err.msg).join(', ');
                        } else if (typeof error.detail === 'string') {
                            errorMessage = error.detail;
                        }
                    } else if (error.message) {
                        errorMessage = error.message;
                    }

                    setMessage(errorMessage);
                }
            } catch (error) {
                logger.error('Error verifying email:', error);
                setVerificationStatus('error');
                setMessage('Có lỗi xảy ra khi xác thực email. Vui lòng thử lại sau.');
            }
        };

        verifyEmailToken();
    }, [searchParams, navigate]);

    return (
        <div className="login-page">
            <h1 className="login-brand-title">STYLEX</h1>
            <div className="login-glass-container">
                <div className="verify-email-content">
                    {verificationStatus === 'loading' && (
                        <div className="loading-state">
                            <div className="spinner"></div>
                            <h2>Đang xác thực email...</h2>
                            <p>Vui lòng chờ trong giây lát.</p>
                        </div>
                    )}

                    {verificationStatus === 'success' && (
                        <div className="success-state">
                            <div className="success-icon">✓</div>
                            <h2>Xác thực thành công!</h2>
                            <p>{message}</p>
                            <p className="redirect-notice">Đang chuyển hướng đến trang đăng nhập...</p>
                        </div>
                    )}

                    {verificationStatus === 'error' && (
                        <div className="error-state">
                            <div className="error-icon">✗</div>
                            <h2>Xác thực thất bại</h2>
                            <p>{message}</p>
                            <div className="action-buttons">
                                <button
                                    className="primary-btn"
                                    onClick={() => navigate('/login')}
                                >
                                    Đăng nhập
                                </button>
                                <button
                                    className="secondary-btn"
                                    onClick={() => navigate('/profile')}
                                >
                                    Gửi lại email xác thực
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default VerifyEmail;
