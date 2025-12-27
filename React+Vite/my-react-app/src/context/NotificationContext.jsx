import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import axios from 'axios';
import { API_ENDPOINTS, getAuthHeaders } from '../config/api.config';

const NotificationContext = createContext();

export const useNotifications = () => {
    const context = useContext(NotificationContext);
    if (!context) {
        throw new Error('useNotifications must be used within a NotificationProvider');
    }
    return context;
};

export const NotificationProvider = ({ children }) => {
    const [unreadCount, setUnreadCount] = useState(0);
    const [lastFetched, setLastFetched] = useState(0);

    const fetchUnreadCount = useCallback(async (force = false) => {
        const token = localStorage.getItem('authToken');
        if (!token) {
            setUnreadCount(0);
            return;
        }

        // Only fetch if forced or if 5 minutes has passed
        const now = Date.now();
        if (!force && now - lastFetched < 300000 && unreadCount !== 0) {
            return;
        }

        try {
            const response = await axios.get(API_ENDPOINTS.NOTIFICATIONS.UNREAD_COUNT, {
                headers: getAuthHeaders()
            });
            setUnreadCount(response.data.unread_count || 0);
            setLastFetched(now);
        } catch (error) {
            console.error('Error fetching unread count:', error);
        }
    }, [lastFetched, unreadCount]);

    useEffect(() => {
        fetchUnreadCount();

        // Auto-refresh every 5 minutes instead of 2 minutes to reduce load
        const interval = setInterval(() => fetchUnreadCount(true), 300000);
        return () => clearInterval(interval);
    }, [fetchUnreadCount]);

    const value = {
        unreadCount,
        setUnreadCount,
        refreshUnreadCount: () => fetchUnreadCount(true)
    };

    return (
        <NotificationContext.Provider value={value}>
            {children}
        </NotificationContext.Provider>
    );
};
