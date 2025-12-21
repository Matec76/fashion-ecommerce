import React, { createContext, useState, useEffect, useCallback, useContext } from 'react';

const API_BASE_URL = "http://localhost:8000/api/v1";

const API_ENDPOINTS = {
    CART: {
        DETAIL: `${API_BASE_URL}/cart/me`,
        SUMMARY: `${API_BASE_URL}/cart/summary`,
        ADD_ITEM: `${API_BASE_URL}/cart/items`,
        UPDATE_ITEM: (itemId) => `${API_BASE_URL}/cart/items/${itemId}`,
        REMOVE_ITEM: (itemId) => `${API_BASE_URL}/cart/items/${itemId}`,
        CLEAR: `${API_BASE_URL}/cart/clear`,
    }
};

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
        console.log('🛒 fetchCart called, token:', token ? 'EXISTS' : 'MISSING');

        if (!token) {
            console.warn('⚠️ No auth token, setting empty cart');
            setCartItems([]);
            setCartSummary({ total_items: 0, total_amount: 0 });
            return;
        }

        setLoading(true);
        try {
            console.log('📡 Fetching cart from:', API_ENDPOINTS.CART.DETAIL);
            const response = await fetch(API_ENDPOINTS.CART.DETAIL, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            console.log('📥 Cart response status:', response.status);

            if (response.ok) {
                const data = await response.json();
                console.log('✅ Cart data received:', data);
                console.log('📦 Cart items:', data.items);
                setCartItems(data.items || data || []);
            } else {
                console.error('❌ Cart fetch failed:', response.status);
            }

            // Fetch summary
            const summaryRes = await fetch(API_ENDPOINTS.CART.SUMMARY, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (summaryRes.ok) {
                const summaryData = await summaryRes.json();
                console.log('📊 Cart summary:', summaryData);
                setCartSummary(summaryData);
            }
        } catch (err) {
            console.error('💥 Error fetching cart:', err);
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
            console.warn("Sản phẩm không có variant_id - sẽ sử dụng product_id");
        }

        try {
            const payload = variantId
                ? { variant_id: variantId, quantity }
                : { product_id: productId, quantity };

            console.log("Đang gọi API:", API_ENDPOINTS.CART.ADD_ITEM);
            console.log("Payload:", payload);

            const response = await fetch(API_ENDPOINTS.CART.ADD_ITEM, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            if (response.status === 401) {
                alert("Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại.");
                localStorage.removeItem('authToken');
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
                    console.error("Backend error response:", err);

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
                console.error("Parsed error message:", message);
                alert(`Không thể thêm vào giỏ: ${message}`);
                return false;
            }
        } catch (error) {
            console.error("Lỗi:", error);
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
            const response = await fetch(API_ENDPOINTS.CART.UPDATE_ITEM(cartItemId), {
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
            console.error('Error updating quantity:', err);
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
            const response = await fetch(API_ENDPOINTS.CART.REMOVE_ITEM(cartItemId), {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!response.ok) {
                throw new Error('Không thể xóa sản phẩm');
            }

            await fetchCart();
            return true;
        } catch (err) {
            console.error('Error removing item:', err);
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
            const response = await fetch(API_ENDPOINTS.CART.CLEAR, {
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
            console.error('Error clearing cart:', err);
            alert(err.message);
            return false;
        } finally {
            setLoading(false);
        }
    };

    // Fetch cart khi component mount
    useEffect(() => {
        fetchCart();
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
        fetchCart
    };

    return (
        <CartContext.Provider value={value}>
            {children}
        </CartContext.Provider>
    );
};

export default CartContext;
