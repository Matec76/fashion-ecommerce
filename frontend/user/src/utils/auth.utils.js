// Authentication utility functions for JWT token management

/**
 * Save authentication tokens to localStorage
 */
export const saveAuthTokens = (accessToken, refreshToken) => {
    localStorage.setItem('authToken', accessToken);
    localStorage.setItem('refreshToken', refreshToken);
};

/**
 * Get access token from localStorage
 */
export const getAccessToken = () => {
    return localStorage.getItem('authToken');
};

/**
 * Get refresh token from localStorage
 */
export const getRefreshToken = () => {
    return localStorage.getItem('refreshToken');
};

/**
 * Clear all authentication tokens
 */
export const clearAuthTokens = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
};

/**
 * Check if user is authenticated
 */
export const isAuthenticated = () => {
    return !!getAccessToken();
};

/**
 * Save user data to localStorage
 */
export const saveUser = (user) => {
    localStorage.setItem('user', JSON.stringify(user));
};

/**
 * Get user data from localStorage
 */
export const getUser = () => {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
};

/**
 * Decode JWT token to get payload
 */
export const decodeToken = (token) => {
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(
            atob(base64)
                .split('')
                .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
                .join('')
        );
        return JSON.parse(jsonPayload);
    } catch (error) {
        console.error('Error decoding token:', error);
        return null;
    }
};

/**
 * Check if token is expired
 */
export const isTokenExpired = (token) => {
    const decoded = decodeToken(token);
    if (!decoded || !decoded.exp) return true;

    const currentTime = Date.now() / 1000;
    return decoded.exp < currentTime;
};

/**
 * Get user info from token
 */
export const getUserFromToken = (token) => {
    const decoded = decodeToken(token);
    return decoded ? {
        userId: decoded.sub,
        email: decoded.email,
        role: decoded.role,
        ...decoded
    } : null;
};
