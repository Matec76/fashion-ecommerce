// 1. GẮN CỨNG URL (Sửa lỗi undefined)
// Dùng luôn chuỗi này, bỏ qua biến môi trường để chắc chắn chạy được
const API_BASE_URL = 'http://localhost:8000/api/v1';

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
        // Password management
        PASSWORD_RESET_REQUEST: `${API_BASE_URL}/auth/password-reset/request`,
        PASSWORD_RESET_CONFIRM: `${API_BASE_URL}/auth/password-reset/confirm`,
        PASSWORD_CHANGE: `${API_BASE_URL}/auth/password/change`,
        // Email verification
        VERIFY_EMAIL: `${API_BASE_URL}/auth/verify-email`,
        RESEND_VERIFICATION: `${API_BASE_URL}/auth/resend-verification`,
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
        AVATAR: `${API_BASE_URL}/users/me/avatar`,
        ADDRESSES: `${API_BASE_URL}/users/me/addresses`,
        ADDRESS_DETAIL: (addressId) => `${API_BASE_URL}/users/me/addresses/${addressId}`,
        SET_DEFAULT_ADDRESS: (addressId) => `${API_BASE_URL}/users/me/addresses/${addressId}/set-default`,
    },

    // Cart
    CART: {
        // Đặt cả 2 tên để tránh lỗi
        GET: `${API_BASE_URL}/cart/me`,
        DETAIL: `${API_BASE_URL}/cart/me`,

        SUMMARY: `${API_BASE_URL}/cart/summary`,

        // Đặt cả 2 tên ADD và ADD_ITEM
        ADD: `${API_BASE_URL}/cart/items`,
        ADD_ITEM: `${API_BASE_URL}/cart/items`,

        UPDATE: (itemId) => `${API_BASE_URL}/cart/items/${itemId}`,
        UPDATE_ITEM: (itemId) => `${API_BASE_URL}/cart/items/${itemId}`,

        REMOVE: (itemId) => `${API_BASE_URL}/cart/items/${itemId}`,
        REMOVE_ITEM: (itemId) => `${API_BASE_URL}/cart/items/${itemId}`,

        CLEAR: `${API_BASE_URL}/cart/clear`,

        // Merge guest cart (requires session_id as query param)
        MERGE: `${API_BASE_URL}/cart/merge`,
    },

    // Orders
    ORDERS: {
        LIST: `${API_BASE_URL}/orders`,
        CREATE: `${API_BASE_URL}/orders`,
        DETAIL: (id) => `${API_BASE_URL}/orders/${id}`,
        MY_ORDERS: `${API_BASE_URL}/orders/me`,
        SHIPPING_METHODS: `${API_BASE_URL}/orders/shipping-methods/all`,
        PAYOS_RETURN: `${API_BASE_URL}/orders/payment/payos/return`,

        // Payment & Order Management
        CONFIRM_COD: (orderId) => `${API_BASE_URL}/orders/${orderId}/payment/confirm-cod`,
        CANCEL_ORDER: (orderId) => `${API_BASE_URL}/orders/me/${orderId}/cancel`,
    },

    // Reviews
    REVIEWS: {
        BY_PRODUCT: (productId) => `${API_BASE_URL}/reviews/products/${productId}`,
        SUMMARY: (productId) => `${API_BASE_URL}/reviews/products/${productId}/summary`,
        CREATE: `${API_BASE_URL}/reviews`,
        DELETE: (reviewId) => `${API_BASE_URL}/reviews/${reviewId}`,
        HELPFUL: (reviewId) => `${API_BASE_URL}/reviews/${reviewId}/helpful`,
        MY_REVIEWS: `${API_BASE_URL}/reviews/me/reviews`,
    },

    // Questions (Q&A)
    QUESTIONS: {
        BY_PRODUCT: (productId) => `${API_BASE_URL}/reviews/products/${productId}/questions`,
        CREATE: `${API_BASE_URL}/reviews/questions`,
        DELETE: (questionId) => `${API_BASE_URL}/reviews/questions/${questionId}`,
    },

    // Payment
    PAYMENT: {
        METHODS: `${API_BASE_URL}/payment_methods`,
        VALIDATE: (methodId, amount) => `${API_BASE_URL}/payment_methods/validate?payment_method_id=${methodId}&order_amount=${amount}`,
        CALCULATE_FEE: (methodId, amount) => `${API_BASE_URL}/payment_methods/calculate-fee?payment_method_id=${methodId}&order_amount=${amount}`,

        TRANSACTIONS: {
            CREATE: `${API_BASE_URL}/payment/transactions`,
            RETRY: (transactionId) => `${API_BASE_URL}/payment/transactions/${transactionId}/retry`,
            GET: (transactionId) => `${API_BASE_URL}/payment/me/transactions/${transactionId}`,
            LIST: `${API_BASE_URL}/payment/me/transactions`,
        },

        PAYOS: {
            CHECK_STATUS: (transactionCode) => `${API_BASE_URL}/payment/payos/check-status/${transactionCode}`,
            WEBHOOK: `${API_BASE_URL}/payment/webhooks/payos`,
        },

        ORDER_TRANSACTIONS: (orderId) => `${API_BASE_URL}/payment/orders/${orderId}/transactions`,
    },
    // Coupons
    COUPONS: {
        PUBLIC: `${API_BASE_URL}/coupons/public`,
        VALIDATE: `${API_BASE_URL}/coupons/validate`,
        BY_CODE: (code) => `${API_BASE_URL}/coupons/code/${code}`,
        LIST: `${API_BASE_URL}/coupons`,
    },

    // Flash Sales
    FLASH_SALES: {
        ACTIVE: `${API_BASE_URL}/coupons/flash-sales/active`,
        UPCOMING: `${API_BASE_URL}/coupons/flash-sales/upcoming`,
        ALL: `${API_BASE_URL}/coupons/flash-sales/all`,
        DETAIL: (id) => `${API_BASE_URL}/coupons/flash-sales/${id}`,
        CHECK_PRODUCT: (productId) => `${API_BASE_URL}/coupons/flash-sales/product/${productId}/check`,
    },

    // Collections
    COLLECTIONS: {
        LIST: `${API_BASE_URL}/categories/collections/all`,
        DETAIL: (id) => `${API_BASE_URL}/categories/collections/${id}`,
        BY_SLUG: (slug) => `${API_BASE_URL}/categories/collections/slug/${slug}`,
    },

    // Attributes
    ATTRIBUTES: {
        COLORS: {
            LIST: `${API_BASE_URL}/attributes/colors`,
            DETAIL: (id) => `${API_BASE_URL}/attributes/colors/${id}`,
        },
        SIZES: {
            LIST: `${API_BASE_URL}/attributes/sizes`,
            DETAIL: (id) => `${API_BASE_URL}/attributes/sizes/${id}`,
        },
    },

    // Notifications
    NOTIFICATIONS: {
        LIST: `${API_BASE_URL}/notifications/me`,
        UNREAD_COUNT: `${API_BASE_URL}/notifications/me/unread-count`,
        MARK_READ: (id) => `${API_BASE_URL}/notifications/${id}/read`,
        MARK_ALL_READ: `${API_BASE_URL}/notifications/mark-all-read`,
        DELETE: (id) => `${API_BASE_URL}/notifications/${id}`,
        PREFERENCES: `${API_BASE_URL}/notifications/preferences`,
    },

    // Loyalty
    LOYALTY: {
        TIERS: `${API_BASE_URL}/loyalty/tiers`,
        ME: `${API_BASE_URL}/loyalty/me`,
        TRANSACTIONS: `${API_BASE_URL}/loyalty/transactions`,
        REDEEM: `${API_BASE_URL}/loyalty/redeem`,
        LEADERBOARD: `${API_BASE_URL}/loyalty/leaderboard`,
        REFERRALS: {
            MY_CODE: `${API_BASE_URL}/loyalty/referrals/my-code`,
            MY_REFERRALS: `${API_BASE_URL}/loyalty/referrals/my-referrals`,
            STATS: `${API_BASE_URL}/loyalty/referrals/stats`,
            APPLY: (code) => `${API_BASE_URL}/loyalty/referrals/apply?referral_code=${code}`,
        },
    },

    // Wishlist
    WISHLIST: {
        LIST: `${API_BASE_URL}/wishlist/me`,
        DEFAULT: `${API_BASE_URL}/wishlist/me/default`,
        CREATE: `${API_BASE_URL}/wishlist`,
        CHECK: (productId) => `${API_BASE_URL}/wishlist/check/${productId}`,
        DETAIL: (id) => `${API_BASE_URL}/wishlist/${id}`,
        UPDATE: (id) => `${API_BASE_URL}/wishlist/${id}`,
        DELETE: (id) => `${API_BASE_URL}/wishlist/${id}`,
        SET_DEFAULT: (id) => `${API_BASE_URL}/wishlist/${id}/set-default`,
        ADD_ITEM: (id) => `${API_BASE_URL}/wishlist/${id}/items`,
        ADD_TO_DEFAULT: `${API_BASE_URL}/wishlist/add-to-default`,
        UPDATE_ITEM: (itemId) => `${API_BASE_URL}/wishlist/items/${itemId}`,
        REMOVE_ITEM: (itemId) => `${API_BASE_URL}/wishlist/items/${itemId}`,
        MOVE_ITEM: (itemId) => `${API_BASE_URL}/wishlist/items/${itemId}/move`,
    },
};

export const getAuthToken = () => {
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