import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_ENDPOINTS, getAuthHeaders } from '../../../config/api.config';
import NotificationDropdown from '../../notifications/NotificationDropdown/NotificationDropdown';
import { useNotifications } from '../../../context/NotificationContext';

const NotificationBell = () => {
    const { unreadCount, setUnreadCount, refreshUnreadCount } = useNotifications();
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);

    const toggleDropdown = () => {
        if (!isDropdownOpen) {
            // Force refresh count when opening
            refreshUnreadCount();
        }
        setIsDropdownOpen(!isDropdownOpen);
    };

    const handleClose = () => {
        setIsDropdownOpen(false);
        refreshUnreadCount(); // Refresh count when closing
    };

    return (
        <div className="notification-bell-container">
            <button
                className="notification-bell"
                onClick={toggleDropdown}
                aria-label="Notifications"
            >
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                    <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                </svg>
                {unreadCount > 0 && (
                    <span className="notification-badge">{unreadCount > 99 ? '99+' : unreadCount}</span>
                )}
            </button>

            {isDropdownOpen && (
                <NotificationDropdown
                    onClose={handleClose}
                />
            )}
        </div>
    );
};

export default NotificationBell;
