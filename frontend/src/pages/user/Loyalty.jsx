import React, { useState, useEffect } from 'react';
import logger from '../../utils/logger';
import { useNavigate } from 'react-router-dom';
import { API_ENDPOINTS } from '../../config/api.config';
import '../../style/LoyaltyPage.css';

const Loyalty = () => {
    const navigate = useNavigate();
    const [loyaltyData, setLoyaltyData] = useState(null);
    const [tiers, setTiers] = useState([]);
    const [leaderboard, setLeaderboard] = useState([]);
    const [transactions, setTransactions] = useState([]);
    const [referralCode, setReferralCode] = useState('');
    const [inputReferralCode, setInputReferralCode] = useState('');
    const [referralStats, setReferralStats] = useState(null);
    const [referralStatus, setReferralStatus] = useState(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('overview');
    const [isEmailVerified, setIsEmailVerified] = useState(false);
    const [sendingVerification, setSendingVerification] = useState(false);
    const [redeemingVoucher, setRedeemingVoucher] = useState(null);
    const [redeemPoints, setRedeemPoints] = useState('');
    const [redeemCoupon, setRedeemCoupon] = useState(null);

    const token = localStorage.getItem('authToken');

    useEffect(() => {
        if (!token) {
            navigate('/login');
            return;
        }
        fetchAllData();
    }, [token, navigate]);

    const fetchUserProfile = async () => {
        try {
            const response = await fetch(API_ENDPOINTS.AUTH.ME, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const data = await response.json();
                setIsEmailVerified(data.is_email_verified || false);
                return data.is_email_verified || false;
            }
        } catch (error) {
            logger.error('Error fetching user profile:', error);
        }
        return false;
    };

    const handleResendVerification = async () => {
        setSendingVerification(true);
        try {
            const response = await fetch(API_ENDPOINTS.AUTH.RESEND_VERIFICATION, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                alert('Email xác thực đã được gửi! Vui lòng kiểm tra hộp thư của bạn.');
            } else {
                const error = await response.json();
                alert(error.detail || 'Không thể gửi email xác thực. Vui lòng thử lại sau.');
            }
        } catch (error) {
            logger.error('Error sending verification email:', error);
            alert('Có lỗi xảy ra. Vui lòng thử lại sau.');
        }
        setSendingVerification(false);
    };

    const fetchAllData = async () => {
        setLoading(true);
        // Check verification status first
        const verified = await fetchUserProfile();

        // Only fetch loyalty data if verified
        if (verified) {
            await Promise.all([
                fetchLoyaltyData(),
                fetchTiers(),
                fetchLeaderboard(),
                fetchReferralCode(),
                fetchReferralStats(),
                fetchReferralStatus(),
                fetchTransactions()
            ]);
        }
        setLoading(false);
    };

    const fetchLoyaltyData = async () => {
        try {
            const response = await fetch(API_ENDPOINTS.LOYALTY.ME, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const data = await response.json();
                setLoyaltyData(data);
            }
        } catch (error) {
            logger.error('Error fetching loyalty data:', error);
        }
    };

    const fetchTiers = async () => {
        try {
            const response = await fetch(API_ENDPOINTS.LOYALTY.TIERS);
            if (response.ok) {
                const data = await response.json();
                setTiers(data);
            }
        } catch (error) {
            logger.error('Error fetching tiers:', error);
        }
    };

    const fetchLeaderboard = async () => {
        try {
            const response = await fetch(`${API_ENDPOINTS.LOYALTY.LEADERBOARD}?limit=10`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const data = await response.json();
                setLeaderboard(data);
            }
        } catch (error) {
            logger.error('Error fetching leaderboard:', error);
        }
    };

    const fetchReferralCode = async () => {
        try {
            const response = await fetch(API_ENDPOINTS.LOYALTY.REFERRALS.MY_CODE, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const data = await response.json();
                setReferralCode(data.referral_code || data.code || '');
            }
        } catch (error) {
            logger.error('Error fetching referral code:', error);
        }
    };

    const fetchReferralStats = async () => {
        try {
            const response = await fetch(API_ENDPOINTS.LOYALTY.REFERRALS.STATS, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const data = await response.json();
                setReferralStats(data);
            }
        } catch (error) {
            logger.error('Error fetching referral stats:', error);
        }
    };

    const fetchReferralStatus = async () => {
        try {
            const response = await fetch(API_ENDPOINTS.LOYALTY.REFERRALS.STATUS, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const data = await response.json();
                setReferralStatus(data);
            }
        } catch (error) {
            logger.error('Error fetching referral status:', error);
        }
    };

    const fetchTransactions = async () => {
        try {
            const response = await fetch(`${API_ENDPOINTS.LOYALTY.TRANSACTIONS}?limit=20`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const data = await response.json();
                setTransactions(data);
            }
        } catch (error) {
            logger.error('Error fetching transactions:', error);
        }
    };

    const copyReferralCode = () => {
        navigator.clipboard.writeText(referralCode);
        alert('Đã sao chép mã giới thiệu!');
    };

    const handleApplyReferral = async () => {
        if (!inputReferralCode.trim()) return;

        try {
            const response = await fetch(API_ENDPOINTS.LOYALTY.REFERRALS.CLAIM, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ referral_code: inputReferralCode.trim() })
            });

            if (response.ok) {
                alert('Áp dụng mã giới thiệu thành công!');
                setInputReferralCode('');
                // Refresh data
                fetchAllData();
            } else {
                const error = await response.json();
                alert(error.detail || 'Không thể áp dụng mã này!');
            }
        } catch (error) {
            logger.error('Error applying referral code:', error);
            alert('Có lỗi xảy ra!');
        }
    };

    const formatPoints = (points) => {
        return new Intl.NumberFormat('vi-VN').format(points || 0);
    };

    const formatDate = (dateString) => {
        if (!dateString) return '';
        return new Date(dateString).toLocaleDateString('vi-VN');
    };

    /**
     * Logic sửa lỗi: Tính toán hạng thực tế dựa trên điểm tích lũy
     * Ưu tiên logic Frontend nếu Backend trả về sai Tier
     */
    const getCurrentTier = () => {
        if (!loyaltyData || !tiers || tiers.length === 0) return loyaltyData?.tier || { tier_name: 'Bronze', discount_percentage: 0 };

        const totalEarned = loyaltyData.total_earned || 0;
        // Sắp xếp tiers theo mốc điểm giảm dần để tìm mốc cao nhất đạt được
        const sortedTiers = [...tiers].sort((a, b) => b.min_points - a.min_points);
        const achievedTier = sortedTiers.find(t => totalEarned >= t.min_points);

        return achievedTier || sortedTiers[sortedTiers.length - 1] || loyaltyData.tier;
    };

    const currentTier = getCurrentTier();

    const handleRedeemPoints = async () => {
        const points = parseInt(redeemPoints);

        // Validation
        if (!redeemPoints || isNaN(points) || points <= 0) {
            return;
        }

        if (points > loyaltyData?.points_balance) {
            return;
        }

        if (!window.confirm(`Bạn có chắc muốn quy đổi ${formatPoints(points)} điểm?`)) {
            return;
        }

        setRedeemingVoucher(true);
        try {
            const response = await fetch(API_ENDPOINTS.LOYALTY.REDEEM, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    points: points,
                    description: `Quy đổi ${formatPoints(points)} điểm thành coupon`
                })
            });

            if (response.ok) {
                const data = await response.json();

                // Chuyển hướng đến trang thành công nếu API trả về coupon
                if (data.coupon_code || data.code) {
                    navigate('/loyalty/success', {
                        state: {
                            couponCode: data.coupon_code || data.code,
                            points: points
                        }
                    });
                }


                // Refresh data
                setRedeemPoints('');
                fetchLoyaltyData();
                fetchTransactions();
            } else {
                const error = await response.json();
                alert(error.detail || 'Không thể quy đổi điểm. Vui lòng thử lại!');
            }
        } catch (error) {
            logger.error('Error redeeming points:', error);
        }
        setRedeemingVoucher(false);
    };

    if (!token) {
        return (
            <div className="loyalty-page">
                <div className="login-prompt">
                    <h2>Vui lòng đăng nhập</h2>
                    <p>Đăng nhập để xem thông tin thành viên</p>
                    <button onClick={() => navigate('/login')}>Đăng nhập</button>
                </div>
            </div>
        );
    }

    if (loading) {
        return (
            <div className="loyalty-page">
                <div className="loading-state">
                    <div className="spinner"></div>
                    <p>Đang tải...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="loyalty-page">
            {/* Hero Section */}
            <div className="loyalty-hero">
                <h1>THAM GIA CÂU LẠC BỘ</h1>
            </div>

            {/* Benefits Section */}
            <div className="benefits-section">
                <div className="benefits-grid">
                    <div className="benefit-card">
                        <h3>Ưu Đãi Độc Quyền</h3>
                        <p>Giảm giá cho các thành viên và quyền truy cập sớm vào đợt giảm giá.</p>
                    </div>
                    <div className="benefit-card">
                        <h3>Sản Phẩm Giới Hạn</h3>
                        <p>Cơ hội mua các mặt hàng độc quyền và giới hạn.</p>
                    </div>
                    <div className="benefit-card">
                        <h3>Miễn phí vận chuyển</h3>
                        <p>Tận hưởng giao hàng miễn phí cho tất cả các đơn hàng.</p>
                    </div>
                </div>
            </div>

            {/* Verification Prompt for unverified users */}
            {!isEmailVerified && (
                <div className="verification-prompt">
                    <div className="verification-card">
                        <h2>Xác thực để trở thành hội viên</h2>
                        <p>Xác thực email của bạn để mở khóa tất cả các đặc quyền hội viên, tích điểm thưởng và nhận ưu đãi độc quyền!</p>
                        <button
                            className="verify-btn"
                            onClick={handleResendVerification}
                            disabled={sendingVerification}
                        >
                            {sendingVerification ? 'Đang gửi...' : 'Xác thực ngay để trở thành hội viên'}
                        </button>
                    </div>
                </div>
            )}

            {/* Only show full loyalty features if email is verified */}
            {isEmailVerified && (
                <>

                    {/* Tabs */}
                    <div className="loyalty-tabs">
                        <button
                            className={activeTab === 'overview' ? 'active' : ''}
                            onClick={() => setActiveTab('overview')}
                        >
                            Tổng quan
                        </button>
                        <button
                            className={activeTab === 'tiers' ? 'active' : ''}
                            onClick={() => setActiveTab('tiers')}
                        >
                            Hạng thành viên
                        </button>
                        <button
                            className={activeTab === 'referral' ? 'active' : ''}
                            onClick={() => setActiveTab('referral')}
                        >
                            Giới thiệu bạn bè
                        </button>
                        <button
                            className={activeTab === 'history' ? 'active' : ''}
                            onClick={() => setActiveTab('history')}
                        >
                            Shop quy đổi
                        </button>
                        <button
                            className={activeTab === 'transactions' ? 'active' : ''}
                            onClick={() => setActiveTab('transactions')}
                        >
                            Lịch sử giao dịch
                        </button>
                    </div>

                    {/* Tab Content */}
                    <div className="loyalty-content">
                        {activeTab === 'overview' && (
                            <div className="overview-tab">
                                <div className="points-card">
                                    <div className="points-main">
                                        <span className="points-value">{formatPoints(loyaltyData?.points_balance)}</span>
                                        <span className="points-label">điểm hiện có</span>
                                    </div>
                                    <div className="tier-badge" data-tier={(currentTier?.tier_name || 'Bronze').toLowerCase()}>
                                        {currentTier?.tier_name || 'Bronze'}
                                    </div>
                                </div>

                                <div className="stats-row">
                                    <div className="stat-box">
                                        <span className="stat-value">{formatPoints(loyaltyData?.total_earned)}</span>
                                        <span className="stat-label">Tổng điểm tích lũy</span>
                                    </div>
                                    <div className="stat-box">
                                        <span className="stat-value">{formatPoints(loyaltyData?.total_spent)}</span>
                                        <span className="stat-label">Điểm đã sử dụng</span>
                                    </div>
                                    <div className="stat-box">
                                        <span className="stat-value">{currentTier?.discount_percentage || 0}%</span>
                                        <span className="stat-label">Giảm giá hạng hiện tại</span>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeTab === 'tiers' && (
                            <div className="tiers-tab">
                                <h2 className="leaderboard-title">Bảng Xếp Hạng Hội Viên</h2>
                                {leaderboard.length === 0 ? (
                                    <p className="no-data">Chưa có dữ liệu xếp hạng</p>
                                ) : (
                                    <div className="leaderboard-table-wrapper">
                                        <table className="leaderboard-table">
                                            <thead>
                                                <tr>
                                                    <th>Hạng</th>
                                                    <th>Người dùng</th>
                                                    <th>Điểm tích lũy</th>
                                                    <th>Thứ hạng</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {leaderboard.map((item, index) => (
                                                    <tr key={item.user?.user_id || index} className={item.rank <= 3 ? `top-${item.rank}` : ''}>
                                                        <td className="rank-cell">
                                                            {item.rank <= 3 ? (
                                                                <span className={`rank-badge rank-${item.rank}`}>{item.rank}</span>
                                                            ) : (
                                                                item.rank
                                                            )}
                                                        </td>
                                                        <td className="name-cell">
                                                            {item.user?.first_name || item.user?.last_name
                                                                ? `${item.user?.first_name || ''} ${item.user?.last_name || ''}`.trim()
                                                                : 'Ẩn danh'}
                                                        </td>
                                                        <td className="points-cell">{formatPoints(item.points || 0)}</td>
                                                        <td className="tier-cell">
                                                            <span className="tier-name" data-tier={(item.tier?.tier_name || item.tier || 'Bronze').toLowerCase()}>
                                                                {item.tier?.tier_name || item.tier || 'Bronze'}
                                                            </span>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </div>
                        )}

                        {activeTab === 'referral' && (
                            <div className="referral-tab">
                                <div className="referral-card">
                                    <h3>Mã giới thiệu của bạn</h3>
                                    <div className="referral-code-box">
                                        <code>{referralCode || 'Chưa có mã'}</code>
                                        {referralCode && (
                                            <button onClick={copyReferralCode}>Sao chép</button>
                                        )}
                                    </div>
                                    <p className="referral-hint">Chia sẻ mã này để nhận thưởng khi bạn bè đăng ký và mua hàng!</p>
                                </div>

                                {/* Only show input referral if user can still claim (hasn't used a code yet) */}
                                {referralStatus?.can_claim && (
                                    <div className="referral-card input-referral-card">
                                        <h3>Nhập mã giới thiệu</h3>
                                        <div className="referral-input-box">
                                            <input
                                                type="text"
                                                placeholder="Nhập mã giới thiệu..."
                                                value={inputReferralCode}
                                                onChange={(e) => setInputReferralCode(e.target.value)}
                                            />
                                            <button onClick={handleApplyReferral}>Áp dụng</button>
                                        </div>
                                        <p className="referral-hint">Nhập mã giới thiệu từ bạn bè để nhận thưởng ngay!</p>
                                    </div>
                                )}

                                {referralStats && (
                                    <div className="referral-stats">
                                        <div className="ref-stat">
                                            <span className="ref-value">{referralStats.total_referrals || 0}</span>
                                            <span className="ref-label">Người đã giới thiệu</span>
                                        </div>
                                        <div className="ref-stat">
                                            <span className="ref-value">{formatPoints(referralStats.total_points_earned || 0)}</span>
                                            <span className="ref-label">Điểm thưởng nhận được</span>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {activeTab === 'history' && (
                            <div className="history-tab">
                                <div className="redeem-shop">
                                    <div className="shop-header">
                                        <h2>Shop Quy Đổi</h2>
                                        <div className="current-points">
                                            Điểm hiện có: <strong>{formatPoints(loyaltyData?.points_balance)}</strong>
                                        </div>
                                    </div>

                                    <div className="redeem-form-container">
                                        <div className="redeem-form">
                                            <h3>Nhập số điểm muốn quy đổi</h3>
                                            <p className="redeem-hint">Điểm sẽ được quy đổi thành mã coupon giảm giá</p>

                                            <div className="points-input-group">
                                                <input
                                                    type="number"
                                                    placeholder="Nhập số điểm..."
                                                    value={redeemPoints}
                                                    onChange={(e) => setRedeemPoints(e.target.value)}
                                                    min="1"
                                                    max={loyaltyData?.points_balance || 0}
                                                    disabled={redeemingVoucher}
                                                />
                                                <span className="points-label">điểm</span>
                                            </div>

                                            <button
                                                className="redeem-submit-btn"
                                                onClick={handleRedeemPoints}
                                                disabled={!redeemPoints || redeemingVoucher}
                                            >
                                                {redeemingVoucher ? 'Đang xử lý...' : 'Quy đổi ngay'}
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeTab === 'transactions' && (
                            <div className="transactions-tab">
                                <div className="transaction-history">
                                    <h2>Lịch sử giao dịch</h2>
                                    {transactions.length === 0 ? (
                                        <p className="no-data">Chưa có giao dịch nào</p>
                                    ) : (
                                        <div className="transactions-list">
                                            {transactions.map((tx, index) => (
                                                <div key={tx.transaction_id || index} className="transaction-item">
                                                    <div className="tx-info">
                                                        <span className={`tx-points ${tx.transaction_type?.includes('EARN') ? 'earn' : 'spend'}`}>
                                                            {tx.transaction_type?.includes('EARN') ? '+' : '-'}{Math.abs(tx.points)} điểm
                                                        </span>
                                                        <span className="tx-desc">{tx.description}</span>
                                                    </div>
                                                    <span className="tx-date">{formatDate(tx.created_at)}</span>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                </>
            )}
        </div>
    );
};

export default Loyalty;
