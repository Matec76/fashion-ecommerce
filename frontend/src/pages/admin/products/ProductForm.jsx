import React, { useState, useEffect } from 'react';
import productApi from '../../../api/productApi';
import ProductImageManager from './ProductImageManager';
import './Products.css';

const ProductForm = ({ onClose, onSuccess, initialData }) => {
  // State form dữ liệu
  const [formData, setFormData] = useState({
    product_name: '', slug: '', category_id: '', description: '',
    base_price: 0, sale_price: 0, cost_price: 0,
    brand: '', collection: '', gender: 'MEN',
    is_active: true, is_featured: false, is_new_arrival: false,
    meta_title: '', meta_keywords: '', meta_description: ''
  });

  // State cho dropdown
  const [categories, setCategories] = useState([]);
  const [collections, setCollections] = useState([]);
  
  // Trạng thái loading
  const [loading, setLoading] = useState(false);
  const [loadingText, setLoadingText] = useState('💾 Lưu thông tin');

  //  STATE MỚI: Lưu các file ảnh được chọn khi TẠO MỚI
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [previewUrls, setPreviewUrls] = useState([]);

  // 1. Load danh mục & collection
  useEffect(() => {
    const fetchInitData = async () => {
        try {
            const [catRes, colRes] = await Promise.all([productApi.getCategories(), productApi.getCollections()]);
            setCategories(Array.isArray(catRes) ? catRes : (catRes.data || []));
            setCollections(Array.isArray(colRes) ? colRes : (colRes.data || []));
        } catch (error) { console.error("Lỗi tải data chọn:", error); }
    };
    fetchInitData();
  }, []);

  // 2. Load dữ liệu khi Edit
  useEffect(() => {
    if (initialData) {
      setFormData({
        ...initialData,
        base_price: initialData.base_price || 0,
        sale_price: initialData.sale_price || 0,
        cost_price: initialData.cost_price || 0,
        is_new_arrival: initialData.is_new_arrival || false,
        category_id: initialData.category_id || '',
        collection: initialData.collection || '',
        gender: initialData.gender || 'MEN' 
      });
    }
    // Reset file khi mở form
    setSelectedFiles([]);
    setPreviewUrls([]);
  }, [initialData]);

  // Xử lý thay đổi input text/checkbox
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
  };

  //  HÀM MỚI: Xử lý chọn file ảnh (cho phần tạo mới)
  const handleFileSelect = (e) => {
      const files = Array.from(e.target.files);
      if (files.length === 0) return;

      // Lưu file để upload sau
      setSelectedFiles(prev => [...prev, ...files]);

      // Tạo URL preview để hiện ảnh chơi
      //  ĐÃ SỬA LỖI Ở DÒNG NÀY (newPreviews viết liền)
      const newPreviews = files.map(file => URL.createObjectURL(file));
      setPreviewUrls(prev => [...prev, ...newPreviews]);
  };

  // Xóa ảnh khỏi danh sách chọn (trước khi upload)
  const handleRemoveSelected = (index) => {
      setSelectedFiles(prev => prev.filter((_, i) => i !== index));
      URL.revokeObjectURL(previewUrls[index]); // Xóa cache bộ nhớ
      setPreviewUrls(prev => prev.filter((_, i) => i !== index));
  };


  // --- SUBMIT FORM ---
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setLoadingText('⏳ Đang xử lý...');

    // Chuẩn hóa payload
    const payload = {
        ...formData,
        base_price: Number(formData.base_price),
        sale_price: Number(formData.sale_price || 0),
        cost_price: Number(formData.cost_price || 0),
        category_id: formData.category_id ? parseInt(formData.category_id) : null,
        slug: formData.slug || formData.product_name.toLowerCase().replace(/ /g, '-').replace(/[^\w-]+/g, ''),
        brand: formData.brand || null,
        collection: formData.collection || null,
    };

    try {
      if (initialData) {
        // === TRƯỜNG HỢP 1: CHỈNH SỬA (Cũ) ===
        await productApi.update(initialData.product_id, payload);
        alert(' Cập nhật thông tin thành công!');
      } else {
        // === TRƯỜNG HỢP 2: TẠO MỚI ) ===
        
        //  Tạo sản phẩm trước để lấy ID
        setLoadingText('📦 Đang tạo sản phẩm...');
        const res = await productApi.add(payload);
        
        // Lấy ID sản phẩm vừa tạo
        const newProduct = res.data || res;
        const newProductId = newProduct?.product_id || newProduct?.id;

        if (!newProductId) throw new Error("Không lấy được ID sản phẩm mới để up ảnh!");

        // BƯỚC 2: Nếu có chọn ảnh, tiến hành upload và gắn vào ID vừa có
        if (selectedFiles.length > 0) {
            setLoadingText(`📸 Đang tải lên ${selectedFiles.length} ảnh...`);
            // Lặp qua từng file để upload (giống logic trong ProductImageManager)
            for (const file of selectedFiles) {
                try {
                    // 2.1 Upload file lên server lấy URL
                    const uploadRes = await productApi.uploadFile(file);
                    const imageUrl = uploadRes.url || uploadRes.image_url || uploadRes;
                    
                    // 2.2 Gắn URL đó vào sản phẩm
                    if (imageUrl && typeof imageUrl === 'string') {
                        await productApi.addImageToProduct(newProductId, imageUrl);
                    }
                } catch (err) {
                    console.error("Lỗi up 1 ảnh:", err);
                    // Có thể thông báo lỗi nhỏ ở đây nhưng vẫn tiếp tục các ảnh khác
                }
            }
        }
        alert(' Thêm mới sản phẩm và hình ảnh thành công!');
      }
      
      // Hoàn tất
      onSuccess();
      onClose();

    } catch (error) {
      console.error(error);
      const errorMsg = error.response?.data?.detail || error.message;
      alert(' Lỗi: ' + (typeof errorMsg === 'object' ? JSON.stringify(errorMsg) : errorMsg));
    } finally {
      setLoading(false);
      setLoadingText('💾 Lưu thông tin');
      // Dọn dẹp bộ nhớ preview url
      previewUrls.forEach(url => URL.revokeObjectURL(url));
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content product-form-modal animate-pop-in" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{initialData ? ' Chỉnh sửa sản phẩm' : ' Thêm sản phẩm mới'}</h3>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </div>

        <div className="modal-body">
          <form id="productForm" onSubmit={handleSubmit}>
            {/* 1. THÔNG TIN CHUNG */}
            <div className="form-section">
              <h4 className="section-title"> Thông tin chung</h4>
              <div className="form-grid-2">
                <div className="form-group span-2">
                  <label>Tên sản phẩm *</label>
                  <input type="text" name="product_name" value={formData.product_name} onChange={handleChange} required />
                </div>
                <div className="form-group">
                  <label>Danh mục (Category) *</label>
                  <select name="category_id" value={formData.category_id} onChange={handleChange} required className="form-control">
                    <option value="">-- Chọn danh mục --</option>
                    {categories.map(cat => (<option key={cat.category_id} value={cat.category_id}>{cat.category_name}</option>))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Slug</label>
                  <input type="text" name="slug" value={formData.slug} onChange={handleChange} placeholder="Tự động tạo..." />
                </div>
              </div>
            </div>

            {/* 2. PHÂN LOẠI */}
            <div className="form-section">
              <h4 className="section-title"> Phân loại</h4>
              <div className="form-grid-3">
                <div className="form-group">
                  <label>Thương hiệu</label>
                  <input type="text" name="brand" value={formData.brand} onChange={handleChange} />
                </div>
                <div className="form-group">
                  <label>Bộ sưu tập</label>
                  <select name="collection" value={formData.collection} onChange={handleChange} className="form-control">
                    <option value="">-- Không --</option>
                    {collections.map(col => (<option key={col.collection_id} value={col.collection_name}>{col.collection_name}</option>))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Giới tính</label>
                  <select name="gender" value={formData.gender} onChange={handleChange} className="form-control">
                    <option value="MEN">Nam (MEN)</option>
                    <option value="WOMEN">Nữ (WOMEN)</option>
                    <option value="KIDS">Trẻ em (KIDS)</option>
                    <option value="UNISEX">Unisex</option>
                  </select>
                </div>
              </div>
            </div>

            {/* 3. GIÁ CẢ */}
            <div className="form-section highlight">
              <h4 className="section-title"> Quản lý Giá</h4>
              <div className="form-grid-3">
                <div className="form-group">
                  <label>Giá niêm yết (₫) *</label>
                  <input type="number" name="base_price" value={formData.base_price} onChange={handleChange} required />
                </div>
                <div className="form-group">
                  <label>Giá khuyến mãi (₫)</label>
                  <input type="number" name="sale_price" value={formData.sale_price} onChange={handleChange} />
                </div>
                <div className="form-group">
                  <label>Giá vốn (₫)</label>
                  <input type="number" name="cost_price" value={formData.cost_price} onChange={handleChange} />
                </div>
              </div>
            </div>
            
            {/*  MỤC CHỌN ẢNH (CHỈ HIỆN KHI TẠO MỚI) */}
            {!initialData && (
                <div className="form-section" style={{border:'2px dashed #4361ee', background:'#f0f7ff'}}>
                    <h4 className="section-title" style={{color:'#4361ee'}}>📸 Chọn hình ảnh ban đầu</h4>
                    <div className="form-group">
                        <label className="upload-btn" style={{background:'#4361ee', display:'inline-block', color:'white', padding:'8px 15px', borderRadius:'5px', cursor:'pointer'}}>
                            + Chọn ảnh từ máy (Nhiều ảnh)
                            <input type="file" multiple accept="image/*" onChange={handleFileSelect} style={{display:'none'}} />
                        </label>
                        <small style={{marginLeft:'10px', color:'#666'}}>{selectedFiles.length} file đã chọn</small>
                    </div>
                    {/* Preview ảnh đã chọn */}
                    <div style={{display:'flex', gap:'10px', flexWrap:'wrap', marginTop:'10px'}}>
                        {previewUrls.map((url, index) => (
                            <div key={index} style={{position:'relative', width:'80px', height:'80px', border:'1px solid #ddd', borderRadius:'5px', overflow:'hidden'}}>
                                <img src={url} alt="preview" style={{width:'100%', height:'100%', objectFit:'cover'}} />
                                <button type="button" onClick={() => handleRemoveSelected(index)} style={{position:'absolute', top:0, right:0, background:'red', color:'white', border:'none', width:'20px', height:'20px', cursor:'pointer', opacity:0.8}}>×</button>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* 4. MÔ TẢ & TRẠNG THÁI */}
            <div className="form-section">
              <div className="form-group">
                <label>Mô tả chi tiết</label>
                <textarea rows="3" name="description" value={formData.description} onChange={handleChange}></textarea>
              </div>
              <div className="checkbox-group">
                <label className="checkbox-label"><input type="checkbox" name="is_active" checked={formData.is_active} onChange={handleChange} /> <span>Đang bán</span></label>
                <label className="checkbox-label"><input type="checkbox" name="is_featured" checked={formData.is_featured} onChange={handleChange} /> <span>Sản phẩm Hot 🔥</span></label>
                <label className="checkbox-label"><input type="checkbox" name="is_new_arrival" checked={formData.is_new_arrival} onChange={handleChange} /> <span>Hàng mới về 🆕</span></label>
              </div>
            </div>
            
            {/* 5. SEO */}
             <div className="form-section collapsed-look">
              <h4 className="section-title"> Tối ưu SEO</h4>
              <div className="form-group">
                <input type="text" name="meta_title" value={formData.meta_title} onChange={handleChange} placeholder="Meta Title" />
              </div>
            </div>
          </form>
          
           {/* KHI CHỈNH SỬA THÌ HIỆN CÁI QUẢN LÝ ẢNH CŨ */}
           {initialData && (
            <div className="form-section image-section-wrapper">
              <h4 className="section-title">📸 Quản lý Hình ảnh</h4>
              <div className="image-manager-box">
                <ProductImageManager productId={initialData.product_id} />
              </div>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button type="button" className="btn-cancel" onClick={onClose} disabled={loading}>Hủy bỏ</button>
          {/* Nút Lưu giờ sẽ hiển thị trạng thái đang làm gì */}
          <button type="submit" form="productForm" className="btn-save" disabled={loading} style={{minWidth:'150px'}}>
            {loadingText}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProductForm;