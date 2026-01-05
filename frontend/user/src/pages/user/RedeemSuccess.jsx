import React from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import '../../style/Vouchers.css'; // Tận dụng style của vouchers hoặc tạo riêng

const RedeemSuccess = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { couponCode, points } = location.state || {};

    if (!couponCode) {
        return (
            <div className="vouchers-loading-container">
                <p>Không tìm thấy thông tin quy đổi. Đang quay lại...</p>
                <button className="copy-btn" onClick={() => navigate('/loyalty')}>Quay lại Hội viên</button>
            </div>
        );
    }

    const handleCopy = () => {
        navigator.clipboard.writeText(couponCode);
        const btn = document.getElementById('copy-success-btn');
        const originalText = btn.innerText;
        btn.innerText = 'Đã sao chép!';
        btn.classList.add('copied');
        setTimeout(() => {
            btn.innerText = originalText;
            btn.classList.remove('copied');
        }, 2000);
    };

    return (
        <div className="redeem-success-page">
            <div className="success-overlay-content">
                <h1 className="success-title">Quy Đổi Thành Công!</h1>
                <p className="success-msg">Mã giảm giá đã được thêm vào kho Voucher của bạn.</p>

                <div className="success-card-premium">
                    <div className="card-top-info">
                        <span>GIÁ TRỊ QUY ĐỔI</span>
                        <strong>{points?.toLocaleString()} điểm</strong>
                    </div>

                    <div className="success-coupon-box">
                        <span className="coupon-label-fixed">MÃ COUPON CỦA BẠN:</span>
                        <div className="coupon-display-main">{couponCode}</div>
                        <button
                            id="copy-success-btn"
                            className="copy-btn-large"
                            onClick={handleCopy}
                        >
                            SAO CHÉP MÃ
                        </button>
                    </div>

                    <div className="card-footer-tip">
                        <p>Bạn có thể xem lại mã này bất cứ lúc nào tại mục <strong>"Voucher của tôi"</strong></p>
                    </div>
                </div>

                <div className="success-actions-row">
                    <Link to="/vouchers" className="action-btn secondary">Kho Voucher</Link>
                    <Link to="/loyalty" className="action-btn primary">Tiếp tục đổi điểm</Link>
                </div>
            </div>

            <style>{`
                .redeem-success-page {
                    min-height: 80vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 40px 20px;
                    background: #fff;
                    animation: fadeIn 0.8s ease-out;
                }
                .success-overlay-content {
                    max-width: 500px;
                    width: 100%;
                    text-align: center;
                }
                .success-icon-main {
                    font-size: 80px;
                    margin-bottom: 20px;
                    display: block;
                    animation: bounce 2s infinite;
                }
                .success-title {
                    font-size: 36px;
                    font-weight: 800;
                    color: #1a1a2e;
                    margin-bottom: 10px;
                }
                .success-msg {
                    color: #666;
                    margin-bottom: 40px;
                    font-size: 16px;
                }
                .success-card-premium {
                    background: white;
                    border-radius: 30px;
                    padding: 30px;
                    box-shadow: none;
                    margin-bottom: 40px;
                    position: relative;
                    border: 1px solid #000;
                }
                .card-top-info {
                    display: flex;
                    flex-direction: column;
                    gap: 5px;
                    margin-bottom: 25px;
                    padding-bottom: 20px;
                    border-bottom: 1px dashed #ddd;
                }
                .card-top-info span { font-size: 12px; color: #999; letter-spacing: 1px; }
                .card-top-info strong { font-size: 20px; color: #ff4757; }

                .success-coupon-box {
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 20px;
                    border: 2px solid #eee;
                    margin-bottom: 20px;
                }
                .coupon-label-fixed { font-size: 11px; font-weight: 700; color: #aaa; margin-bottom: 10px; display: block; }
                .coupon-display-main {
                    font-size: 28px;
                    font-family: 'JetBrains Mono', monospace;
                    font-weight: 800;
                    color: #1a1a2e;
                    margin-bottom: 20px;
                    letter-spacing: 2px;
                }
                .copy-btn-large {
                    width: 100%;
                    background: #1a1a2e;
                    color: white;
                    border: none;
                    padding: 15px;
                    border-radius: 12px;
                    font-weight: 700;
                    cursor: pointer;
                    transition: all 0.3s;
                }
                .copy-btn-large:hover { background: #333; transform: scale(1.02); }
                .copy-btn-large.copied { background: #2ecc71; }

                .card-footer-tip { font-size: 13px; color: #888; }
                .card-footer-tip strong { color: #1a1a2e; }

                .success-actions-row {
                    display: flex;
                    gap: 15px;
                }
                .action-btn {
                    flex: 1;
                    padding: 15px;
                    border-radius: 15px;
                    text-decoration: none;
                    font-weight: 700;
                    transition: all 0.3s;
                    font-size: 15px;
                }
                .action-btn.primary { background: #ff4757; color: white; }
                .action-btn.secondary { background: #eee; color: #333; }
                .action-btn:hover { transform: translateY(-3px); opacity: 0.9; }

                @keyframes bounce {
                    0%, 20%, 50%, 80%, 100% {transform: translateY(0);}
                    40% {transform: translateY(-20px);}
                    60% {transform: translateY(-10px);}
                }
                @keyframes fadeIn {
                    from {opacity: 0; transform: scale(0.95);}
                    to {opacity: 1; transform: scale(1);}
                }
            `}</style>
        </div>
    );
};

export default RedeemSuccess;
