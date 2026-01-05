import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { API_ENDPOINTS } from '../../config/api.config';
import useFetch from '../../hooks/useFetch';
import '../../style/ReturnRefunds.css';

const ReturnRefunds = () => {
    const [selectedStatus, setSelectedStatus] = useState('all');
    const navigate = useNavigate();

    // Fetch return requests
    const { data: returns, loading, error } = useFetch(
        `${API_ENDPOINTS.RETURN_REFUNDS.MY_RETURNS}?limit=50&skip=0`,
        { auth: true, skipCache: true }
    );

    // Status configuration
    const statusConfig = {
        'PENDING': {
            label: 'Chờ duyệt',
            color: '#ffc107'
        },
        'APPROVED': {
            label: 'Đã duyệt',
            color: '#28a745'
        },
        'REJECTED': {
            label: 'Từ chối',
            color: '#dc3545'
        },
        'COMPLETED': {
            label: 'Hoàn thành',
            color: '#17a2b8'
        }
    };

    // Refund method labels
    const refundMethodLabels = {
        'ORIGINAL_PAYMENT': 'Hoàn về gốc',
        'STORE_CREDIT': 'Tích điểm',
        'BANK_TRANSFER': 'Chuyển khoản'
    };

    // Return reason labels
    const returnReasonLabels = {
        'DEFECTIVE': 'Sản phẩm lỗi',
        'WRONG_ITEM': 'Giao sai sản phẩm',
        'NOT_AS_DESCRIBED': 'Không đúng mô tả',
        'SIZE_ISSUE': 'Vấn đề về size',
        'CHANGED_MIND': 'Đổi ý'
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
            color: '#6c757d'
        };
    };

    // Filter returns by status
    const returnsList = Array.isArray(returns) ? returns : [];
    const filteredReturns = selectedStatus === 'all'
        ? returnsList
        : returnsList.filter(ret => ret.status === selectedStatus);

    if (loading) {
        return (
            <div className="return-refunds-page">
                <div className="loading-container">
                    <div className="spinner"></div>
                    <p>Đang tải yêu cầu trả hàng...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="return-refunds-page">
                <div className="error-container">
                    <p>Không thể tải dữ liệu. Vui lòng thử lại sau.</p>
                    <Link to="/orders" className="btn-primary">Về trang đơn hàng</Link>
                </div>
            </div>
        );
    }

    return (
        <div className="return-refunds-page">
            <div className="return-refunds-container">
                <header className="page-header">
                    <h1>Đơn trả hàng & Hoàn tiền</h1>
                    <p>Quản lý các yêu cầu đổi trả và theo dõi trạng thái hoàn tiền</p>
                </header>

                {/* Status Filter */}
                <div className="status-filter">
                    <button
                        className={`filter-btn ${selectedStatus === 'all' ? 'active' : ''}`}
                        onClick={() => setSelectedStatus('all')}
                    >
                        Tất cả ({returnsList.length})
                    </button>
                    {Object.entries(statusConfig).map(([key, config]) => {
                        const count = returnsList.filter(r => r.status === key).length;
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

                {/* Returns List or Empty State */}
                {filteredReturns.length === 0 ? (
                    <div className="no-returns">
                        <h3>Chưa có yêu cầu trả hàng nào</h3>
                        <p>
                            {selectedStatus === 'all'
                                ? 'Bạn chưa tạo yêu cầu trả hàng nào. Truy cập trang đơn hàng để tạo yêu cầu trả hàng cho các đơn đã giao.'
                                : `Không có yêu cầu nào ở trạng thái "${statusConfig[selectedStatus]?.label}"`
                            }
                        </p>
                        <Link to="/orders" className="btn-primary">Xem đơn hàng</Link>
                    </div>
                ) : (
                    <div className="returns-grid">
                        {filteredReturns.map((returnItem) => {
                            const statusInfo = getStatusInfo(returnItem.status);
                            return (
                                <div key={returnItem.return_id} className="return-card">
                                    {/* Card Header */}
                                    <div className="return-header">
                                        <div className="return-info">
                                            <span className="return-id">Mã trả hàng: #{returnItem.return_id}</span>
                                            <span className="order-id">Đơn hàng: #{returnItem.order_id}</span>
                                        </div>
                                        <span
                                            className="status-badge"
                                            style={{
                                                backgroundColor: `${statusInfo.color}20`,
                                                color: statusInfo.color,
                                                borderColor: statusInfo.color
                                            }}
                                        >
                                            {statusInfo.label}
                                        </span>
                                    </div>

                                    {/* Card Body */}
                                    <div className="return-body">
                                        <div className="return-detail">
                                            <span className="label">Lý do:</span>
                                            <span className="value">{returnReasonLabels[returnItem.return_reason] || returnItem.return_reason}</span>
                                        </div>
                                        {returnItem.reason_details && (
                                            <div className="return-detail">
                                                <span className="label">Chi tiết:</span>
                                                <span className="value reason-text">{returnItem.reason_details}</span>
                                            </div>
                                        )}
                                        <div className="return-detail">
                                            <span className="label">Số tiền hoàn:</span>
                                            <span className="value amount">{formatPrice(returnItem.refund_amount)}</span>
                                        </div>
                                        <div className="return-detail">
                                            <span className="label">Phương thức:</span>
                                            <span className="value">{refundMethodLabels[returnItem.refund_method] || returnItem.refund_method}</span>
                                        </div>
                                        <div className="return-detail">
                                            <span className="label">Ngày tạo:</span>
                                            <span className="value">{formatDate(returnItem.created_at)}</span>
                                        </div>
                                    </div>

                                    {/* Card Footer */}
                                    <div className="return-footer">
                                        <Link
                                            to={`/returns/${returnItem.return_id}`}
                                            className="btn-view-detail"
                                        >
                                            Xem chi tiết
                                        </Link>
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

export default ReturnRefunds;
