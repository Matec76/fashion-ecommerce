import React, { useState, useEffect } from 'react';
import systemApi from '../../../api/systemApi';

const LoyaltyConfig = () => {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const KEYS = {
    EXPIRATION: 'point_expiration_days',
    REFERRAL: 'referral_reward_points',
    REFEREE: 'referee_reward_points',
    EARN_RATE: 'loyalty_exchange_rate',      // Tỷ lệ tích điểm
    REDEEM_RATE: 'redeem_point_exchange_rate', // Tỷ lệ tiêu điểm
    LIMIT_BRONZE: 'redeem_limit_bronze',
    LIMIT_SILVER: 'redeem_limit_silver',
    LIMIT_GOLD: 'redeem_limit_gold',
    LIMIT_DIAMOND: 'redeem_limit_diamond',
    COUPON_VALIDITY: 'redeem_coupon_validity_days'
  };

  const [formData, setFormData] = useState({
    expiration: '', referral: '', referee: '', earn_rate: '', redeem_rate: '',
    bronze: '', silver: '', gold: '', diamond: '', validity: ''
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const res = await systemApi.getAll();
        const settings = Array.isArray(res) ? res : (res.data || []);
        const getValue = (key) => settings.find(s => s.setting_key === key)?.setting_value || '';

        setFormData({
            expiration: getValue(KEYS.EXPIRATION),
            referral: getValue(KEYS.REFERRAL),
            referee: getValue(KEYS.REFEREE),
            earn_rate: getValue(KEYS.EARN_RATE),
            redeem_rate: getValue(KEYS.REDEEM_RATE),
            bronze: getValue(KEYS.LIMIT_BRONZE),
            silver: getValue(KEYS.LIMIT_SILVER),
            gold: getValue(KEYS.LIMIT_GOLD),
            diamond: getValue(KEYS.LIMIT_DIAMOND),
            validity: getValue(KEYS.COUPON_VALIDITY)
        });
      } catch (error) { console.error(error); } finally { setLoading(false); }
    };
    fetchData();
  }, []);

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

  const handleSave = async () => {
    try {
      setSaving(true);
      await Promise.all([
        systemApi.setValue(KEYS.EXPIRATION, formData.expiration),
        systemApi.setValue(KEYS.REFERRAL, formData.referral),
        systemApi.setValue(KEYS.REFEREE, formData.referee),
        systemApi.setValue(KEYS.EARN_RATE, formData.earn_rate),
        systemApi.setValue(KEYS.REDEEM_RATE, formData.redeem_rate),
        systemApi.setValue(KEYS.LIMIT_BRONZE, formData.bronze),
        systemApi.setValue(KEYS.LIMIT_SILVER, formData.silver),
        systemApi.setValue(KEYS.LIMIT_GOLD, formData.gold),
        systemApi.setValue(KEYS.LIMIT_DIAMOND, formData.diamond),
        systemApi.setValue(KEYS.COUPON_VALIDITY, formData.validity),
      ]);
      alert(" Đã lưu cấu hình Điểm thưởng!");
    } catch (error) { alert("Lỗi: " + error.message); } finally { setSaving(false); }
  };

  if (loading) return <div className="p-4 text-center">Đang tải...</div>;

  return (
    <div className="settings-card">
      <div className="card-header">
        <h3> Cấu hình Loyalty (Điểm thưởng)</h3>
        <p className="text-muted">Quản lý tỷ lệ tích điểm, đổi điểm và quyền lợi thành viên.</p>
      </div>
      <div className="card-body">
        {/* TÍCH ĐIỂM */}
        <h4 style={{marginBottom:'10px', color:'#2563eb'}}>1. Quy tắc Tích điểm</h4>
        <div className="form-row" style={{display:'flex', gap:'15px', marginBottom:'15px'}}>
            <div className="form-group half" style={{flex:1}}>
                <label>Tỷ lệ tích điểm (VNĐ tiêu thụ = 1 điểm)</label>
                <input type="number" name="earn_rate" className="form-control" value={formData.earn_rate} onChange={handleChange} />
                <small className="text-muted">VD: Nhập 100 &rarr; Khách tiêu 100đ được 1 điểm.</small>
            </div>
            <div className="form-group half" style={{flex:1}}>
                <label>Thời hạn điểm (Ngày)</label>
                <input type="number" name="expiration" className="form-control" value={formData.expiration} onChange={handleChange} />
            </div>
        </div>
        <div className="form-row" style={{display:'flex', gap:'15px', marginBottom:'20px'}}>
            <div className="form-group half" style={{flex:1}}>
                <label>Điểm thưởng người giới thiệu (Referral)</label>
                <input type="number" name="referral" className="form-control" value={formData.referral} onChange={handleChange} />
            </div>
            <div className="form-group half" style={{flex:1}}>
                <label>Điểm thưởng người được giới thiệu (Referee)</label>
                <input type="number" name="referee" className="form-control" value={formData.referee} onChange={handleChange} />
            </div>
        </div>

        {/* TIÊU ĐIỂM */}
        <h4 style={{marginBottom:'10px', color:'#d97706', borderTop:'1px solid #eee', paddingTop:'15px'}}>2. Quy tắc Đổi điểm (Redeem)</h4>
        <div className="form-row" style={{display:'flex', gap:'15px', marginBottom:'15px'}}>
             <div className="form-group half" style={{flex:1}}>
                <label>Giá trị quy đổi (1 điểm = ? VNĐ)</label>
                <input type="number" name="redeem_rate" className="form-control" value={formData.redeem_rate} onChange={handleChange} />
            </div>
             <div className="form-group half" style={{flex:1}}>
                <label>Hạn sử dụng mã đổi được (Ngày)</label>
                <input type="number" name="validity" className="form-control" value={formData.validity} onChange={handleChange} />
            </div>
        </div>
        
        <label style={{fontWeight:'bold', marginBottom:'10px', display:'block'}}>Hạn mức đổi điểm tối đa (VNĐ) theo hạng:</label>
        <div className="form-row" style={{display:'flex', gap:'15px'}}>
            <div className="form-group" style={{flex:1}}>
                <label>🥉 Bronze</label>
                <input type="number" name="bronze" className="form-control" value={formData.bronze} onChange={handleChange} />
            </div>
            <div className="form-group" style={{flex:1}}>
                <label>🥈 Silver</label>
                <input type="number" name="silver" className="form-control" value={formData.silver} onChange={handleChange} />
            </div>
            <div className="form-group" style={{flex:1}}>
                <label>🥇 Gold</label>
                <input type="number" name="gold" className="form-control" value={formData.gold} onChange={handleChange} />
            </div>
            <div className="form-group" style={{flex:1}}>
                <label>💎 Diamond</label>
                <input type="number" name="diamond" className="form-control" value={formData.diamond} onChange={handleChange} />
            </div>
        </div>

        <div className="text-right" style={{marginTop:'20px'}}>
            <button className="btn-primary" onClick={handleSave} disabled={saving}>{saving ? 'Đang lưu...' : 'Lưu thay đổi'}</button>
        </div>
      </div>
    </div>
  );
};

export default LoyaltyConfig;