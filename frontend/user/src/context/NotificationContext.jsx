import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import logger from '../utils/logger';
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

        // Only fetch if forced or if 1 minute has passed
        const now = Date.now();
        if (!force && now - lastFetched < 60000 && unreadCount !== 0) {
            return;
        }

        try {
            const response = await axios.get(API_ENDPOINTS.NOTIFICATIONS.UNREAD_COUNT, {
                headers: getAuthHeaders()
            });
            setUnreadCount(response.data.unread_count || 0);
            setLastFetched(now);
        } catch (error) {
            logger.error('Error fetching unread count:', error);
        }
    }, [lastFetched, unreadCount]);

    useEffect(() => {
        const token = localStorage.getItem('authToken');
        if (!token) {
            setUnreadCount(0);
            return;
        }

        // Initial fetch
        fetchUnreadCount();

        // Auto-refresh every 1 minute for faster notification updates
        const interval = setInterval(() => fetchUnreadCount(true), 60000);
        return () => clearInterval(interval);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []); // Empty dependencies - only run on mount

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
