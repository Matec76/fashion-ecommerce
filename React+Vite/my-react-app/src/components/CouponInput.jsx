import { useState } from 'react';
import { API_ENDPOINTS } from '../config/api.config';
import '../style/CouponInput.css';

const CouponInput = ({ orderAmount, onApply, onRemove, appliedCoupon }) => {
    const [couponCode, setCouponCode] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleApplyCoupon = async () => {
        if (!couponCode.trim()) {
            setError('Vui lòng nhập mã giảm giá');
            return;
        }

        setLoading(true);
        setError('');

        try {
            const token = localStorage.getItem('authToken');
            const response = await fetch(API_ENDPOINTS.COUPONS.VALIDATE, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token && { 'Authorization': `Bearer ${token}` })
                },
                body: JSON.stringify({
                    coupon_code: couponCode.trim().toUpperCase(),
                    order_total: orderAmount
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || data.message || 'Mã giảm giá không hợp lệ');
            }

            // Call parent callback with coupon data
            onApply({
                code: couponCode.trim().toUpperCase(),
                discount_type: data.discount_type,
                discount_value: data.discount_value,
                discount_amount: data.discount_amount || calculateDiscount(data, orderAmount),
                min_order_amount: data.min_order_amount,
                max_discount: data.max_discount,
                ...data
            });

            setCouponCode('');
            setError('');
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const calculateDiscount = (coupon, amount) => {
        if (coupon.discount_type === 'percentage') {
            const discount = (amount * coupon.discount_value) / 100;
            return coupon.max_discount ? Math.min(discount, coupon.max_discount) : discount;
        }
        return coupon.discount_value;
    };

    const handleRemove = () => {
        onRemove();
        setCouponCode('');
        setError('');
    };

    if (appliedCoupon) {
        return (
            <div className="coupon-applied">
                <div className="coupon-info">
                    <span className="coupon-icon">🎫</span>
                    <div className="coupon-details">
                        <span className="coupon-code">{appliedCoupon.code}</span>
                    </div>
                </div>
                <button
                    className="remove-coupon-btn"
                    onClick={handleRemove}
                    type="button"
                >
                    ✕
                </button>
            </div>
        );
    }

    return (
        <div className="coupon-input-container">
            <div className="coupon-input-wrapper">
                <input
                    type="text"
                    placeholder="Nhập mã giảm giá"
                    value={couponCode}
                    onChange={(e) => {
                        setCouponCode(e.target.value.toUpperCase());
                        setError('');
                    }}
                    className="coupon-input"
                    disabled={loading}
                />
                <button
                    onClick={handleApplyCoupon}
                    disabled={loading || !couponCode.trim()}
                    className="apply-coupon-btn"
                    type="button"
                >
                    {loading ? '...' : 'Áp dụng'}
                </button>
            </div>
            {error && <div className="coupon-error">{error}</div>}
        </div>
    );
};

export default CouponInput;
