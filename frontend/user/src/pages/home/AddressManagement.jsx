import React, { useState, useEffect } from 'react';
import logger from '../../utils/logger';
import { useNavigate } from 'react-router-dom';
import useMutation from '../../hooks/useMutation';
import usePatch from '../../hooks/usePatch';
import useDelete from '../../hooks/useDelete';
import { API_ENDPOINTS } from '../../config/api.config';
import '../../style/AddressManagement.css';

const AddressManagement = () => {
    const navigate = useNavigate();
    const [addresses, setAddresses] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [editingId, setEditingId] = useState(null);
    const [formData, setFormData] = useState({
        recipient_name: '',
        phone_number: '',
        street_address: '',
        ward: '',
        city: '',
        postal_code: '',
        is_default: false
    });

    const { mutate, loading: mutateLoading } = useMutation();
    const { patch, loading: patchLoading } = usePatch();
    const { remove, loading: deleteLoading } = useDelete();

    useEffect(() => {
        fetchAddresses();
    }, []);

    const fetchAddresses = async () => {
        try {
            const token = localStorage.getItem('authToken');
            const response = await fetch(API_ENDPOINTS.USERS.ADDRESSES, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.ok) {
                const data = await response.json();
                logger.log('📍 Addresses from API:', data);
                logger.log('📍 is_default values:', data.map(a => ({ id: a.address_id, is_default: a.is_default })));
                setAddresses(data);
            } else if (response.status === 401) {
                navigate('/login');
            }
        } catch (error) {
            logger.error('Error fetching addresses:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleInputChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        let result;
        if (editingId) {
            result = await patch(API_ENDPOINTS.USERS.ADDRESS_DETAIL(editingId), formData);
        } else {
            result = await mutate(API_ENDPOINTS.USERS.ADDRESSES, {
                method: 'POST',
                body: formData
            });
        }

        if (result.success) {
            await fetchAddresses();
            resetForm();
            alert(editingId ? 'Cập nhật địa chỉ thành công!' : 'Thêm địa chỉ thành công!');
        } else {
            alert(result.error || 'Không thể lưu địa chỉ!');
        }
    };

    const handleEdit = (address) => {
        setFormData({
            recipient_name: address.recipient_name || '',
            phone_number: address.phone_number || '',
            street_address: address.street_address || '',
            ward: address.ward || '',
            city: address.city || '',
            postal_code: address.postal_code || '',
            is_default: address.is_default || false
        });
        setEditingId(address.address_id);
        setShowForm(true);
    };

    const handleDelete = async (addressId) => {
        if (!window.confirm('Bạn có chắc muốn xóa địa chỉ này?')) return;

        const result = await remove(API_ENDPOINTS.USERS.ADDRESS_DETAIL(addressId));

        if (result.success) {
            await fetchAddresses();
            alert('Xóa địa chỉ thành công!');
        } else {
            alert(result.error || 'Không thể xóa địa chỉ!');
        }
    };

    const handleSetDefault = async (addressId) => {
        const result = await mutate(
            API_ENDPOINTS.USERS.SET_DEFAULT_ADDRESS(addressId),
            { method: 'POST' }
        );

        if (result.success) {
            // Small delay to allow backend database commit
            await new Promise(resolve => setTimeout(resolve, 300));
            // Refresh addresses list
            await fetchAddresses();
        } else {
            alert(result.error || 'Không thể đặt làm mặc định!');
        }
    };

    const resetForm = () => {
        setFormData({
            recipient_name: '',
            phone_number: '',
            street_address: '',
            ward: '',
            city: '',
            postal_code: '',
            is_default: false
        });
        setEditingId(null);
        setShowForm(false);
    };

    if (loading && addresses.length === 0) {
        return (
            <div className="address-loading">
                <div className="spinner"></div>
                <p>Đang tải địa chỉ...</p>
            </div>
        );
    }

    return (
        <div className="address-management-page">
            <div className="address-container">
                <div className="address-header">
                    <div>
                        <h1>Địa chỉ của tôi</h1>
                        <p>Quản lý địa chỉ giao hàng</p>
                    </div>
                    <button
                        className="add-address-btn"
                        onClick={() => {
                            resetForm();
                            setShowForm(true);
                        }}
                    >
                        + Thêm địa chỉ mới
                    </button>
                </div>

                {/* Address Form */}
                {showForm && (
                    <div className="address-form-card">
                        <div className="form-header">
                            <h2>{editingId ? 'Cập nhật địa chỉ' : 'Thêm địa chỉ mới'}</h2>
                            <button className="close-btn" onClick={resetForm}>✕</button>
                        </div>

                        <form onSubmit={handleSubmit}>
                            <div className="form-row">
                                <div className="form-group">
                                    <label>Họ và tên người nhận <span className="required">*</span></label>
                                    <input
                                        type="text"
                                        name="recipient_name"
                                        value={formData.recipient_name}
                                        onChange={handleInputChange}
                                        required
                                    />
                                </div>

                                <div className="form-group">
                                    <label>Số điện thoại <span className="required">*</span></label>
                                    <input
                                        type="tel"
                                        name="phone_number"
                                        value={formData.phone_number}
                                        onChange={handleInputChange}
                                        required
                                    />
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Địa chỉ <span className="required">*</span></label>
                                <input
                                    type="text"
                                    name="street_address"
                                    value={formData.street_address}
                                    onChange={handleInputChange}
                                    placeholder="Số nhà, tên đường"
                                    required
                                />
                            </div>

                            <div className="form-row">
                                <div className="form-group">
                                    <label>Phường/Xã</label>
                                    <input
                                        type="text"
                                        name="ward"
                                        value={formData.ward}
                                        onChange={handleInputChange}
                                    />
                                </div>

                                <div className="form-group">
                                    <label>Tỉnh/Thành phố <span className="required">*</span></label>
                                    <input
                                        type="text"
                                        name="city"
                                        value={formData.city}
                                        onChange={handleInputChange}
                                        required
                                    />
                                </div>

                                <div className="form-group">
                                    <label>Mã bưu chính</label>
                                    <input
                                        type="text"
                                        name="postal_code"
                                        value={formData.postal_code}
                                        onChange={handleInputChange}
                                    />
                                </div>
                            </div>



                            <div className="form-group checkbox-group">
                                <label>
                                    <input
                                        type="checkbox"
                                        name="is_default"
                                        checked={formData.is_default}
                                        onChange={handleInputChange}
                                    />
                                    Đặt làm địa chỉ mặc định
                                </label>
                            </div>

                            <div className="form-actions">
                                <button type="button" className="cancel-btn" onClick={resetForm}>
                                    Hủy
                                </button>
                                <button type="submit" className="save-btn" disabled={loading}>
                                    {loading ? 'Đang lưu...' : editingId ? 'Cập nhật' : 'Thêm địa chỉ'}
                                </button>
                            </div>
                        </form>
                    </div>
                )}

                {/* Address List */}
                <div className="address-list">
                    {addresses.length === 0 ? (
                        <div className="empty-state">
                            <h3>Chưa có địa chỉ nào</h3>
                            <p>Thêm địa chỉ giao hàng để thuận tiện cho việc đặt hàng</p>
                            <button
                                className="add-first-btn"
                                onClick={() => {
                                    resetForm();
                                    setShowForm(true);
                                }}
                            >
                                + Thêm địa chỉ đầu tiên
                            </button>
                        </div>
                    ) : (
                        addresses.map((address) => (
                            <div
                                key={address.address_id}
                                className={`address-card ${address.is_default ? 'default' : ''}`}
                            >
                                <div className="address-info">
                                    <div className="recipient-info">
                                        <h3>{address.recipient_name}</h3>
                                        <p className="phone">{address.phone_number}</p>
                                    </div>

                                    <div className="address-detail">
                                        <p>{address.street_address}</p>
                                        <p>
                                            {[address.ward, address.city]
                                                .filter(Boolean)
                                                .join(', ')}
                                        </p>
                                    </div>
                                </div>

                                <div className="address-actions">
                                    {address.is_default ? (
                                        <div className="default-badge">MẶC ĐỊNH</div>
                                    ) : (
                                        <button
                                            className="action-btn set-default"
                                            onClick={() => handleSetDefault(address.address_id)}
                                        >
                                            Đặt làm mặc định
                                        </button>
                                    )}
                                    <button
                                        className="action-btn edit"
                                        onClick={() => handleEdit(address)}
                                    >
                                        Sửa
                                    </button>
                                    <button
                                        className="action-btn delete"
                                        onClick={() => handleDelete(address.address_id)}
                                    >
                                        Xóa
                                    </button>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};

export default AddressManagement;
