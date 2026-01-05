import React, { useEffect } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { useCart } from './CartContext';
import '../../style/Payment.css';

const PaymentSuccess = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { fetchCart } = useCart();
    const { orderId, orderNumber, isCOD } = location.state || {};

    // Backend handles cart clearing, just sync frontend state
    useEffect(() => {
        fetchCart();
    }, [fetchCart]);

    return (
        <div className="payment-result-page">
            <div className="payment-result-container">
                <div className="payment-result-card success">
                    <div className="result-icon success-icon">
                        <svg viewBox="0 0 24 24" fill="none">
                            <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                    </div>

                    <h1>{isCOD ? 'Đặt hàng thành công!' : 'Thanh toán thành công!'}</h1>
                    <p>
                        {isCOD
                            ? 'Cảm ơn bạn đã đặt hàng. Vui lòng thanh toán khi nhận hàng.'
                            : 'Cảm ơn bạn đã mua hàng. Đơn hàng của bạn đã được xác nhận.'
                        }
                    </p>

                    {(orderId || orderNumber) && (
                        <div className="order-info">
                            <span className="label">Mã đơn hàng:</span>
                            <span className="value">{orderNumber || `#${orderId}`}</span>
                        </div>
                    )}

                    <div className="result-message">
                        <p>Chúng tôi sẽ gửi email xác nhận đơn hàng cho bạn trong giây lát.</p>
                        <p>Đơn hàng sẽ được xử lý và giao đến bạn sớm nhất có thể.</p>
                    </div>

                    <div className="result-actions">
                        <Link to="/product" className="primary-btn">
                            Tiếp tục mua sắm
                        </Link>
                        {orderId && (
                            <Link to={`/order/${orderId}`} className="secondary-btn">
                                Xem đơn hàng
                            </Link>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PaymentSuccess;
