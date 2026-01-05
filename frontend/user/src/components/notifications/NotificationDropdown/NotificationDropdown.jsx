import React, { useState, useEffect } from 'react';
import logger from '../../../utils/logger';
import axios from 'axios';
import { API_ENDPOINTS, getAuthHeaders } from '../../../config/api.config';
import NotificationPreferencesModal from '../../modals/NotificationPreferencesModal/NotificationPreferencesModal';
import { useNotifications } from '../../../context/NotificationContext';

const NotificationDropdown = ({ onClose }) => {
    const { setUnreadCount, refreshUnreadCount } = useNotifications();
    const [notifications, setNotifications] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showPreferences, setShowPreferences] = useState(false);

    useEffect(() => {
        fetchNotifications();
    }, []);

    const fetchNotifications = async () => {
        try {
            setLoading(true);
            const response = await axios.get(API_ENDPOINTS.NOTIFICATIONS.LIST, {
                headers: getAuthHeaders(),
                params: { limit: 10 }
            });
            logger.log('📥 Fetched notifications:', response.data);
            response.data.forEach(n => {
                logger.log(`Notification ${n.notification_id}: is_read=${n.is_read} (type: ${typeof n.is_read})`);
            });
            setNotifications(response.data);
        } catch (error) {
            logger.error('Error fetching notifications:', error);
        } finally {
            setLoading(false);
        }
    };

    const markAsRead = async (notificationId) => {
        try {
            logger.log('🔔 Marking notification as read:', notificationId);
            logger.log('API Endpoint:', API_ENDPOINTS.NOTIFICATIONS.MARK_READ(notificationId));

            const response = await axios.post(
                API_ENDPOINTS.NOTIFICATIONS.MARK_READ(notificationId),
                {},
                { headers: getAuthHeaders() }
            );

            logger.log('✅ Mark as read response:', response.data);

            // Update local state
            setNotifications(notifications.map(n =>
                n.notification_id === notificationId ? { ...n, is_read: true } : n
            ));

            // Update unread count
            const unreadCount = notifications.filter(n => !n.is_read && n.notification_id !== notificationId).length;
            setUnreadCount(unreadCount);

            logger.log('✅ Local state updated, new unread count:', unreadCount);
        } catch (error) {
            logger.error('❌ Error marking notification as read:', error);
            logger.error('❌ Error response:', error.response?.data);
        }
    };

    const markAllAsRead = async () => {
        try {
            await axios.post(
                API_ENDPOINTS.NOTIFICATIONS.MARK_ALL_READ,
                {},
                { headers: getAuthHeaders() }
            );

            setNotifications(notifications.map(n => ({ ...n, is_read: true })));
            setUnreadCount(0);
        } catch (error) {
            logger.error('Error marking all as read:', error);
        }
    };

    const deleteNotification = async (notificationId) => {
        try {
            logger.log('🗑️ Deleting notification:', notificationId);

            await axios.delete(
                API_ENDPOINTS.NOTIFICATIONS.DELETE(notificationId),
                { headers: getAuthHeaders() }
            );

            logger.log('✅ Delete successful');

            const updatedNotifications = notifications.filter(n => n.notification_id !== notificationId);
            setNotifications(updatedNotifications);

            // Force refresh from server để đồng bộ chính xác
            refreshUnreadCount();

            logger.log('✅ Badge refreshed immediately');
        } catch (error) {
            logger.error('❌ Error deleting notification:', error);
            logger.error('❌ Error response:', error.response?.data);
        }
    };

    const formatTime = (dateString) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Vừa xong';
        if (diffMins < 60) return `${diffMins} phút trước`;
        if (diffHours < 24) return `${diffHours} giờ trước`;
        if (diffDays < 7) return `${diffDays} ngày trước`;
        return date.toLocaleDateString('vi-VN');
    };

    return (
        <>
            <div className="notification-dropdown">
                <div className="notification-header">
                    <h3>Thông báo</h3>
                    <div className="notification-actions">
                        <button
                            className="settings-icon"
                            onClick={() => setShowPreferences(true)}
                            title="Cài đặt"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"></path>
                                <circle cx="12" cy="12" r="3"></circle>
                            </svg>
                        </button>
                        <button className="close-btn" onClick={onClose}>✕</button>
                    </div>
                </div>

                {notifications.length > 0 && (
                    <button className="mark-all-read-btn" onClick={markAllAsRead}>
                        Đánh dấu tất cả đã đọc
                    </button>
                )}

                <div className="notification-list">
                    {loading ? (
                        <div className="notification-loading">Đang tải...</div>
                    ) : notifications.length === 0 ? (
                        <div className="notification-empty">
                            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
                                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                                <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                            </svg>
                            <p>Không có thông báo mới</p>
                        </div>
                    ) : (
                        notifications.map((notification) => (
                            <div
                                key={notification.notification_id}
                                className={`notification-item ${!notification.is_read ? 'unread' : ''}`}
                                onClick={() => !notification.is_read && markAsRead(notification.notification_id)}
                            >
                                <div className="notification-content">
                                    <div className="notification-title">{notification.title}</div>
                                    <div className="notification-message">{notification.message}</div>
                                    <div className="notification-time">{formatTime(notification.created_at)}</div>
                                </div>
                                <button
                                    className="delete-btn"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        deleteNotification(notification.notification_id);
                                    }}
                                    title="Xóa"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <polyline points="3 6 5 6 21 6"></polyline>
                                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                    </svg>
                                </button>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {showPreferences && (
                <NotificationPreferencesModal onClose={() => setShowPreferences(false)} />
            )}
        </>
    );
};

export default NotificationDropdown;
