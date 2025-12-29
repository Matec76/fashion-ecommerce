import React, { useState } from 'react';
import { API_ENDPOINTS } from '../../config/api.config';
import useFetch from '../../components/useFetch';
import '../../style/Vouchers.css';

const Vouchers = () => {
    const [copySuccess, setCopySuccess] = useState('');

    // Fetch vouchers with skipCache to always get fresh data from database
    const { data: vouchers, loading } = useFetch(
        `${API_ENDPOINTS.COUPONS.AVAILABLE}?limit=50`,
        { auth: true, skipCache: true }
    );

    const handleCopyCode = (code) => {
        navigator.clipboard.writeText(code);
        setCopySuccess(code);
        setTimeout(() => setCopySuccess(''), 2000);
    };

    if (loading) return (
        <div className="vouchers-loading-container">
            <div className="vouchers-loader"></div>
            <p>Đang tải mã giảm giá của bạn...</p>
        </div>
    );

    return (
        <div className="vouchers-container">
            <header className="vouchers-header">
                <h1>Voucher của tôi</h1>
                <p>Tổng hợp các mã giảm giá bạn đã quy đổi từ điểm thưởng</p>
            </header>

            {vouchers.length === 0 ? (
                <div className="no-vouchers">
                    <div className="no-vouchers-icon">🎫</div>
                    <h3>Bạn chưa có mã giảm giá nào</h3>
                    <p>Hãy quy đổi điểm thưởng tại trang Hội viên để nhận ưu đãi nhé!</p>
                </div>
            ) : (
                <div className="vouchers-grid">
                    {vouchers.map((voucher) => (
                        <div key={voucher.coupon_id || voucher.id} className="voucher-card">
                            <div className="voucher-left">
                                <div className="voucher-icon-wrapper">
                                    <span className="voucher-tag">GIẢM</span>
                                    <div className="voucher-value">
                                        {voucher.discount_type === 'PERCENTAGE'
                                            ? `${voucher.discount_value}%`
                                            : `${Math.floor(voucher.discount_value).toLocaleString()}đ`}
                                    </div>
                                </div>
                            </div>
                            <div className="voucher-right">
                                <h3 className="voucher-name">{voucher.description || 'Mã giảm giá quy đổi'}</h3>
                                <div className="voucher-details">
                                    {voucher.min_purchase_amount > 0 && (
                                        <div className="voucher-condition">
                                            Đơn tối thiểu {Math.floor(voucher.min_purchase_amount).toLocaleString()}đ
                                        </div>
                                    )}
                                    <div className="voucher-expiry">
                                        Hạn dùng: {new Date(voucher.end_date).toLocaleDateString('vi-VN')}
                                    </div>
                                </div>
                                <div className="voucher-footer">
                                    <div className="voucher-code-wrapper">
                                        <span className="voucher-code">{voucher.coupon_code || voucher.code || 'COUPON'}</span>
                                        <button
                                            className={`copy-btn ${copySuccess === (voucher.coupon_code || voucher.code) ? 'copied' : ''}`}
                                            onClick={() => handleCopyCode(voucher.coupon_code || voucher.code)}
                                        >
                                            {copySuccess === (voucher.coupon_code || voucher.code) ? 'Đã chép' : 'Sao chép'}
                                        </button>
                                    </div>
                                </div>
                            </div>
                            <div className="voucher-decor-dot top"></div>
                            <div className="voucher-decor-dot bottom"></div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default Vouchers;
