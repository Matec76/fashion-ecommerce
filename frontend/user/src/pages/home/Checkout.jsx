import React, { useState, useEffect } from 'react';
import logger from '../../utils/logger';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import '../../style/Checkout.css';
import '../../style/Loyalty.css';
import { API_ENDPOINTS, getAuthHeaders } from '../../config/api.config';
import { authFetch } from '../../utils/authInterceptor';
import CouponInput from '../../components/forms/CouponInput/CouponInput';
import VoucherPickerModal from '../../components/modals/VoucherPickerModal/VoucherPickerModal';
import { useCart } from './CartContext';

const Checkout = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { fetchCart } = useCart();

    const { selectedItems = [], selectedTotal = 0 } = location.state || {};

    // Redirect if no items selected
    useEffect(() => {
        if (!selectedItems || selectedItems.length === 0) {
            alert('Vui lòng chọn sản phẩm để thanh toán!');
            navigate('/cart');
        }
    }, [selectedItems, navigate]);

    const [formData, setFormData] = useState({
        fullName: '',
        phone: '',
        email: '',
        address: '',
        ward: '',
        city: '',
        notes: ''
    });

    const [paymentMethods, setPaymentMethods] = useState([]);
    const [selectedPaymentMethod, setSelectedPaymentMethod] = useState(null);
    const [loading, setLoading] = useState(false);
    const [processingFee, setProcessingFee] = useState(0);
    const [userData, setUserData] = useState(null);
    const [addresses, setAddresses] = useState([]);
    const [selectedShippingAddress, setSelectedShippingAddress] = useState(null);
    const [selectedBillingAddress, setSelectedBillingAddress] = useState(null);
    const [shippingMethods, setShippingMethods] = useState([]);
    const [selectedShippingMethod, setSelectedShippingMethod] = useState(null);
    const [shippingFee, setShippingFee] = useState(0);
    const [appliedCoupon, setAppliedCoupon] = useState(null);

    // Loyalty points states
    const [userPoints, setUserPoints] = useState(0);
    const [pointsToRedeem, setPointsToRedeem] = useState(0);
    const [pointsDiscount, setPointsDiscount] = useState(0);
    const [pointsApplied, setPointsApplied] = useState(false);

    //  Voucher picker modal state
    const [isVoucherModalOpen, setIsVoucherModalOpen] = useState(false);

    // Fetch user addresses
    useEffect(() => {
        const fetchAddresses = async () => {
            try {
                const token = localStorage.getItem('authToken');
                const response = await authFetch(API_ENDPOINTS.USERS.ADDRESSES, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (response.ok) {
                    const data = await response.json();
                    logger.log('Addresses fetched:', data);
                    setAddresses(data);

                    // Auto-select default address
                    const defaultAddress = data.find(addr => addr.is_default);
                    if (defaultAddress) {
                        setSelectedShippingAddress(defaultAddress.address_id);
                        setSelectedBillingAddress(defaultAddress.address_id);
                    } else if (data.length > 0) {
                        // If no default, select first address
                        setSelectedShippingAddress(data[0].address_id);
                        setSelectedBillingAddress(data[0].address_id);
                    }
                }
            } catch (error) {
                logger.error('Error fetching addresses:', error);
            }
        };

        fetchAddresses();
    }, []);

    // Fetch shipping methods
    useEffect(() => {
        const fetchShippingMethods = async () => {
            try {
                const token = localStorage.getItem('authToken');
                const response = await authFetch(API_ENDPOINTS.ORDERS.SHIPPING_METHODS, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (response.ok) {
                    const data = await response.json();
                    logger.log('Shipping methods:', data);
                    setShippingMethods(data);

                    // Auto-select first shipping method
                    if (data.length > 0) {
                        setSelectedShippingMethod(data[0].shipping_method_id);
                        setShippingFee(parseFloat(data[0].base_cost) || 0);
                    }
                }
            } catch (error) {
                logger.error('Error fetching shipping methods:', error);
            }
        };

        fetchShippingMethods();
    }, []);

    // Fetch payment methods
    useEffect(() => {
        const fetchPaymentMethods = async () => {
            try {
                const token = localStorage.getItem('authToken');
                const response = await authFetch(API_ENDPOINTS.PAYMENT.METHODS, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (response.ok) {
                    const responseData = await response.json();
                    // Backend returns { data: [...] } structure
                    const methods = responseData.data || responseData;
                    setPaymentMethods(methods);

                    logger.log('Payment methods:', methods);

                    // Auto-select first method
                    if (methods.length > 0) {
                        setSelectedPaymentMethod(methods[0].payment_method_id);
                        calculateFee(methods[0].payment_method_id);
                    }
                }
            } catch (error) {
                logger.error('Error fetching payment methods:', error);
            }
        };

        fetchPaymentMethods();
    }, []);

    // Fetch user loyalty points
    useEffect(() => {
        const fetchUserLoyalty = async () => {
            try {
                const token = localStorage.getItem('authToken');
                if (!token) return;

                const response = await authFetch(API_ENDPOINTS.LOYALTY.ME, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (response.ok) {
                    const data = await response.json();
                    setUserPoints(data.points_balance || 0);
                }
            } catch (error) {
                logger.error('Error fetching user loyalty:', error);
            }
        };

        fetchUserLoyalty();
    }, []);

    // Points rate: 10 points = 1,000 VND (adjust as needed)
    const POINTS_TO_VND_RATE = 100;

    const handlePointsChange = (e) => {
        const value = parseInt(e.target.value) || 0;
        const maxPoints = Math.min(userPoints, Math.floor(selectedTotal / POINTS_TO_VND_RATE));
        setPointsToRedeem(Math.min(Math.max(0, value), maxPoints));
    };

    const applyPoints = () => {
        if (pointsToRedeem <= 0) {
            alert('Vui lòng nhập số điểm muốn sử dụng!');
            return;
        }
        const discount = pointsToRedeem * POINTS_TO_VND_RATE;
        setPointsDiscount(discount);
        setPointsApplied(true);
    };

    const removePoints = () => {
        setPointsToRedeem(0);
        setPointsDiscount(0);
        setPointsApplied(false);
    };

    // Calculate processing fee when payment method changes
    const calculateFee = async (methodId) => {
        try {
            const token = localStorage.getItem('authToken');
            const response = await authFetch(
                API_ENDPOINTS.PAYMENT.CALCULATE_FEE(methodId, selectedTotal),
                {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                }
            );

            if (response.ok) {
                const data = await response.json();
                logger.log('Processing fee response:', data);
                setProcessingFee(parseFloat(data.processing_fee || data.fee || 0));
            } else {
                logger.warn('Could not calculate fee, using 0');
                setProcessingFee(0);
            }
        } catch (error) {
            logger.error('Error calculating fee:', error);
            setProcessingFee(0);
        }
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handlePaymentMethodChange = (methodId) => {
        setSelectedPaymentMethod(methodId);
        calculateFee(methodId);
    };

    const formatPrice = (price) => {
        return new Intl.NumberFormat('vi-VN', {
            style: 'currency',
            currency: 'VND'
        }).format(price);
    };

    const getItemPrice = (item) => {
        // Ưu tiên: sale_price > base_price
        const product = item.variant?.product || item.product;
        const priceValue = product?.sale_price || product?.base_price || 0;
        const numPrice = typeof priceValue === 'string' ? parseFloat(priceValue) : priceValue;
        return isNaN(numPrice) ? 0 : numPrice;
    };

    const handlePlaceOrder = async () => {
        // Validate required selections
        if (!selectedShippingAddress) {
            alert('Vui lòng chọn địa chỉ giao hàng!');
            return;
        }

        if (!selectedBillingAddress) {
            alert('Vui lòng chọn địa chỉ thanh toán!');
            return;
        }

        if (!selectedShippingMethod) {
            alert('Vui lòng chọn phương thức vận chuyển!');
            return;
        }

        if (!selectedPaymentMethod) {
            alert('Vui lòng chọn phương thức thanh toán!');
            return;
        }

        setLoading(true);

        try {
            const token = localStorage.getItem('authToken');

            // Create Order - Backend creates order AND payment transaction together
            const orderPayload = {
                shipping_address_id: selectedShippingAddress,
                billing_address_id: selectedBillingAddress,
                shipping_method_id: selectedShippingMethod,
                payment_method_id: selectedPaymentMethod,
                notes: formData.notes || "",
                coupon_code: appliedCoupon?.code || null,
                // Backend expects variant_ids, not cart_item_ids
                variant_ids: selectedItems.map(item => item.variant?.variant_id || item.variant_id)
            };

            logger.log('🛒 CHECKOUT DEBUG - Payload:', orderPayload);
            logger.log('📦 Selected Items:', selectedItems);
            logger.log('🔢 Variant IDs:', orderPayload.variant_ids);
            logger.log('📋 Full item details:', selectedItems.map(item => ({
                cart_item_id: item.cart_item_id,
                variant_id: item.variant?.variant_id || item.variant_id,
                quantity: item.quantity,
                product: item.product?.product_name
            })));

            const orderResponse = await authFetch(API_ENDPOINTS.ORDERS.CREATE, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(orderPayload)
            });

            if (!orderResponse.ok) {
                const errorData = await orderResponse.json();
                throw new Error(errorData.detail || 'Không thể tạo đơn hàng');
            }

            const responseData = await orderResponse.json();

            logger.log('Full order response:', responseData);

            // Backend returns: { order: {...}, payment: {...} }
            const order = responseData.order;
            const payment = responseData.payment;

            logger.log('Order data:', order);
            logger.log('Payment data:', payment);

            const orderId = order.order_id;

            // Try multiple possible locations for transaction_code
            let transactionCode = null;
            if (order.payment_transactions?.length > 0) {
                transactionCode = order.payment_transactions[0].transaction_code;
                logger.log('Found transaction_code in order.payment_transactions[0]:', transactionCode);
            } else if (payment.transaction_id) {
                transactionCode = String(payment.transaction_id);
                logger.log('Using payment.transaction_id as fallback:', transactionCode);
            } else {
                logger.error('No transaction_code found!');
            }

            const paymentUrl = payment.payment_url || order.payment_transactions?.[0]?.payment_url;
            const qrCode = payment.qr_code || order.payment_transactions?.[0]?.qr_code;

            logger.log('Transaction code:', transactionCode);
            logger.log('Payment URL:', paymentUrl);
            logger.log('QR Code:', qrCode ? 'Available' : 'Not available');

            // Check if payment method is COD (Cash on Delivery)
            const selectedMethod = paymentMethods.find(m => m.payment_method_id === selectedPaymentMethod);
            logger.log('Selected payment method:', selectedMethod);
            logger.log('Method name:', selectedMethod?.method_name);

            const isCOD = selectedMethod?.method_name?.toLowerCase().includes('cod') ||
                selectedMethod?.method_name?.toLowerCase().includes('nhận hàng') ||
                selectedMethod?.method_name?.toLowerCase().includes('nhan hang') ||
                selectedMethod?.method_name?.toLowerCase().includes('tiền mặt') ||
                selectedMethod?.method_name?.toLowerCase().includes('tien mat') ||
                selectedMethod?.method_name?.toLowerCase().includes('thanh toán khi') ||
                selectedMethod?.method_name?.toLowerCase().includes('thanh toan khi') ||
                selectedMethod?.method_name?.toLowerCase().includes('cash on delivery') ||
                selectedMethod?.payment_method_id === 1; // Thường COD có ID = 1

            logger.log('Is COD?', isCOD);

            if (isCOD) {
                // COD: Backend handles cart clearing, just sync frontend state
                await fetchCart();
                navigate('/payment/success', {
                    state: {
                        orderId,
                        orderNumber: order.order_number,
                        isCOD: true
                    }
                });
            } else {
                // Online payment: DON'T clear cart yet - will clear after payment success
                navigate('/payment-qr', {
                    state: {
                        orderId,
                        orderNumber: order.order_number,
                        transactionCode,
                        paymentUrl,
                        qrCode,
                        totalAmount: parseFloat(order.total_amount),
                        paymentInstructions: payment.payment_instructions || payment.message
                    }
                });
            }

        } catch (error) {
            logger.error('Error placing order:', error);
            alert(`Lỗi: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    const discountAmount = Number(appliedCoupon?.discount_amount) || 0;
    const totalDiscount = discountAmount + pointsDiscount;
    const taxAmount = Number(selectedTotal) * 0.1; // VAT 10%
    const finalTotal = Number(selectedTotal) + Number(shippingFee) + Number(processingFee) + taxAmount - totalDiscount;

    // Debug log
    logger.log('Price Debug:', {
        selectedTotal,
        shippingFee,
        processingFee,
        taxAmount,
        discountAmount,
        pointsDiscount,
        totalDiscount,
        finalTotal
    });

    return (
        <div className="checkout-page">
            <div className="checkout-container">
                <div className="checkout-content">
                    {/* Left: Address & Shipping Selection */}
                    <div className="checkout-form-section">
                        <h1>Thông tin giao hàng</h1>

                        {/* Address Selection */}
                        <div className="address-selection">
                            <h3>Địa chỉ giao hàng</h3>
                            {addresses.length === 0 ? (
                                <div className="no-address-warning">
                                    <p>⚠️ Bạn chưa có địa chỉ nào. Vui lòng thêm địa chỉ để tiếp tục.</p>
                                    <Link to="/profile" className="add-address-link">
                                        + Thêm địa chỉ mới
                                    </Link>
                                </div>
                            ) : (
                                <div className="address-list">
                                    {addresses.map(address => (
                                        <label
                                            key={address.address_id}
                                            className={`address-card ${selectedShippingAddress === address.address_id ? 'selected' : ''}`}
                                        >
                                            <input
                                                type="radio"
                                                name="shippingAddress"
                                                value={address.address_id}
                                                checked={selectedShippingAddress === address.address_id}
                                                onChange={() => setSelectedShippingAddress(address.address_id)}
                                            />
                                            <div className="address-info">
                                                <div className="address-header">
                                                    <strong>{address.recipient_name}</strong>
                                                    {address.is_default && <span className="default-badge">Mặc định</span>}
                                                </div>
                                                <p>{address.phone_number}</p>
                                                <p className="address-text">
                                                    {address.street_address}, {address.ward}, {address.city}
                                                </p>
                                            </div>
                                        </label>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Shipping Methods */}
                        <div className="shipping-methods-section">
                            <h3>Phương thức vận chuyển</h3>
                            {shippingMethods.length === 0 ? (
                                <p>Đang tải phương thức vận chuyển...</p>
                            ) : (
                                <div className="shipping-methods">
                                    {shippingMethods.map(method => (
                                        <label
                                            key={method.shipping_method_id}
                                            className={`shipping-method ${selectedShippingMethod === method.shipping_method_id ? 'selected' : ''}`}
                                        >
                                            <input
                                                type="radio"
                                                name="shippingMethod"
                                                value={method.shipping_method_id}
                                                checked={selectedShippingMethod === method.shipping_method_id}
                                                onChange={(e) => {
                                                    setSelectedShippingMethod(method.shipping_method_id);
                                                    setShippingFee(parseFloat(method.base_cost) || 0);
                                                }}
                                            />
                                            <div className="method-info">
                                                <div className="method-header">
                                                    <strong>{method.method_name}</strong>
                                                    <span className="method-price">{formatPrice(parseFloat(method.base_cost))}</span>
                                                </div>
                                                {method.description && <p className="method-desc">{method.description}</p>}
                                                {method.estimated_days && (
                                                    <p className="method-time">⏱ Dự kiến: {method.estimated_days}</p>
                                                )}
                                            </div>
                                        </label>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Notes */}
                        <div className="form-group">
                            <label>Ghi chú đơn hàng</label>
                            <textarea
                                name="notes"
                                value={formData.notes}
                                onChange={handleInputChange}
                                placeholder="Ghi chú về đơn hàng (tùy chọn)"
                                rows="3"
                            />
                        </div>

                        {/* Payment Methods */}
                        <div className="payment-methods-section">
                            <h2>Phương thức thanh toán</h2>
                            <div className="payment-methods">
                                {paymentMethods.map(method => (
                                    <label
                                        key={method.payment_method_id}
                                        className={`payment-method ${selectedPaymentMethod === method.payment_method_id ? 'selected' : ''}`}
                                    >
                                        <input
                                            type="radio"
                                            name="paymentMethod"
                                            value={method.payment_method_id}
                                            checked={selectedPaymentMethod === method.payment_method_id}
                                            onChange={() => handlePaymentMethodChange(method.payment_method_id)}
                                        />
                                        <div className="method-info">
                                            <span className="method-name">{method.method_name}</span>
                                            {method.description && (
                                                <span className="method-desc">{method.description}</span>
                                            )}
                                        </div>
                                    </label>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Right: Order Summary */}
                    <div className="order-summary-section">
                        <div className="order-summary-sticky">
                            <h2>Đơn hàng của bạn</h2>

                            <div className="summary-items">
                                {selectedItems.map((item, index) => (
                                    <div key={index} className="summary-item">
                                        <img
                                            src={item.product?.images?.[0]?.image_url || '/placeholder.jpg'}
                                            alt={item.product?.product_name}
                                        />
                                        <div className="item-info">
                                            <h4>{item.product?.product_name}</h4>
                                            <p>
                                                {item.variant?.color?.name && `Màu: ${item.variant.color.name}`}
                                                {item.variant?.size?.name && ` | Size: ${item.variant.size.name}`}
                                            </p>
                                            <p>Số lượng: {item.quantity}</p>
                                        </div>
                                        <div className="item-price">
                                            {formatPrice(getItemPrice(item) * item.quantity)}
                                        </div>
                                    </div>
                                ))}
                            </div>

                            <div className="summary-divider"></div>

                            {/* Coupon Input */}
                            <CouponInput
                                orderAmount={selectedTotal}
                                onApply={(couponData) => setAppliedCoupon(couponData)}
                                onRemove={() => setAppliedCoupon(null)}
                                appliedCoupon={appliedCoupon}
                                onOpenPicker={() => setIsVoucherModalOpen(true)}
                            />

                            {/* Voucher Picker Modal */}
                            <VoucherPickerModal
                                isOpen={isVoucherModalOpen}
                                onClose={() => setIsVoucherModalOpen(false)}
                                onSelectVoucher={(voucher) => setAppliedCoupon(voucher)}
                                orderAmount={selectedTotal}
                                currentCoupon={appliedCoupon}
                            />

                            {/* Points Redemption - Tạm ẩn
                            {userPoints > 0 && (
                                <div className="points-redemption-section">
                                    <h3>Đổi điểm thưởng</h3>
                                    <p className="points-available">
                                        Bạn có <strong>{userPoints.toLocaleString('vi-VN')}</strong> điểm
                                        (tối đa giảm {formatPrice(Math.min(userPoints * POINTS_TO_VND_RATE, selectedTotal))})
                                    </p>

                                    {!pointsApplied ? (
                                        <div className="points-input-row">
                                            <input
                                                type="number"
                                                className="points-input"
                                                value={pointsToRedeem || ''}
                                                onChange={handlePointsChange}
                                                placeholder="Nhập số điểm"
                                                min="0"
                                                max={Math.min(userPoints, Math.floor(selectedTotal / POINTS_TO_VND_RATE))}
                                            />
                                            <button
                                                className="apply-points-btn"
                                                onClick={applyPoints}
                                                disabled={pointsToRedeem <= 0}
                                            >
                                                Áp dụng
                                            </button>
                                        </div>
                                    ) : (
                                        <div className="points-applied">
                                            <span className="points-applied-text">
                                                ✓ Đã dùng {pointsToRedeem.toLocaleString('vi-VN')} điểm (-{formatPrice(pointsDiscount)})
                                            </span>
                                            <button
                                                className="remove-points-btn"
                                                onClick={removePoints}
                                            >
                                                Bỏ
                                            </button>
                                        </div>
                                    )}
                                </div>
                            )}
                            */}

                            <div className="summary-totals">
                                <div className="summary-row">
                                    <span>Tạm tính</span>
                                    <span>{formatPrice(selectedTotal)}</span>
                                </div>
                                <div className="summary-row">
                                    <span>Phí vận chuyển</span>
                                    <span>{shippingFee > 0 ? formatPrice(shippingFee) : 'Miễn phí'}</span>
                                </div>
                                <div className="summary-row">
                                    <span>Thuế VAT (10%)</span>
                                    <span>{formatPrice(taxAmount)}</span>
                                </div>
                                {processingFee > 0 && (
                                    <div className="summary-row">
                                        <span>Phí thanh toán</span>
                                        <span>{formatPrice(processingFee)}</span>
                                    </div>
                                )}
                                {appliedCoupon && (
                                    <div className="summary-row discount">
                                        <span>Giảm giá ({appliedCoupon.code})</span>
                                        <span className="discount-amount">-{formatPrice(discountAmount)}</span>
                                    </div>
                                )}
                                {pointsApplied && pointsDiscount > 0 && (
                                    <div className="summary-row discount">
                                        <span>Đổi điểm ({pointsToRedeem} điểm)</span>
                                        <span className="discount-amount">-{formatPrice(pointsDiscount)}</span>
                                    </div>
                                )}
                                <div className="summary-row total">
                                    <span>Tổng cộng</span>
                                    <span className="total-amount">{formatPrice(finalTotal)}</span>
                                </div>
                            </div>

                            <button
                                className="place-order-btn"
                                onClick={handlePlaceOrder}
                                disabled={loading}
                            >
                                {loading ? 'Đang xử lý...' : 'Đặt hàng'}
                            </button>
                        </div>
                    </div>
                </div >
            </div >
        </div >
    );
};

export default Checkout;
