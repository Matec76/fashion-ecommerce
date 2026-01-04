import React, { useState, useEffect } from 'react';
import systemApi from '../../../api/systemApi';

const SystemControl = () => {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const [config, setConfig] = useState({
    chatbot_enabled: 'false',
    maintenance_mode: 'false'
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const res = await systemApi.getAll();
        const settings = Array.isArray(res) ? res : (res.data || []);
        const getValue = (key) => settings.find(s => s.setting_key === key)?.setting_value || 'false';

        setConfig({
            chatbot_enabled: getValue('chatbot_enabled'),
            maintenance_mode: getValue('maintenance_mode')
        });
      } catch (error) { console.error(error); } finally { setLoading(false); }
    };
    fetchData();
  }, []);

  const handleToggle = (e) => {
    setConfig({ ...config, [e.target.name]: String(e.target.checked) });
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      await Promise.all([
        systemApi.setValue('chatbot_enabled', config.chatbot_enabled),
        systemApi.setValue('maintenance_mode', config.maintenance_mode)
      ]);
      alert(" Đã lưu cấu hình Hệ thống!");
    } catch (error) { alert("Lỗi: " + error.message); } finally { setSaving(false); }
  };

  if (loading) return <div className="p-4 text-center">Đang tải...</div>;

  return (
    <div className="settings-card">
      <div className="card-header">
        <h3> Kiểm soát Hệ thống</h3>
        <p className="text-muted">Các thiết lập cấp cao ảnh hưởng toàn bộ website.</p>
      </div>
      <div className="card-body">
        
        <div className="form-group checkbox-group" style={{background:'#f0fdf4', padding:'20px', borderRadius:'8px', marginBottom:'20px', border:'1px solid #dcfce7'}}>
            <label style={{display:'flex', alignItems:'center', cursor:'pointer', fontSize:'16px', fontWeight:'600', color:'#166534'}}>
                <input 
                    type="checkbox" name="chatbot_enabled" 
                    checked={config.chatbot_enabled === 'true'} onChange={handleToggle}
                    style={{width:'20px', height:'20px', marginRight:'15px'}} 
                />
                 Bật tính năng Chatbot AI (Hỗ trợ khách hàng tự động)
            </label>
        </div>

        <div className="form-group checkbox-group" style={{background:'#fef2f2', padding:'20px', borderRadius:'8px', border:'1px solid #fee2e2'}}>
            <label style={{display:'flex', alignItems:'center', cursor:'pointer', fontSize:'16px', fontWeight:'600', color:'#991b1b'}}>
                <input 
                    type="checkbox" name="maintenance_mode" 
                    checked={config.maintenance_mode === 'true'} onChange={handleToggle}
                    style={{width:'20px', height:'20px', marginRight:'15px'}} 
                />
                 Bật chế độ BẢO TRÌ (Sẽ tắt website phía khách hàng)
            </label>
            <p style={{marginLeft:'35px', marginTop:'5px', color:'#b91c1c', fontSize:'13px'}}>
                Lưu ý: Khi bật chế độ này, chỉ có Admin mới truy cập được hệ thống. Khách hàng sẽ thấy trang "Đang bảo trì".
            </p>
        </div>

        <div className="text-right" style={{marginTop:'30px'}}>
            <button className="btn-primary" onClick={handleSave} disabled={saving}>{saving ? 'Đang lưu...' : 'Lưu thay đổi'}</button>
        </div>
      </div>
    </div>
  );
};

export default SystemControl;