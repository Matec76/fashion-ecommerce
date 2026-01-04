import React, { useState, useEffect } from 'react';
import systemApi from '../../../api/systemApi';

const MarketingContact = () => {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const KEYS = {
    CART_DELAY: 'abandoned_cart_delay_hours',   // Số giờ gửi email nhắc
    MAX_EMAILS: 'max_abandoned_cart_emails',    // Số email tối đa
    COUPON_LIMIT: 'max_coupon_usage_per_user'   // Giới hạn dùng mã
  };

  const [formData, setFormData] = useState({
    cart_delay: '',
    max_emails: '',
    coupon_limit: ''
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const res = await systemApi.getAll();
        const settings = Array.isArray(res) ? res : (res.data || []);
        const getValue = (key) => settings.find(s => s.setting_key === key)?.setting_value || '';

        setFormData({
            cart_delay: getValue(KEYS.CART_DELAY),
            max_emails: getValue(KEYS.MAX_EMAILS),
            coupon_limit: getValue(KEYS.COUPON_LIMIT)
        });
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

  const handleSave = async () => {
    try {
      setSaving(true);
      await Promise.all([
        systemApi.setValue(KEYS.CART_DELAY, formData.cart_delay),
        systemApi.setValue(KEYS.MAX_EMAILS, formData.max_emails),
        systemApi.setValue(KEYS.COUPON_LIMIT, formData.coupon_limit)
      ]);
      alert("Đã lưu cấu hình Marketing!");
    } catch (error) {
      alert("Lỗi: " + error.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="p-4 text-center">Đang tải...</div>;

  return (
    <div className="settings-card">
      <div className="card-header">
        <h3> Marketing & Chăm sóc khách hàng</h3>
        <p className="text-muted">Cấu hình tự động gửi email và giới hạn khuyến mãi.</p>
      </div>
      <div className="card-body">
        
        <h4 style={{marginBottom: '15px', borderBottom: '1px solid #eee', paddingBottom: '5px'}}>Giỏ hàng bỏ quên (Abandoned Cart)</h4>
        <div className="form-row" style={{display:'flex', gap:'20px', marginBottom:'20px'}}>
            <div className="form-group half" style={{flex:1}}>
                <label>Gửi email nhắc nhở sau (Giờ)</label>
                <input type="number" name="cart_delay" className="form-control" value={formData.cart_delay} onChange={handleChange} />
                <small className="text-muted">Thời gian chờ sau khi khách bỏ giỏ hàng để hệ thống gửi mail nhắc.</small>
            </div>
            <div className="form-group half" style={{flex:1}}>
                <label>Số lượng email nhắc tối đa</label>
                <input type="number" name="max_emails" className="form-control" value={formData.max_emails} onChange={handleChange} />
                <small className="text-muted">Tránh spam khách hàng (VD: Tối đa 3 email/đơn hàng).</small>
            </div>
        </div>

        <h4 style={{marginBottom: '15px', borderBottom: '1px solid #eee', paddingBottom: '5px'}}>Khuyến mãi (Coupon)</h4>
        <div className="form-group" style={{maxWidth: '50%'}}>
            <label>Giới hạn sử dụng mã / 1 Khách hàng</label>
            <input type="number" name="coupon_limit" className="form-control" value={formData.coupon_limit} onChange={handleChange} />
            <small className="text-muted">Mặc định số lần tối đa 1 người được dùng mã giảm giá (VD: 1 lần).</small>
        </div>

        <div className="text-right" style={{marginTop:'20px'}}>
            <button className="btn-primary" onClick={handleSave} disabled={saving}>{saving ? 'Đang lưu...' : 'Lưu thay đổi'}</button>
        </div>
      </div>
    </div>
  );
};

export default MarketingContact;