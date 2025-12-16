import React, { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useCart } from '../context/useCart';
import './style/Cart.css';

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

    useEffect(() => {
        fetchCart();
    }, [fetchCart]);

    const formatPrice = (price) => {
        return new Intl.NumberFormat('vi-VN', {
            style: 'currency',
            currency: 'VND'
        }).format(price);
    };

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
                    <div className="empty-icon">🛒</div>
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
                    <h1>Giỏ hàng của bạn</h1>
                    <span className="cart-count">{itemCount} sản phẩm</span>
                </div>

                {/* Cart Items */}
                <div className="cart-content">
                    <div className="cart-items">
                        {cartItems.map((item) => (
                            <div key={item.cart_item_id || item.id} className="cart-item">
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
                                            {item.variant.color && `Màu: ${item.variant.color}`}
                                            {item.variant.size && ` | Size: ${item.variant.size}`}
                                        </p>
                                    )}
                                    <p className="item-price">
                                        {formatPrice(item.unit_price || item.price)}
                                    </p>
                                </div>

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
                                    {formatPrice((item.unit_price || item.price) * item.quantity)}
                                </div>

                                <button
                                    className="remove-btn"
                                    onClick={() => handleRemove(item.cart_item_id || item.id)}
                                    title="Xóa sản phẩm"
                                >
                                    ✕
                                </button>
                            </div>
                        ))}
                    </div>

                    {/* Cart Summary */}
                    <div className="cart-summary">
                        <h3>Tổng đơn hàng</h3>

                        <div className="summary-row">
                            <span>Tạm tính ({itemCount} sản phẩm)</span>
                            <span>{formatPrice(totalAmount)}</span>
                        </div>

                        <div className="summary-row">
                            <span>Phí vận chuyển</span>
                            <span className="free-shipping">Miễn phí</span>
                        </div>

                        <div className="summary-divider"></div>

                        <div className="summary-row total">
                            <span>Tổng cộng</span>
                            <span className="total-amount">{formatPrice(totalAmount)}</span>
                        </div>

                        <button
                            className="checkout-btn"
                            onClick={() => navigate('/checkout')}
                        >
                            Tiến hành thanh toán
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
