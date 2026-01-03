import React, { useState, useEffect } from 'react';
import logger from '../../utils/logger';
import { Link, useParams, useLocation } from 'react-router-dom';
import { API_ENDPOINTS } from '../../config/api.config';
import { authFetch } from '../../utils/authInterceptor';
// Xóa import CreateReturnModal cũ vì sẽ gộp trực tiếp vào đây
import '../../style/OrderTracking.css';
import '../../components/modals/CreateReturnModal/CreateReturnModal.css';

const OrderTracking = () => {
    const { orderId } = useParams(); // Get orderId from URL if viewing single order
    const location = useLocation(); // Track navigation changes
    const [orders, setOrders] = useState([]);
    const [selectedOrder, setSelectedOrder] = useState(null); // For detail view
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedStatus, setSelectedStatus] = useState('all');
    const [isReturnModalOpen, setIsReturnModalOpen] = useState(false);

    // --- State cho chức năng Trả hàng (Hợp nhất) ---
    const [selectedItems, setSelectedItems] = useState([]);
    const [returnReason, setReturnReason] = useState('');
    const [reasonDetails, setReasonDetails] = useState('');
    const [refundMethod, setRefundMethod] = useState('ORIGINAL_PAYMENT');
    const [notes, setNotes] = useState('');
    const [images, setImages] = useState([]);
    const [submittingReturn, setSubmittingReturn] = useState(false);

    // Order status mapping
    const statusConfig = {
        'PENDING': { label: 'Chờ xác nhận', color: '#ffc107', step: 1 },
        'CONFIRMED': { label: 'Đã xác nhận', color: '#17a2b8', step: 2 },
        'PROCESSING': { label: 'Đang xử lý', color: '#6f42c1', step: 2 },
        'AWAITING_SHIPMENT': { label: 'Chờ vận chuyển', color: '#fd7e14', step: 3 },
        'SHIPPED': { label: 'Đang vận chuyển', color: '#007bff', step: 4 },
        'DELIVERED': { label: 'Hoàn thành', color: '#28a745', step: 5 },
        'COMPLETED': { label: 'Đã hoàn thành', color: '#20c997', step: 6 },
        'RETURN_REQUESTED': { label: 'Hoàn trả', color: '#9b59b6', step: 0 },
        'CANCELLED': { label: 'Đã hủy', color: '#dc3545', step: 0 }
    };

    const returnReasons = [
        { value: '', label: '-- Chọn lý do --' },
        { value: 'DEFECTIVE', label: 'Sản phẩm bị lỗi/hỏng' },
        { value: 'WRONG_ITEM', label: 'Giao sai sản phẩm' },
        { value: 'NOT_AS_DESCRIBED', label: 'Không đúng mô tả' },
        { value: 'SIZE_ISSUE', label: 'Vấn đề về kích thước' },
        { value: 'CHANGED_MIND', label: 'Đổi ý không muốn mua' }
    ];

    const refundMethods = [
        { value: 'ORIGINAL_PAYMENT', label: 'Hoàn về phương thức thanh toán gốc' },
        { value: 'STORE_CREDIT', label: 'Hoàn bằng điểm tích lũy' },
        { value: 'BANK_TRANSFER', label: 'Chuyển khoản ngân hàng' }
    ];

    const conditionOptions = [
        { value: 'UNOPENED', label: 'Chưa mở hộp' },
        { value: 'USED', label: 'Đã sử dụng' },
        { value: 'DAMAGED', label: 'Bị hư hỏng' }
    ];

    // Force re-fetch on every navigation using location.key
    useEffect(() => {
        console.log('🔄 useEffect triggered - orderId:', orderId, 'location.key:', location.key);
        // Reset loading state when switching views
        setLoading(true);
        setOrders([]); // Clear old orders to prevent stale data display
        if (orderId) {
            fetchOrderDetail(orderId);
        } else {
            fetchOrders();
        }
    }, [orderId, location.key]); // Add location.key to force re-fetch on navigation

    // GIẢI PHÁP 2: Đảm bảo selectedOrder luôn đồng bộ với orders array
    useEffect(() => {
        if (orderId && orders.length > 0) {
            const updatedOrder = orders.find(o => Number(o.order_id) === Number(orderId));
            if (updatedOrder && selectedOrder) {
                // Chỉ update nếu status thực sự thay đổi
                if (updatedOrder.order_status !== selectedOrder.order_status) {
                    console.log('🔄 Syncing selectedOrder with orders array');
                    setSelectedOrder(prev => ({
                        ...prev,
                        order_status: updatedOrder.order_status
                    }));
                }
            }
        }
    }, [orders, orderId]); // Dependency: orders, orderId

    const fetchOrderDetail = async (id) => {
        const token = localStorage.getItem('authToken');
        if (!token) {
            setError('Vui lòng đăng nhập để xem đơn hàng');
            setLoading(false);
            return;
        }

        try {
            // Cache-busting để đảm bảo data mới nhất
            const url = `${API_ENDPOINTS.ORDERS.MY_ORDER_DETAIL(id)}?_t=${Date.now()}`;
            const response = await authFetch(url, {
                cache: 'no-store',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                }
            });

            if (response.ok) {
                const data = await response.json();
                setSelectedOrder(data);
            } else {
                setError('Không thể tải thông tin đơn hàng');
            }
        } catch (err) {
            logger.error('Error fetching order detail:', err);
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
            // Cache-busting để đảm bảo data mới nhất
            const url = `${API_ENDPOINTS.ORDERS.MY_ORDERS}?_t=${Date.now()}`;
            console.log('🌐 Fetching orders from URL:', url);

            const response = await authFetch(url, {
                cache: 'no-store',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                }
            });

            console.log('📡 Response status:', response.status, response.statusText);

            if (response.ok) {
                const data = await response.json();

                console.log('📦 Raw API response:', data);
                console.log('📦 Number of orders received:', Array.isArray(data) ? data.length : (data.items?.length || data.orders?.length || 'unknown'));

                // API trả về trực tiếp mảng đơn hàng (JSON Array)
                // Hoặc object có chứa items/orders/data (fallback)
                const ordersList = Array.isArray(data)
                    ? data
                    : (data.items || data.orders || data.data || []);

                console.log('📋 Parsed orders list:', ordersList);
                console.log('🔍 Order statuses:', ordersList.map(o => ({
                    order_number: o.order_number,
                    order_status: o.order_status,
                    order_id: o.order_id
                })));

                // GIẢI PHÁP 3: Chỉ update nếu data thực sự khác
                // Tránh ghi đè state mới (từ optimistic update) bằng stale data
                setOrders(prevOrders => {
                    // So sánh nhanh: số lượng khác hoặc data mới hơn
                    if (prevOrders.length !== ordersList.length) {
                        return ordersList;
                    }
                    // So sánh chi tiết status để tránh downgrade
                    const hasNewerData = ordersList.some((newOrder, idx) => {
                        const oldOrder = prevOrders.find(o => o.order_id === newOrder.order_id);
                        // Nếu API trả về status khác với local → cần check
                        if (oldOrder && oldOrder.order_status !== newOrder.order_status) {
                            // Nếu local đã CANCELLED nhưng API vẫn PENDING → giữ local
                            if (oldOrder.order_status === 'CANCELLED' && newOrder.order_status === 'PENDING') {
                                console.log('⚠️ Keeping local CANCELLED status, ignoring stale PENDING from API');
                                return false; // Không update
                            }
                        }
                        return true;
                    });
                    return hasNewerData ? ordersList : prevOrders;
                });
            } else {
                setError('Không thể tải đơn hàng');
            }
        } catch (err) {
            if (err.name === 'AbortError') {
                console.log('Fetch cancelled');
                return;
            }
            logger.error('Error fetching orders:', err);
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

    // --- Hàm xử lý Trả hàng (Hợp nhất từ CreateReturnModal) ---
    const getItemId = (item) => {
        // Luôn ưu tiên variant_id hoặc product_id từ dữ liệu gốc của đơn hàng
        return item.variant_id || item.product_id || item.order_item_id || item.id;
    };

    const handleItemToggle = (item) => {
        const uniqueId = getItemId(item);
        if (!uniqueId) {
            alert('Lỗi: Không tìm thấy ID sản phẩm');
            return;
        }

        setSelectedItems(prev => {
            const exists = prev.find(i => getItemId(i) === uniqueId);
            if (exists) {
                return prev.filter(i => getItemId(i) !== uniqueId);
            } else {
                return [...prev, {
                    ...item,
                    quantity: item.quantity,
                    condition: 'UNOPENED',
                    itemNotes: ''
                }];
            }
        });
    };

    const isItemSelected = (item) => {
        const uniqueId = getItemId(item);
        return selectedItems.some(i => getItemId(i) === uniqueId);
    };

    const handleConditionChange = (item, condition) => {
        const uniqueId = getItemId(item);
        setSelectedItems(prev => prev.map(i =>
            getItemId(i) === uniqueId ? { ...i, condition } : i
        ));
    };

    const handleItemNotesChange = (item, itemNotes) => {
        const uniqueId = getItemId(item);
        setSelectedItems(prev => prev.map(i =>
            getItemId(i) === uniqueId ? { ...i, itemNotes } : i
        ));
    };

    const handleImageUpload = (e) => {
        const files = Array.from(e.target.files);
        if (files.length + images.length > 5) {
            alert('Tối đa 5 ảnh');
            return;
        }
        const newImages = files.map(file => ({
            file,
            preview: URL.createObjectURL(file)
        }));
        setImages(prev => [...prev, ...newImages]);
    };

    const removeImage = (index) => {
        setImages(prev => {
            const newImages = [...prev];
            URL.revokeObjectURL(newImages[index].preview);
            newImages.splice(index, 1);
            return newImages;
        });
    };

    const calculateRefundAmount = () => {
        if (!selectedOrder || !selectedOrder.items || selectedItems.length === 0) return 0;
        return selectedItems.reduce((total, selectedItem) => {
            const orderItem = selectedOrder.items.find(i => getItemId(i) === getItemId(selectedItem));
            if (orderItem) {
                const price = parseFloat(orderItem.price) || (orderItem.subtotal / orderItem.quantity);
                return total + (price * selectedItem.quantity);
            }
            return total;
        }, 0);
    };

    // Helper: Lấy product_id từ product_name (vì API không trả variants trong list)
    const getProductIdFromName = async (productName) => {
        if (!productName) return null;
        try {
            const response = await fetch(`${API_ENDPOINTS.PRODUCTS.LIST}?page=1&page_size=100`);
            if (!response.ok) return null;
            const data = await response.json();

            const products = Array.isArray(data) ? data : (data.items || data.products || []);

            // Tìm product theo tên (case-insensitive)
            const product = products.find(p =>
                p.product_name === productName ||
                p.name === productName ||
                p.product_name?.toLowerCase() === productName.toLowerCase() ||
                p.name?.toLowerCase() === productName.toLowerCase()
            );

            return product ? (product.product_id || product.id) : null;
        } catch (error) {
            logger.error('Error fetching product_id:', error);
            return null;
        }
    };

    const handleReturnSubmit = async (e) => {
        e.preventDefault();

        if (selectedItems.length === 0) {
            alert('Vui lòng chọn ít nhất một sản phẩm để trả');
            return;
        }
        if (!returnReason) {
            alert('Vui lòng chọn lý do trả hàng');
            return;
        }
        if (!reasonDetails.trim()) {
            alert('Vui lòng nhập chi tiết lý do trả hàng');
            return;
        }

        setSubmittingReturn(true);

        try {
            // --- 1. Lấy IDs trực tiếp từ selectedOrder ---
            const userId = selectedOrder.user_id;
            const orderIdDb = selectedOrder.order_id;

            // --- 2. Xây dựng Payload theo Swagger API ---
            const payload = {
                order_id: parseInt(orderIdDb, 10),
                user_id: parseInt(userId, 10),
                return_reason: returnReason,
                reason_detail: reasonDetails,
                status: "PENDING",
                refund_amount: Math.round(calculateRefundAmount()),
                refund_method: refundMethod,
                images: [],
                items: [] // Will populate after fetching
            };

            // Fetch product_id cho tất cả items
            const itemsWithProductId = await Promise.all(
                selectedItems.map(async (item) => {
                    const productName = item.product_name || item.name || '';
                    const pId = await getProductIdFromName(productName);
                    const vId = item.variant_id || null;

                    return {
                        product_id: parseInt(pId || 0, 10),
                        variant_id: vId ? parseInt(vId, 10) : null,
                        quantity: parseInt(item.quantity, 10),
                        condition: item.condition || 'UNOPENED',
                        note: item.itemNotes || ""
                    };
                })
            );
            payload.items = itemsWithProductId;

            if (!userId || userId === 0) {
                alert('❌ Lỗi: Không tìm thấy user_id. Vui lòng đăng nhập lại.');
                setSubmittingReturn(false);
                return;
            }

            if (!orderIdDb || orderIdDb === 0) {
                alert('❌ Lỗi: Không tìm thấy order_id.');
                setSubmittingReturn(false);
                return;
            }

            const token = localStorage.getItem('authToken');
            const response = await authFetch(API_ENDPOINTS.RETURN_REFUNDS.CREATE, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            const responseData = await response.json();

            if (response.ok) {
                alert('Tạo yêu cầu trả hàng thành công!');
                closeReturnModal();
                if (orderIdDb) fetchOrderDetail(orderIdDb);
            } else {
                logger.error('❌ API Error:', {
                    status: response.status,
                    statusText: response.statusText,
                    data: responseData
                });
                alert(`Lỗi: ${responseData.detail || responseData.message || 'Không thể tạo yêu cầu trả hàng'}`);
            }
        } catch (err) {
            logger.error('Submit Error:', err);
            alert('Lỗi kết nối server');
        } finally {
            setSubmittingReturn(false);
        }
    };

    const closeReturnModal = () => {
        setIsReturnModalOpen(false);
        setSelectedItems([]);
        setReturnReason('');
        setReasonDetails('');
        setNotes('');
        setImages([]);
    };

    const handleCancelOrder = async (orderIdToCancel, paymentStatus) => {
        const isPaid = paymentStatus === 'COMPLETED';
        const confirmMessage = isPaid
            ? 'Đơn hàng này đã được thanh toán. Bạn có chắc chắn muốn hủy đơn hàng này không?'
            : 'Bạn có chắc chắn muốn hủy đơn hàng này?';

        if (!window.confirm(confirmMessage)) return;

        const token = localStorage.getItem('authToken');
        const cancelledId = Number(orderIdToCancel);

        try {
            console.log('🔄 Calling cancel API for order:', orderIdToCancel);

            const response = await authFetch(
                API_ENDPOINTS.ORDERS.CANCEL_ORDER(orderIdToCancel),
                {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` }
                }
            );

            console.log('📥 Cancel API response:', response.status);

            if (response.ok) {
                console.log('✅ Cancel successful, updating UI immediately...');

                // FIX 1: CẬP NHẬT STATE NGAY LẬP TỨC (Synchronous)

                // 1. Cập nhật selectedOrder (nếu đang xem chi tiết)
                if (orderId && selectedOrder && Number(selectedOrder.order_id) === cancelledId) {
                    setSelectedOrder(prev => ({
                        ...prev,
                        order_status: 'CANCELLED'
                    }));
                }

                // 2. Cập nhật orders array (QUAN TRỌNG - luôn cập nhật)
                setOrders(prevOrders => {
                    console.log('� Updating orders array...');
                    return prevOrders.map(order => {
                        if (Number(order.order_id) === cancelledId) {
                            console.log(`✅ Updated order ${order.order_number} to CANCELLED`);
                            return { ...order, order_status: 'CANCELLED' };
                        }
                        return order;
                    });
                });

                // FIX 2: HIỂN THỊ ALERT SAU KHI STATE ĐÃ CẬP NHẬT
                // requestAnimationFrame đảm bảo UI đã render trước khi alert block thread
                requestAnimationFrame(() => {
                    const message = isPaid
                        ? 'Hủy đơn hàng thành công! Bạn sẽ được hoàn tiền trong vòng 1 tuần.'
                        : 'Đã hủy đơn hàng thành công!';
                    alert(message);
                });

                // FIX 3: KHÔNG FETCH LẠI NGAY - Tránh ghi đè state bằng cached data
                // Optimistic update đã đủ, không cần fetch lại

            } else {
                // XỬ LÝ LỖI: Đơn hàng đã bị hủy từ trước
                const error = await response.json();
                const errorMessage = error.detail || 'Không thể hủy đơn hàng';

                console.log('❌ Cancel error:', errorMessage);

                // Nếu đơn hàng đã bị hủy → Cập nhật UI
                if (errorMessage.includes('CANCELLED') || errorMessage.includes('already cancelled')) {
                    console.log('⚠️ Order already cancelled, updating UI...');

                    // Cập nhật CẢ HAI state
                    if (orderId && selectedOrder && Number(selectedOrder.order_id) === cancelledId) {
                        setSelectedOrder(prev => ({ ...prev, order_status: 'CANCELLED' }));
                    }

                    setOrders(prevOrders =>
                        prevOrders.map(order =>
                            Number(order.order_id) === cancelledId
                                ? { ...order, order_status: 'CANCELLED' }
                                : order
                        )
                    );

                    requestAnimationFrame(() => {
                        alert('Đơn hàng này đã được hủy từ trước.');
                    });
                } else {
                    alert(errorMessage);
                }
            }

        } catch (err) {
            logger.error('Error cancelling order:', err);
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
                                <span className={`payment-badge ${selectedOrder.payment_status === 'PAID' ? 'paid' : 'unpaid'}`}>
                                    {selectedOrder.payment_status === 'PAID' ? 'Đã thanh toán' :
                                        selectedOrder.payment_status === 'PENDING' ? 'Chưa thanh toán' :
                                            selectedOrder.payment_status === 'PROCESSING' ? 'Đang xử lý' :
                                                selectedOrder.payment_status === 'FAILED' ? 'Thất bại' :
                                                    selectedOrder.payment_status === 'CANCELLED' ? 'Đã hủy' :
                                                        selectedOrder.payment_status === 'EXPIRED' ? 'Hết hạn' :
                                                            selectedOrder.payment_status === 'REFUNDED' ? 'Đã hoàn tiền' :
                                                                selectedOrder.payment_status === 'PARTIAL_REFUNDED' ? 'Hoàn một phần' :
                                                                    'Chưa thanh toán'}
                                </span>
                            </div>
                        </div>

                        {/* Progress Tracker */}
                        <div className="progress-tracker">
                            <div className="progress-steps">
                                {['Đặt hàng', 'Xác nhận', 'Chờ gửi', 'Đang giao', 'Hoàn thành', 'Đã hoàn thành'].map((step, index) => {
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

                        {/* Return Request Button */}
                        {(selectedOrder.order_status === 'COMPLETED' ||
                            selectedOrder.order_status === 'DELIVERED' ||
                            (selectedOrder.order_status === 'CANCELLED' &&
                                selectedOrder.payment_status === 'PAID')) &&
                            // Không hiện nếu đã có return request hoặc đã refund
                            selectedOrder.order_status !== 'RETURN_REQUESTED' &&
                            selectedOrder.order_status !== 'REFUNDED' &&
                            selectedOrder.order_status !== 'PARTIAL_REFUNDED' &&
                            selectedOrder.payment_status !== 'REFUNDED' &&
                            selectedOrder.payment_status !== 'PARTIAL_REFUNDED' && (
                                <div className="order-actions">
                                    <button
                                        className="btn-return-request"
                                        onClick={() => setIsReturnModalOpen(true)}
                                    >
                                        Yêu cầu trả hàng
                                    </button>
                                </div>
                            )}

                    </div>
                </div>

                {/* Hợp nhất CreateReturnModal trực tiếp vào đây */}
                {isReturnModalOpen && (
                    <div className="return-modal-overlay" onClick={closeReturnModal}>
                        <div className="return-modal-content" onClick={(e) => e.stopPropagation()}>
                            <div className="return-modal-header">
                                <h2>Tạo yêu cầu trả hàng</h2>
                                <button className="return-modal-close" onClick={closeReturnModal}>✕</button>
                            </div>

                            <form onSubmit={handleReturnSubmit} className="return-modal-body">
                                <div className="form-section">
                                    <div className="order-info-summary">
                                        <span>Đơn hàng: <strong>#{selectedOrder.order_number}</strong></span>
                                    </div>
                                </div>

                                <div className="form-section">
                                    <label className="form-label required">Chọn sản phẩm cần trả</label>
                                    <div className="items-grid">
                                        {(selectedOrder.items || []).map((item, index) => (
                                            <div
                                                key={index}
                                                className={`item-card ${isItemSelected(item) ? 'selected' : ''}`}
                                                onClick={() => handleItemToggle(item)}
                                            >
                                                <input
                                                    type="checkbox"
                                                    checked={isItemSelected(item)}
                                                    readOnly
                                                    className="item-checkbox"
                                                />
                                                <div className="item-details">
                                                    <span className="item-name">{item.product_name}</span>
                                                    {(item.color || item.size) && (
                                                        <span className="item-variant">
                                                            {item.color && `Màu: ${item.color}`}
                                                            {item.size && ` | Size: ${item.size}`}
                                                        </span>
                                                    )}
                                                    <span className="item-qty">Số lượng: {item.quantity}</span>
                                                    <span className="item-price">{formatPrice(item.price || item.subtotal / item.quantity)}</span>

                                                    {isItemSelected(item) && (
                                                        <div className="item-condition" onClick={(e) => e.stopPropagation()}>
                                                            <label>Tình trạng:</label>
                                                            <select
                                                                value={selectedItems.find(i => getItemId(i) === getItemId(item))?.condition || 'UNOPENED'}
                                                                onChange={(e) => handleConditionChange(item, e.target.value)}
                                                                className="condition-select"
                                                            >
                                                                {conditionOptions.map(opt => (
                                                                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                                                                ))}
                                                            </select>
                                                            <label style={{ marginTop: '8px' }}>Ghi chú cho sản phẩm này:</label>
                                                            <textarea
                                                                value={selectedItems.find(i => getItemId(i) === getItemId(item))?.itemNotes || ''}
                                                                onChange={(e) => handleItemNotesChange(item, e.target.value)}
                                                                className="form-textarea"
                                                                placeholder="Ghi chú riêng cho sản phẩm này..."
                                                                rows="2"
                                                                style={{ marginTop: '4px', fontSize: '3.5rem' }}
                                                            />
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                <div className="form-section">
                                    <label className="form-label required">Lý do trả hàng</label>
                                    <select
                                        value={returnReason}
                                        onChange={(e) => setReturnReason(e.target.value)}
                                        className="form-select"
                                        required
                                    >
                                        {returnReasons.map(reason => (
                                            <option key={reason.value} value={reason.value}>
                                                {reason.label}
                                            </option>
                                        ))}
                                    </select>
                                </div>

                                <div className="form-section">
                                    <label className="form-label required">Chi tiết lý do</label>
                                    <textarea
                                        value={reasonDetails}
                                        onChange={(e) => setReasonDetails(e.target.value)}
                                        className="form-textarea"
                                        placeholder="Vui lòng mô tả chi tiết lý do trả hàng..."
                                        rows="4"
                                        required
                                    />
                                </div>

                                <div className="form-section">
                                    <label className="form-label required">Phương thức hoàn tiền</label>
                                    <div className="refund-methods">
                                        {refundMethods.map(method => (
                                            <label key={method.value} className="radio-label">
                                                <input
                                                    type="radio"
                                                    name="refundMethod"
                                                    value={method.value}
                                                    checked={refundMethod === method.value}
                                                    onChange={(e) => setRefundMethod(e.target.value)}
                                                />
                                                <span>{method.label}</span>
                                            </label>
                                        ))}
                                    </div>
                                </div>

                                {/* Bổ sung Ghi chú */}
                                <div className="form-section">
                                    <label className="form-label">Ghi chú (tùy chọn)</label>
                                    <textarea
                                        value={notes}
                                        onChange={(e) => setNotes(e.target.value)}
                                        className="form-textarea"
                                        placeholder="Thêm ghi chú nếu cần..."
                                        rows="2"
                                    />
                                </div>

                                {/* Bổ sung Tải ảnh */}
                                <div className="form-section">
                                    <label className="form-label">Hình ảnh minh chứng (tối đa 5 ảnh)</label>
                                    <div className="image-upload-section">
                                        <input
                                            type="file"
                                            id="imageUploadUnified"
                                            multiple
                                            accept="image/*"
                                            onChange={handleImageUpload}
                                            style={{ display: 'none' }}
                                        />
                                        <label htmlFor="imageUploadUnified" className="upload-btn">
                                            Chọn ảnh
                                        </label>

                                        {images.length > 0 && (
                                            <div className="image-preview-grid">
                                                {images.map((img, index) => (
                                                    <div key={index} className="image-preview-item">
                                                        <img src={img.preview} alt={`Preview ${index + 1}`} />
                                                        <button
                                                            type="button"
                                                            className="remove-image-btn"
                                                            onClick={() => removeImage(index)}
                                                        >
                                                            ✕
                                                        </button>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>

                                <div className="form-section refund-summary">
                                    <div className="refund-amount-display">
                                        <span>Số tiền hoàn dự kiến:</span>
                                        <span className="amount">{formatPrice(calculateRefundAmount())}</span>
                                    </div>
                                </div>

                                <div className="form-actions">
                                    <button type="button" onClick={closeReturnModal} className="btn-cancel">
                                        Hủy
                                    </button>
                                    <button type="submit" className="btn-submit" disabled={submittingReturn}>
                                        {submittingReturn ? 'Đang xử lý...' : 'Tạo yêu cầu'}
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}
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
                                            {['Đặt hàng', 'Xác nhận', 'Chờ gửi', 'Đang giao', 'Hoàn thành', 'Đã nhận hàng'].map((step, index) => {
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
                                                    width: order.order_status === 'CANCELLED' ? '0%' : `${(statusInfo.step - 1) * 20}%`,
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
