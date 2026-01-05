import React, { useState, useEffect } from 'react';
import logger from '../../utils/logger';
import { useNavigate } from 'react-router-dom';
import usePatch from '../../hooks/usePatch';
import { API_ENDPOINTS } from '../../config/api.config';
import '../../style/UserProfile.css';
import '../../style/Loyalty.css';

const UserProfile = () => {
    const navigate = useNavigate();
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [editing, setEditing] = useState(false);
    const [formData, setFormData] = useState({
        first_name: '',
        last_name: '',
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
    const [avatarUploading, setAvatarUploading] = useState(false);
    const [verificationSending, setVerificationSending] = useState(false);

    const { patch, loading: patchLoading } = usePatch();

    // Handle avatar upload
    const handleAvatarUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        // Validate file type
        if (!file.type.startsWith('image/')) {
            alert('Vui lòng chọn file ảnh!');
            return;
        }

        // Validate file size (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
            alert('Ảnh không được vượt quá 5MB!');
            return;
        }

        setAvatarUploading(true);

        try {
            const token = localStorage.getItem('authToken');
            const formData = new FormData();
            formData.append('file', file);

            // Upload to backend
            const uploadResponse = await fetch(API_ENDPOINTS.USERS.AVATAR, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });

            if (uploadResponse.ok) {
                const data = await uploadResponse.json();
                setUser(prev => ({ ...prev, avatar_url: data.avatar_url }));
                alert('Cập nhật ảnh đại diện thành công!');
            } else {
                const error = await uploadResponse.json();
                alert(error.detail || 'Không thể tải ảnh lên!');
            }
        } catch (error) {
            logger.error('Error uploading avatar:', error);
            alert('Có lỗi xảy ra khi tải ảnh!');
        } finally {
            setAvatarUploading(false);
        }
    };

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
            logger.error('Error fetching loyalty data:', error);
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
            logger.error('Error fetching referral code:', error);
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
            logger.error('Error fetching transactions:', error);
        }
    };

    const copyReferralCode = () => {
        navigator.clipboard.writeText(referralCode);
        alert('Đã sao chép mã giới thiệu!');
    };

    const handleResendVerification = async () => {
        setVerificationSending(true);
        try {
            const token = localStorage.getItem('authToken');
            const response = await fetch(API_ENDPOINTS.AUTH.RESEND_VERIFICATION, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                alert('Email xác thực đã được gửi! Vui lòng kiểm tra hộp thư của bạn.');
            } else {
                const error = await response.json();
                alert(error.detail || 'Không thể gửi email xác thực!');
            }
        } catch (error) {
            logger.error('Error sending verification:', error);
            alert('Có lỗi xảy ra khi gửi email xác thực!');
        } finally {
            setVerificationSending(false);
        }
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
            const response = await fetch(API_ENDPOINTS.USERS.ME, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.ok) {
                const data = await response.json();
                setUser(data);
                setFormData({
                    first_name: data.first_name || '',
                    last_name: data.last_name || '',
                    email: data.email || '',
                    phone_number: data.phone_number || '',
                    date_of_birth: data.date_of_birth || '',
                    gender: data.gender || ''
                });
            } else if (response.status === 401) {
                navigate('/login');
            }
        } catch (error) {
            logger.error('Error fetching user data:', error);
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

        const result = await patch(API_ENDPOINTS.USERS.UPDATE, formData);

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
            const response = await fetch(API_ENDPOINTS.USERS.ADDRESSES, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.ok) {
                const addresses = await response.json();
                const defaultAddr = addresses.find(addr => addr.is_default) || addresses[0];
                setDefaultAddress(defaultAddr);
            }
        } catch (error) {
            logger.error('Error fetching addresses:', error);
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
                        <div className="avatar-wrapper">
                            {user?.avatar_url ? (
                                <img
                                    src={user.avatar_url}
                                    alt="Avatar"
                                    className="avatar-image"
                                />
                            ) : (
                                <div className="avatar-circle">
                                    {user?.first_name?.charAt(0)?.toUpperCase() || user?.last_name?.charAt(0)?.toUpperCase() || 'U'}
                                </div>
                            )}
                            <label className="avatar-upload-btn" htmlFor="avatar-input">
                                {avatarUploading ? 'Đang tải...' : 'Chỉnh sửa'}
                            </label>
                            <input
                                type="file"
                                id="avatar-input"
                                accept="image/*"
                                onChange={handleAvatarUpload}
                                style={{ display: 'none' }}
                                disabled={avatarUploading}
                            />
                        </div>
                    </div>
                    <div className="profile-title">
                        <div className="profile-title-row">
                            <h1>Tài khoản của tôi</h1>
                            {user?.is_email_verified ? (
                                <span className="verification-badge verified">
                                    ✓ Đã xác thực
                                </span>
                            ) : (
                                <button
                                    className="verification-btn"
                                    onClick={handleResendVerification}
                                    disabled={verificationSending}
                                >
                                    {verificationSending ? 'Đang gửi...' : 'Xác thực ngay'}
                                </button>
                            )}
                        </div>
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
                                        <label>Họ</label>
                                        <input
                                            type="text"
                                            name="last_name"
                                            value={formData.last_name}
                                            onChange={handleInputChange}
                                            placeholder="Nguyễn"
                                        />
                                    </div>

                                    <div className="form-group">
                                        <label>Tên</label>
                                        <input
                                            type="text"
                                            name="first_name"
                                            value={formData.first_name}
                                            onChange={handleInputChange}
                                            placeholder="Văn A"
                                        />
                                    </div>
                                </div>

                                <div className="form-row">
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
                                    <span className="info-label">Họ và Tên</span>
                                    <span className="info-value">
                                        {user?.last_name || user?.first_name
                                            ? `${user?.last_name || ''} ${user?.first_name || ''}`.trim()
                                            : 'Chưa cập nhật'}
                                    </span>
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
                                                {defaultAddress.city}
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
