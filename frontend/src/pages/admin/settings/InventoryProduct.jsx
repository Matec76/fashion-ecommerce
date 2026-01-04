import React, { useState, useEffect } from 'react';
import systemApi from '../../../api/systemApi';

const InventoryProduct = () => {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  // KEY CHUẨN TỪ DATABASE
  const KEYS = {
    LOW_STOCK: 'low_stock_threshold',           // Cảnh báo sắp hết hàng
    CART_MAX: 'cart_max_item_qty',              // Max số lượng 1 món trong giỏ
    FEATURED_LIMIT: 'featured_products_limit',  // Số SP nổi bật hiển thị
    RELATED_LIMIT: 'related_products_limit',    // Số SP liên quan hiển thị
    SEARCH_MIN: 'search_min_query_length'       // Độ dài từ khóa tìm kiếm tối thiểu
  };

  const [formData, setFormData] = useState({
    low_stock: '',
    cart_max: '',
    featured_limit: '',
    related_limit: '',
    search_min: ''
  });

  // Load dữ liệu
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const res = await systemApi.getAll();
        const settings = Array.isArray(res) ? res : (res.data || []);
        
        const getValue = (key) => {
            const found = settings.find(s => s.setting_key === key);
            return found ? found.setting_value : '';
        };

        setFormData({
            low_stock: getValue(KEYS.LOW_STOCK),
            cart_max: getValue(KEYS.CART_MAX),
            featured_limit: getValue(KEYS.FEATURED_LIMIT),
            related_limit: getValue(KEYS.RELATED_LIMIT),
            search_min: getValue(KEYS.SEARCH_MIN)
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
      await Promise.all([
        systemApi.setValue(KEYS.LOW_STOCK, formData.low_stock),
        systemApi.setValue(KEYS.CART_MAX, formData.cart_max),
        systemApi.setValue(KEYS.FEATURED_LIMIT, formData.featured_limit),
        systemApi.setValue(KEYS.RELATED_LIMIT, formData.related_limit),
        systemApi.setValue(KEYS.SEARCH_MIN, formData.search_min)
      ]);
      alert(" Đã lưu cấu hình Sản phẩm & Kho!");
    } catch (error) {
      alert(" Lỗi: " + error.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="p-4 text-center"> Đang tải cấu hình...</div>;

  return (
    <div className="settings-card">
      <div className="card-header">
        <h3> Cấu hình Sản phẩm & Kho hàng</h3>
        <p className="text-muted">Thiết lập các thông số hiển thị và vận hành kho.</p>
      </div>
      
      <div className="card-body">
        
        {/* NHÓM 1: KHO HÀNG & GIỎ HÀNG */}
        <h4 style={{marginBottom: '15px', borderBottom: '1px solid #eee', paddingBottom: '5px', color: '#2b2d42'}}>Kho & Giỏ hàng</h4>
        <div className="form-row" style={{display: 'flex', gap: '20px', marginBottom: '20px'}}>
            <div className="form-group half" style={{flex: 1}}>
                <label>Ngưỡng cảnh báo sắp hết hàng (Low Stock)</label>
                <input 
                    type="number" name="low_stock" className="form-control" 
                    value={formData.low_stock} onChange={handleChange} 
                    placeholder="VD: 5"
                />
                <small className="text-muted" style={{fontSize: '12px', marginTop: '5px', display: 'block'}}>
                    Khi tồn kho dưới mức này, hệ thống sẽ báo đỏ trong trang quản lý.
                </small>
            </div>
            <div className="form-group half" style={{flex: 1}}>
                <label>Giới hạn số lượng mua (Max Qty/Item)</label>
                <input 
                    type="number" name="cart_max" className="form-control" 
                    value={formData.cart_max} onChange={handleChange} 
                    placeholder="VD: 99"
                />
                <small className="text-muted" style={{fontSize: '12px', marginTop: '5px', display: 'block'}}>
                    Số lượng tối đa khách được phép chọn cho 1 sản phẩm trong giỏ hàng.
                </small>
            </div>
        </div>

        {/* NHÓM 2: HIỂN THỊ WEBSITE */}
        <h4 style={{marginBottom: '15px', borderBottom: '1px solid #eee', paddingBottom: '5px', color: '#2b2d42'}}>Hiển thị Website</h4>
        <div className="form-row" style={{display: 'flex', gap: '20px', marginBottom: '20px'}}>
            <div className="form-group half" style={{flex: 1}}>
                <label>Số lượng Sản phẩm Nổi bật (Home)</label>
                <input 
                    type="number" name="featured_limit" className="form-control" 
                    value={formData.featured_limit} onChange={handleChange} 
                />
            </div>
            <div className="form-group half" style={{flex: 1}}>
                <label>Số lượng Sản phẩm Liên quan (Detail)</label>
                <input 
                    type="number" name="related_limit" className="form-control" 
                    value={formData.related_limit} onChange={handleChange} 
                />
            </div>
        </div>

        {/* NHÓM 3: TÌM KIẾM */}
        <h4 style={{marginBottom: '15px', borderBottom: '1px solid #eee', paddingBottom: '5px', color: '#2b2d42'}}>Tìm kiếm</h4>
        <div className="form-group" style={{maxWidth: '50%'}}>
            <label>Độ dài từ khóa tối thiểu</label>
            <input 
                type="number" name="search_min" className="form-control" 
                value={formData.search_min} onChange={handleChange} 
                placeholder="VD: 2"
            />
            <small className="text-muted" style={{fontSize: '12px', marginTop: '5px', display: 'block'}}>
                Khách hàng phải nhập ít nhất bao nhiêu ký tự thì hệ thống mới bắt đầu tìm kiếm.
            </small>
        </div>

        <div className="form-actions text-right" style={{marginTop: '30px', textAlign: 'right', borderTop: '1px solid #f3f4f6', paddingTop: '20px'}}>
            <button className="btn-primary" onClick={handleSave} disabled={saving}>
                {saving ? 'Đang lưu...' : 'Lưu thay đổi'}
            </button>
        </div>
      </div>
    </div>
  );
};

export default InventoryProduct;