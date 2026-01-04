import React, { useEffect, useState } from 'react';
import productApi from '../../../api/productApi';

const ProductImageManager = ({ productId }) => {
  const [images, setImages] = useState([]);
  const [uploading, setUploading] = useState(false);

  // Load danh sách ảnh
  const fetchImages = async () => {
    try {
      const res = await productApi.getImages(productId);
      const list = Array.isArray(res) ? res : (res.data || res.results || []);
      // Sắp xếp: Ảnh chính lên đầu, còn lại theo thứ tự
      const sorted = list.sort((a, b) => (b.is_primary === true) - (a.is_primary === true));
      setImages(sorted);
    } catch (error) {
      console.error("Lỗi tải ảnh:", error);
    }
  };

  useEffect(() => { if (productId) fetchImages(); }, [productId]);

  //  TỐI ƯU: Upload song song (Nhanh hơn gấp n lần)
  const handleFileChange = async (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    setUploading(true);
    try {
      // 1. Tạo một mảng các Promise để upload cùng lúc
      const uploadPromises = files.map(async (file) => {
        try {
            // Upload file lên server
            const uploadRes = await productApi.uploadFile(file);
            const imageUrl = uploadRes.url || uploadRes.image_url || uploadRes;
            
            // Gắn vào sản phẩm ngay
            if (imageUrl) {
                await productApi.addImageToProduct(productId, imageUrl);
            }
        } catch (err) {
            console.error("Lỗi file:", file.name, err);
        }
      });

      // 2. Chạy tất cả cùng lúc, chờ xong hết mới báo
      await Promise.all(uploadPromises);

      // 3. Load lại danh sách
      await fetchImages();
      
    } catch (error) {
      alert("Lỗi upload: " + error.message);
    } finally {
      setUploading(false);
      e.target.value = null; // Reset input để chọn lại file cũ được
    }
  };

  const handleDelete = async (imageId) => {
    if (!window.confirm('Xóa ảnh này?')) return;
    try { 
      // Xóa giao diện trước cho mượt (Optimistic update)
      setImages(prev => prev.filter(img => img.image_id !== imageId));
      
      // Gọi API xóa thật
      await productApi.deleteImage(imageId);
    } catch (error) {
      alert("Lỗi xóa ảnh, vui lòng tải lại trang.");
      fetchImages(); // Lỗi thì load lại cái cũ
    }
  };

  const handleSetPrimary = async (imageId) => {
    try { 
        // Cập nhật giao diện trước cho mượt
        setImages(prev => prev.map(img => ({
            ...img,
            is_primary: img.image_id === imageId
        })));

        // Gọi API
        await productApi.setPrimaryImage(imageId);
        fetchImages(); // Load lại để đảm bảo đồng bộ server
    } catch (e) { alert('Lỗi đặt ảnh chính'); }
  };

  return (
    <div className="image-manager-container" style={{border: 'none', background: 'transparent', padding: 0}}>
      
      {/* KHU VỰC UPLOAD - Style giống hệt lúc Thêm mới */}
      <div className="upload-section" style={{marginBottom: '15px', background: '#f0f7ff', padding: '15px', borderRadius: '8px', border: '2px dashed #4361ee', textAlign: 'center'}}>
        <label className="upload-btn" style={{
            background: '#4361ee', color: 'white', padding: '10px 20px', 
            borderRadius: '6px', cursor: 'pointer', fontWeight: '600', display: 'inline-flex', alignItems: 'center', gap: '8px'
        }}>
          {uploading ? '⏳ Đang tải lên...' : '📸 Tải thêm ảnh từ máy'}
          <input type="file" multiple accept="image/*" onChange={handleFileChange} disabled={uploading} style={{display: 'none'}} />
        </label>
        <div style={{marginTop: '8px', fontSize: '12px', color: '#666'}}>Chấp nhận nhiều ảnh cùng lúc (JPG, PNG, WEBP)</div>
      </div>

      {/* DANH SÁCH ẢNH - Grid đẹp hơn */}
      <div className="image-grid" style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(100px, 1fr))', gap: '12px'}}>
        {images.map((img, index) => {
          const finalUrl = img.image_url || img.url || "https://via.placeholder.com/150";
          return (
            <div key={img.image_id || index} className={`image-card ${img.is_primary ? 'primary' : ''}`} 
                 style={{
                     position: 'relative', borderRadius: '8px', overflow: 'hidden', 
                     border: img.is_primary ? '2px solid #f59e0b' : '1px solid #e5e7eb',
                     aspectRatio: '1/1', boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
                 }}>
              
              <img src={finalUrl} alt="Product" style={{width: '100%', height: '100%', objectFit: 'cover'}} 
                   onError={(e)=>{e.target.src='https://via.placeholder.com/150?text=Err'}} 
              />
              
              {/* Overlay hành động */}
              <div className="image-actions" style={{
                  position: 'absolute', bottom: 0, left: 0, right: 0, 
                  background: 'rgba(0,0,0,0.6)', padding: '6px', 
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center'
              }}>
                {!img.is_primary ? (
                    <button type="button" onClick={() => handleSetPrimary(img.image_id)} title="Đặt làm ảnh chính"
                        style={{background: 'none', border: 'none', color: '#fbbf24', cursor: 'pointer', fontSize: '16px'}}>
                        ★
                    </button>
                ) : <span style={{fontSize:'12px', color:'#fbbf24', fontWeight:'bold'}}>Chính</span>}

                <button type="button" onClick={() => handleDelete(img.image_id)} title="Xóa"
                    style={{background: '#ef4444', border: 'none', color: 'white', borderRadius: '4px', width: '20px', height: '20px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px'}}>
                    &times;
                </button>
              </div>
            </div>
          );
        })}
      </div>
      
      {images.length === 0 && !uploading && (
          <div style={{textAlign: 'center', color: '#999', padding: '20px', fontStyle: 'italic'}}>
              Chưa có hình ảnh nào.
          </div>
      )}
    </div>
  );
};

export default ProductImageManager;