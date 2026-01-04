import React, { useEffect, useState } from 'react';
import productApi from '../../../api/productApi';

const ProductThumbnail = ({ productId }) => {
  const [imageUrl, setImageUrl] = useState(null);

  useEffect(() => {
    let isMounted = true; // Để tránh lỗi khi lướt nhanh quá
    
    const fetchImage = async () => {
      try {
        // Gọi API lấy danh sách ảnh của sản phẩm này
        const res = await productApi.getImages(productId);
        const list = Array.isArray(res) ? res : (res.data || res.results || []);

        if (list.length > 0 && isMounted) {
          // 1. Ưu tiên lấy ảnh nào được đánh dấu là ảnh chính (is_primary = true)
          const primaryImg = list.find(img => img.is_primary);
          
          // 2. Nếu không có ảnh chính thì lấy tạm cái ảnh đầu tiên
          const finalImg = primaryImg || list[0];
          
          // 3. Lấy đường dẫn (xử lý các trường hợp tên khác nhau)
          const url = finalImg.image_url || finalImg.url || finalImg.link;
          setImageUrl(url);
        }
      } catch (error) {
        // Lỗi thì thôi, để null nó tự hiện ảnh mặc định
      }
    };

    if (productId) fetchImage();

    return () => { isMounted = false; };
  }, [productId]);

  if (!imageUrl) {
    // Chưa có ảnh thì hiện khung xám
    return (
      <div style={{
        width:'50px', height:'50px', background:'#f0f0f0', 
        display:'flex', alignItems:'center', justifyContent:'center', 
        borderRadius:'4px', color:'#ccc', fontSize:'10px', border:'1px solid #ddd'
      }}>
         NO IMG
      </div>
    );
  }

  return (
    <img 
      src={imageUrl} 
      alt="Product" 
      style={{
        width: '50px', height: '50px', objectFit: 'cover', 
        borderRadius: '4px', border: '1px solid #ddd', cursor: 'pointer'
      }}
      onError={(e) => {e.target.src = "https://via.placeholder.com/50?text=Error"}}
    />
  );
};

export default ProductThumbnail;