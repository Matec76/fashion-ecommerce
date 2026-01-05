import React from 'react';
import logger from '../../utils/logger';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { API_ENDPOINTS } from '../../config/api.config';
import '../../style/Payment.css';

const PaymentFailure = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { orderId, transactionId, errorMessage } = location.state || {};

    const handleRetry = async () => {
        if (!transactionId) {
            navigate('/cart');
            return;
        }

        try {
            const token = localStorage.getItem('authToken');
            const response = await fetch(
                API_ENDPOINTS.PAYMENT.TRANSACTIONS.RETRY(transactionId),
                {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` }
                }
            );

            if (response.ok) {
                const data = await response.json();
                navigate('/payment-qr', {
                    state: {
                        orderId,
                        paymentData: data,
                        totalAmount: data.amount
                    }
                });
            } else {
                alert('Không thể thử lại thanh toán. Vui lòng liên hệ hỗ trợ.');
            }
        } catch (error) {
            logger.error('Error retrying payment:', error);
            alert('Đã có lỗi xảy ra. Vui lòng thử lại sau.');
        }
    };

    return (
        <div className="payment-result-page">
            <div className="payment-result-container">
                <div className="payment-result-card failure">
                    <div className="result-icon error-icon">
                        <svg viewBox="0 0 24 24" fill="none">
                            <path d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                    </div>

                    <h1>Thanh toán thất bại</h1>
                    <p>Rất tiếc, giao dịch của bạn không thành công.</p>

                    {orderId && (
                        <div className="order-info">
                            <span className="label">Mã đơn hàng:</span>
                            <span className="value">#{orderId}</span>
                        </div>
                    )}

                    {errorMessage && (
                        <div className="error-message">
                            <strong>Lý do:</strong> {errorMessage}
                        </div>
                    )}

                    <div className="result-message">
                        <p>Đơn hàng của bạn vẫn được lưu và đang chờ thanh toán.</p>
                        <p>Bạn có thể thử lại thanh toán hoặc chọn phương thức khác.</p>
                    </div>

                    <div className="result-actions">
                        {transactionId && (
                            <button className="primary-btn" onClick={handleRetry}>
                                Thử lại thanh toán
                            </button>
                        )}
                        <Link to="/cart" className="secondary-btn">
                            Quay lại giỏ hàng
                        </Link>
                        <Link to="/contact" className="text-link">
                            Liên hệ hỗ trợ
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PaymentFailure;
