import React, { useState, useEffect } from 'react';
import marketingApi from '../../../api/marketingApi';

const FlashSaleManager = () => {
  const [sales, setSales] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // State cho Modal TẠO MỚI
  const [showModal, setShowModal] = useState(false);
  const [products, setProducts] = useState([]); 
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    sale_name: '', description: '', start_time: '', end_time: '',
    discount_type: 'PERCENTAGE', discount_value: '', is_active: true, selected_products: [] 
  });

  // State cho Modal XEM CHI TIẾT
  const [viewingSale, setViewingSale] = useState(null); 

  // --- 1. Load danh sách Flash Sale ---
  const fetchSales = async () => {
    try {
      setLoading(true);
      const res = await marketingApi.getAllFlashSales({ _t: Date.now() });
      setSales(Array.isArray(res) ? res : (res.data || []));
    } catch (error) { console.error(error); } finally { setLoading(false); }
  };

  // --- 2. Load sản phẩm để chọn ---
  const fetchProducts = async () => {
    try {
      const res = await marketingApi.getProductsForSelection();
      setProducts(Array.isArray(res) ? res : (res.data || res.items || []));
    } catch (error) { console.error("Lỗi tải SP:", error); }
  };

  useEffect(() => { fetchSales(); }, []);

  // --- HÀM XỬ LÝ CHI TIẾT (MỚI) ---
  const handleViewDetail = async (id) => {
    try {
        setLoading(true);
        // Gọi API lấy chi tiết Flash Sale (Kèm danh sách sản phẩm bên trong)
        const res = await marketingApi.getFlashSaleById(id);
        setViewingSale(res.data || res);
    } catch (error) {
        alert("Lỗi tải chi tiết: " + error.message);
    } finally {
        setLoading(false);
    }
  };

  // --- FORM HANDLERS (TẠO MỚI) ---
  const handleInitCreate = () => {
    setStep(1);
    setFormData({
        sale_name: '', description: '', start_time: '', end_time: '',
        discount_type: 'PERCENTAGE', discount_value: '', is_active: true, selected_products: []
    });
    fetchProducts();
    setShowModal(true);
  };

  const handleInput = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

  const toggleProduct = (prodId) => {
    const exists = formData.selected_products.find(p => p.product_id === prodId);
    let newSelection;
    if (exists) {
        newSelection = formData.selected_products.filter(p => p.product_id !== prodId);
    } else {
        newSelection = [...formData.selected_products, { product_id: prodId, quantity_limit: 10 }];
    }
    setFormData({ ...formData, selected_products: newSelection });
  };

  const handleLimitChange = (prodId, val) => {
    const newSelection = formData.selected_products.map(p => 
        p.product_id === prodId ? { ...p, quantity_limit: parseInt(val) || 0 } : p
    );
    setFormData({ ...formData, selected_products: newSelection });
  };

  const handleSubmit = async () => {
    try {
        setLoading(true);
        const salePayload = {
            sale_name: formData.sale_name,
            description: formData.description,
            start_time: new Date(formData.start_time).toISOString(),
            end_time: new Date(formData.end_time).toISOString(),
            discount_type: formData.discount_type,
            discount_value: Number(formData.discount_value),
            is_active: formData.is_active
        };

        const resCreate = await marketingApi.createFlashSale(salePayload);
        const newSaleId = resCreate.flash_sale_id || resCreate.id || resCreate.data?.flash_sale_id;

        if (!newSaleId) throw new Error("Không lấy được ID sau khi tạo!");

        const addPromises = formData.selected_products.map(prod => 
            marketingApi.addProductToFlashSale(newSaleId, {
                product_id: prod.product_id,
                quantity_limit: prod.quantity_limit
            })
        );

        await Promise.all(addPromises);
        alert("Tạo chương trình thành công!");
        setShowModal(false);
        fetchSales();
    } catch (error) {
        alert("Lỗi: " + (error.response?.data?.detail || error.message));
    } finally {
        setLoading(false);
    }
  };

  const handleDelete = async (id) => {
      if(window.confirm("Xóa chương trình này?")) {
          try {
            await marketingApi.deleteFlashSale(id);
            fetchSales();
          } catch (e) { alert("Lỗi xóa: " + e.message); }
      }
  }

  const isSelected = (id) => formData.selected_products.find(p => p.product_id === id);
  const formatMoney = (val) => new Intl.NumberFormat('vi-VN').format(val || 0);

  return (
    <div className="flash-sale-manager">
      <div className="fs-header" style={{display:'flex', justifyContent:'space-between', marginBottom:'20px'}}>
        <h3>Danh sách Flash Sale</h3>
        <button className="btn-create flash-btn" onClick={handleInitCreate}> Tạo Flash Sale Mới</button>
      </div>

      <div className="coupon-grid">
        {loading && sales.length === 0 && <p>Đang tải...</p>}
        {sales.map(sale => (
            <div key={sale.flash_sale_id} className="coupon-card flash-card">
                <div className="coupon-left flash-left">
                    <div className="coupon-value"></div>
                    <span className="off-label" style={{fontSize:'13px', fontWeight:'bold'}}>
                        {sale.discount_type === 'PERCENTAGE' ? `-${sale.discount_value}%` : `-${formatMoney(sale.discount_value)}`}
                    </span>
                </div>
                <div className="coupon-right">
                    <div className="coupon-header">
                        <span className="code-text" style={{background:'#fff3cd', color:'#856404', border:'none'}}>{sale.sale_name}</span>
                        <span className={`status-tag ${sale.is_active ? 'active' : 'inactive'}`}>
                            {sale.is_active ? 'Đang chạy' : 'Đã tắt'}
                        </span>
                    </div>
                    <div className="coupon-desc">
                        <div style={{fontSize:'13px'}}>{sale.description || 'Không có mô tả'}</div>
                        <div style={{fontSize:'12px', color:'#666', marginTop:'5px'}}>
                           Start: {new Date(sale.start_time).toLocaleString('vi-VN')}
                        </div>
                    </div>
                    <div className="coupon-footer">
                        <div className="expiry-date" style={{color:'#d9534f', fontWeight:'bold'}}>
                           End: {new Date(sale.end_time).toLocaleString('vi-VN')}
                        </div>
                        <div className="actions">
                            {/*  NÚT CHI TIẾT MỚI THÊM */}
                            <button className="btn-icon view" title="Xem chi tiết" onClick={() => handleViewDetail(sale.flash_sale_id)}>👁️</button>
                            <button className="btn-icon delete" title="Xóa" onClick={() => handleDelete(sale.flash_sale_id)}>🗑️</button>
                        </div>
                    </div>
                </div>
            </div>
        ))}
      </div>

      {/* --- MODAL 1: TẠO MỚI (GIỮ NGUYÊN) --- */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content" style={{width:'750px', maxWidth:'95%'}}>
            <div className="modal-header">
                <h4>{step === 1 ? 'Bước 1: Cài đặt chung' : 'Bước 2: Chọn sản phẩm & Số lượng'}</h4>
                <button className="close-btn" onClick={() => setShowModal(false)}>×</button>
            </div>
            {/* ... (Nội dung modal tạo mới giữ nguyên như code cũ) ... */}
            {step === 1 && (
                <div>
                    <div className="form-group"><label>Tên chương trình *</label><input type="text" name="sale_name" className="form-control" value={formData.sale_name} onChange={handleInput} placeholder="VD: Flash Sale 12h trưa" /></div>
                    <div className="form-row">
                        <div className="form-group half"><label>Bắt đầu</label><input type="datetime-local" name="start_time" className="form-control" value={formData.start_time} onChange={handleInput} /></div>
                        <div className="form-group half"><label>Kết thúc</label><input type="datetime-local" name="end_time" className="form-control" value={formData.end_time} onChange={handleInput} /></div>
                    </div>
                    <div className="form-row">
                        <div className="form-group half"><label>Loại giảm giá</label><select name="discount_type" className="form-control" value={formData.discount_type} onChange={handleInput}><option value="PERCENTAGE">Theo Phần trăm (%)</option><option value="FIXED_AMOUNT">Theo Tiền mặt (VNĐ)</option></select></div>
                        <div className="form-group half"><label>Giá trị giảm</label><input type="number" name="discount_value" className="form-control" value={formData.discount_value} onChange={handleInput} /></div>
                    </div>
                    <div className="modal-actions"><button className="btn-primary" onClick={() => setStep(2)}>Tiếp theo &rarr;</button></div>
                </div>
            )}
            {step === 2 && (
                <div>
                    <div style={{marginBottom:'10px', fontStyle:'italic', color:'#666'}}>Chọn sản phẩm tham gia và đặt giới hạn số lượng bán.</div>
                    <div className="product-list-scroll" style={{maxHeight:'400px', overflowY:'auto', border:'1px solid #eee', padding:'0', borderRadius:'6px'}}>
                        <table className="data-table" style={{marginTop:0}}>
                            <thead><tr><th width="40">#</th><th>Sản phẩm</th><th>Giá gốc</th><th>Giới hạn SL bán</th></tr></thead>
                            <tbody>
                                {products.map(p => {
                                    const prodId = p.product_id || p.id;
                                    const selected = isSelected(prodId);
                                    return (
                                        <tr key={prodId} style={{background: selected ? '#fffbf0' : 'white'}}>
                                            <td><input type="checkbox" checked={!!selected} onChange={() => toggleProduct(prodId)} style={{width:'18px', height:'18px', cursor:'pointer'}} /></td>
                                            <td><div style={{fontWeight:'600'}}>{p.product_name || p.name}</div><small style={{color:'#888'}}>Kho: {p.stock_quantity || p.quantity || 0}</small></td>
                                            <td>{formatMoney(p.price)}</td>
                                            <td><input type="number" disabled={!selected} value={selected ? selected.quantity_limit : ''} onChange={(e) => handleLimitChange(prodId, e.target.value)} className="form-control" style={{width:'100px', padding:'5px', height:'35px'}} placeholder="Limit" /></td>
                                        </tr>
                                    )
                                })}
                            </tbody>
                        </table>
                    </div>
                    <div style={{marginTop:'15px', display:'flex', justifyContent:'space-between', alignItems:'center'}}>
                        <span>Đã chọn: <strong>{formData.selected_products.length}</strong> món</span>
                        <div style={{display:'flex', gap:'10px'}}><button className="btn-secondary" onClick={() => setStep(1)}>&larr; Quay lại</button><button className="btn-primary" onClick={handleSubmit} disabled={loading}>{loading ? 'Đang xử lý...' : 'Hoàn tất & Lưu'}</button></div>
                    </div>
                </div>
            )}
          </div>
        </div>
      )}

      {/* ---  MODAL 2: XEM CHI TIẾT (MỚI) --- */}
      {viewingSale && (
        <div className="modal-overlay">
            <div className="modal-content" style={{width:'800px', maxWidth:'95%'}}>
                <div className="modal-header">
                    <h4>Chi tiết: {viewingSale.sale_name}</h4>
                    <button className="close-btn" onClick={() => setViewingSale(null)}>×</button>
                </div>
                
                {/* Thông tin chung */}
                <div style={{background:'#f9fafb', padding:'15px', borderRadius:'8px', marginBottom:'20px', display:'flex', gap:'30px', border:'1px solid #e5e7eb'}}>
                    <div>
                        <div style={{fontSize:'12px', color:'#666'}}>Trạng thái</div>
                        <span className={`status-tag ${viewingSale.is_active ? 'active' : 'inactive'}`}>
                            {viewingSale.is_active ? 'Đang chạy' : 'Đã kết thúc'}
                        </span>
                    </div>
                    <div>
                        <div style={{fontSize:'12px', color:'#666'}}>Mức giảm</div>
                        <strong style={{color:'#d97706', fontSize:'16px'}}>
                            {viewingSale.discount_type === 'PERCENTAGE' ? `Giảm ${viewingSale.discount_value}%` : `Giảm ${formatMoney(viewingSale.discount_value)}`}
                        </strong>
                    </div>
                    <div>
                         <div style={{fontSize:'12px', color:'#666'}}>Thời gian</div>
                         <div style={{fontSize:'13px'}}>
                            {new Date(viewingSale.start_time).toLocaleString('vi-VN')} <br/>
                            &darr; <br/>
                            {new Date(viewingSale.end_time).toLocaleString('vi-VN')}
                         </div>
                    </div>
                </div>

                {/* Danh sách sản phẩm */}
                <h5 style={{marginBottom:'10px', fontSize:'15px', borderLeft:'4px solid #4361ee', paddingLeft:'10px'}}>📦 Sản phẩm tham gia ({viewingSale.products?.length || 0})</h5>
                <div className="product-list-scroll" style={{maxHeight:'350px', overflowY:'auto', border:'1px solid #eee'}}>
                    <table className="data-table" style={{margin:0}}>
                        <thead>
                            <tr>
                                <th>Tên sản phẩm</th>
                                <th>Giá gốc</th>
                                <th style={{color:'#d97706'}}>Giá Sale</th>
                                <th>Giới hạn</th>
                                <th>Đã bán</th>
                            </tr>
                        </thead>
                        <tbody>
                            {viewingSale.products && viewingSale.products.length > 0 ? viewingSale.products.map((p, idx) => {
                                // Tính giá sau giảm để hiển thị chơi cho đẹp
                                let salePrice = p.price; 
                                if (viewingSale.discount_type === 'PERCENTAGE') {
                                    salePrice = p.price * (1 - viewingSale.discount_value / 100);
                                } else {
                                    salePrice = p.price - viewingSale.discount_value;
                                }

                                return (
                                    <tr key={idx}>
                                        <td>
                                            <strong>{p.product_name}</strong>
                                        </td>
                                        <td style={{textDecoration:'line-through', color:'#999'}}>{formatMoney(p.price)}</td>
                                        <td style={{fontWeight:'bold', color:'#d97706'}}>{formatMoney(salePrice)}</td>
                                        <td>{p.quantity_limit}</td>
                                        <td>{p.quantity_sold}</td>
                                    </tr>
                                );
                            }) : (
                                <tr><td colSpan="5" className="text-center">Chưa có sản phẩm nào.</td></tr>
                            )}
                        </tbody>
                    </table>
                </div>

                <div className="modal-actions">
                    <button className="btn-secondary" onClick={() => setViewingSale(null)}>Đóng</button>
                </div>
            </div>
        </div>
      )}

    </div>
  );
};

export default FlashSaleManager;