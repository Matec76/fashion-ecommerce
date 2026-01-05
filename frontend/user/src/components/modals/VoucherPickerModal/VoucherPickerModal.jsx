import { useState, useEffect } from 'react';
import logger from '../../../utils/logger';
import { API_ENDPOINTS } from '../../../config/api.config';
import './VoucherPickerModal.css';

const VoucherPickerModal = ({ isOpen, onClose, onSelectVoucher, orderAmount, currentCoupon }) => {
    const [vouchers, setVouchers] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (isOpen) {
            fetchVouchers();
        }
    }, [isOpen]);

    const fetchVouchers = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('authToken');
            const response = await fetch(`${API_ENDPOINTS.COUPONS.AVAILABLE}?limit=50`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                setVouchers(data || []);
            }
        } catch (error) {
            logger.error('Error fetching vouchers:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleVoucherClick = async (voucher) => {
        // Validate voucher first
        try {
            const token = localStorage.getItem('authToken');
            const response = await fetch(API_ENDPOINTS.COUPONS.VALIDATE, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token && { 'Authorization': `Bearer ${token}` })
                },
                body: JSON.stringify({
                    coupon_code: voucher.coupon_code || voucher.code,
                    order_total: orderAmount
                })
            });

            const data = await response.json();

            if (!response.ok) {
                alert(data.detail || data.message || 'Mã giảm giá không hợp lệ');
                return;
            }

            // Calculate discount and check if it exceeds order amount
            const calculatedDiscount = data.discount_amount || calculateDiscount(data, orderAmount);

            if (calculatedDiscount > orderAmount) {
                alert(`Mã giảm giá này (giảm ${formatPrice(calculatedDiscount)}) chỉ áp dụng cho đơn hàng có giá trị lớn hơn hoặc bằng giá trị giảm giá.\n\nGiá trị đơn hàng hiện tại: ${formatPrice(orderAmount)}`);
                return;
            }

            // Apply voucher
            onSelectVoucher({
                code: voucher.coupon_code || voucher.code,
                discount_type: data.discount_type,
                discount_value: data.discount_value,
                discount_amount: Math.min(calculatedDiscount, orderAmount), // Cap at order amount
                min_order_amount: data.min_order_amount,
                max_discount: data.max_discount,
                ...data
            });

            onClose();
        } catch (err) {
            alert(`Lỗi: ${err.message}`);
        }
    };

    const calculateDiscount = (coupon, amount) => {
        if (coupon.discount_type === 'percentage') {
            const discount = (amount * coupon.discount_value) / 100;
            return coupon.max_discount ? Math.min(discount, coupon.max_discount) : discount;
        }
        return coupon.discount_value;
    };

    const formatPrice = (price) => {
        return new Intl.NumberFormat('vi-VN').format(price) + 'đ';
    };

    const isVoucherDisabled = (voucher) => {
        const minAmount = voucher.min_order_amount || 0;

        // Check if order amount is less than minimum required
        if (orderAmount < minAmount) {
            return true;
        }

        // Calculate potential discount
        const potentialDiscount = calculateDiscount(voucher, orderAmount);

        // Disable if discount would exceed order amount
        if (potentialDiscount > orderAmount) {
            return true;
        }

        return false;
    };

    if (!isOpen) return null;

    return (
        <div className="voucher-modal-overlay" onClick={onClose}>
            <div className="voucher-modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="voucher-modal-header">
                    <h2>Chọn Voucher</h2>
                    <button className="voucher-modal-close" onClick={onClose}>✕</button>
                </div>

                <div className="voucher-modal-body">
                    {loading ? (
                        <div className="voucher-loading">
                            <div className="spinner"></div>
                            <p>Đang tải vouchers...</p>
                        </div>
                    ) : vouchers.length === 0 ? (
                        <div className="voucher-empty">
                            <p>Bạn chưa có voucher nào</p>
                        </div>
                    ) : (
                        <div className="voucher-list">
                            {vouchers.map((voucher) => {
                                const isDisabled = isVoucherDisabled(voucher);
                                const isCurrent = currentCoupon?.code === (voucher.coupon_code || voucher.code);
                                const discountText = voucher.discount_type === 'percentage'
                                    ? `Giảm ${voucher.discount_value}%`
                                    : `Giảm ${formatPrice(voucher.discount_value)}`;

                                return (
                                    <div
                                        key={voucher.coupon_id}
                                        className={`voucher-card ${isDisabled ? 'disabled' : ''} ${isCurrent ? 'selected' : ''}`}
                                        onClick={() => !isDisabled && handleVoucherClick(voucher)}
                                    >
                                        <div className="voucher-card-left">
                                            <div className="voucher-info">
                                                <div className="voucher-code">
                                                    {voucher.coupon_code || voucher.code}
                                                </div>
                                                <div className="voucher-description">
                                                    {voucher.description || discountText}
                                                </div>
                                                {voucher.min_order_amount > 0 && (
                                                    <div className="voucher-min">
                                                        Đơn tối thiểu: {formatPrice(voucher.min_order_amount)}
                                                    </div>
                                                )}
                                                {voucher.max_discount && voucher.discount_type === 'percentage' && (
                                                    <div className="voucher-max">
                                                        Giảm tối đa: {formatPrice(voucher.max_discount)}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                        <div className="voucher-card-right">
                                            <div className="voucher-discount">
                                                {discountText}
                                            </div>
                                            {isDisabled && (
                                                <div className="voucher-disabled-label">
                                                    Không đủ điều kiện
                                                </div>
                                            )}
                                            {isCurrent && (
                                                <div className="voucher-current-label">
                                                    Đang dùng
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default VoucherPickerModal;
