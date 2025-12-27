import React, { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import { API_ENDPOINTS } from '../../config/api.config';
import '../../style/OrderTracking.css';

const OrderTracking = () => {
    const { orderId } = useParams(); // Get orderId from URL if viewing single order
    const [orders, setOrders] = useState([]);
    const [selectedOrder, setSelectedOrder] = useState(null); // For detail view
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedStatus, setSelectedStatus] = useState('all');

    // Order status mapping
    const statusConfig = {
        'PENDING': {
            label: 'Chờ xác nhận',
            color: '#ffc107',
            step: 1
        },
        'CONFIRMED': {
            label: 'Đã xác nhận',
            color: '#17a2b8',
            step: 2
        },
        'PROCESSING': {
            label: 'Đang xử lý',
            color: '#6f42c1',
            step: 2
        },
        'AWAITING_SHIPMENT': {
            label: 'Chờ vận chuyển',
            color: '#fd7e14',
            step: 3
        },
        'SHIPPED': {
            label: 'Đang vận chuyển',
            color: '#007bff',
            step: 4
        },
        'DELIVERED': {
            label: 'Đã giao hàng',
            color: '#28a745',
            step: 5
        },
        'COMPLETED': {
            label: 'Hoàn thành',
            color: '#28a745',
            step: 5
        },
        'CANCELLED': {
            label: 'Đã hủy',
            color: '#dc3545',
            step: 0
        }
    };

    useEffect(() => {
        if (orderId) {
            fetchOrderDetail(orderId);
        } else {
            fetchOrders();
        }
    }, [orderId]);

    const fetchOrderDetail = async (id) => {
        const token = localStorage.getItem('authToken');
        if (!token) {
            setError('Vui lòng đăng nhập để xem đơn hàng');
            setLoading(false);
            return;
        }

        try {
            const response = await fetch(API_ENDPOINTS.ORDERS.MY_ORDER_DETAIL(id), {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.ok) {
                const data = await response.json();
                console.log('Order detail fetched:', data);
                setSelectedOrder(data);
            } else {
                setError('Không thể tải thông tin đơn hàng');
            }
        } catch (err) {
            console.error('Error fetching order detail:', err);
            setError('Lỗi kết nối server');
        } finally {
            setLoading(false);
        }
    };

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
            step: 0
        };
    };

    const handleCancelOrder = async (orderId, paymentStatus) => {
        // Different confirm message for paid orders
        const isPaid = paymentStatus === 'COMPLETED';
        const confirmMessage = isPaid
            ? 'Đơn hàng này đã được thanh toán. Bạn có chắc chắn muốn hủy đơn hàng này không?'
            : 'Bạn có chắc chắn muốn hủy đơn hàng này?';

        if (!window.confirm(confirmMessage)) {
            return;
        }

        const token = localStorage.getItem('authToken');
        try {
            const response = await fetch(API_ENDPOINTS.ORDERS.CANCEL_ORDER(orderId), {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                // Different success message for paid orders
                if (isPaid) {
                    alert('Hủy đơn hàng thành công! Bạn sẽ được hoàn tiền trong vòng 1 tuần.');
                } else {
                    alert('Đã hủy đơn hàng thành công!');
                }
                fetchOrders(); // Refresh orders
            } else {
                const error = await response.json();
                alert(error.detail || 'Không thể hủy đơn hàng');
            }
        } catch (err) {
            console.error('Error cancelling order:', err);
            alert('Lỗi kết nối server');
        }
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

    // Order Detail View
    if (orderId && selectedOrder) {
        const statusInfo = getStatusInfo(selectedOrder.order_status);
        return (
            <div className="order-tracking-page">
                <div className="order-tracking-container">
                    <div className="order-detail-header">
                        <Link to="/orders" className="back-btn">← Quay lại</Link>
                        <h1>Chi tiết đơn hàng</h1>
                    </div>

                    <div className="order-detail-card">
                        {/* Order Info */}
                        <div className="order-detail-info">
                            <div className="detail-row">
                                <span className="label">Mã đơn hàng:</span>
                                <span className="value">{selectedOrder.order_number}</span>
                            </div>
                            <div className="detail-row">
                                <span className="label">Ngày đặt:</span>
                                <span className="value">{formatDate(selectedOrder.created_at)}</span>
                            </div>
                            <div className="detail-row">
                                <span className="label">Trạng thái:</span>
                                <span className="status-badge" style={{
                                    backgroundColor: `${statusInfo.color}20`,
                                    color: statusInfo.color
                                }}>
                                    {statusInfo.label}
                                </span>
                            </div>
                            <div className="detail-row">
                                <span className="label">Thanh toán:</span>
                                <span className={`payment-badge ${selectedOrder.payment_status === 'COMPLETED' ? 'paid' : 'unpaid'}`}>
                                    {selectedOrder.payment_status === 'COMPLETED' ? 'Đã thanh toán' : 'Chưa thanh toán'}
                                </span>
                            </div>
                        </div>

                        {/* Progress Tracker */}
                        <div className="progress-tracker">
                            <div className="progress-steps">
                                {['Đặt hàng', 'Xác nhận', 'Chờ gửi', 'Đang giao', 'Hoàn thành'].map((step, index) => {
                                    const stepNum = index + 1;
                                    const isCompleted = statusInfo.step >= stepNum;
                                    const isCurrent = statusInfo.step === stepNum;
                                    const isCancelled = selectedOrder.order_status === 'CANCELLED';

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
                        </div>

                        {/* Shipping Address */}
                        {selectedOrder.shipping_snapshot && (
                            <div className="order-section">
                                <h3>Địa chỉ giao hàng</h3>
                                <p><strong>{selectedOrder.shipping_snapshot.recipient_name}</strong></p>
                                <p>{selectedOrder.shipping_snapshot.phone_number}</p>
                                <p>{selectedOrder.shipping_snapshot.street_address}, {selectedOrder.shipping_snapshot.ward}, {selectedOrder.shipping_snapshot.city}</p>
                            </div>
                        )}

                        {/* Order Items */}
                        <div className="order-section">
                            <h3>Sản phẩm</h3>
                            <div className="order-items-detail">
                                {(selectedOrder.items || []).map((item, index) => (
                                    <div key={index} className="order-item-detail">
                                        <div className="item-image">
                                            <img src={item.product_image || '/placeholder.jpg'} alt={item.product_name} />
                                        </div>
                                        <div className="item-info">
                                            <span className="item-name">{item.product_name}</span>
                                            <span className="item-variant">
                                                {item.color && `Màu: ${item.color}`}
                                                {item.size && ` | Size: ${item.size}`}
                                            </span>
                                            <span className="item-qty">Số lượng: {item.quantity}</span>
                                        </div>
                                        <div className="item-price">{formatPrice(item.price || item.subtotal / item.quantity)}</div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Order Summary */}
                        <div className="order-summary-detail">
                            <div className="summary-row">
                                <span>Tạm tính:</span>
                                <span>{formatPrice(selectedOrder.subtotal || selectedOrder.total_amount)}</span>
                            </div>
                            <div className="summary-row">
                                <span>Phí vận chuyển:</span>
                                <span>{formatPrice(selectedOrder.shipping_fee || 0)}</span>
                            </div>
                            {selectedOrder.discount_amount > 0 && (
                                <div className="summary-row discount">
                                    <span>Giảm giá:</span>
                                    <span>-{formatPrice(selectedOrder.discount_amount)}</span>
                                </div>
                            )}
                            <div className="summary-row total">
                                <span>Tổng cộng:</span>
                                <span className="total-amount">{formatPrice(selectedOrder.total_amount)}</span>
                            </div>
                        </div>


                    </div>
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
                                {config.label} ({count})
                            </button>
                        );
                    })}
                </div>

                {/* Orders List */}
                {filteredOrders.length === 0 ? (
                    <div className="no-orders">

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
                                        <div className="order-status-badges">
                                            {/* Payment Status */}
                                            <div
                                                className="payment-status-badge"
                                                style={{
                                                    backgroundColor: order.payment_status === 'COMPLETED' ? '#d4edda' : '#fff3cd',
                                                    color: order.payment_status === 'COMPLETED' ? '#28a745' : '#856404',
                                                    borderColor: order.payment_status === 'COMPLETED' ? '#28a745' : '#ffc107'
                                                }}
                                            >
                                                {order.payment_status === 'COMPLETED' ? 'Đã thanh toán' : 'Chưa thanh toán'}
                                            </div>
                                            {/* Order Status */}
                                            <div
                                                className="order-status"
                                                style={{
                                                    backgroundColor: `${statusInfo.color}20`,
                                                    color: statusInfo.color,
                                                    borderColor: statusInfo.color
                                                }}
                                            >
                                                {statusInfo.label}
                                            </div>
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
                                            {order.order_status === 'PENDING' && (
                                                <button
                                                    className="cancel-order-btn"
                                                    onClick={() => handleCancelOrder(order.order_id, order.payment_status)}
                                                >
                                                    Hủy đơn
                                                </button>
                                            )}
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
