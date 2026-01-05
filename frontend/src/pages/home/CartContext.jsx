import React, { createContext, useState, useEffect, useCallback, useContext } from 'react';
import logger from '../../utils/logger';
import { authFetch } from '../../utils/authInterceptor';
import { API_ENDPOINTS } from '../../config/api.config';

// Helper function to get auth token
const getAuthToken = () => {
    return localStorage.getItem('authToken');
};

const CartContext = createContext();

// Custom hook để sử dụng Cart Context
export const useCart = () => {
    const context = useContext(CartContext);
    if (!context) {
        throw new Error('useCart must be used within CartProvider');
    }
    return context;
};

export const CartProvider = ({ children }) => {
    const [cartItems, setCartItems] = useState([]);
    const [cartSummary, setCartSummary] = useState({ total_items: 0, total_amount: 0 });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Fetch cart từ API
    const fetchCart = useCallback(async () => {
        const token = getAuthToken();
        logger.log('fetchCart called, token:', token ? 'EXISTS' : 'MISSING');

        if (!token) {
            logger.warn('No auth token, setting empty cart');
            setCartItems([]);
            setCartSummary({ total_items: 0, total_amount: 0 });
            return;
        }

        setLoading(true);
        try {
            logger.log('Fetching cart from:', API_ENDPOINTS.CART.DETAIL);
            const response = await authFetch(API_ENDPOINTS.CART.DETAIL, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            logger.log('Cart response status:', response.status);

            if (response.ok) {
                const data = await response.json();
                logger.log('Cart data received:', data);
                logger.log('Cart items:', data.items);
                setCartItems(data.items || data || []);
            } else {
                logger.error('Cart fetch failed:', response.status);
            }

            // Fetch summary
            const summaryRes = await authFetch(API_ENDPOINTS.CART.SUMMARY, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (summaryRes.ok) {
                const summaryData = await summaryRes.json();
                logger.log('Cart summary:', summaryData);
                setCartSummary(summaryData);
            }
        } catch (err) {
            logger.error('Error fetching cart:', err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    // Thêm sản phẩm vào giỏ
    const addToCart = async (productId, quantity = 1, variantId = null) => {
        const token = getAuthToken();

        if (!token) {
            alert("Bạn cần đăng nhập để mua hàng!");
            window.location.href = '/login';
            return false;
        }

        if (!variantId) {
            logger.warn("Sản phẩm không có variant_id - sẽ sử dụng product_id");
        }

        try {
            const payload = variantId
                ? { variant_id: variantId, quantity }
                : { product_id: productId, quantity };

            logger.log("Đang gọi API:", API_ENDPOINTS.CART.ADD_ITEM);
            logger.log("Payload:", payload);

            const response = await authFetch(API_ENDPOINTS.CART.ADD_ITEM, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            if (response.status === 401) {
                logger.warn('401 Unauthorized for cart add');
                alert("Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại.");
                window.location.href = '/login';
                return false;
            }

            if (response.ok) {
                await fetchCart();
                alert("Thêm vào giỏ hàng thành công!");
                return true;
            } else {
                let message = "Lỗi không xác định";
                try {
                    const err = await response.json();
                    logger.error("Backend error response:", err);

                    if (typeof err.detail === 'string') {
                        message = err.detail;
                    } else if (Array.isArray(err.detail)) {
                        message = err.detail.map(e => `${e.loc?.join('→') || 'Field'}: ${e.msg}`).join(', ');
                    } else if (typeof err.detail === 'object') {
                        message = JSON.stringify(err.detail, null, 2);
                    } else {
                        message = err.message || JSON.stringify(err);
                    }
                } catch (e) {
                    message = `Lỗi Server (${response.status})`;
                }
                logger.error("Parsed error message:", message);
                alert(`Không thể thêm vào giỏ: ${message}`);
                return false;
            }
        } catch (error) {
            logger.error("Lỗi:", error);
            alert("Lỗi kết nối Server!");
            return false;
        }
    };

    // Cập nhật số lượng
    const updateQuantity = async (cartItemId, quantity) => {
        const token = getAuthToken();
        if (!token) return false;

        setLoading(true);
        try {
            const response = await authFetch(API_ENDPOINTS.CART.UPDATE_ITEM(cartItemId), {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ quantity })
            });

            if (!response.ok) {
                throw new Error('Không thể cập nhật số lượng');
            }

            await fetchCart();
            return true;
        } catch (err) {
            logger.error('Error updating quantity:', err);
            alert(err.message);
            return false;
        } finally {
            setLoading(false);
        }
    };

    // Xóa sản phẩm khỏi giỏ
    const removeItem = async (cartItemId) => {
        const token = getAuthToken();
        if (!token) return false;

        setLoading(true);
        try {
            const response = await authFetch(API_ENDPOINTS.CART.REMOVE_ITEM(cartItemId), {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!response.ok) {
                throw new Error('Không thể xóa sản phẩm');
            }

            await fetchCart();
            return true;
        } catch (err) {
            logger.error('Error removing item:', err);
            alert(err.message);
            return false;
        } finally {
            setLoading(false);
        }
    };

    // Xóa toàn bộ giỏ hàng
    const clearCart = async () => {
        const token = getAuthToken();
        if (!token) return false;

        setLoading(true);
        try {
            const response = await authFetch(API_ENDPOINTS.CART.CLEAR, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!response.ok) {
                throw new Error('Không thể xóa giỏ hàng');
            }

            setCartItems([]);
            setCartSummary({ total_items: 0, total_amount: 0 });
            return true;
        } catch (err) {
            logger.error('Error clearing cart:', err);
            alert(err.message);
            return false;
        } finally {
            setLoading(false);
        }
    };

    // Merge guest cart sau khi login
    const mergeGuestCart = async () => {
        const token = getAuthToken();
        const guestSessionId = localStorage.getItem('guestSessionId');

        // Nếu không có token hoặc không có guest session, bỏ qua
        if (!token || !guestSessionId) {
            return;
        }

        logger.log('Merging guest cart, session_id:', guestSessionId);

        try {
            const response = await authFetch(`${API_ENDPOINTS.CART.MERGE}?session_id=${guestSessionId}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                logger.log('Guest cart merged successfully:', data);

                // Xóa guest session sau khi merge thành công
                localStorage.removeItem('guestSessionId');

                // Refresh cart để hiển thị items mới
                await fetchCart();
            } else {
                logger.error('Failed to merge guest cart:', response.status);
            }
        } catch (err) {
            logger.error('Error merging guest cart:', err);
        }
    };

    // Fetch cart khi component mount và merge guest cart nếu cần
    useEffect(() => {
        const initCart = async () => {
            const token = getAuthToken();
            if (token) {
                // Nếu có token, thử merge guest cart trước
                await mergeGuestCart();
            }
            // Sau đó fetch cart
            await fetchCart();
        };
        initCart();
    }, [fetchCart]);

    const value = {
        cartItems,
        cartSummary,
        loading,
        error,
        itemCount: cartSummary.total_items || cartItems.length,
        totalAmount: cartSummary.total_amount || 0,
        addToCart,
        updateQuantity,
        removeItem,
        clearCart,
        fetchCart,
        mergeGuestCart
    };

    return (
        <CartContext.Provider value={value}>
            {children}
        </CartContext.Provider>
    );
};

export default CartContext;
