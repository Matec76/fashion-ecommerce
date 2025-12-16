
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const API_CONFIG = {
    BASE_URL: API_BASE_URL,
    VERSION: 'v1',
    FULL_URL: API_BASE_URL,
};

export const API_ENDPOINTS = {
    // Authentication
    AUTH: {
        LOGIN: `${API_BASE_URL}/auth/login`,
        REGISTER: `${API_BASE_URL}/auth/register`,
        LOGOUT: `${API_BASE_URL}/auth/logout`,
        REFRESH: `${API_BASE_URL}/auth/refresh`,
        ME: `${API_BASE_URL}/users/me`,
    },

    // Products
    PRODUCTS: {
        LIST: `${API_BASE_URL}/products`,
        DETAIL: (id) => `${API_BASE_URL}/products/${id}`,
        BY_SLUG: (slug) => `${API_BASE_URL}/products/slug/${slug}`,
        SEARCH: `${API_BASE_URL}/products/search`,
        BY_CATEGORY: (categoryId) => `${API_BASE_URL}/products?category_id=${categoryId}`,
        IMAGES: (productId) => `${API_BASE_URL}/products/${productId}/images`,
        VARIANTS: (productId) => `${API_BASE_URL}/products/${productId}/variants`,
        RELATED: (productId) => `${API_BASE_URL}/products/${productId}/related`,
        FEATURED: `${API_BASE_URL}/products/featured`,
        NEW_ARRIVALS: `${API_BASE_URL}/products/new-arrivals`,
        BEST_SELLERS: `${API_BASE_URL}/products/best-sellers`,
    },

    // Categories
    CATEGORIES: {
        LIST: `${API_BASE_URL}/categories`,
        TREE: `${API_BASE_URL}/categories/tree`,
        DETAIL: (id) => `${API_BASE_URL}/categories/${id}`,
    },

    // Users
    USERS: {
        ME: `${API_BASE_URL}/users/me`,
        UPDATE: `${API_BASE_URL}/users/me`,
    },

    // Cart
    CART: {
        GET: `${API_BASE_URL}/cart/me`,
        SUMMARY: `${API_BASE_URL}/cart/summary`,
        ADD: `${API_BASE_URL}/cart/items`,
        UPDATE: (itemId) => `${API_BASE_URL}/cart/items/${itemId}`,
        REMOVE: (itemId) => `${API_BASE_URL}/cart/items/${itemId}`,
        CLEAR: `${API_BASE_URL}/cart/clear`,
    },

    // Orders
    ORDERS: {
        LIST: `${API_BASE_URL}/orders`,
        CREATE: `${API_BASE_URL}/orders`,
        DETAIL: (id) => `${API_BASE_URL}/orders/${id}`,
    },

    // Wishlist
    WISHLIST: {
        GET: `${API_BASE_URL}/wishlist`,
        ADD: `${API_BASE_URL}/wishlist/items`,
        REMOVE: (itemId) => `${API_BASE_URL}/wishlist/items/${itemId}`,
    },

    // Reviews
    REVIEWS: {
        BY_PRODUCT: (productId) => `${API_BASE_URL}/reviews/products/${productId}`,
        SUMMARY: (productId) => `${API_BASE_URL}/reviews/products/${productId}/summary`,
        CREATE: `${API_BASE_URL}/reviews`,
    },
};

export const getAuthToken = () => {
    // Tương thích với cả 2 key (Login.jsx dùng 'accessToken', auth.utils.js dùng 'authToken')
    return localStorage.getItem('accessToken') || localStorage.getItem('authToken');
};


export const getAuthHeaders = () => {
    const token = getAuthToken();
    return token ? {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
    } : {
        'Content-Type': 'application/json',
    };
};

export default API_ENDPOINTS;