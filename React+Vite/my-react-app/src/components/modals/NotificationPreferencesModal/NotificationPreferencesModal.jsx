import React, { useState, useEffect } from 'react';
import logger from '../../../utils/logger';
import axios from 'axios';
import { API_ENDPOINTS, getAuthHeaders } from '../../../config/api.config';

const NotificationPreferencesModal = ({ onClose }) => {
    const [preferences, setPreferences] = useState({
        email_notifications: false,
        push_notifications: false,
        order_updates: false,
        promotions: false,
        product_back_in_stock: false,
        new_arrivals: false,
        review_responses: false,
        system_announcements: false,
    });
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        fetchPreferences();
    }, []);

    const fetchPreferences = async () => {
        try {
            const response = await axios.get(API_ENDPOINTS.NOTIFICATIONS.PREFERENCES, {
                headers: getAuthHeaders()
            });
            setPreferences(response.data);
        } catch (error) {
            logger.error('Error fetching preferences:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleToggle = (key) => {
        setPreferences(prev => ({
            ...prev,
            [key]: !prev[key]
        }));
    };

    const handleSave = async () => {
        try {
            setSaving(true);
            await axios.patch(
                API_ENDPOINTS.NOTIFICATIONS.PREFERENCES,
                preferences,
                { headers: getAuthHeaders() }
            );
            alert('Đã lưu cài đặt thành công!');
            onClose();
        } catch (error) {
            logger.error('Error saving preferences:', error);
            alert('Lỗi khi lưu cài đặt. Vui lòng thử lại.');
        } finally {
            setSaving(false);
        }
    };

    const preferenceLabels = {
        email_notifications: 'Thông báo qua Email',
        push_notifications: 'Push Notifications',
        order_updates: 'Cập nhật đơn hàng',
        promotions: 'Khuyến mãi',
        product_back_in_stock: 'Sản phẩm mới nhập',
        new_arrivals: 'Sản phẩm mới',
        review_responses: 'Phản hồi đánh giá',
        system_announcements: 'Thông báo hệ thống',
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="preferences-modal" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>Cài đặt thông báo</h2>
                    <button className="close-btn" onClick={onClose}>✕</button>
                </div>

                <div className="modal-body">
                    {loading ? (
                        <div className="loading">Đang tải...</div>
                    ) : (
                        <div className="preferences-list">
                            {Object.keys(preferenceLabels).map((key) => (
                                <div key={key} className="preference-item">
                                    <label>
                                        <span>{preferenceLabels[key]}</span>
                                        <div className="toggle-switch">
                                            <input
                                                type="checkbox"
                                                checked={preferences[key]}
                                                onChange={() => handleToggle(key)}
                                            />
                                            <span className="slider"></span>
                                        </div>
                                    </label>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                <div className="modal-footer">
                    <button className="cancel-btn" onClick={onClose}>Hủy</button>
                    <button
                        className="save-btn"
                        onClick={handleSave}
                        disabled={saving}
                    >
                        {saving ? 'Đang lưu...' : 'Lưu thay đổi'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default NotificationPreferencesModal;
