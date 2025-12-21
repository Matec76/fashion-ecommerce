import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import usePatch from '../../components/usePatch';
import { API_ENDPOINTS } from '../../config/api.config';
import '../../style/UserProfile.css';
import '../../style/Loyalty.css';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const UserProfile = () => {
    const navigate = useNavigate();
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [editing, setEditing] = useState(false);
    const [formData, setFormData] = useState({
        full_name: '',
        email: '',
        phone_number: '',
        date_of_birth: '',
        gender: ''
    });
    const [defaultAddress, setDefaultAddress] = useState(null);

    // Loyalty states
    const [loyaltyData, setLoyaltyData] = useState(null);
    const [referralCode, setReferralCode] = useState('');
    const [transactions, setTransactions] = useState([]);
    const [showTransactionsModal, setShowTransactionsModal] = useState(false);

    const { patch, loading: patchLoading } = usePatch();

    // Fetch user data
    useEffect(() => {
        fetchUserData();
        fetchDefaultAddress();
        fetchLoyaltyData();
        fetchReferralCode();
    }, []);

    const fetchLoyaltyData = async () => {
        try {
            const token = localStorage.getItem('authToken');
            const response = await fetch(API_ENDPOINTS.LOYALTY.ME, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const data = await response.json();
                setLoyaltyData(data);
            }
        } catch (error) {
            console.error('Error fetching loyalty data:', error);
        }
    };

    const fetchReferralCode = async () => {
        try {
            const token = localStorage.getItem('authToken');
            const response = await fetch(API_ENDPOINTS.LOYALTY.REFERRALS.MY_CODE, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const data = await response.json();
                setReferralCode(data.referral_code || data.code || '');
            }
        } catch (error) {
            console.error('Error fetching referral code:', error);
        }
    };

    const fetchTransactions = async () => {
        try {
            const token = localStorage.getItem('authToken');
            const response = await fetch(`${API_ENDPOINTS.LOYALTY.TRANSACTIONS}?limit=20`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const data = await response.json();
                setTransactions(data);
            }
        } catch (error) {
            console.error('Error fetching transactions:', error);
        }
    };

    const copyReferralCode = () => {
        navigator.clipboard.writeText(referralCode);
        alert('Đã sao chép mã giới thiệu!');
    };

    const openTransactionsModal = () => {
        fetchTransactions();
        setShowTransactionsModal(true);
    };

    const formatPoints = (points) => {
        return new Intl.NumberFormat('vi-VN').format(points || 0);
    };

    const fetchUserData = async () => {
        try {
            const token = localStorage.getItem('authToken');
            const response = await fetch(`${API_BASE_URL}/users/me`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.ok) {
                const data = await response.json();
                setUser(data);
                setFormData({
                    full_name: data.full_name || '',
                    email: data.email || '',
                    phone_number: data.phone_number || '',
                    date_of_birth: data.date_of_birth || '',
                    gender: data.gender || ''
                });
            } else if (response.status === 401) {
                navigate('/login');
            }
        } catch (error) {
            console.error('Error fetching user data:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        const result = await patch(`${API_BASE_URL}/users/me`, formData);

        if (result.success) {
            setUser(result.data);
            setEditing(false);
            alert('Cập nhật thông tin thành công!');
        } else {
            alert(result.error || 'Không thể cập nhật thông tin!');
        }
    };

    const formatDate = (dateString) => {
        if (!dateString) return 'Chưa cập nhật';
        const date = new Date(dateString);
        return date.toLocaleDateString('vi-VN');
    };

    const fetchDefaultAddress = async () => {
        try {
            const token = localStorage.getItem('authToken');
            const response = await fetch(`${API_BASE_URL}/users/me/addresses`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.ok) {
                const addresses = await response.json();
                const defaultAddr = addresses.find(addr => addr.is_default) || addresses[0];
                setDefaultAddress(defaultAddr);
            }
        } catch (error) {
            console.error('Error fetching addresses:', error);
        }
    };

    if (loading) {
        return (
            <div className="profile-loading">
                <div className="spinner"></div>
                <p>Đang tải thông tin...</p>
            </div>
        );
    }

    return (
        <div className="user-profile-page">
            <div className="profile-container">
                <div className="profile-header">
                    <div className="profile-avatar">
                        <div className="avatar-circle">
                            {user?.full_name?.charAt(0)?.toUpperCase() || 'U'}
                        </div>
                    </div>
                    <div className="profile-title">
                        <h1>Tài khoản của tôi</h1>
                        <p>Quản lý thông tin cá nhân của bạn</p>
                    </div>
                </div>

                <div className="profile-content">
                    {/* Personal Information Section */}
                    <div className="profile-section">
                        <div className="section-header">
                            <h2>Thông tin cá nhân</h2>
                            {!editing ? (
                                <button
                                    className="edit-btn"
                                    onClick={() => setEditing(true)}
                                >
                                    Chỉnh sửa
                                </button>
                            ) : (
                                <div className="edit-actions">
                                    <button
                                        className="cancel-btn"
                                        onClick={() => {
                                            setEditing(false);
                                            fetchUserData();
                                        }}
                                    >
                                        Hủy
                                    </button>
                                    <button
                                        className="save-btn"
                                        onClick={handleSubmit}
                                        disabled={loading}
                                    >
                                        {loading ? 'Đang lưu...' : 'Lưu'}
                                    </button>
                                </div>
                            )}
                        </div>

                        {editing ? (
                            <form className="profile-form" onSubmit={handleSubmit}>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label>Họ và tên</label>
                                        <input
                                            type="text"
                                            name="full_name"
                                            value={formData.full_name}
                                            onChange={handleInputChange}
                                            placeholder="Nguyễn Văn A"
                                        />
                                    </div>

                                    <div className="form-group">
                                        <label>Số điện thoại</label>
                                        <input
                                            type="tel"
                                            name="phone_number"
                                            value={formData.phone_number}
                                            onChange={handleInputChange}
                                            placeholder="0912345678"
                                        />
                                    </div>
                                </div>

                                <div className="form-row">
                                    <div className="form-group">
                                        <label>Email</label>
                                        <input
                                            type="email"
                                            name="email"
                                            value={formData.email}
                                            onChange={handleInputChange}
                                            placeholder="email@example.com"
                                            disabled
                                        />
                                        <small>Email không thể thay đổi</small>
                                    </div>

                                    <div className="form-group">
                                        <label>Giới tính</label>
                                        <select
                                            name="gender"
                                            value={formData.gender}
                                            onChange={handleInputChange}
                                        >
                                            <option value="">Chọn giới tính</option>
                                            <option value="MALE">Nam</option>
                                            <option value="FEMALE">Nữ</option>
                                            <option value="OTHER">Khác</option>
                                        </select>
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label>Ngày sinh</label>
                                    <input
                                        type="date"
                                        name="date_of_birth"
                                        value={formData.date_of_birth}
                                        onChange={handleInputChange}
                                    />
                                </div>
                            </form>
                        ) : (
                            <div className="info-grid">
                                <div className="info-item">
                                    <span className="info-label">Họ và tên</span>
                                    <span className="info-value">{user?.full_name || 'Chưa cập nhật'}</span>
                                </div>

                                <div className="info-item">
                                    <span className="info-label">Email</span>
                                    <span className="info-value">{user?.email}</span>
                                </div>

                                <div className="info-item">
                                    <span className="info-label">Số điện thoại</span>
                                    <span className="info-value">{user?.phone_number || 'Chưa cập nhật'}</span>
                                </div>

                                <div className="info-item">
                                    <span className="info-label">Giới tính</span>
                                    <span className="info-value">
                                        {user?.gender === 'MALE' ? 'Nam' :
                                            user?.gender === 'FEMALE' ? 'Nữ' :
                                                user?.gender === 'OTHER' ? 'Khác' : 'Chưa cập nhật'}
                                    </span>
                                </div>

                                <div className="info-item">
                                    <span className="info-label">Ngày sinh</span>
                                    <span className="info-value">{formatDate(user?.date_of_birth)}</span>
                                </div>

                                <div className="info-item">
                                    <span className="info-label">Ngày tạo tài khoản</span>
                                    <span className="info-value">{formatDate(user?.created_at)}</span>
                                </div>

                                <div className="info-item full-width">
                                    <span className="info-label">Địa chỉ</span>
                                    <span className="info-value">
                                        {defaultAddress ? (
                                            <>
                                                {defaultAddress.street_address}, {defaultAddress.ward && `${defaultAddress.ward}, `}
                                                {defaultAddress.district}, {defaultAddress.city}
                                                <button
                                                    className="manage-address-link"
                                                    onClick={() => navigate('/addresses')}
                                                >
                                                    Quản lý địa chỉ →
                                                </button>
                                            </>
                                        ) : (
                                            <button
                                                className="add-address-link"
                                                onClick={() => navigate('/addresses')}
                                            >
                                                + Thêm địa chỉ
                                            </button>
                                        )}
                                    </span>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Loyalty Section */}
                    <div className="profile-section loyalty-section">
                        <div className="section-header">
                            <h2>Thành viên</h2>
                            <button
                                className="view-history-btn"
                                onClick={openTransactionsModal}
                            >
                                Xem lịch sử điểm
                            </button>
                        </div>

                        <div className="loyalty-card">
                            <div className="loyalty-main">
                                <div className="points-display">
                                    <span className="points-value">{formatPoints(loyaltyData?.points_balance)}</span>
                                    <span className="points-label">điểm</span>
                                </div>
                                <div className="tier-info">
                                    <span className="tier-badge" data-tier={loyaltyData?.tier?.tier_name?.toLowerCase()}>
                                        {loyaltyData?.tier?.tier_name || 'Bronze'}
                                    </span>
                                    {loyaltyData?.tier?.discount_percentage > 0 && (
                                        <span className="tier-discount">
                                            Giảm {loyaltyData.tier.discount_percentage}% mọi đơn
                                        </span>
                                    )}
                                </div>
                            </div>

                            <div className="loyalty-stats">
                                <div className="stat-item">
                                    <span className="stat-value">{formatPoints(loyaltyData?.total_earned)}</span>
                                    <span className="stat-label">Tổng tích lũy</span>
                                </div>
                                <div className="stat-item">
                                    <span className="stat-value">{formatPoints(loyaltyData?.total_spent)}</span>
                                    <span className="stat-label">Đã sử dụng</span>
                                </div>
                            </div>

                            {referralCode && (
                                <div className="referral-section">
                                    <span className="referral-label">Mã giới thiệu của bạn:</span>
                                    <div className="referral-code-box">
                                        <code className="referral-code">{referralCode}</code>
                                        <button
                                            className="copy-btn"
                                            onClick={copyReferralCode}
                                            title="Sao chép mã"
                                        >
                                            Copy
                                        </button>
                                    </div>
                                    <span className="referral-hint">Chia sẻ mã này để nhận thưởng khi bạn bè đăng ký!</span>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Transactions Modal */}
            {
                showTransactionsModal && (
                    <div className="modal-overlay" onClick={() => setShowTransactionsModal(false)}>
                        <div className="modal-content transactions-modal" onClick={e => e.stopPropagation()}>
                            <div className="modal-header">
                                <h3>Lịch sử điểm thưởng</h3>
                                <button
                                    className="modal-close"
                                    onClick={() => setShowTransactionsModal(false)}
                                >
                                    ✕
                                </button>
                            </div>
                            <div className="transactions-list">
                                {transactions.length === 0 ? (
                                    <p className="no-transactions">Chưa có giao dịch nào</p>
                                ) : (
                                    transactions.map((tx, index) => (
                                        <div key={tx.transaction_id || index} className="transaction-item">
                                            <div className="transaction-info">
                                                <span className={`transaction-type ${tx.transaction_type?.includes('EARN') ? 'earn' : 'spend'}`}>
                                                    {tx.transaction_type?.includes('EARN') ? '+' : '-'}{Math.abs(tx.points)} điểm
                                                </span>
                                                <span className="transaction-desc">{tx.description}</span>
                                            </div>
                                            <span className="transaction-date">
                                                {formatDate(tx.created_at)}
                                            </span>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    </div>
                )
            }
        </div >
    );
};

export default UserProfile;
