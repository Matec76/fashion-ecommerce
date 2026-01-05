/**
 * Authentication Interceptor
 * Wraps fetch to handle session expiry globally
 */

/**
 * Authenticated fetch wrapper that handles token expiry
 * @param {string} url - The URL to fetch
 * @param {RequestInit} options - Fetch options
 * @returns {Promise<Response>} - The fetch response
 */
export const authFetch = async (url, options = {}) => {
    try {
        const response = await fetch(url, options);

        // Check for authentication errors (401 Unauthorized or 403 Forbidden)
        if (response.status === 401 || response.status === 403) {
            // Show alert
            alert('Hết phiên đăng nhập');

            // Clear authentication data
            localStorage.removeItem('authToken');
            localStorage.removeItem('user');

            // Redirect to login
            window.location.href = '/login';

            // Throw to prevent further processing
            throw new Error('Session expired');
        }

        return response;
    } catch (error) {
        // If it's a network error or other fetch error, rethrow
        if (error.message !== 'Session expired') {
            throw error;
        }
        // For session expired, we already handled it, just rethrow
        throw error;
    }
};

/**
 * Helper to get auth headers
 * @returns {Object} Headers object with Authorization if token exists
 */
export const getAuthHeaders = () => {
    const token = localStorage.getItem('authToken');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
};
