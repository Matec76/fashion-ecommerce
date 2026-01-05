// API utility functions for handling requests and responses

import { getAccessToken, getRefreshToken, saveAuthTokens, clearAuthTokens } from './auth.utils';
import { API_CONFIG } from '/src/config/api.config';

/**
 * Handle API response and normalize format
 */
export const handleApiResponse = async (response) => {
    const data = await response.json();

    if (!response.ok) {
        throw {
            status: response.status,
            message: data.detail || data.message || 'An error occurred',
            data: data
        };
    }

    return data;
};

/**
 * Handle API errors and format error messages
 */
export const handleApiError = (error) => {
    if (error.response) {
        // Server responded with error
        return {
            message: error.response.data?.detail || error.response.data?.message || 'Server error',
            status: error.response.status
        };
    } else if (error.request) {
        // Request made but no response
        return {
            message: 'No response from server. Please check your connection.',
            status: 0
        };
    } else {
        // Error in request setup
        return {
            message: error.message || 'An unexpected error occurred',
            status: -1
        };
    }
};

/**
 * Make authenticated API request with automatic token injection
 */
export const makeAuthenticatedRequest = async (url, options = {}) => {
    const token = getAccessToken();

    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(url, {
            ...options,
            headers,
        });

        // Handle 401 Unauthorized - token expired
        if (response.status === 401) {
            // Try to refresh token
            const refreshed = await refreshAccessToken();
            if (refreshed) {
                // Retry request with new token
                headers['Authorization'] = `Bearer ${getAccessToken()}`;
                const retryResponse = await fetch(url, {
                    ...options,
                    headers,
                });
                return handleApiResponse(retryResponse);
            } else {
                // Refresh failed, clear tokens and redirect to login
                clearAuthTokens();
                window.location.href = '/login';
                throw new Error('Session expired. Please login again.');
            }
        }

        return handleApiResponse(response);
    } catch (error) {
        throw handleApiError(error);
    }
};

/**
 * Refresh access token using refresh token
 */
export const refreshAccessToken = async () => {
    const refreshToken = getRefreshToken();

    if (!refreshToken) {
        return false;
    }

    try {
        const response = await fetch(`${API_CONFIG.FULL_URL}/auth/refresh`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refresh_token: refreshToken }),
        });

        if (response.ok) {
            const data = await response.json();
            saveAuthTokens(data.access_token, data.refresh_token);
            return true;
        }

        return false;
    } catch (error) {
        console.error('Token refresh failed:', error);
        return false;
    }
};

/**
 * Make API request (wrapper for fetch with error handling)
 */
export const apiRequest = async (url, options = {}) => {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        });

        return handleApiResponse(response);
    } catch (error) {
        throw handleApiError(error);
    }
};
