import React, { useState, useEffect } from 'react';
import inventoryApi from '../../../api/inventoryApi';
import './Inventory.css';

const Inventory = () => {
  const [activeTab, setActiveTab] = useState('warehouses');
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);

  // --- STATE MODAL ---
  const [showModal, setShowModal] = useState(false);
  const [showTransModal, setShowTransModal] = useState(false);

  // State Form Kho
  const [isEditMode, setIsEditMode] = useState(false);
  const [currentId, setCurrentId] = useState(null);
  const [formData, setFormData] = useState({
    warehouse_name: '', address: '', city: '', postal_code: '', phone: '', email: '', is_active: true
  });

  // State Form Giao Dịch
  const [transData, setTransData] = useState({
    warehouse_id: '', variant_id: '', transaction_type: 'IMPORT', quantity: 1, note: ''
  });

  // =================================================================
  // 1. HÀM LOAD DỮ LIỆU (ĐÃ THÊM CHỐNG CACHE)
  // =================================================================
  const fetchData = async () => {
    setLoading(true);
    try {
      
      const noCacheParams = { _t: new Date().getTime() }; 
      
      let res;
      if (activeTab === 'warehouses') {
        res = await inventoryApi.getAll(noCacheParams);
      } else {
        res = await inventoryApi.getTransactions(noCacheParams);
      }
      
      // Log ra xem dữ liệu về là gì
      console.log("Dữ liệu mới từ Server:", res); 

      // Xử lý mọi trường hợp dữ liệu trả về
      let list = [];
      if (Array.isArray(res)) {
          list = res;
      } else if (res && Array.isArray(res.data)) {
          list = res.data;
      } else if (res && Array.isArray(res.items)) {
          list = res.items;
      }

      setData(list);
    } catch (error) {
      console.warn("Lỗi tải dữ liệu:", error);
      setData([]); 
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  // =================================================================
  // 2. XỬ LÝ CRUD KHO (FIX LỖI KHÔNG CẬP NHẬT)
  // =================================================================
  const handleOpenCreate = () => {
      setIsEditMode(false);
      setFormData({ warehouse_name: '', address: '', city: '', postal_code: '', phone: '', email: '', is_active: true });
      setShowModal(true);
  };

  const handleOpenEdit = (item) => {
      setIsEditMode(true);
      setCurrentId(item.warehouse_id);
      setFormData({
          warehouse_name: item.warehouse_name || '',
          address: item.address || '',
          city: item.city || '',
          postal_code: item.postal_code || '',
          phone: item.phone || '',
          email: item.email || '',
          is_active: item.is_active
      });
      setShowModal(true);
  };

  const handleSubmitWarehouse = async (e) => {
    e.preventDefault();
    // Làm sạch dữ liệu trước khi gửi
    const payload = {
        ...formData,
        email: formData.email === '' ? null : formData.email,
        phone: formData.phone === '' ? null : formData.phone,
        city: formData.city === '' ? null : formData.city,
        postal_code: formData.postal_code === '' ? null : formData.postal_code
    };

    try {
        if (isEditMode) {
            await inventoryApi.update(currentId, payload);
            alert('Cập nhật thành công! ');
        } else {
            await inventoryApi.create(payload);
            alert('Thêm kho mới thành công! ');
        }
        
        setShowModal(false);

        setData([]); 
        setTimeout(() => {
            fetchData();
        }, 300);

    } catch (error) {
        console.error("Lỗi Save:", error);
        const msg = error.response?.data?.detail 
            ? JSON.stringify(error.response.data.detail) 
            : error.message;
        alert('Lỗi: ' + msg);
    }
  };

  // =================================================================
  // 3. XỬ LÝ NHẬP/XUẤT (GỌI API THẬT /inventory/adjust)
  // =================================================================
  const handleOpenTrans = () => {
    const defaultWh = (activeTab === 'warehouses' && data.length > 0) ? data[0].warehouse_id : '';
    setTransData({ warehouse_id: defaultWh, variant_id: '', transaction_type: 'IMPORT', quantity: 1, note: '' });
    setShowTransModal(true);
  };

  const handleSubmitTrans = async (e) => {
    e.preventDefault();
    const payload = {
        warehouse_id: parseInt(transData.warehouse_id),
        variant_id: parseInt(transData.variant_id),
        quantity: parseInt(transData.quantity),
        transaction_type: transData.transaction_type,
        note: transData.note
    };

    try {
        await inventoryApi.createTransaction(payload);
        alert('Giao dịch thành công! ');
        setShowTransModal(false);
        
        // Chuyển tab và load lại
        setActiveTab('transactions');
        setData([]); 
        setTimeout(() => fetchData(), 300);

    } catch (error) {
        console.error("Lỗi Trans:", error);
        const msg = error.response?.data?.detail || error.message;
        alert('Lỗi: ' + msg);
    }
  };

  // =================================================================
  // 4. GIAO DIỆN & UTILS
  // =================================================================
  const handleSetDefault = async (id) => { 
      if(window.confirm('Đặt kho này làm mặc định?')) { 
          await inventoryApi.setAsDefault(id); 
          setTimeout(() => fetchData(), 300);
      } 
  };
  
  const handleDelete = async (id) => { 
      if(window.confirm('CẢNH BÁO: Bạn có chắc muốn xóa kho này?')) { 
          try { 
              await inventoryApi.delete(id); 
              alert("Đã xóa thành công!");
              setData([]);
              setTimeout(() => fetchData(), 300);
          }
          catch(e) { alert("Lỗi: " + e.message); }
      } 
  };
  
  const getTransColor = (type) => ['IMPORT','RETURN','TRANSFER_IN', 'ADJUSTMENT'].includes(type) ? 'text-green bold' : 'text-red bold';

  return (
    <div className="page-container">
      <div className="page-header">
        <div><h2 className="page-title">Quản lý Kho hàng</h2></div>
        <div className="header-actions">
            <button className="btn-secondary mr-2" onClick={handleOpenTrans}>Nhập/Xuất Hàng</button>
            <button className="btn-primary" onClick={handleOpenCreate}>+ Thêm Kho</button>
        </div>
      </div>

      <div className="tabs-container">
        <button className={`tab-btn ${activeTab === 'warehouses' ? 'active' : ''}`} onClick={() => setActiveTab('warehouses')}> Danh sách Kho</button>
        <button className={`tab-btn ${activeTab === 'transactions' ? 'active' : ''}`} onClick={() => setActiveTab('transactions')}> Lịch sử GD</button>
      </div>

      <div className="table-card">
        {loading ? <div className="loading-state"> Đang tải dữ liệu mới...</div> : (
            data.length === 0 ? <div className="empty-state">Chưa có dữ liệu nào.</div> : (
                activeTab === 'warehouses' ? (
                    <table className="data-table">
                      <thead><tr><th>ID</th><th>Tên kho</th><th>Địa chỉ</th><th>Trạng thái</th><th className="text-right">Hành động</th></tr></thead>
                      <tbody>
                        {data.map((item) => (
                          <tr key={item.warehouse_id}>
                            <td>#{item.warehouse_id}</td>
                            <td><strong>{item.warehouse_name}</strong>{item.is_default && <span className="badge-default">Mặc định</span>}</td>
                            <td>{item.address} <br/><small className="text-muted">{item.city}</small></td>
                            <td><span className={`status-pill ${item.is_active ? 'active' : 'inactive'}`}>{item.is_active ? 'Hoạt động' : 'Đã khóa'}</span></td>
                            <td className="text-right action-cell">
                               {!item.is_default && <button className="btn-icon text-blue" onClick={() => handleSetDefault(item.warehouse_id)}>⭐</button>}
                               <button className="btn-icon" onClick={() => handleOpenEdit(item)}>✏️</button>
                               <button className="btn-icon text-red" onClick={() => handleDelete(item.warehouse_id)}>🗑️</button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                ) : (
                    <table className="data-table">
                        <thead><tr><th>Mã GD</th><th>Loại</th><th>SP (ID)</th><th>Số lượng</th><th>Kho</th><th>Thời gian</th></tr></thead>
                        <tbody>
                            {data.map((item) => (
                                <tr key={item.transaction_id}>
                                    <td>#{item.transaction_id}</td>
                                    <td><span className={`trans-type ${item.transaction_type}`}>{item.transaction_type}</span></td>
                                    <td>SP-{item.variant_id}</td>
                                    <td className={getTransColor(item.transaction_type)}>{item.quantity > 0 ? `+${item.quantity}` : item.quantity}</td>
                                    <td>Kho #{item.warehouse_id}</td>
                                    <td>{new Date(item.created_at).toLocaleString('vi-VN')}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )
            )
        )}
      </div>

      {/* MODAL 1: KHO */}
      {showModal && (
        <div className="modal-backdrop" onClick={() => setShowModal(false)}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                <div className="modal-header"><h3>{isEditMode ? 'Sửa Kho' : 'Thêm Kho'}</h3><button onClick={() => setShowModal(false)}>&times;</button></div>
                <form onSubmit={handleSubmitWarehouse}>
                    <div className="modal-body">
                        <div className="form-group"><label>Tên kho *</label><input type="text" value={formData.warehouse_name} onChange={e => setFormData({...formData, warehouse_name: e.target.value})} required /></div>
                        <div className="form-group"><label>Địa chỉ</label><input type="text" value={formData.address} onChange={e => setFormData({...formData, address: e.target.value})} /></div>
                        <div className="form-row">
                            <div className="form-group half"><label>Thành phố</label><input type="text" value={formData.city} onChange={e => setFormData({...formData, city: e.target.value})} /></div>
                            <div className="form-group half"><label>ZIP Code</label><input type="text" value={formData.postal_code} onChange={e => setFormData({...formData, postal_code: e.target.value})} /></div>
                        </div>
                        <div className="form-row">
                             <div className="form-group half"><label>SĐT</label><input type="text" value={formData.phone} onChange={e => setFormData({...formData, phone: e.target.value})} /></div>
                             <div className="form-group half"><label>Email</label><input type="email" value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} /></div>
                        </div>
                        <div className="form-group checkbox-group"><input type="checkbox" checked={formData.is_active} onChange={e => setFormData({...formData, is_active: e.target.checked})} /><label>Hoạt động</label></div>
                    </div>
                    <div className="modal-footer"><button type="submit" className="btn-primary">Lưu lại</button></div>
                </form>
            </div>
        </div>
      )}

      {/* MODAL 2: GIAO DỊCH */}
      {showTransModal && (
        <div className="modal-backdrop" onClick={() => setShowTransModal(false)}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                <div className="modal-header"><h3> Tạo Giao Dịch</h3><button onClick={() => setShowTransModal(false)}>&times;</button></div>
                <form onSubmit={handleSubmitTrans}>
                    <div className="modal-body">
                        <div className="form-group">
                            <label>Loại giao dịch *</label>
                            <select value={transData.transaction_type} onChange={e => setTransData({...transData, transaction_type: e.target.value})} style={{width:'100%', padding:'10px'}}>
                                <option value="IMPORT">Nhập hàng (Import)</option>
                                <option value="TRANSFER_OUT"> Xuất hàng (Export)</option>
                                <option value="SALE"> Bán hàng (Sale)</option>
                                <option value="RETURN">Hoàn trả (Return)</option>
                            </select>
                        </div>
                        <div className="form-row">
                            <div className="form-group half"><label>ID Kho *</label><input type="number" value={transData.warehouse_id} onChange={e => setTransData({...transData, warehouse_id: e.target.value})} required /></div>
                            <div className="form-group half"><label>ID SP *</label><input type="number" value={transData.variant_id} onChange={e => setTransData({...transData, variant_id: e.target.value})} required /></div>
                        </div>
                        <div className="form-group"><label>Số lượng *</label><input type="number" value={transData.quantity} onChange={e => setTransData({...transData, quantity: e.target.value})} required /></div>
                        <div className="form-group"><label>Ghi chú</label><input type="text" value={transData.note} onChange={e => setTransData({...transData, note: e.target.value})} /></div>
                    </div>
                    <div className="modal-footer"><button type="submit" className="btn-primary">Xác nhận</button></div>
                </form>
            </div>
        </div>
      )}
    </div>
  );
};

export default Inventory;