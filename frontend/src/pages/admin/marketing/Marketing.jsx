import React, { useState, useEffect } from 'react';
import marketingApi from '../../../api/marketingApi';
import CouponForm from './CouponForm';
import FlashSaleManager from './FlashSaleManager';
import './Marketing.css';

const Marketing = () => {
  const [activeTab, setActiveTab] = useState('coupons');
  const [coupons, setCoupons] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [selectedCoupon, setSelectedCoupon] = useState(null);

  const fetchCoupons = async () => {
    try {
      setLoading(true);
      const res = await marketingApi.getAllCoupons({ _t: Date.now() });
      let list = Array.isArray(res) ? res : (res.data || []);
      setCoupons(list);
    } catch (error) {
      console.error("Lỗi tải coupon:", error);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => { 
      if (activeTab === 'coupons') fetchCoupons(); 
  }, [activeTab]);

  const handleCreate = () => {
    setSelectedCoupon(null);
    setShowModal(true);
  };

  const handleEdit = (coupon) => {
    setSelectedCoupon(coupon);
    setShowModal(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm("Xóa vĩnh viễn mã này?")) {
      try {
        await marketingApi.deleteCoupon(id);
        setCoupons(prevCoupons => prevCoupons.filter(c => c.coupon_id !== id));
      } catch (error) {
        alert("Lỗi khi xóa: " + (error.response?.data?.detail || error.message));
      }
    }
  };

  const handleModalSuccess = () => {
    setShowModal(false);
    fetchCoupons();
  };

  const formatMoney = (val) => new Intl.NumberFormat('vi-VN').format(val || 0);
  
  const isExpired = (endDate) => {
      if (!endDate) return false;
      return new Date(endDate) < new Date();
  };

  return (
    <div className="marketing-page">
      <div className="page-header" style={{display: 'block'}}>
        <div className="title-area" style={{marginBottom: '20px'}}>
          <h2>Quản lý Tiếp thị</h2>
          <p>Quản lý mã giảm giá và các chương trình khuyến mãi.</p>
        </div>
        
        {/* THANH TAB NAVIGATION */}
        <div className="marketing-tabs">
            <button 
                className={`tab-btn ${activeTab === 'coupons' ? 'active' : ''}`} 
                onClick={() => setActiveTab('coupons')}
            >
              Mã Giảm Giá
            </button>
            <button 
                className={`tab-btn ${activeTab === 'flash_sale' ? 'active' : ''}`} 
                onClick={() => setActiveTab('flash_sale')}
            >
                 Flash Sale
            </button>
        </div>
      </div>

      <div className="marketing-content">
        {/* --- TAB 1: COUPONS --- */}
        {activeTab === 'coupons' && (
            <>
                <div style={{textAlign: 'right', marginBottom: '15px'}}>
                    <button className="btn-create" onClick={handleCreate}>+ Tạo Coupon Mới</button>
                </div>

                <div className="coupon-grid">
                    {loading && coupons.length === 0 ? (
                        <p style={{padding: '20px'}}>Đang tải danh sách... </p>
                    ) : (
                        coupons.length > 0 ? coupons.map(coupon => (
                        <div key={coupon.coupon_id} className={`coupon-card ${!coupon.is_active ? 'inactive' : ''}`}>
                            {/* Phần Trái (Màu sắc) */}
                            <div className="coupon-left">
                                <div className="coupon-value">
                                    {coupon.discount_type === 'PERCENTAGE' 
                                        ? `${coupon.discount_value}%` 
                                        : `${formatMoney(coupon.discount_value/1000)}k`}
                                    <span className="off-label">OFF</span>
                                </div>
                            </div>
                            
                            {/* Phần Phải (Thông tin) */}
                            <div className="coupon-right">
                                <div className="coupon-header">
                                    <span className="code-text" onClick={() => {
                                        navigator.clipboard.writeText(coupon.coupon_code);
                                        alert("Đã copy mã: " + coupon.coupon_code);
                                    }}>
                                        {coupon.coupon_code} 📋
                                    </span>
                                    <span className={`status-tag ${coupon.is_active ? 'active' : 'inactive'}`}>
                                        {coupon.is_active ? 'Hoạt động' : 'Tạm ẩn'}
                                    </span>
                                </div>
                                
                                <div className="coupon-desc">
                                    <div style={{fontWeight: '600', color: '#2b2d42'}}>{coupon.description || 'Không có mô tả'}</div>
                                    <div style={{marginTop: '8px', fontSize:'12px', color:'#4361ee', display: 'flex', alignItems: 'center', gap: '4px'}}>
                                        <span style={{background: '#eef2ff', padding: '2px 6px', borderRadius: '4px', fontWeight: 'bold', border: '1px solid #4361ee'}}>
                                             {coupon.customer_eligibility === 'ALL' ? 'Tất cả khách' : `Hạng ${coupon.customer_eligibility}`}
                                        </span>
                                    </div>
                                    <div style={{marginTop: '5px', fontSize:'12px', color:'#666'}}>
                                        Đơn tối thiểu: <strong>{formatMoney(coupon.min_purchase_amount)}đ</strong>
                                    </div>
                                </div>
                                
                                <div className="coupon-footer">
                                    <div className={`expiry-date ${isExpired(coupon.end_date) ? 'expired' : ''}`}>
                                        {isExpired(coupon.end_date) 
                                            ? ' Đã hết hạn' 
                                            : `HSD: ${new Date(coupon.end_date).toLocaleDateString('vi-VN')}`}
                                    </div>
                                    <div className="actions">
                                        <button className="btn-icon edit" onClick={() => handleEdit(coupon)}>✏️</button>
                                        <button className="btn-icon delete" onClick={() => handleDelete(coupon.coupon_id)}>🗑️</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        )) : (
                            <p style={{padding: '20px', color: '#888'}}>Chưa có mã giảm giá nào!</p>
                        )
                    )}
                </div>

                {/* MODAL FORM TẠO/SỬA COUPON */}
                {showModal && (
                    <CouponForm 
                        onClose={() => setShowModal(false)}
                        initialData={selectedCoupon}
                        onSuccess={handleModalSuccess}
                    />
                )}
            </>
        )}

        {/* --- TAB 2: FLASH SALE --- */}
        {activeTab === 'flash_sale' && (
            <FlashSaleManager />
        )}
      </div>
    </div>
  );
};

export default Marketing;