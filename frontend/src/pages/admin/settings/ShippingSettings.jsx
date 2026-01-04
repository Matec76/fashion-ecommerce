import React, { useState, useEffect } from 'react';
import systemApi from '../../../api/systemApi';

const ShippingSettings = () => {
  // --- STATE CẤU HÌNH CHUNG (Lưu vào system_settings) ---
  const [generalConfig, setGeneralConfig] = useState({
    free_shipping_threshold: '',
    return_window_days: ''
  });
  const [savingConfig, setSavingConfig] = useState(false);

  // --- STATE DANH SÁCH PHƯƠNG THỨC (Lưu vào shipping_methods) ---
  const [methods, setMethods] = useState([]);
  const [loadingMethods, setLoadingMethods] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [currentId, setCurrentId] = useState(null);
  
  const [methodForm, setMethodForm] = useState({
    method_name: '',
    description: '',
    base_cost: 0,
    estimated_days: '',
    is_active: true
  });

  // --- 1. LOAD DỮ LIỆU ---
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoadingMethods(true);

        // A. Load Cấu hình chung (Freeship & Đổi trả)
        const settingsRes = await systemApi.getAll();
        const settings = Array.isArray(settingsRes) ? settingsRes : (settingsRes.data || []);
        
        // Hàm tìm giá trị theo key
        const getValue = (key) => {
            const found = settings.find(s => s.setting_key === key);
            return found ? found.setting_value : '';
        };
        
        setGeneralConfig({
            free_shipping_threshold: getValue('free_shipping_threshold'),
            return_window_days: getValue('return_window_days')
        });

        // B. Load Phương thức vận chuyển
        const methodsRes = await systemApi.getShippingMethods();
        // Xử lý dữ liệu trả về linh hoạt (đề phòng backend trả về mảng hoặc object)
        let methodsData = [];
        if (Array.isArray(methodsRes)) {
            methodsData = methodsRes;
        } else if (methodsRes.data && Array.isArray(methodsRes.data)) {
            methodsData = methodsRes.data;
        } else if (methodsRes.items) {
            methodsData = methodsRes.items;
        }
        
        setMethods(methodsData);

      } catch (error) {
        console.error("Lỗi tải dữ liệu vận chuyển:", error);
      } finally {
        setLoadingMethods(false);
      }
    };
    fetchData();
  }, []);

  // --- 2. XỬ LÝ LƯU CẤU HÌNH CHUNG ---
  const handleConfigChange = (e) => {
    setGeneralConfig({ ...generalConfig, [e.target.name]: e.target.value });
  };

  const saveGeneralConfig = async () => {
    try {
      setSavingConfig(true);
      // Gọi API setValue theo đúng systemApi đại ca gửi
      await Promise.all([
        systemApi.setValue('free_shipping_threshold', generalConfig.free_shipping_threshold),
        systemApi.setValue('return_window_days', generalConfig.return_window_days)
      ]);
      alert(" Đã lưu cấu hình chung!");
    } catch (error) {
      console.error(error);
      alert(" Lỗi lưu cấu hình: " + (error.response?.data?.detail || error.message));
    } finally {
      setSavingConfig(false);
    }
  };

  // --- 3. XỬ LÝ QUẢN LÝ PHƯƠNG THỨC (CRUD) ---
  const handleMethodChange = (e) => {
    const { name, value, type, checked } = e.target;
    setMethodForm(prev => ({
        ...prev,
        [name]: type === 'checkbox' ? checked : value
    }));
  };

  const openAddModal = () => {
    setIsEditing(false);
    setMethodForm({ method_name: '', description: '', base_cost: 0, estimated_days: '', is_active: true });
    setShowModal(true);
  };

  const openEditModal = (item) => {
    setIsEditing(true);
    setCurrentId(item.shipping_method_id || item.id);
    setMethodForm({
        method_name: item.method_name,
        description: item.description || '',
        base_cost: Number(item.base_cost),
        estimated_days: item.estimated_days || '',
        is_active: Boolean(item.is_active)
    });
    setShowModal(true);
  };

  const handleMethodSubmit = async (e) => {
    e.preventDefault();
    const payload = { ...methodForm, base_cost: Number(methodForm.base_cost) };
    
    try {
        if (isEditing) {
            await systemApi.updateShippingMethod(currentId, payload);
            alert(" Cập nhật thành công!");
        } else {
            await systemApi.createShippingMethod(payload);
            alert(" Thêm mới thành công!");
        }
        setShowModal(false);
        
        // Reload danh sách
        const res = await systemApi.getShippingMethods();
        let methodsData = [];
        if (Array.isArray(res)) methodsData = res;
        else if (res.data) methodsData = res.data;
        
        setMethods(methodsData);
    } catch (error) {
        alert(" Lỗi: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleDeleteMethod = async (item) => {
    const idToDelete = item.shipping_method_id || item.id;
    if (window.confirm(`Xóa phương thức "${item.method_name}"?`)) {
        try {
            await systemApi.deleteShippingMethod(idToDelete);
            setMethods(prev => prev.filter(m => (m.shipping_method_id || m.id) !== idToDelete));
        } catch (error) {
            alert(" Không thể xóa (Có thể đang được sử dụng).");
        }
    }
  };

  const formatMoney = (val) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val || 0);

  return (
    <div className="shipping-settings-container">
      
      {/* PHẦN 1: CẤU HÌNH CHUNG (FREESHIP & RETURN) */}
      <div className="settings-card mb-4" style={{marginBottom: '20px'}}>
        <div className="card-header">
            <h3> Cấu hình Vận chuyển & Đổi trả</h3>
            <p className="text-muted">Thiết lập ngưỡng miễn phí vận chuyển và chính sách đổi trả hàng.</p>
        </div>
        <div className="card-body">
            <div className="form-row" style={{display: 'flex', gap: '20px', marginBottom: '15px'}}>
                <div className="form-group half" style={{flex: 1}}>
                    <label>Ngưỡng miễn phí vận chuyển (VNĐ)</label>
                    <input 
                        type="number" 
                        name="free_shipping_threshold" 
                        className="form-control"
                        value={generalConfig.free_shipping_threshold} 
                        onChange={handleConfigChange}
                        placeholder="VD: 500000"
                    />
                    <small className="text-muted" style={{display:'block', marginTop:'5px', fontSize:'12px'}}>Đơn hàng trên mức này sẽ được FreeShip.</small>
                </div>
                <div className="form-group half" style={{flex: 1}}>
                    <label>Thời gian đổi trả (Ngày)</label>
                    <input 
                        type="number" 
                        name="return_window_days" 
                        className="form-control"
                        value={generalConfig.return_window_days} 
                        onChange={handleConfigChange}
                        placeholder="VD: 7"
                    />
                    <small className="text-muted" style={{display:'block', marginTop:'5px', fontSize:'12px'}}>Số ngày khách hàng được phép yêu cầu hoàn trả.</small>
                </div>
            </div>
            <div style={{textAlign: 'right'}}>
                <button className="btn-primary" onClick={saveGeneralConfig} disabled={savingConfig}>
                    {savingConfig ? 'Đang lưu...' : 'Lưu cấu hình chung'}
                </button>
            </div>
        </div>
      </div>

      {/* PHẦN 2: DANH SÁCH PHƯƠNG THỨC (SHIPPING METHODS) */}
      <div className="settings-card">
        <div className="card-header" style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
            <div>
                <h3> Danh sách Phương thức Vận chuyển</h3>
                <p className="text-muted">Quản lý các gói giao hàng hiển thị khi thanh toán.</p>
            </div>
            <button className="btn-primary" onClick={openAddModal}>+ Thêm mới</button>
        </div>
        
        <div className="card-body">
            {loadingMethods ? <div className="text-center p-4">⏳ Đang tải danh sách...</div> : (
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>Tên phương thức</th>
                            <th>Phí cơ bản</th>
                            <th>Thời gian</th>
                            <th>Trạng thái</th>
                            <th className="text-right">Hành động</th>
                        </tr>
                    </thead>
                    <tbody>
                        {methods.length > 0 ? methods.map((item, idx) => (
                            <tr key={idx}>
                                <td>
                                    <strong>{item.method_name}</strong>
                                    <div style={{fontSize:'12px', color:'#666'}}>{item.description}</div>
                                </td>
                                <td style={{color:'#2563eb', fontWeight:'bold'}}>{formatMoney(item.base_cost)}</td>
                                <td>{item.estimated_days}</td>
                                <td>
                                    <span className={`badge ${item.is_active ? 'badge-success' : 'badge-default'}`}>
                                        {item.is_active ? '● Đang bật' : '○ Tạm tắt'}
                                    </span>
                                </td>
                                <td className="text-right">
                                    <button className="btn-icon" onClick={() => openEditModal(item)} title="Sửa">✏️</button>
                                    <button className="btn-icon delete" onClick={() => handleDeleteMethod(item)} title="Xóa">🗑️</button>
                                </td>
                            </tr>
                        )) : (
                            <tr><td colSpan="5" className="text-center p-4">Chưa có phương thức nào.</td></tr>
                        )}
                    </tbody>
                </table>
            )}
        </div>
      </div>

      {/* MODAL THÊM/SỬA PHƯƠNG THỨC */}
      {showModal && (
          <div className="modal-overlay">
              <div className="modal-content">
                  <div className="modal-header">
                      <h4>{isEditing ? 'Sửa phương thức' : 'Thêm phương thức mới'}</h4>
                      <button className="close-btn" onClick={() => setShowModal(false)}>×</button>
                  </div>
                  <form onSubmit={handleMethodSubmit}>
                      <div className="form-group">
                          <label>Tên phương thức *</label>
                          <input required type="text" name="method_name" className="form-control" value={methodForm.method_name} onChange={handleMethodChange} placeholder="VD: Giao hàng nhanh" />
                      </div>
                      <div className="form-row" style={{display: 'flex', gap: '15px', marginBottom: '15px'}}>
                          <div className="form-group half" style={{flex: 1}}>
                              <label>Phí vận chuyển (VNĐ) *</label>
                              <input required type="number" name="base_cost" className="form-control" value={methodForm.base_cost} onChange={handleMethodChange} />
                          </div>
                          <div className="form-group half" style={{flex: 1}}>
                              <label>Thời gian ước tính</label>
                              <input type="text" name="estimated_days" className="form-control" value={methodForm.estimated_days} onChange={handleMethodChange} placeholder="VD: 2-3 ngày" />
                          </div>
                      </div>
                      <div className="form-group">
                          <label>Mô tả</label>
                          <textarea name="description" className="form-control" rows="2" value={methodForm.description} onChange={handleMethodChange}></textarea>
                      </div>
                      <div className="form-group checkbox-group" style={{background:'#f9fafb', padding:'10px', borderRadius:'6px'}}>
                          <label style={{display:'flex', alignItems:'center', cursor:'pointer', fontWeight:'bold', color: methodForm.is_active ? 'green' : '#666'}}>
                              <input 
                                type="checkbox" name="is_active" 
                                checked={methodForm.is_active} onChange={handleMethodChange} 
                                style={{marginRight:'10px', width:'18px', height:'18px'}} 
                              />
                              {methodForm.is_active ? 'Kích hoạt ngay' : 'Tạm ẩn phương thức này'}
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

export default ShippingSettings;