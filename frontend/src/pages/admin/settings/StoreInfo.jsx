import React, { useState, useEffect } from 'react';
import systemApi from '../../../api/systemApi'; // Import đúng đường dẫn
// Không cần import CSS vì file cha Settings.jsx đã import rồi

const StoreInfo = () => {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  //  CẬP NHẬT KEY CHO KHỚP VỚI DB MỚI
  const KEYS = {
    // name: 'site_title', // Key cũ
    // hotline: 'hotline_number', // Key cũ
    HOTLINE: 'contact_hotline',
    EMAIL: 'contact_email',
    ADDRESS: 'contact_address',
    // Thêm mấy cái Social Media vào đây luôn cho xôm
    FACEBOOK: 'social_facebook',
    INSTAGRAM: 'social_instagram',
    TWITTER: 'social_twitter'
  };

  const [formData, setFormData] = useState({
    hotline: '',
    email: '',
    address: '',
    facebook: '',
    instagram: '',
    twitter: ''
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const res = await systemApi.getAll();
        const settings = Array.isArray(res) ? res : (res.data || []);
        
        const getValue = (targetKey) => {
            const item = settings.find(s => s.setting_key === targetKey);
            return item ? item.setting_value : '';
        };

        setFormData({
            hotline: getValue(KEYS.HOTLINE),
            email: getValue(KEYS.EMAIL),
            address: getValue(KEYS.ADDRESS),
            facebook: getValue(KEYS.FACEBOOK),
            instagram: getValue(KEYS.INSTAGRAM),
            twitter: getValue(KEYS.TWITTER)
        });
      } catch (error) {
        console.error("Lỗi tải cấu hình:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      
      // Lưu từng key một (Giữ nguyên logic của đại ca vì nó an toàn)
      await Promise.all([
        systemApi.setValue(KEYS.HOTLINE, formData.hotline),
        systemApi.setValue(KEYS.EMAIL, formData.email),
        systemApi.setValue(KEYS.ADDRESS, formData.address),
        systemApi.setValue(KEYS.FACEBOOK, formData.facebook),
        systemApi.setValue(KEYS.INSTAGRAM, formData.instagram),
        systemApi.setValue(KEYS.TWITTER, formData.twitter)
      ]);

      alert(" Đã lưu thông tin cửa hàng thành công!");
    } catch (error) {
      console.error("Lỗi:", error);
      alert(" Không lưu được: " + (error.message || "Lỗi không xác định"));
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="p-4 text-center">⏳ Đang tải dữ liệu...</div>;

  return (
    <div className="settings-card">
      <div className="card-header">
        <h3>Thông tin cửa hàng</h3>
        <p className="text-muted">Thông tin hiển thị trên Website, Hóa đơn và Footer.</p>
      </div>
      <div className="card-body">
        
        {/* Phần thông tin liên hệ */}
        <div className="form-group">
            <label>Địa chỉ văn phòng</label>
            <input type="text" name="address" value={formData.address} onChange={handleChange} className="form-control" placeholder="Ví dụ: Tầng 10, Tòa nhà ABC..." />
        </div>

        <div className="form-row" style={{display: 'flex', gap: '15px'}}>
            <div className="form-group half" style={{flex: 1}}>
                <label>Hotline</label>
                <input type="text" name="hotline" value={formData.hotline} onChange={handleChange} className="form-control" />
            </div>
            <div className="form-group half" style={{flex: 1}}>
                <label>Email hỗ trợ</label>
                <input type="text" name="email" value={formData.email} onChange={handleChange} className="form-control" />
            </div>
        </div>

        <hr style={{margin: '20px 0', border: '0', borderTop: '1px solid #eee'}} />
        
        {/* Phần Mạng xã hội */}
        <h4 style={{marginBottom: '15px', fontSize: '15px'}}>Mạng xã hội</h4>
        <div className="form-group">
            <label>Facebook Fanpage</label>
            <input type="text" name="facebook" value={formData.facebook} onChange={handleChange} className="form-control" />
        </div>
        <div className="form-group">
            <label>Instagram Link</label>
            <input type="text" name="instagram" value={formData.instagram} onChange={handleChange} className="form-control" />
        </div>
        <div className="form-group">
            <label>Twitter / X Link</label>
            <input type="text" name="twitter" value={formData.twitter} onChange={handleChange} className="form-control" />
        </div>

        <div className="form-actions text-right" style={{marginTop: '20px', textAlign: 'right'}}>
            <button className="btn-primary" onClick={handleSave} disabled={saving}>
                {saving ? 'Đang lưu...' : 'Lưu thay đổi'}
            </button>
        </div>
      </div>
    </div>
  );
};

export default StoreInfo;