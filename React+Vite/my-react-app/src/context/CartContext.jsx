import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import API_ENDPOINTS, { getAuthToken } from '../config/api.config';

const CartContext = createContext();

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
        const token = getAuthToken(); // Lấy token mới mỗi lần gọi
        if (!token) {
            setCartItems([]);
            setCartSummary({ total_items: 0, total_amount: 0 });
            return;
        }

        setLoading(true);
        try {
            const response = await fetch(API_ENDPOINTS.CART.GET, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const data = await response.json();
                setCartItems(data.items || data || []);
            }

            // Fetch summary
            const summaryRes = await fetch(API_ENDPOINTS.CART.SUMMARY, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (summaryRes.ok) {
                const summaryData = await summaryRes.json();
                setCartSummary(summaryData);
            }
        } catch (err) {
            console.error('Error fetching cart:', err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    // Thêm sản phẩm vào giỏ
    const addToCart = async (productId, quantity = 1, variantId = null) => {
        const token = getAuthToken(); // Lấy token mới mỗi lần gọi
        console.log('=== ADD TO CART DEBUG ===');
        console.log('Token:', token ? `${token.substring(0, 20)}...` : 'NO TOKEN');
        console.log('Product ID:', productId);
        console.log('Quantity:', quantity);
        console.log('Variant ID:', variantId);

        if (!token) {
            alert('Vui lòng đăng nhập để thêm vào giỏ hàng!');
            return false;
        }

        setLoading(true);
        try {
            // API yêu cầu variant_id, không phải product_id
            const body = {
                variant_id: variantId,
                quantity: quantity
            };

            console.log('Request URL:', API_ENDPOINTS.CART.ADD);
            console.log('Request Body:', body);

            const response = await fetch(API_ENDPOINTS.CART.ADD, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(body)
            });

            console.log('Response Status:', response.status);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Không thể thêm vào giỏ hàng');
            }

            await fetchCart(); // Refresh cart
            return true;
        } catch (err) {
            console.error('Error adding to cart:', err);
            alert(err.message);
            return false;
        } finally {
            setLoading(false);
        }
    };

    // Cập nhật số lượng
    const updateQuantity = async (cartItemId, quantity) => {
        const token = getAuthToken();
        if (!token) return false;

        setLoading(true);
        try {
            const response = await fetch(API_ENDPOINTS.CART.UPDATE(cartItemId), {
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
            const response = await fetch(API_ENDPOINTS.CART.REMOVE(cartItemId), {
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

    // Fetch cart khi component mount hoặc token thay đổi
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
