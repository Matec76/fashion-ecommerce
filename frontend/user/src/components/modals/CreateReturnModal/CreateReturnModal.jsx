import React, { useState } from 'react';
import logger from '../../../utils/logger';
import { API_ENDPOINTS } from '../../../config/api.config';
import './CreateReturnModal.css';

const CreateReturnModal = ({ isOpen, onClose, order, onSuccess }) => {
    const [selectedItems, setSelectedItems] = useState([]);
    const [returnReason, setReturnReason] = useState('');
    const [reasonDetails, setReasonDetails] = useState('');
    const [refundMethod, setRefundMethod] = useState('ORIGINAL_PAYMENT');
    const [notes, setNotes] = useState('');
    const [images, setImages] = useState([]);
    const [submitting, setSubmitting] = useState(false);

    if (!isOpen || !order) return null;

    const returnReasons = [
        { value: '', label: '-- Chọn lý do --' },
        { value: 'DEFECTIVE', label: 'Sản phẩm bị lỗi/hỏng' },
        { value: 'WRONG_ITEM', label: 'Giao sai sản phẩm' },
        { value: 'OTHER', label: 'Không đúng mô tả / Lý do khác' },
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

    const getItemId = (item) => {
        // Updated to handle cases where product_id is missing (e.g. only variant_id or order_item_id exists)
        const id = item.product_id || item.variant_id || item.order_item_id || item.id;
        if (!id) {
            logger.warn('Could not find any ID for item:', item);
        }
        return id;
    };

    const handleItemToggle = (item) => {
        const uniqueId = getItemId(item); // Use generic unique ID for selection state

        if (!uniqueId) {
            alert('Lỗi: Không tìm thấy ID sản phẩm');
            return;
        }

        setSelectedItems(prev => {
            // Check based on the same unique ID logic
            const exists = prev.find(i => getItemId(i) === uniqueId);
            if (exists) {
                return prev.filter(i => getItemId(i) !== uniqueId);
            } else {
                return [...prev, {
                    ...item, // Keep all item props
                    quantity: item.quantity,
                    condition: 'UNOPENED',
                    notes: ''
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
        if (!order.items || selectedItems.length === 0) return 0;

        return selectedItems.reduce((total, selectedItem) => {
            const orderItem = order.items.find(i => getItemId(i) === getItemId(selectedItem));
            if (orderItem) {
                // Use unit_price if available, fallback to subtotal/quantity
                const price = parseFloat(orderItem.unit_price) || (orderItem.price) || (orderItem.subtotal / orderItem.quantity);
                return total + (price * selectedItem.quantity);
            }
            return total;
        }, 0);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        // ... (validation checks same)
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

        setSubmitting(true);
        logger.log('Original order object:', order);

        const payload = {
            user_id: parseInt(order.user_id, 10),
            order_id: parseInt(order.order_id, 10),
            return_reason: returnReason,
            reason_detail: reasonDetails,
            status: 'PENDING',
            refund_amount: Math.round(calculateRefundAmount()),
            refund_method: refundMethod,
            images: [],
            items: selectedItems.map(item => ({
                product_id: (() => {
                    const pId = item.product_id || item.productId || (item.product && (item.product.id || item.product.product_id)) || item.id;
                    return pId ? parseInt(pId, 10) : 0;
                })(),
                variant_id: (() => {
                    const vId = item.variant_id || item.variantId || (item.variant && (item.variant.id || item.variant.variant_id)) || 0;
                    return vId ? parseInt(vId, 10) : 0;
                })(),
                quantity: parseInt(item.quantity, 10),
                condition: item.condition || 'UNOPENED',
                note: notes || "" // Use global notes
            }))
        };

        logger.log('Sending return request payload:', JSON.stringify(payload, null, 2));

        // ... (fetch logic)
        try {
            const token = localStorage.getItem('authToken');
            const response = await fetch(API_ENDPOINTS.RETURN_REFUNDS.CREATE, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                const data = await response.json();
                alert('Tạo yêu cầu trả hàng thành công!');
                if (onSuccess) onSuccess(data);
                handleClose();
            } else {
                const error = await response.json();
                logger.error("Return error:", error);
                const errorMessage = typeof error.detail === 'object'
                    ? JSON.stringify(error.detail)
                    : error.detail || 'Không thể tạo yêu cầu trả hàng';
                alert(`Lỗi: ${errorMessage}`);
            }
        } catch (err) {
            logger.error('Error creating return request:', err);
            alert('Lỗi kết nối server');
        } finally {
            setSubmitting(false);
        }
    };

    const handleClose = () => {
        setSelectedItems([]);
        setReturnReason('');
        setReasonDetails('');
        setRefundMethod('ORIGINAL_PAYMENT');
        setNotes('');
        setImages([]);
        setSubmitting(false);
        onClose();
    };

    const formatPrice = (price) => {
        return new Intl.NumberFormat('vi-VN', {
            style: 'currency',
            currency: 'VND'
        }).format(price);
    };

    return (
        <div className="return-modal-overlay" onClick={handleClose}>
            <div className="return-modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="return-modal-header">
                    <h2>Tạo yêu cầu trả hàng</h2>
                    <button className="return-modal-close" onClick={handleClose}>✕</button>
                </div>

                <form onSubmit={handleSubmit} className="return-modal-body">
                    {/* Order Info */}
                    <div className="form-section">
                        <div className="order-info-summary">
                            <span>Đơn hàng: <strong>#{order.order_number || order.order_id}</strong></span>
                        </div>
                    </div>

                    {/* Select Items */}
                    <div className="form-section">
                        <label className="form-label required">Chọn sản phẩm cần trả</label>
                        <div className="items-grid">
                            {(order.items || []).map((item, index) => (
                                <div
                                    key={index}
                                    className={`item-card ${isItemSelected(item) ? 'selected' : ''}`}
                                    onClick={() => handleItemToggle(item)}
                                >
                                    <input
                                        type="checkbox"
                                        checked={isItemSelected(item)}
                                        onChange={() => { }}
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
                                                    value={selectedItems.find(i => {
                                                        const pId = getItemId(item);
                                                        const vId = item.variant_id || item.product_variant_id || null;
                                                        return i.product_id === pId && i.variant_id === vId;
                                                    })?.condition || 'UNOPENED'}
                                                    onChange={(e) => handleConditionChange(item, e.target.value)}
                                                    className="condition-select"
                                                >
                                                    {conditionOptions.map(opt => (
                                                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                                                    ))}
                                                </select>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Return Reason */}
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

                    {/* Reason Details */}
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

                    {/* Refund Method */}
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

                    {/* Notes */}
                    <div className="form-section">
                        <label className="form-label">Ghi chú (tùy chọn)</label>
                        <textarea
                            value={notes}
                            onChange={(e) => setNotes(e.target.value)}
                            className="form-textarea"
                            placeholder="Thêm ghi chú nếu cần..."
                            rows="3"
                        />
                    </div>

                    {/* Image Upload */}
                    <div className="form-section">
                        <label className="form-label">Hình ảnh minh chứng (tùy chọn, tối đa 5 ảnh)</label>
                        <div className="image-upload-section">
                            <input
                                type="file"
                                id="imageUpload"
                                multiple
                                accept="image/*"
                                onChange={handleImageUpload}
                                style={{ display: 'none' }}
                            />
                            <label htmlFor="imageUpload" className="upload-btn">
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

                    {/* Refund Amount */}
                    <div className="form-section refund-summary">
                        <div className="refund-amount-display">
                            <span>Số tiền hoàn dự kiến:</span>
                            <span className="amount">{formatPrice(calculateRefundAmount())}</span>
                        </div>
                    </div>

                    {/* Submit Button */}
                    <div className="form-actions">
                        <button type="button" onClick={handleClose} className="btn-cancel">
                            Hủy
                        </button>
                        <button type="submit" className="btn-submit" disabled={submitting}>
                            {submitting ? 'Đang xử lý...' : 'Tạo yêu cầu'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default CreateReturnModal;
