import React, { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useCart } from './CartContext';
import '../../style/Cart.css';

const Cart = () => {
    const navigate = useNavigate();
    const {
        cartItems,
        loading,
        itemCount,
        totalAmount,
        updateQuantity,
        removeItem,
        clearCart,
        fetchCart
    } = useCart();

    // State for selected items
    const [selectedItems, setSelectedItems] = React.useState(new Set());
    const [hasInitialized, setHasInitialized] = React.useState(false);

    useEffect(() => {
        fetchCart();
    }, [fetchCart]);

    // Auto-select all items ONLY on initial load
    useEffect(() => {
        if (cartItems && cartItems.length > 0 && !hasInitialized) {
            const allItemIds = new Set(cartItems.map(item => item.cart_item_id || item.id));
            setSelectedItems(allItemIds);
            setHasInitialized(true);
        } else if (cartItems && cartItems.length === 0) {
            // Reset when cart is empty
            setSelectedItems(new Set());
            setHasInitialized(false);
        } else if (hasInitialized && cartItems && cartItems.length > 0) {
            // Clean up selectedItems: remove IDs that no longer exist in cart
            const currentItemIds = new Set(cartItems.map(item => item.cart_item_id || item.id));
            setSelectedItems(prevSelected => {
                const cleaned = new Set([...prevSelected].filter(id => currentItemIds.has(id)));
                return cleaned;
            });
        }
    }, [cartItems, hasInitialized]);

    // Handle select all toggle
    const handleSelectAll = () => {
        if (selectedItems.size === cartItems.length) {
            setSelectedItems(new Set());
        } else {
            const allItemIds = new Set(cartItems.map(item => item.cart_item_id || item.id));
            setSelectedItems(allItemIds);
        }
    };

    // Handle individual item selection
    const handleSelectItem = (itemId) => {
        const newSelected = new Set(selectedItems);
        if (newSelected.has(itemId)) {
            newSelected.delete(itemId);
        } else {
            newSelected.add(itemId);
        }
        setSelectedItems(newSelected);
    };

    const formatPrice = (price) => {
        return new Intl.NumberFormat('vi-VN', {
            style: 'currency',
            currency: 'VND'
        }).format(price);
    };

    // Safely parse price from item (handles string/number and different field names)
    const getItemPrice = (item) => {
        // Price is prioritized: sale_price > base_price
        const product = item.variant?.product || item.product;

        // Use the fields from the API: sale_price and base_price
        const priceValue = product?.sale_price || product?.base_price || 0;

        const numPrice = typeof priceValue === 'string' ? parseFloat(priceValue) : priceValue;
        return isNaN(numPrice) ? 0 : numPrice;
    };

    // Calculate total for selected items only
    const selectedTotal = cartItems
        .filter(item => selectedItems.has(item.cart_item_id || item.id))
        .reduce((sum, item) => sum + (getItemPrice(item) * item.quantity), 0);

    const selectedCount = selectedItems.size;

    const handleQuantityChange = async (itemId, newQuantity) => {
        if (newQuantity < 1) return;
        await updateQuantity(itemId, newQuantity);
    };

    const handleRemove = async (itemId) => {
        if (window.confirm('Bạn có chắc muốn xóa sản phẩm này?')) {
            await removeItem(itemId);
        }
    };

    const handleClearCart = async () => {
        if (window.confirm('Bạn có chắc muốn xóa toàn bộ giỏ hàng?')) {
            await clearCart();
        }
    };

    if (loading) {
        return (
            <div className="cart-page">
                <div className="cart-loading">
                    <div className="spinner"></div>
                    <p>Đang tải giỏ hàng...</p>
                </div>
            </div>
        );
    }

    if (!cartItems || cartItems.length === 0) {
        return (
            <div className="cart-page">
                <div className="cart-empty">
                    <h2>Giỏ hàng trống</h2>
                    <p>Bạn chưa có sản phẩm nào trong giỏ hàng</p>
                    <Link to="/product" className="continue-shopping-btn">
                        Tiếp tục mua sắm
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="cart-page">
            <div className="cart-container">
                {/* Header */}
                <div className="cart-header">
                    <div className="header-left">
                        <input
                            type="checkbox"
                            className="select-all-checkbox"
                            checked={selectedItems.size === cartItems.length && cartItems.length > 0}
                            onChange={handleSelectAll}
                        />
                        <h1>Giỏ hàng của bạn</h1>
                    </div>
                    <span className="cart-count">{itemCount} sản phẩm</span>
                </div>

                {/* Cart Items */}
                <div className="cart-content">
                    <div className="cart-items">
                        {cartItems.map((item) => {
                            const itemId = item.cart_item_id || item.id;
                            const isSelected = selectedItems.has(itemId);

                            return (
                                <div key={itemId} className={`cart-item ${isSelected ? 'selected' : ''}`}>
                                    <input
                                        type="checkbox"
                                        className="item-checkbox"
                                        checked={isSelected}
                                        onChange={() => handleSelectItem(itemId)}
                                    />
                                    <div className="item-image">
                                        <img
                                            src={item.product?.images?.[0]?.image_url || item.image_url || '/placeholder.jpg'}
                                            alt={item.product?.product_name || item.product_name}
                                        />
                                    </div>

                                    <div className="item-details">
                                        <h3 className="item-name">
                                            {item.product?.product_name || item.product_name}
                                        </h3>
                                        {item.variant && (
                                            <p className="item-variant">
                                                {item.variant.color?.name && `Màu: ${item.variant.color.name}`}
                                                {item.variant.color && typeof item.variant.color === 'string' && `Màu: ${item.variant.color}`}
                                                {item.variant.size?.name && ` | Size: ${item.variant.size.name}`}
                                                {item.variant.size && typeof item.variant.size === 'string' && ` | Size: ${item.variant.size}`}
                                            </p>
                                        )}
                                    </div>

                                    <p className="item-price">
                                        {formatPrice(getItemPrice(item))}
                                    </p>

                                    <div className="item-quantity">
                                        <button
                                            className="qty-btn"
                                            onClick={() => handleQuantityChange(item.cart_item_id || item.id, item.quantity - 1)}
                                            disabled={item.quantity <= 1}
                                        >
                                            −
                                        </button>
                                        <span className="qty-value">{item.quantity}</span>
                                        <button
                                            className="qty-btn"
                                            onClick={() => handleQuantityChange(item.cart_item_id || item.id, item.quantity + 1)}
                                        >
                                            +
                                        </button>
                                    </div>

                                    <div className="item-subtotal">
                                        {formatPrice(getItemPrice(item) * item.quantity)}
                                    </div>

                                    <button
                                        className="remove-btn"
                                        onClick={() => handleRemove(item.cart_item_id || item.id)}
                                        title="Xóa sản phẩm"
                                    >
                                        ✕
                                    </button>
                                </div>
                            );
                        })}
                    </div>

                    {/* Cart Summary */}
                    <div className="cart-summary">
                        <h3>Tổng đơn hàng</h3>

                        <div className="summary-row">
                            <span>Tạm tính ({selectedCount} sản phẩm đã chọn)</span>
                            <span>{formatPrice(selectedTotal)}</span>
                        </div>



                        <div className="summary-divider"></div>

                        <div className="summary-row total">
                            <span>Tổng cộng</span>
                            <span className="total-amount">{formatPrice(selectedTotal)}</span>
                        </div>

                        <button
                            className="checkout-btn"
                            onClick={() => {
                                const selectedCartItems = cartItems.filter(item =>
                                    selectedItems.has(item.cart_item_id || item.id)
                                );
                                navigate('/checkout', {
                                    state: {
                                        selectedItems: selectedCartItems,
                                        selectedTotal
                                    }
                                });
                            }}
                            disabled={selectedCount === 0}
                        >
                            Tiến hành thanh toán ({selectedCount})
                        </button>

                        <button
                            className="clear-cart-btn"
                            onClick={handleClearCart}
                        >
                            Xóa giỏ hàng
                        </button>

                        <Link to="/product" className="continue-link">
                            ← Tiếp tục mua sắm
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Cart;
