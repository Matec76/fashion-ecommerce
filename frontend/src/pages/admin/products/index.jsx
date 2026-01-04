import React, { useEffect, useState } from 'react';
import productApi from '../../../api/productApi';
import ProductForm from './ProductForm';
import ProductThumbnail from './ProductThumbnail'; 
// Import 2 file quản lý
import CategoryManager from './CategoryManager';
import CollectionManager from './CollectionManager';
import './Products.css';

const Products = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  
  // State Modal
  const [showModal, setShowModal] = useState(false);
  const [showCatModal, setShowCatModal] = useState(false); // Modal Danh mục
  const [showColModal, setShowColModal] = useState(false); // Modal Collection
  const [selectedProduct, setSelectedProduct] = useState(null);

  // 1. Fetch dữ liệu
  const fetchProducts = async () => {
    try {
      setLoading(true);
      const response = await productApi.getAll({
        page: 1, 
        page_size: 20, 
        search: searchTerm,
        _timestamp: new Date().getTime() 
      });
      setProducts(Array.isArray(response) ? response : response.data || []);
    } catch (error) {
      console.error("Lỗi tải danh sách:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchProducts(); }, [searchTerm]);

  // 2. Xóa sản phẩm
  const handleDelete = async (id) => {
    if (window.confirm('Xóa vĩnh viễn sản phẩm này?')) {
      try {
        await productApi.remove(id);
        alert('Đã xóa thành công!');
        fetchProducts(); 
      } catch (error) {
        alert('Lỗi xóa sản phẩm!');
      }
    }
  };

  const handleSaveSuccess = () => {
    setShowModal(false);
    setSelectedProduct(null);
    fetchProducts(); 
  };

  const formatPrice = (price) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(price);

  return (
    <div className="products-page">
      {/* HEADER */}
      <div className="page-header">
        <h2>Quản lý Sản phẩm</h2>
        <div className="toolbar" style={{display: 'flex', gap: '10px'}}>
          <input 
            type="text" 
            placeholder="Tìm kiếm..." 
            className="search-input" 
            value={searchTerm} 
            onChange={(e) => setSearchTerm(e.target.value)} 
          />
          
          {/* 2 NÚT QUẢN LÝ MỚI */}
          <button className="btn-secondary" onClick={() => setShowCatModal(true)} style={{background:'white', color:'#333', border:'1px solid #ddd', padding:'8px 12px', borderRadius:'6px', cursor:'pointer'}}>
             Danh mục
          </button>
          <button className="btn-secondary" onClick={() => setShowColModal(true)} style={{background:'white', color:'#333', border:'1px solid #ddd', padding:'8px 12px', borderRadius:'6px', cursor:'pointer'}}>
             Bộ sưu tập
          </button>

          <button className="btn-add" onClick={() => { setSelectedProduct(null); setShowModal(true); }}>
            + Thêm sản phẩm
          </button>
        </div>
      </div>

      {/* TABLE */}
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th width="70" className="text-center">ẢNH</th>
              <th>TÊN SẢN PHẨM</th>
              <th>GIÁ BÁN</th>
              <th className="text-center">ĐÃ BÁN / TỒN</th> 
              <th className="text-center">TRẠNG THÁI</th>
              <th width="150" className="text-center">HÀNH ĐỘNG</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan="6" className="text-center">Đang tải dữ liệu...</td></tr>
            ) : products.length > 0 ? (
              products.map((item) => (
                <tr key={item.product_id}>
                  <td className="text-center">
                    <ProductThumbnail productId={item.product_id} />
                  </td>
                  <td>
                    <div className="product-name">{item.product_name}</div>
                    <small className="text-muted">{item.slug}</small>
                    {item.category_id && <div style={{fontSize:'11px', color:'#4361ee', marginTop:'2px'}}>Cat ID: {item.category_id}</div>}
                  </td>
                  <td>
                    <div className="price-group">
                      {item.sale_price > 0 ? (
                        <>
                          <div className="price-original" style={{textDecoration: 'line-through', color: '#999', fontSize: '13px'}}>
                            {formatPrice(item.base_price)}
                          </div>
                          <div className="price-sale" style={{color: '#d00000', fontWeight: 'bold', fontSize: '15px'}}>
                            {formatPrice(item.sale_price)}
                          </div>
                        </>
                      ) : (
                        <div className="price-current" style={{fontWeight: 'bold'}}>
                          {formatPrice(item.base_price)}
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="text-center">
                    <div className="stock-wrapper">
                      <span className="sold-count" title="Đã bán">{item.sold_count || 0}</span>
                      <span className="divider">/</span>
                      <span className="stock-count" title="Tổng tồn kho">{item.stock ?? item.stock_quantity ?? item.quantity ?? '-'}</span>
                    </div>
                  </td>
                  <td className="text-center">
                    {item.is_active ? <span className="badge-success">Đang bán</span> : <span className="badge-error">Ngừng</span>}
                  </td>
                  <td className="text-center">
                    <button className="action-btn edit" onClick={() => { setSelectedProduct(item); setShowModal(true); }}>Sửa</button>
                    <button className="action-btn delete" onClick={() => handleDelete(item.product_id)}>Xóa</button>
                  </td>
                </tr>
              ))
            ) : (
              <tr><td colSpan="6" className="text-center">Không có dữ liệu.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* HIỂN THỊ CÁC MODAL */}
      {showModal && (
        <ProductForm 
          onClose={() => setShowModal(false)} 
          onSuccess={handleSaveSuccess} 
          initialData={selectedProduct} 
        />
      )}
      {showCatModal && <CategoryManager onClose={() => setShowCatModal(false)} />}
      {showColModal && <CollectionManager onClose={() => setShowColModal(false)} />}
    </div>
  );
};

export default Products;