import React from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { API_ENDPOINTS } from '../../config/api.config';
import useFetch from '../../hooks/useFetch';
import '../../style/ReturnRefunds.css';

const ReturnRefundDetail = () => {
    const { returnId } = useParams();
    const navigate = useNavigate();

    // Fetch return detail
    const { data: returnDetail, loading, error } = useFetch(
        API_ENDPOINTS.RETURN_REFUNDS.RETURN_DETAIL(returnId),
        { auth: true }
    );

    // Status configuration
    const statusConfig = {
        'PENDING': { label: 'Chờ duyệt', color: '#ffc107', step: 2 },
        'APPROVED': { label: 'Đã duyệt', color: '#28a745', step: 3 },
        'PROCESSING': { label: 'Đang xử lý', color: '#17a2b8', step: 4 },
        'REJECTED': { label: 'Từ chối', color: '#dc3545', step: 0 },
        'COMPLETED': { label: 'Hoàn thành', color: '#17a2b8', step: 5 }
    };

    const refundMethodLabels = {
        'ORIGINAL_PAYMENT': 'Hoàn về phương thức thanh toán gốc',
        'STORE_CREDIT': 'Hoàn bằng điểm tích lũy',
        'BANK_TRANSFER': 'Chuyển khoản ngân hàng'
    };

    const returnReasonLabels = {
        'DEFECTIVE': 'Sản phẩm bị lỗi/hỏng',
        'WRONG_ITEM': 'Giao sai sản phẩm',
        'NOT_AS_DESCRIBED': 'Không đúng mô tả',
        'SIZE_ISSUE': 'Vấn đề về kích thước',
        'CHANGED_MIND': 'Đổi ý không muốn mua'
    };

    const formatPrice = (price) => {
        const numPrice = typeof price === 'string' ? parseFloat(price) : price;
        return new Intl.NumberFormat('vi-VN', {
            style: 'currency',
            currency: 'VND'
        }).format(numPrice);
    };

    const formatDate = (dateString) => {
        if (!dateString) return 'N/A';
        return new Date(dateString).toLocaleDateString('vi-VN', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const getStatusInfo = (status) => {
        return statusConfig[status] || { label: status, color: '#6c757d', step: 0 };
    };

    if (loading) {
        return (
            <div className="return-refunds-page">
                <div className="loading-container">
                    <div className="spinner"></div>
                    <p>Đang tải chi tiết...</p>
                </div>
            </div>
        );
    }

    if (error || !returnDetail) {
        return (
            <div className="return-refunds-page">
                <div className="error-container">
                    <p>Không tìm thấy yêu cầu trả hàng này.</p>
                    <Link to="/returns" className="btn-primary">Quay lại danh sách</Link>
                </div>
            </div>
        );
    }

    const statusInfo = getStatusInfo(returnDetail.status);

    return (
        <div className="return-refunds-page">
            <div className="return-detail-container">
                {/* Header */}
                <div className="detail-header">
                    <Link to="/returns" className="back-btn">← Quay lại</Link>
                    <h1>Chi tiết yêu cầu trả hàng</h1>
                </div>

                {/* Main Detail Card */}
                <div className="detail-card">
                    {/* Return Info Section */}
                    <div className="detail-section">
                        <h2>Thông tin yêu cầu</h2>
                        <div className="info-grid">
                            <div className="info-item">
                                <span className="info-label">Mã trả hàng:</span>
                                <span className="info-value">#{returnDetail.return_id}</span>
                            </div>
                            <div className="info-item">
                                <span className="info-label">Mã đơn hàng:</span>
                                <span className="info-value">#{returnDetail.order_id}</span>
                            </div>
                            <div className="info-item">
                                <span className="info-label">Ngày tạo:</span>
                                <span className="info-value">{formatDate(returnDetail.created_at)}</span>
                            </div>
                            <div className="info-item">
                                <span className="info-label">Trạng thái:</span>
                                <span
                                    className="status-badge-large"
                                    style={{
                                        backgroundColor: `${statusInfo.color}20`,
                                        color: statusInfo.color,
                                        borderColor: statusInfo.color
                                    }}
                                >
                                    {statusInfo.label}
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Progress Timeline */}
                    {returnDetail.status !== 'REJECTED' && (
                        <div className="detail-section">
                            <h3>Tiến trình xử lý</h3>
                            <div className="timeline">
                                {['Tạo yêu cầu', 'Chờ duyệt', 'Đã duyệt', 'Đang xử lý', 'Hoàn thành'].map((step, index) => {
                                    const stepNum = index + 1;
                                    const isCompleted = statusInfo.step >= stepNum;
                                    const isCurrent = statusInfo.step === stepNum;

                                    return (
                                        <div
                                            key={index}
                                            className={`timeline-step ${isCompleted ? 'completed' : ''} ${isCurrent ? 'current' : ''}`}
                                        >
                                            <div className="timeline-dot">
                                                {isCompleted ? '✓' : stepNum}
                                            </div>
                                            <span className="timeline-label">{step}</span>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}

                    {/* Return Reason Section */}
                    <div className="detail-section">
                        <h3>Lý do trả hàng</h3>
                        <div className="info-grid">
                            <div className="info-item full-width">
                                <span className="info-label">Lý do:</span>
                                <span className="info-value">{returnReasonLabels[returnDetail.return_reason] || returnDetail.return_reason}</span>
                            </div>
                            {returnDetail.reason_details && (
                                <div className="info-item full-width">
                                    <span className="info-label">Chi tiết:</span>
                                    <p className="reason-details">{returnDetail.reason_details}</p>
                                </div>
                            )}
                            {returnDetail.notes && (
                                <div className="info-item full-width">
                                    <span className="info-label">Ghi chú:</span>
                                    <p className="reason-details">{returnDetail.notes}</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Refund Information */}
                    <div className="detail-section">
                        <h3>Thông tin hoàn tiền</h3>
                        {(() => {
                            // Logic fallback: Nếu thông tin trên returnDetail chưa có, lấy từ refund transaction mới nhất
                            const latestRefund = returnDetail.refunds && returnDetail.refunds.length > 0
                                ? returnDetail.refunds[0]
                                : null;

                            const displayAmount = returnDetail.refund_amount || (latestRefund ? latestRefund.refund_amount || latestRefund.amount : null);
                            const displayMethod = returnDetail.refund_method || (latestRefund ? latestRefund.refund_method || latestRefund.method : null);

                            return (
                                <div className="info-grid">
                                    <div className="info-item">
                                        <span className="info-label">Số tiền hoàn:</span>
                                        <span className="info-value amount-highlight">
                                            {displayAmount ? formatPrice(displayAmount) : 'Chờ xử lý'}
                                        </span>
                                    </div>
                                    <div className="info-item">
                                        <span className="info-label">Phương thức:</span>
                                        <span className="info-value">
                                            {displayMethod ? (refundMethodLabels[displayMethod] || displayMethod) : 'Chờ xử lý'}
                                        </span>
                                    </div>
                                </div>
                            );
                        })()}

                        {/* Refunds List */}
                        {returnDetail.refunds && returnDetail.refunds.length > 0 && (
                            <div className="refunds-list">
                                <h4>Lịch sử hoàn tiền</h4>
                                {returnDetail.refunds.map((refund, index) => (
                                    <div key={index} className="refund-item">
                                        <div className="refund-info">
                                            <span>Mã hoàn tiền: #{refund.refund_id}</span>
                                            <span className={`refund-status ${refund.status}`}>
                                                {refund.status === 'COMPLETED' ? 'Hoàn thành' :
                                                    refund.status === 'PENDING' ? 'Chờ xử lý' :
                                                        refund.status === 'PROCESSING' ? 'Đang xử lý' : 'Thất bại'}
                                            </span>
                                        </div>
                                        {refund.processed_at && (
                                            <div className="refund-date">
                                                Xử lý lúc: {formatDate(refund.processed_at)}
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Admin Processing Notes */}
                    {returnDetail.processed_note && (
                        <div className="detail-section">
                            <h3>Ghi chú từ người xử lý</h3>
                            <div className="admin-note">
                                <p>{returnDetail.processed_note}</p>
                                {returnDetail.processed_by && (
                                    <span className="processed-by">Xử lý bởi: Admin #{returnDetail.processed_by}</span>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Images */}
                    {returnDetail.images && returnDetail.images.length > 0 && (
                        <div className="detail-section">
                            <h3>Hình ảnh đính kèm</h3>
                            <div className="images-grid">
                                {returnDetail.images.map((image, index) => (
                                    <img key={index} src={image} alt={`Evidence ${index + 1}`} className="evidence-image" />
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ReturnRefundDetail;
