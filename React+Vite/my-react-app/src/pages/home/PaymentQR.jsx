import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { QRCodeSVG } from 'qrcode.react';
import '../../style/Payment.css';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const PaymentQR = () => {
    const location = useLocation();
    const navigate = useNavigate();

    const {
        orderId,
        orderNumber,
        transactionCode,
        paymentUrl,
        qrCode,
        totalAmount,
        paymentInstructions
    } = location.state || {};

    const [paymentStatus, setPaymentStatus] = useState('pending');
    const [countdown, setCountdown] = useState(900); // 15 minutes

    // Redirect if no payment data
    useEffect(() => {
        if (!orderId || !transactionCode) {
            alert('Không tìm thấy thông tin thanh toán!');
            navigate('/cart');
        }
    }, [orderId, transactionCode, navigate]);

    // Countdown timer
    useEffect(() => {
        if (countdown <= 0) {
            setPaymentStatus('expired');
            return;
        }

        const timer = setInterval(() => {
            setCountdown(prev => prev - 1);
        }, 1000);

        return () => clearInterval(timer);
    }, [countdown]);

    // Check payment status periodically
    useEffect(() => {
        if (!transactionCode) {
            console.warn('⚠️ No transaction code available for status checking');
            return;
        }

        console.log('🔄 Starting payment status polling for transaction:', transactionCode);

        const checkStatus = async () => {
            try {
                const token = localStorage.getItem('authToken');
                const url = `${API_BASE_URL}/payment/payos/check-status/${transactionCode}`;

                console.log('📡 Checking payment status:', url);

                const response = await fetch(url, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                console.log('📥 Response status:', response.status, response.statusText);

                if (response.ok) {
                    const data = await response.json();
                    console.log('✅ Payment status response:', data);

                    // Based on PayOS status
                    if (data.status === 'PAID' || data.status === 'success' || data.status === 'COMPLETED') {
                        console.log('🎉 Payment successful!');
                        setPaymentStatus('success');
                        setTimeout(() => {
                            navigate('/payment/success', { state: { orderId, orderNumber } });
                        }, 2000);
                    } else if (data.status === 'CANCELLED' || data.status === 'failed' || data.status === 'FAILED') {
                        console.log('❌ Payment failed');
                        setPaymentStatus('failed');
                        setTimeout(() => {
                            navigate('/payment/failure', {
                                state: { orderId, orderNumber, transactionCode }
                            });
                        }, 2000);
                    } else {
                        console.log('⏳ Payment still pending, status:', data.status);
                    }
                } else {
                    // Don't spam console on errors, just log once
                    if (response.status !== 500) {
                        console.warn('⚠️ Check status returned:', response.status);
                    }
                }
            } catch (error) {
                // Silently handle network errors (CORS, etc.)
                // Payment can still work via redirect
            }
        };

        // Check immediately once
        checkStatus();

        // Then check every 5 seconds (reduced from 3 to avoid spam)
        const interval = setInterval(checkStatus, 5000);
        return () => {
            console.log('🛑 Stopping payment status polling');
            clearInterval(interval);
        };
    }, [transactionCode, orderId, orderNumber, navigate]);

    const formatPrice = (price) => {
        return new Intl.NumberFormat('vi-VN', {
            style: 'currency',
            currency: 'VND'
        }).format(price);
    };

    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    const handleCancel = () => {
        if (window.confirm('Bạn có chắc muốn hủy thanh toán?')) {
            navigate('/cart');
        }
    };

    return (
        <div className="payment-qr-page">
            <div className="payment-qr-container">
                <div className="payment-qr-card">
                    <div className="payment-header">
                        <h1>Quét mã QR để thanh toán</h1>
                        <p className="order-id">Mã đơn hàng: {orderNumber || `#${orderId}`}</p>
                    </div>

                    <div className="qr-section">
                        {qrCode ? (
                            <div className="qr-code" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                                {/* Render QR code from backend data */}
                                <QRCodeSVG
                                    value={qrCode}
                                    size={320}
                                    level="H"
                                    includeMargin={false}
                                    style={{
                                        background: 'white',
                                        padding: '20px',
                                        borderRadius: '16px',
                                        boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
                                        width: '100%',
                                        maxWidth: '320px',
                                        height: 'auto'
                                    }}
                                />
                                <p style={{ marginTop: '16px', fontSize: '14px', color: '#666' }}>
                                    {paymentInstructions || 'Quét mã QR bằng app ngân hàng để thanh toán'}
                                </p>
                            </div>
                        ) : paymentUrl ? (
                            <div className="qr-code">
                                <div className="qr-placeholder">
                                    <p style={{ marginBottom: '20px', fontSize: '16px', fontWeight: 600 }}>
                                        {paymentInstructions || 'Vui lòng nhấn vào nút bên dưới để thanh toán'}
                                    </p>
                                    <a
                                        href={paymentUrl}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="payment-link-btn"
                                    >
                                        Thanh toán ngay
                                    </a>
                                </div>
                            </div>
                        ) : (
                            <div className="qr-loading">
                                <div className="spinner"></div>
                                <p>Đang tạo liên kết thanh toán...</p>
                            </div>
                        )}

                        <div className="payment-amount">
                            <span>Số tiền thanh toán</span>
                            <span className="amount">{formatPrice(totalAmount)}</span>
                        </div>

                        <div className="timer-section">
                            <div className={`timer ${countdown < 60 ? 'warning' : ''}`}>
                                ⏱️ {formatTime(countdown)}
                            </div>
                            <p className="timer-label">Thời gian còn lại</p>
                        </div>
                    </div>

                    <div className="payment-instructions">
                        <h3>Hướng dẫn thanh toán</h3>
                        <ol>
                            <li>Nhấn vào nút "Thanh toán ngay" bên trên</li>
                            <li>Chọn ngân hàng MBBank</li>
                            <li>Đăng nhập vào tài khoản ngân hàng</li>
                            <li>Xác nhận thông tin thanh toán</li>
                            <li>Chờ hệ thống xác nhận (tự động)</li>
                        </ol>
                    </div>

                    {paymentStatus === 'pending' && (
                        <div className="payment-status">
                            <div className="status-indicator pending">
                                <div className="pulse"></div>
                                <span>Đang chờ thanh toán...</span>
                            </div>
                            <button
                                onClick={async () => {
                                    const token = localStorage.getItem('authToken');
                                    try {
                                        const response = await fetch(
                                            `${API_BASE_URL}/payment/payos/check-status/${transactionCode}`,
                                            { headers: { 'Authorization': `Bearer ${token}` } }
                                        );
                                        if (response.ok) {
                                            const data = await response.json();
                                            console.log('Manual check result:', data);
                                            if (data.status === 'PAID' || data.status === 'success' || data.status === 'COMPLETED') {
                                                setPaymentStatus('success');
                                                setTimeout(() => {
                                                    navigate('/payment/success', { state: { orderId, orderNumber } });
                                                }, 1500);
                                            } else {
                                                alert(`Trạng thái: ${data.status || 'Chưa thanh toán'}`);
                                            }
                                        } else {
                                            alert('Không thể kiểm tra. Vui lòng đợi hoặc liên hệ hỗ trợ.');
                                        }
                                    } catch (error) {
                                        console.error('Check error:', error);
                                        alert('Lỗi kết nối. Vui lòng thử lại.');
                                    }
                                }}
                                style={{
                                    marginTop: '16px',
                                    padding: '12px 24px',
                                    background: '#4CAF50',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '8px',
                                    cursor: 'pointer',
                                    fontWeight: 600,
                                    fontSize: '14px'
                                }}
                            >
                                ✓ Tôi đã thanh toán
                            </button>
                        </div>
                    )}

                    {paymentStatus === 'success' && (
                        <div className="payment-status">
                            <div className="status-indicator success">
                                <span>✓ Thanh toán thành công!</span>
                            </div>
                        </div>
                    )}

                    {paymentStatus === 'expired' && (
                        <div className="payment-status">
                            <div className="status-indicator error">
                                <span>⚠️ Phiên thanh toán đã hết hạn</span>
                            </div>
                        </div>
                    )}

                    <button className="cancel-payment-btn" onClick={handleCancel}>
                        Hủy thanh toán
                    </button>
                </div>
            </div>
        </div>
    );
};

export default PaymentQR;
