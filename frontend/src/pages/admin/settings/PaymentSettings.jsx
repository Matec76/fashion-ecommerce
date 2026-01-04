import React, { useState, useEffect } from 'react';
import systemApi from '../../../api/systemApi';

const PaymentSettings = () => {
  // --- 1. STATE ---
  const [generalConfig, setGeneralConfig] = useState({
    payment_method_cod_enabled: 'false', 
    payment_method_payos_enabled: 'false'
  });
  const [savingConfig, setSavingConfig] = useState(false);
  const [methods, setMethods] = useState([]);
  const [loadingMethods, setLoadingMethods] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [currentId, setCurrentId] = useState(null);
  
  const [methodForm, setMethodForm] = useState({
    method_code: '',
    method_name: '',
    description: '',
    processing_fee: 0,
    is_active: true
  });

  // --- HÀM LOAD DỮ LIỆU ---
  const fetchData = async () => {
    try {
      setLoadingMethods(true);
      // Load cấu hình chung
      const sysRes = await systemApi.getAll();
      const settings = Array.isArray(sysRes) ? sysRes : (sysRes.data || []);
      const getValue = (key) => settings.find(s => s.setting_key === key)?.setting_value || 'false';
      setGeneralConfig({
          payment_method_cod_enabled: getValue('payment_method_cod_enabled'),
          payment_method_payos_enabled: getValue('payment_method_payos_enabled')
      });

      // Load danh sách phương thức
      const methodsRes = await systemApi.getPaymentMethods();
      setMethods(Array.isArray(methodsRes) ? methodsRes : (methodsRes.data || []));
    } catch (error) {
      console.error("Lỗi tải dữ liệu:", error);
    } finally {
      setLoadingMethods(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  // --- CẤU HÌNH CHUNG ---
  const handleToggleChange = (e) => {
    const { name, checked } = e.target;
    setGeneralConfig(prev => ({ ...prev, [name]: String(checked) }));
  };

  const saveGeneralConfig = async () => {
    try {
      setSavingConfig(true);
      await Promise.all([
        systemApi.setValue('payment_method_cod_enabled', generalConfig.payment_method_cod_enabled),
        systemApi.setValue('payment_method_payos_enabled', generalConfig.payment_method_payos_enabled)
      ]);
      alert("Đã lưu cấu hình chung.");
    } catch (error) {
      alert("Lỗi: " + error.message);
    } finally {
      setSavingConfig(false);
    }
  };

  // --- QUẢN LÝ PHƯƠNG THỨC ---
  const handleMethodChange = (e) => {
    const { name, value, type, checked } = e.target;
    setMethodForm(prev => ({
        ...prev,
        [name]: type === 'checkbox' ? checked : value
    }));
  };

  const openAddModal = () => {
    setIsEditing(false);
    setMethodForm({ method_code: '', method_name: '', description: '', processing_fee: 0, is_active: true });
    setShowModal(true);
  };

  const openEditModal = (item) => {
    setIsEditing(true);
    setCurrentId(item.payment_method_id || item.id);
    setMethodForm({
        method_code: item.method_code || '',
        method_name: item.method_name,
        description: item.description || '',
        processing_fee: Number(item.processing_fee || 0),
        is_active: Boolean(item.is_active)
    });
    setShowModal(true);
  };

  //  Cập nhật State ngay lập tức sau khi Tạo mới
  const handleMethodSubmit = async (e) => {
    e.preventDefault();
    const payload = { ...methodForm, processing_fee: Number(methodForm.processing_fee) };
    
    try {
        if (isEditing) {
            await systemApi.updatePaymentMethod(currentId, payload);
            
            // Cập nhật nóng vào danh sách
            setMethods(prev => prev.map(item => 
                (item.payment_method_id || item.id) === currentId ? { ...item, ...payload } : item
            ));
            alert("Cập nhật thành công.");
        } else {
            // 1. Gọi API tạo mới và hứng lấy dữ liệu trả về
            const res = await systemApi.createPaymentMethod(payload);
            
            // 2. Lấy object vừa tạo từ response (Backend thường trả về chính nó)
            const newMethod = res.data || res;
            
            // 3. Nếu có dữ liệu, thêm ngay vào đầu danh sách
            if (newMethod && typeof newMethod === 'object') {
                setMethods(prev => [newMethod, ...prev]);
            } else {
                // Fallback: Nếu backend không trả data, buộc phải fetch lại sau 1s
                setTimeout(() => fetchData(), 1000);
            }
            alert("Thêm mới thành công.");
        }
        setShowModal(false);
        
    } catch (error) {
        alert("Lỗi: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleDeleteMethod = async (item) => {
    if (window.confirm(`Xóa cổng "${item.method_name}"?`)) {
        try {
            await systemApi.deletePaymentMethod(item.payment_method_id || item.id);
            setMethods(prev => prev.filter(m => (m.payment_method_id || m.id) !== (item.payment_method_id || item.id)));
        } catch (error) {
            alert("Không thể xóa (Có thể đang có giao dịch).");
        }
    }
  };

  const formatMoney = (val) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val || 0);

  return (
    <div className="payment-settings-container">
      {/* 1. CẤU HÌNH CHUNG */}
      <div className="settings-card mb-4" style={{marginBottom: '20px'}}>
        <div className="card-header">
            <h3>Cấu hình Thanh toán Hệ thống</h3>
            <p className="text-muted">Bật/Tắt các luồng thanh toán chính.</p>
        </div>
        <div className="card-body">
            <div className="form-group checkbox-group" style={{background:'#f9fafb', padding:'15px', borderRadius:'6px', marginBottom:'10px'}}>
                <label style={{display:'flex', alignItems:'center', cursor:'pointer', fontWeight:'600', color: generalConfig.payment_method_cod_enabled === 'true' ? '#2563eb' : '#374151'}}>
                    <input type="checkbox" name="payment_method_cod_enabled" checked={generalConfig.payment_method_cod_enabled === 'true'} onChange={handleToggleChange} style={{marginRight:'12px', width:'18px', height:'18px'}} />
                    Thanh toán khi nhận hàng (COD)
                </label>
            </div>
            <div className="form-group checkbox-group" style={{background:'#f9fafb', padding:'15px', borderRadius:'6px'}}>
                <label style={{display:'flex', alignItems:'center', cursor:'pointer', fontWeight:'600', color: generalConfig.payment_method_payos_enabled === 'true' ? '#2563eb' : '#374151'}}>
                    <input type="checkbox" name="payment_method_payos_enabled" checked={generalConfig.payment_method_payos_enabled === 'true'} onChange={handleToggleChange} style={{marginRight:'12px', width:'18px', height:'18px'}} />
                    Thanh toán Online qua PayOS
                </label>
            </div>
            <div style={{textAlign: 'right', marginTop: '15px'}}>
                <button className="btn-primary" onClick={saveGeneralConfig} disabled={savingConfig}>
                    {savingConfig ? 'Đang lưu...' : 'Lưu cấu hình chung'}
                </button>
            </div>
        </div>
      </div>

      {/* 2. DANH SÁCH CỔNG THANH TOÁN */}
      <div className="settings-card">
        <div className="card-header" style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
            <h3>Danh sách Cổng thanh toán</h3>
            <button className="btn-primary" onClick={openAddModal}>+ Thêm cổng</button>
        </div>
        <div className="card-body">
            {loadingMethods ? <div className="text-center p-4">Đang tải...</div> : (
                <table className="data-table">
                    <thead>
                        <tr>
                            <th style={{width: '15%'}}>Mã Code</th>
                            <th style={{width: '35%'}}>Tên hiển thị</th>
                            <th style={{width: '20%'}}>Phí xử lý</th>
                            <th style={{width: '15%'}}>Trạng thái</th>
                            <th className="text-right" style={{width: '15%'}}>Hành động</th>
                        </tr>
                    </thead>
                    <tbody>
                        {methods.length > 0 ? methods.map((item, idx) => (
                            <tr key={idx}>
                                <td style={{fontFamily:'monospace', fontWeight:'600', color:'#555'}}>{item.method_code}</td>
                                <td>
                                    <div style={{fontWeight:'600', color:'#333'}}>{item.method_name}</div>
                                    <div style={{fontSize:'12px', color:'#888'}}>{item.description}</div>
                                </td>
                                <td style={{color:'#d32f2f'}}>{item.processing_fee > 0 ? `+${formatMoney(item.processing_fee)}` : 'Miễn phí'}</td>
                                <td>
                                    <span className={`badge ${item.is_active ? 'badge-success' : 'badge-default'}`}>
                                        {item.is_active ? 'Hoạt động' : 'Tạm tắt'}
                                    </span>
                                </td>
                                <td className="text-right">
                                    <button className="btn-icon" onClick={() => openEditModal(item)} title="Sửa">✏️</button>
                                    <button className="btn-icon delete" onClick={() => handleDeleteMethod(item)} title="Xóa">🗑️</button>
                                </td>
                            </tr>
                        )) : (
                            <tr><td colSpan="5" className="text-center p-4" style={{color:'#888'}}>Chưa có phương thức thanh toán nào.</td></tr>
                        )}
                    </tbody>
                </table>
            )}
        </div>
      </div>

      {/* MODAL */}
      {showModal && (
          <div className="modal-overlay">
              <div className="modal-content">
                  <div className="modal-header">
                      <h4>{isEditing ? 'Cập nhật' : 'Thêm mới'}</h4>
                      <button className="close-btn" onClick={() => setShowModal(false)}>×</button>
                  </div>
                  <form onSubmit={handleMethodSubmit}>
                      <div className="form-row" style={{display:'flex', gap:'15px', marginBottom:'15px'}}>
                          <div className="form-group half" style={{flex:1}}>
                              <label>Mã Code *</label>
                              <input required type="text" name="method_code" className="form-control" value={methodForm.method_code} onChange={handleMethodChange} disabled={isEditing} style={{textTransform:'uppercase'}} placeholder="MOMO..." />
                          </div>
                          <div className="form-group half" style={{flex:1}}>
                              <label>Phí xử lý (VNĐ)</label>
                              <input type="number" name="processing_fee" className="form-control" value={methodForm.processing_fee} onChange={handleMethodChange} />
                          </div>
                      </div>
                      <div className="form-group">
                          <label>Tên hiển thị *</label>
                          <input required type="text" name="method_name" className="form-control" value={methodForm.method_name} onChange={handleMethodChange} />
                      </div>
                      <div className="form-group">
                          <label>Mô tả</label>
                          <textarea name="description" className="form-control" rows="2" value={methodForm.description} onChange={handleMethodChange}></textarea>
                      </div>
                      <div className="form-group checkbox-group" style={{background:'#f9fafb', padding:'10px', borderRadius:'6px'}}>
                          <label style={{display:'flex', alignItems:'center', cursor:'pointer', fontWeight:'600'}}>
                              <input type="checkbox" name="is_active" checked={methodForm.is_active} onChange={handleMethodChange} style={{marginRight:'10px', width:'18px', height:'18px'}} />
                              Kích hoạt ngay
                          </label>
                      </div>
                      <div className="modal-actions">
                          <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>Hủy</button>
                          <button type="submit" className="btn-primary">Lưu lại</button>
                      </div>
                  </form>
              </div>
          </div>
      )}
    </div>
  );
};

export default PaymentSettings;