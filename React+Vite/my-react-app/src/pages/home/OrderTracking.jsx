import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { API_ENDPOINTS } from '../../config/api.config';
import '../../style/OrderTracking.css';

const OrderTracking = () => {
    const [orders, setOrders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedStatus, setSelectedStatus] = useState('all');

    // Order status mapping
    const statusConfig = {
        'PENDING': {
            label: 'Chờ xác nhận',
            color: '#ffc107',
            icon: '⏳',
            step: 1
        },
        'CONFIRMED': {
            label: 'Đã xác nhận',
            color: '#17a2b8',
            icon: '✓',
            step: 2
        },
        'PROCESSING': {
            label: 'Đang xử lý',
            color: '#6f42c1',
            icon: '📦',
            step: 2
        },
        'AWAITING_SHIPMENT': {
            label: 'Chờ vận chuyển',
            color: '#fd7e14',
            icon: '📋',
            step: 3
        },
        'SHIPPED': {
            label: 'Đang vận chuyển',
            color: '#007bff',
            icon: '🚚',
            step: 4
        },
        'DELIVERED': {
            label: 'Đã giao hàng',
            color: '#28a745',
            icon: '✅',
            step: 5
        },
        'CANCELLED': {
            label: 'Đã hủy',
            color: '#dc3545',
            icon: '❌',
            step: 0
        }
    };

    useEffect(() => {
        fetchOrders();
    }, []);

    const fetchOrders = async () => {
        const token = localStorage.getItem('authToken');
        if (!token) {
            setError('Vui lòng đăng nhập để xem đơn hàng');
            setLoading(false);
            return;
        }

        try {
            const response = await fetch(API_ENDPOINTS.ORDERS.MY_ORDERS, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.ok) {
                const data = await response.json();
                console.log('Orders fetched:', data);
                // Handle both array and object with items property
                const ordersList = Array.isArray(data) ? data : (data.items || data.orders || []);
                setOrders(ordersList);
            } else {
                setError('Không thể tải đơn hàng');
            }
        } catch (err) {
            console.error('Error fetching orders:', err);
            setError('Lỗi kết nối server');
        } finally {
            setLoading(false);
        }
    };

    const formatPrice = (price) => {
        const numPrice = typeof price === 'string' ? parseFloat(price) : price;
        return new Intl.NumberFormat('vi-VN', {
            style: 'currency',
            currency: 'VND'
        }).format(numPrice);
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleDateString('vi-VN', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const getStatusInfo = (status) => {
        return statusConfig[status] || {
            label: status,
            color: '#6c757d',
            icon: '•',
            step: 0
        };
    };

    const filteredOrders = selectedStatus === 'all'
        ? orders
        : orders.filter(order => order.order_status === selectedStatus);

    if (loading) {
        return (
            <div className="order-tracking-page">
                <div className="loading-container">
                    <div className="spinner"></div>
                    <p>Đang tải đơn hàng...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="order-tracking-page">
                <div className="error-container">
                    <p>{error}</p>
                    <Link to="/login" className="login-btn">Đăng nhập</Link>
                </div>
            </div>
        );
    }

    return (
        <div className="order-tracking-page">
            <div className="order-tracking-container">
                <h1>Theo dõi đơn hàng</h1>

                {/* Status Filter */}
                <div className="status-filter">
                    <button
                        className={`filter-btn ${selectedStatus === 'all' ? 'active' : ''}`}
                        onClick={() => setSelectedStatus('all')}
                    >
                        Tất cả ({orders.length})
                    </button>
                    {Object.entries(statusConfig).map(([key, config]) => {
                        const count = orders.filter(o => o.order_status === key).length;
                        if (count === 0) return null;
                        return (
                            <button
                                key={key}
                                className={`filter-btn ${selectedStatus === key ? 'active' : ''}`}
                                onClick={() => setSelectedStatus(key)}
                                style={{ '--btn-color': config.color }}
                            >
                                {config.icon} {config.label} ({count})
                            </button>
                        );
                    })}
                </div>

                {/* Orders List */}
                {filteredOrders.length === 0 ? (
                    <div className="no-orders">
                        <div className="empty-icon">📦</div>
                        <p>Không có đơn hàng nào</p>
                        <Link to="/product" className="shop-btn">Mua sắm ngay</Link>
                    </div>
                ) : (
                    <div className="orders-list">
                        {filteredOrders.map(order => {
                            const statusInfo = getStatusInfo(order.order_status);
                            return (
                                <div key={order.order_id} className="order-card">
                                    {/* Order Header */}
                                    <div className="order-header">
                                        <div className="order-info">
                                            <span className="order-number">{order.order_number}</span>
                                            <span className="order-date">{formatDate(order.created_at)}</span>
                                        </div>
                                        <div
                                            className="order-status"
                                            style={{
                                                backgroundColor: `${statusInfo.color}20`,
                                                color: statusInfo.color,
                                                borderColor: statusInfo.color
                                            }}
                                        >
                                            {statusInfo.icon} {statusInfo.label}
                                        </div>
                                    </div>

                                    {/* Progress Tracker */}
                                    <div className="progress-tracker">
                                        <div className="progress-steps">
                                            {['Đặt hàng', 'Xác nhận', 'Chờ gửi', 'Đang giao', 'Hoàn thành'].map((step, index) => {
                                                const stepNum = index + 1;
                                                const isCompleted = statusInfo.step >= stepNum;
                                                const isCurrent = statusInfo.step === stepNum;
                                                const isCancelled = order.order_status === 'CANCELLED';

                                                return (
                                                    <div
                                                        key={index}
                                                        className={`progress-step ${isCompleted ? 'completed' : ''} ${isCurrent ? 'current' : ''} ${isCancelled ? 'cancelled' : ''}`}
                                                    >
                                                        <div className="step-dot">
                                                            {isCompleted ? '✓' : stepNum}
                                                        </div>
                                                        <span className="step-label">{step}</span>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                        <div className="progress-line">
                                            <div
                                                className="progress-fill"
                                                style={{
                                                    width: order.order_status === 'CANCELLED' ? '0%' : `${(statusInfo.step - 1) * 25}%`,
                                                    backgroundColor: statusInfo.color
                                                }}
                                            ></div>
                                        </div>
                                    </div>

                                    {/* Order Items */}
                                    <div className="order-items">
                                        {(order.items || []).slice(0, 2).map((item, index) => (
                                            <div key={index} className="order-item">
                                                <div className="item-info">
                                                    <span className="item-name">{item.product_name}</span>
                                                    <span className="item-variant">
                                                        {item.color && `${item.color}`}
                                                        {item.size && ` / Size ${item.size}`}
                                                    </span>
                                                </div>
                                                <div className="item-qty">x{item.quantity}</div>
                                                <div className="item-price">{formatPrice(item.subtotal)}</div>
                                            </div>
                                        ))}
                                        {(order.items || []).length > 2 && (
                                            <div className="more-items">
                                                +{order.items.length - 2} sản phẩm khác
                                            </div>
                                        )}
                                    </div>

                                    {/* Shipping Info */}
                                    {order.tracking_number && (
                                        <div className="shipping-info">
                                            <span className="shipping-label">Mã vận đơn:</span>
                                            <span className="tracking-number">{order.tracking_number}</span>
                                            {order.carrier && (
                                                <span className="carrier">({order.carrier})</span>
                                            )}
                                        </div>
                                    )}

                                    {/* Order Footer */}
                                    <div className="order-footer">
                                        <div className="order-total">
                                            <span>Tổng tiền:</span>
                                            <span className="total-amount">{formatPrice(order.total_amount)}</span>
                                        </div>
                                        <div className="order-actions">
                                            <Link
                                                to={`/order/${order.order_id}`}
                                                className="view-detail-btn"
                                            >
                                                Xem chi tiết
                                            </Link>
                                            {order.order_status === 'SHIPPED' && (
                                                <button className="confirm-delivery-btn">
                                                    Đã nhận hàng
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
};

export default OrderTracking;
