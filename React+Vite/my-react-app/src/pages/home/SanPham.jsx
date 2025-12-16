import { useState, useEffect, useMemo, memo } from 'react';
import { useLocation, Link } from 'react-router-dom';
import useFetch from '../../components/useFetch'; // Import hook đã tối ưu
import { API_ENDPOINTS } from '/src/config/api.config'; // Đảm bảo đường dẫn đúng
import '../../style/SanPham.css';

// ==========================================
// 1. SUB-COMPONENT: PRODUCT CARD
// Tự động tải ảnh riêng lẻ, giúp trang load nhanh hơn
// ==========================================
const ProductCard = memo(({ product }) => {
  // Gọi API lấy ảnh cho từng sản phẩm (Sẽ tự động cache lại)
  const { data: imagesData, loading } = useFetch(
    API_ENDPOINTS.PRODUCTS.IMAGES(product.id)
  );

  // Logic chọn ảnh: Ưu tiên ảnh primary, không thì lấy cái đầu tiên
  const imageUrl = useMemo(() => {
    if (!imagesData || !Array.isArray(imagesData) || imagesData.length === 0) {
      return null;
    }
    const primary = imagesData.find(img => img.is_primary) || imagesData[0];
    return primary.image_url;
  }, [imagesData]);

  // Ảnh hiển thị (Fallback nếu chưa có)
  const displayImage = imageUrl || 'https://placehold.co/400x400?text=No+Image';

  return (
    // Link tới trang chi tiết (dùng Slug nếu có, không thì dùng ID)
    <Link to={`/products/${product.slug || product.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
      <div className="product-card">
        {product.isNew && <span className="new-badge">NEW</span>}

        <div className="product-image">
          {loading ? (
            // Hiệu ứng Skeleton khi đang tải ảnh
            <div className="skeleton-image"></div>
          ) : (
            <img src={displayImage} alt={product.name} loading="lazy" />
          )}
        </div>

        <div className="product-info">
          <h3 className="product-name">{product.name}</h3>
          <p className="product-type">{product.type}</p>
          <p className="product-price">
            {product.price?.toLocaleString('vi-VN')}₫
          </p>
        </div>
      </div>
    </Link>
  );
});

// ==========================================
// 2. MAIN COMPONENT
// ==========================================
function SanPham() {
  const location = useLocation();
  
  // --- STATE ---
  const [selectedTypes, setSelectedTypes] = useState([]);
  const [selectedSizes, setSelectedSizes] = useState([]);
  const [selectedGenders, setSelectedGenders] = useState([]);
  const [categories, setCategories] = useState([]); // Dùng để map ID -> Tên danh mục

  // --- API 1: LẤY DANH MỤC (Để lấy tên loại sản phẩm) ---
  useEffect(() => {
    const fetchCats = async () => {
      try {
        const res = await fetch(API_ENDPOINTS.CATEGORIES.TREE);
        if (res.ok) {
          const data = await res.json();
          // Làm phẳng cây danh mục để dễ tìm kiếm tên
          const flatten = (nodes, result = []) => {
            nodes.forEach(node => {
              result.push(node);
              if (node.children) flatten(node.children, result);
            });
            return result;
          };
          const roots = Array.isArray(data) ? data : (data.items || data.data || []);
          setCategories(flatten(roots));
        }
      } catch (e) { console.error("Lỗi tải danh mục", e); }
    };
    fetchCats();
  }, []);

  // --- API 2: LẤY DANH SÁCH SẢN PHẨM ---
  const buildApiUrl = () => {
    const params = new URLSearchParams(location.search);
    // Tối ưu: Nếu lọc "Hàng mới", gọi API chuyên biệt sẽ nhanh hơn
    if (params.get('new') === 'true') {
        return API_ENDPOINTS.PRODUCTS.NEW_ARRIVALS || '/api/v1/products/new-arrivals';
    }
    // Mặc định gọi List
    return API_ENDPOINTS.PRODUCTS.LIST;
  };

  const { data, loading, error } = useFetch(buildApiUrl());

  // --- XỬ LÝ URL PARAMS (Đồng bộ URL với bộ lọc) ---
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const gender = params.get('gender');
    const type = params.get('type');
    
    if (gender) {
        const mapGender = { 'MEN': 'Nam', 'WOMEN': 'Nữ', 'KIDS': 'Trẻ em' };
        setSelectedGenders([mapGender[gender?.toUpperCase()] || gender]);
    }
    if (type) setSelectedTypes([type]);
  }, [location.search]);

  // --- LOGIC LỌC SẢN PHẨM (Dùng useMemo để tối ưu hiệu năng) ---
  const filteredProducts = useMemo(() => {
    let rawProducts = [];
    if (Array.isArray(data)) rawProducts = data;
    else if (data?.items) rawProducts = data.items;
    else if (data?.data) rawProducts = data.data;

    if (!rawProducts.length) return [];

    // 1. Chuẩn hóa dữ liệu (Mapping)
    // 1. Chuẩn hóa dữ liệu (Mapping)
    const normalized = rawProducts.map(p => {
      // --- SỬA DÒNG NÀY (Ép kiểu về String để so sánh chính xác) ---
      const catObj = categories.find(c => 
          String(c.category_id) === String(p.category_id) || 
          String(c.id) === String(p.category_id)
      );
      // -------------------------------------------------------------
      
      // Debug: Bật lên xem nó tìm thấy tên gì (F12 Console)
      // console.log(`SP: ${p.product_name}, ID Loại: ${p.category_id}, Tìm thấy: ${catObj?.category_name}`);

      return {
        id: p.product_id || p.id,
        slug: p.slug,
        name: p.product_name || p.name,
        price: typeof p.base_price === 'string' ? parseFloat(p.base_price) : (p.base_price || 0),
        isNew: p.is_new_arrival || false,
        gender: (() => {
           const g = (p.gender || '').toUpperCase();
           return g === 'MEN' ? 'Nam' : g === 'WOMEN' ? 'Nữ' : g === 'KIDS' ? 'Trẻ em' : 'Unisex';
        })(),
        // Lấy tên loại (Ưu tiên tên tìm được trong bảng Category)
        type: catObj?.category_name || p.category_name || 'Khác',
        sizes: p.variants ? p.variants.map(v => v.size) : [] 
      };
    });

    // 2. Thực hiện lọc
    return normalized.filter(product => {
      // Lọc Giới tính
      if (selectedGenders.length > 0 && !selectedGenders.includes(product.gender)) return false;
      
      // Lọc Loại
      if (selectedTypes.length > 0) {
          // 1. Lấy tên loại của sản phẩm (ví dụ: "Giày Dép") và chuyển về chữ thường
          const productTypeLower = (product.type || '').toLowerCase();
          
          // 2. Kiểm tra xem tên loại sản phẩm có CHỨA từ khóa bạn chọn không (ví dụ chọn "Giày")
          // Logic: "giày dép" có chứa chữ "giày" -> ĐÚNG
          const isMatch = selectedTypes.some(selectedFilter => 
              productTypeLower.includes(selectedFilter.toLowerCase())
          );
          
          // 3. Nếu không khớp bất kỳ từ khóa nào thì ẩn sản phẩm đi
          if (!isMatch) return false;
      }
      
      // Lọc Size 
      // (Thêm check length để tránh ẩn hết sản phẩm khi API thiếu data size)
      if (selectedSizes.length > 0 && product.sizes.length > 0) {
          if (!product.sizes.some(s => selectedSizes.includes(s))) return false;
      }
      
      return true;
    });
  }, [data, categories, selectedGenders, selectedTypes, selectedSizes]);

  // Helper toggle
  const toggleFilter = (state, setState, value) => {
    setState(prev => prev.includes(value) ? prev.filter(i => i !== value) : [...prev, value]);
  };

  // --- RENDER UI ---
  if (loading && !data) return <div className="loading-container"><div className="loading-spinner"></div><p>Đang tải dữ liệu...</p></div>;
  if (error) return <div className="error-container">Lỗi kết nối: {error}</div>;

  return (
    <div className="san-pham-page">
      {/* Hero Header */}
      <div className="hero-header">
        {/* Có thể thêm ảnh banner tĩnh ở đây thay vì lấy ảnh sp đầu tiên */}
        <div className="hero-product-image" style={{backgroundColor: '#1a1a2e'}}>
            <div className="hero-overlay"></div>
            <h1 style={{position:'absolute', color:'white', bottom: 20, left: 40}}>SẢN PHẨM</h1>
        </div>
      </div>

      <div className="content-wrapper">
        {/* SIDEBAR */}
        <aside className="sidebar-filters">
          <div className="filter-section">
            <h3>BỘ LỌC</h3>

            {/* Giới tính */}
            <div className="filter-group">
                <h4>Đối tượng</h4>
                {['Nam', 'Nữ', 'Trẻ em'].map(g => (
                    <label key={g} className="filter-checkbox">
                        <input 
                            type="checkbox" 
                            checked={selectedGenders.includes(g)}
                            onChange={() => toggleFilter(selectedGenders, setSelectedGenders, g)}
                        />
                        <span>{g}</span>
                    </label>
                ))}
            </div>
            {/* Loại sản phẩm */}
            <div className="filter-group">
                <h4>Loại sản phẩm</h4>
                <div className="filter-options">
                    {/* Danh sách các loại sản phẩm phổ biến */}
                    {['Giày', 'Quần', 'Áo', 'Đầm', 'Váy', 'Phụ kiện'].map(type => (
                        <label key={type} className="filter-checkbox">
                            <input 
                                type="checkbox" 
                                checked={selectedTypes.includes(type)}
                                onChange={() => toggleFilter(selectedTypes, setSelectedTypes, type)}
                            />
                            <span>{type}</span>
                        </label>
                    ))}
                </div>
            </div>
            {/* Kích cỡ (Cảnh báo: Hiện tại API chưa hỗ trợ lọc cái này) */}
            <div className="filter-group">
                <h4>Kích cỡ</h4>
                <div className="size-options">
                    {['S', 'M', 'L', 'XL', '39', '40', '41', '42'].map(s => (
                        <button 
                            key={s} 
                            className={`size-button ${selectedSizes.includes(s) ? 'active' : ''}`}
                            onClick={() => toggleFilter(selectedSizes, setSelectedSizes, s)}
                        >
                            {s}
                        </button>
                    ))}
                </div>
            </div>

            {/* Nút xóa */}
            {(selectedGenders.length > 0 || selectedSizes.length > 0 || selectedTypes.length > 0) && (
                <button 
                    className="clear-filters-btn"
                    onClick={() => { setSelectedGenders([]); setSelectedSizes([]); setSelectedTypes([]); }}
                >
                    Xóa bộ lọc
                </button>
            )}
          </div>
        </aside>

        {/* MAIN CONTENT */}
        <main className="main-content">
          <div className="product-count">
            <p>Hiển thị {filteredProducts.length} sản phẩm</p>
          </div>

          {filteredProducts.length === 0 ? (
             <div className="no-products"><p>Không tìm thấy sản phẩm phù hợp.</p></div>
          ) : (
             <div className="products-grid">
               {filteredProducts.map(p => (
                 <ProductCard key={p.id} product={p} />
               ))}
             </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default SanPham;