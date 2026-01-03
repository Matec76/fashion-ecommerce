import React, { useState, useEffect } from 'react';
import logger from '../../utils/logger';
import { useLocation, useNavigate } from 'react-router-dom';
import { QRCodeSVG } from 'qrcode.react';
import { API_ENDPOINTS } from '../../config/api.config';
import '../../style/Payment.css';

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

    // Helper function to cancel order
    const cancelOrder = async () => {
        if (!orderId) {
            logger.warn('No orderId to cancel');
            return false;
        }
        try {
            const token = localStorage.getItem('authToken');
            logger.log('Attempting to cancel order:', orderId);

            const response = await fetch(API_ENDPOINTS.ORDERS.CANCEL_ORDER(orderId), {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ is_user_cancel: true })
            });

            logger.log('Cancel response status:', response.status);

            if (response.ok) {
                logger.log('Order cancelled successfully');
                return true;
            } else {
                const errorData = await response.json().catch(() => ({}));
                logger.error('Cancel failed:', response.status, errorData);
                alert(`Không thể hủy đơn hàng: ${errorData.detail || response.statusText}`);
                return false;
            }
        } catch (error) {
            logger.error('Cancel order error:', error);
            alert('Lỗi khi hủy đơn hàng: ' + error.message);
            return false;
        }
    };

    // Handle user trying to leave the page
    useEffect(() => {
        const handleBeforeUnload = (e) => {
            if (paymentStatus === 'pending') {
                e.preventDefault();
                e.returnValue = 'Bạn có chắc muốn rời trang? Đơn hàng sẽ bị hủy.';
                return e.returnValue;
            }
        };

        window.addEventListener('beforeunload', handleBeforeUnload);
        return () => window.removeEventListener('beforeunload', handleBeforeUnload);
    }, [paymentStatus]);

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

            // Auto-cancel the order when payment expires
            const cancelExpiredOrder = async () => {
                try {
                    const token = localStorage.getItem('authToken');
                    await fetch(API_ENDPOINTS.ORDERS.CANCEL_ORDER(orderId), {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${token}`,
                            'Content-Type': 'application/json'
                        }
                    });
                    logger.log('Order cancelled due to payment timeout');
                } catch (error) {
                    logger.warn('Could not auto-cancel expired order:', error);
                }
            };

            if (orderId) {
                cancelExpiredOrder();
            }
            return;
        }

        const timer = setInterval(() => {
            setCountdown(prev => prev - 1);
        }, 1000);

        return () => clearInterval(timer);
    }, [countdown, orderId]);

    // Check payment status periodically
    useEffect(() => {
        if (!transactionCode) {
            logger.warn('No transaction code available for status checking');
            return;
        }

        logger.log('Starting payment status polling for transaction:', transactionCode);

        const checkStatus = async () => {
            try {
                const token = localStorage.getItem('authToken');
                const url = API_ENDPOINTS.PAYMENT.PAYOS.CHECK_STATUS(transactionCode);

                logger.log('Checking payment status:', url);

                const response = await fetch(url, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                logger.log('Response status:', response.status, response.statusText);

                if (response.ok) {
                    const data = await response.json();
                    logger.log('Payment status response:', data);

                    // Backend returns: local_status, payos_status, paid
                    // Check both local_status and payos_status for compatibility
                    const status = data.local_status || data.payos_status || data.status;
                    const isPaid = data.paid === true || status === 'PAID' || status === 'success' || status === 'COMPLETED';
                    const isFailed = status === 'CANCELLED' || status === 'failed' || status === 'FAILED';

                    logger.log('Parsed status:', { status, isPaid, isFailed });

                    if (isPaid) {
                        logger.log('Payment successful!');
                        setPaymentStatus('success');
                        setTimeout(() => {
                            navigate('/payment/success', { state: { orderId, orderNumber } });
                        }, 2000);
                    } else if (isFailed) {
                        logger.log('Payment failed');
                        setPaymentStatus('failed');

                        // Auto-cancel the order when payment fails
                        try {
                            await fetch(API_ENDPOINTS.ORDERS.CANCEL_ORDER(orderId), {
                                method: 'POST',
                                headers: {
                                    'Authorization': `Bearer ${token}`,
                                    'Content-Type': 'application/json'
                                }
                            });
                            logger.log('Order cancelled due to payment failure');
                        } catch (cancelError) {
                            logger.warn('Could not auto-cancel order:', cancelError);
                        }

                        setTimeout(() => {
                            navigate('/payment/failure', {
                                state: { orderId, orderNumber, transactionCode }
                            });
                        }, 2000);
                    } else {
                        logger.log('Payment still pending, status:', status);
                    }
                } else {
                    // Don't spam console on errors, just log once
                    if (response.status !== 500) {
                        logger.warn('Check status returned:', response.status);
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
            logger.log('Stopping payment status polling');
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

    const handleCancel = async () => {
        if (window.confirm('Bạn có chắc muốn hủy thanh toán? Đơn hàng sẽ bị hủy.')) {
            await cancelOrder();
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
                            <>
                                <div className="qr-code" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '0' }}>
                                    {/* Render QR code from backend data */}
                                    <QRCodeSVG
                                        value={qrCode}
                                        size={280}
                                        level="H"
                                        includeMargin={false}
                                        style={{
                                            width: '100%',
                                            height: '100%',
                                            maxWidth: '280px',
                                            maxHeight: '280px'
                                        }}
                                    />
                                </div>
                                <p style={{ marginTop: '16px', fontSize: '14px', color: '#666', textAlign: 'center' }}>
                                    {paymentInstructions || 'Quét mã QR bằng app ngân hàng để thanh toán'}
                                </p>
                            </>
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
                                {formatTime(countdown)}
                            </div>
                            <p className="timer-label">Thời gian còn lại</p>
                        </div>
                    </div>

                    <div className="payment-instructions">
                        <h3>Hướng dẫn thanh toán</h3>
                        <ol>
                            <li>Nhấn vào nút "Thanh toán ngay" bên trên</li>
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
                                <span> Phiên thanh toán đã hết hạn</span>
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
