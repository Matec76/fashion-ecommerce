import React, { useState, useEffect } from 'react';
import marketingApi from '../../../api/marketingApi';

const CouponForm = ({ onClose, initialData, onSuccess }) => {
  const [formData, setFormData] = useState({
    coupon_code: '',
    description: '',
    discount_type: 'PERCENTAGE',
    discount_value: '',
    min_purchase_amount: 0,
    max_discount_amount: 0,
    start_date: '',
    end_date: '',
    usage_limit: 100,
    is_active: true,
    free_shipping: false,
    customer_eligibility: 'ALL' // Thêm mới
  });

  const [loading, setLoading] = useState(false);

  const formatDateForInput = (isoString) => {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toISOString().slice(0, 16); 
  };

  useEffect(() => {
    if (initialData) {
      setFormData({
        coupon_code: initialData.coupon_code || '',
        description: initialData.description || '',
        discount_type: initialData.discount_type || 'PERCENTAGE',
        discount_value: initialData.discount_value || '',
        min_purchase_amount: initialData.min_purchase_amount || 0,
        max_discount_amount: initialData.max_discount_amount || 0,
        start_date: formatDateForInput(initialData.start_date),
        end_date: formatDateForInput(initialData.end_date),
        usage_limit: initialData.usage_limit || 100,
        is_active: initialData.is_active,
        free_shipping: initialData.free_shipping || false,
        customer_eligibility: initialData.customer_eligibility || 'ALL'
      });
    } else {
        const now = new Date();
        setFormData(prev => ({...prev, start_date: formatDateForInput(now)}));
    }
  }, [initialData]);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const payload = {
        ...formData,
        start_date: new Date(formData.start_date).toISOString(),
        end_date: new Date(formData.end_date).toISOString(),
    };

    try {
      if (initialData) {
        await marketingApi.updateCoupon(initialData.coupon_id, payload);
        alert("Cập nhật mã thành công!");
      } else {
        await marketingApi.createCoupon(payload);
        alert("Tạo mã mới thành công!");
      }
      onSuccess(); 
    } catch (error) {
      alert("Lỗi: " + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content animate-slide-down" onClick={e => e.stopPropagation()}>
        <h3>{initialData ? 'Cập nhật mã giảm giá' : 'Tạo mã giảm giá mới'}</h3>
        
        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <div className="form-group col-1">
              <label>Mã Code *</label>
              <input 
                type="text" name="coupon_code" 
                value={formData.coupon_code} onChange={handleInputChange} 
                required disabled={!!initialData}
                style={{textTransform: 'uppercase', fontWeight: 'bold'}}
              />
            </div>
            <div className="form-group col-2">
              <label>Mô tả ngắn</label>
              <input type="text" name="description" value={formData.description} onChange={handleInputChange} />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group col-1">
              <label>Loại giảm giá</label>
              <select name="discount_type" value={formData.discount_type} onChange={handleInputChange}>
                <option value="PERCENTAGE">Phần trăm (%)</option>
                <option value="FIXED_AMOUNT">Tiền mặt (VNĐ)</option>
              </select>
            </div>
            <div className="form-group col-1">
              <label>Giá trị giảm *</label>
              <input type="number" name="discount_value" value={formData.discount_value} onChange={handleInputChange} required />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group col-1">
              <label>Đơn tối thiểu</label>
              <input type="number" name="min_purchase_amount" value={formData.min_purchase_amount} onChange={handleInputChange} />
            </div>
            <div className="form-group col-1">
              <label>Giảm tối đa (Max)</label>
              <input type="number" name="max_discount_amount" value={formData.max_discount_amount} onChange={handleInputChange} />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group col-1">
              <label>Ngày bắt đầu</label>
              <input type="datetime-local" name="start_date" value={formData.start_date} onChange={handleInputChange} required />
            </div>
            <div className="form-group col-1">
              <label>Ngày kết thúc</label>
              <input type="datetime-local" name="end_date" value={formData.end_date} onChange={handleInputChange} required />
            </div>
          </div>

          {/* DÒNG MỚI: THỨ HẠNG KHÁCH HÀNG */}
          <div className="form-row">
            <div className="form-group col-1">
              <label>Thứ hạng áp dụng</label>
              <select name="customer_eligibility" value={formData.customer_eligibility} onChange={handleInputChange}>
                <option value="ALL">Tất cả (ALL)</option>
                <option value="Bronze">Hạng Đồng (Bronze)</option>
                <option value="Silver">Hạng Bạc (Silver)</option>
                <option value="Gold">Hạng Vàng (Gold)</option>
                <option value="Diamond">Hạng Kim cương (Diamond)</option>
              </select>
            </div>
            <div className="form-group col-1">
              <label>Số lượng mã</label>
              <input type="number" name="usage_limit" value={formData.usage_limit} onChange={handleInputChange} />
            </div>
          </div>

          <div className="form-row checkbox-area" style={{marginTop: '10px'}}>
            <div className="checkbox-group">
                <input type="checkbox" id="freeShip" name="free_shipping" checked={formData.free_shipping} onChange={handleInputChange} />
                <label htmlFor="freeShip">Freeship</label>
            </div>
            <div className="checkbox-group">
                <input type="checkbox" id="activeCheck" name="is_active" checked={formData.is_active} onChange={handleInputChange} />
                <label htmlFor="activeCheck">Kích hoạt</label>
            </div>
          </div>

          <div className="modal-actions">
            <button type="button" className="btn-cancel" onClick={onClose}>Hủy</button>
            <button type="submit" className="btn-submit" disabled={loading}>
              {loading ? 'Đang lưu...' : 'Lưu mã'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CouponForm;