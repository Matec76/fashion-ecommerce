import { useState, useEffect, useMemo, memo } from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import useFetch from '../../components/useFetch';
import useMutation from '../../components/useMutation';
import useDelete from '../../components/useDelete';
import { API_ENDPOINTS, API_CONFIG } from '/src/config/api.config';
import '../../style/SanPham.css';

// ==========================================
// 1. SUB-COMPONENT: PRODUCT CARD
// Tự động tải ảnh riêng lẻ, giúp trang load nhanh hơn
// ==========================================
const ProductCard = memo(({ product }) => {
  const navigate = useNavigate();
  const [isInWishlist, setIsInWishlist] = useState(false);

  // Hooks cho API calls
  const { mutate, loading: addLoading } = useMutation();
  const { remove, loading: removeLoading } = useDelete();

  const wishlistLoading = addLoading || removeLoading;

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

  const [imgError, setImgError] = useState(false);

  // Reset error khi đổi sản phẩm/ảnh
  useEffect(() => {
    setImgError(false);
  }, [imageUrl]);

  // Ảnh hiển thị (Fallback nếu chưa có hoặc lỗi)
  const displayImage = (imageUrl && !imgError) ? imageUrl : 'https://placehold.co/600x600?text=No+Image';
  const isPlaceholder = !imageUrl || imgError;

  // Debug images (chỉ log khi có data để tránh spam)
  useEffect(() => {
    if (imagesData && imagesData.length > 0) {
      console.log(`🖼️ Images for ${product.name}:`, imagesData);
    } else if (imagesData) {
      console.log(`⚠️ No images for ${product.name}`);
    }
  }, [imagesData, product.name]);

  // Toggle wishlist
  const handleWishlistClick = async (e) => {
    e.preventDefault();
    e.stopPropagation();

    const token = localStorage.getItem('authToken');
    if (!token) {
      alert('Vui lòng đăng nhập để thêm vào yêu thích!');
      navigate('/login');
      return;
    }

    if (isInWishlist) {
      // Xóa khỏi wishlist - cần tìm item_id trước
      try {
        const checkResponse = await fetch(`${API_CONFIG.BASE_URL}/wishlist/check/${product.id}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (checkResponse.ok) {
          const wishlistData = await checkResponse.json();
          const itemId = Object.values(wishlistData)[0]?.item_id;
          if (itemId) {
            const result = await remove(`${API_CONFIG.BASE_URL}/wishlist/items/${itemId}`);
            if (result.success) {
              setIsInWishlist(false);
            }
          }
        }
      } catch (err) {
        console.error('Error removing from wishlist:', err);
      }
    } else {
      // Thêm vào wishlist
      const result = await mutate(`${API_CONFIG.BASE_URL}/wishlist/add-to-default`, {
        method: 'POST',
        body: { product_id: product.id }
      });
      if (result.success) {
        setIsInWishlist(true);
      } else {
        console.error('Error adding to wishlist:', result.error);
      }
    }
  };

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
            <img
              src={displayImage}
              alt={product.name}
              loading="lazy"
              className={isPlaceholder ? 'is-placeholder' : ''}
              onError={() => setImgError(true)}
            />
          )}
        </div>

        <div className="product-info">
          <h3 className="product-name">{product.name}</h3>
          <p className="product-type">{product.type}</p>
          <div className="product-price-wrapper">
            {product.salePrice ? (
              <>
                <span className="product-sale-price">
                  {product.salePrice.toLocaleString('vi-VN')}₫
                </span>
                <span className="product-base-price-strikethrough">
                  {product.basePrice.toLocaleString('vi-VN')}₫
                </span>
              </>
            ) : (
              <span className="product-price">
                {product.basePrice.toLocaleString('vi-VN')}₫
              </span>
            )}
          </div>
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

  // --- TÍNH TOÁN GIÁ TRỊ KHỞI TẠO TỪ URL PARAMS ---
  const getInitialFilters = () => {
    const params = new URLSearchParams(location.search);
    const gender = params.get('gender');
    const type = params.get('type');

    const genders = [];
    const types = [];

    if (gender) {
      const mapGender = { 'MEN': 'Nam', 'WOMEN': 'Nữ', 'KIDS': 'Trẻ em' };
      genders.push(mapGender[gender?.toUpperCase()] || gender);
    }
    if (type) types.push(type);

    return { genders, types };
  };

  const initialFilters = getInitialFilters();

  // --- STATE (khởi tạo từ URL params) ---
  const [selectedTypes, setSelectedTypes] = useState(initialFilters.types);
  const [selectedSizes, setSelectedSizes] = useState([]);
  const [selectedGenders, setSelectedGenders] = useState(initialFilters.genders);
  const [categories, setCategories] = useState([]); // Dùng để map ID -> Tên danh mục
  const [activeTab, setActiveTab] = useState('all'); // 'all', 'featured', 'best-sellers', 'new'
  const [priceSort, setPriceSort] = useState('none'); // 'none', 'asc', 'desc'

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
  const apiUrl = useMemo(() => {
    const params = new URLSearchParams(location.search);
    const searchKeyword = params.get('search');

    // Nếu có từ khóa tìm kiếm, luôn gọi API search
    if (searchKeyword) {
      return `${API_ENDPOINTS.PRODUCTS.LIST}?search=${encodeURIComponent(searchKeyword)}`;
    }

    // Chọn API dựa trên tab đang active
    switch (activeTab) {
      case 'featured':
        return `${API_ENDPOINTS.PRODUCTS.FEATURED}?limit=50`;
      case 'best-sellers':
        return `${API_ENDPOINTS.PRODUCTS.BEST_SELLERS}?limit=50`;
      case 'new':
        return `${API_ENDPOINTS.PRODUCTS.NEW_ARRIVALS}?limit=50`;
      default:
        // Tab "Tất cả" hoặc khi có param new=true từ URL
        if (params.get('new') === 'true') {
          return API_ENDPOINTS.PRODUCTS.NEW_ARRIVALS;
        }
        return API_ENDPOINTS.PRODUCTS.LIST;
    }
  }, [activeTab, location.search]);

  const { data, loading, error, refetch } = useFetch(apiUrl);

  // --- LOGIC LỌC SẢN PHẨM (Dùng useMemo để tối ưu hiệu năng) ---
  const filteredProducts = useMemo(() => {
    // Safety check: return empty array if data is null/undefined
    if (!data) return [];

    let rawProducts = [];
    if (Array.isArray(data)) rawProducts = data;
    else if (data?.items) rawProducts = data.items;
    else if (data?.data) rawProducts = data.data;

    if (!rawProducts || !rawProducts.length) return [];

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
        basePrice: typeof p.base_price === 'string' ? parseFloat(p.base_price) : (p.base_price || 0),
        salePrice: p.sale_price ? (typeof p.sale_price === 'string' ? parseFloat(p.sale_price) : p.sale_price) : null,
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
    let filtered = normalized.filter(product => {
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

    // 3. Sắp xếp theo giá (nếu có)
    if (priceSort === 'asc') {
      filtered = [...filtered].sort((a, b) => a.price - b.price);
    } else if (priceSort === 'desc') {
      filtered = [...filtered].sort((a, b) => b.price - a.price);
    }

    return filtered;
  }, [data, categories, selectedGenders, selectedTypes, selectedSizes, priceSort, location.search]);

  // --- PAGINATION LOGIC ---
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 18;

  // Reset trang về 1 khi filter thay đổi
  useEffect(() => {
    setCurrentPage(1);
  }, [filteredProducts]);

  // Lấy sản phẩm cho trang hiện tại
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentProducts = filteredProducts.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(filteredProducts.length / itemsPerPage);

  // Scroll to top khi đổi trang
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [currentPage]);

  // Helper toggle
  const toggleFilter = (state, setState, value) => {
    setState(prev => prev.includes(value) ? prev.filter(i => i !== value) : [...prev, value]);
  };

  // Toggle price sort: none -> asc -> desc -> none
  const togglePriceSort = () => {
    setPriceSort(prev => {
      if (prev === 'none') return 'asc';
      if (prev === 'asc') return 'desc';
      return 'none';
    });
  };

  // --- RENDER UI ---
  if (loading && !data) return <div className="loading-container"><div className="loading-spinner"></div><p>Đang tải dữ liệu...</p></div>;
  if (error) return <div className="error-container">Lỗi kết nối: {error}</div>;

  return (
    <div className="san-pham-page">
      {/* Hero Header */}
      <div className="hero-header">
        {/* Có thể thêm ảnh banner tĩnh ở đây thay vì lấy ảnh sp đầu tiên */}
        <div className="hero-product-image" style={{ backgroundColor: '#1a1a2e' }}>
          <div className="hero-overlay"></div>
          <h1 style={{ position: 'absolute', color: 'white', bottom: 20, left: 40 }}>SẢN PHẨM</h1>
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
                {/* Danh sách các loại sản phẩm từ API (chỉ lấy child categories) */}
                {categories.length > 0 ? (
                  // Lọc chỉ lấy categories có parent (child categories)
                  // Và lấy unique type names (bỏ suffix Nam/Nữ)
                  [...new Set(
                    categories
                      .filter(cat => cat.parent_category_id !== null)
                      .map(cat => cat.category_name.replace(/\s*(Nam|Nữ)$/i, '').trim())
                  )].map(typeName => (
                    <label key={typeName} className="filter-checkbox">
                      <input
                        type="checkbox"
                        checked={selectedTypes.includes(typeName)}
                        onChange={() => toggleFilter(selectedTypes, setSelectedTypes, typeName)}
                      />
                      <span>{typeName}</span>
                    </label>
                  ))
                ) : (
                  <span className="loading-text">Đang tải...</span>
                )}
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
          {/* Category Tabs */}
          <div className="category-tabs">
            <button
              className={`product-tab-btn ${activeTab === 'all' ? 'active' : ''}`}
              onClick={() => setActiveTab('all')}
            >
              Tất cả
            </button>
            <button
              className={`product-tab-btn ${activeTab === 'featured' ? 'active' : ''}`}
              onClick={() => setActiveTab('featured')}
            >
              Nổi bật
            </button>
            <button
              className={`product-tab-btn ${activeTab === 'best-sellers' ? 'active' : ''}`}
              onClick={() => setActiveTab('best-sellers')}
            >
              Bán chạy
            </button>
            <button
              className={`product-tab-btn ${activeTab === 'new' ? 'active' : ''}`}
              onClick={() => setActiveTab('new')}
            >
              Mới
            </button>
            <button
              className="product-tab-btn price-sort-btn"
              onClick={togglePriceSort}
              title={priceSort === 'none' ? 'Sắp xếp theo giá' : priceSort === 'asc' ? 'Giá tăng dần' : 'Giá giảm dần'}
              style={{ display: 'inline-flex', alignItems: 'center' }}
            >
              Giá
              {priceSort === 'none' && (
                <span style={{ marginLeft: '6px', display: 'inline-flex', flexDirection: 'column', fontSize: '10px', gap: '1px' }}>
                  <span style={{ lineHeight: '1' }}>▲</span>
                  <span style={{ lineHeight: '1' }}>▼</span>
                </span>
              )}
              {priceSort === 'asc' && <span style={{ marginLeft: '6px', fontSize: '11px' }}>▲</span>}
              {priceSort === 'desc' && <span style={{ marginLeft: '6px', fontSize: '11px' }}>▼</span>}
            </button>
          </div>

          <div className="product-count">
            {new URLSearchParams(location.search).get('search') ? (
              <p>Kết quả tìm kiếm "{new URLSearchParams(location.search).get('search')}": {filteredProducts.length} sản phẩm</p>
            ) : (
              <p>Hiển thị {filteredProducts.length} sản phẩm</p>
            )}
          </div>

          {filteredProducts.length === 0 ? (
            <div className="no-products"><p>Không tìm thấy sản phẩm phù hợp.</p></div>
          ) : (
            <div className="products-grid">
              {currentProducts.map(p => (
                <ProductCard key={p.id} product={p} />
              ))}
            </div>
          )}

          {/* Pagination Controls */}
          {filteredProducts.length > itemsPerPage && (
            <div className="pagination-container">
              <button
                className="pagination-btn"
                disabled={currentPage === 1}
                onClick={() => setCurrentPage(prev => prev - 1)}
              >
                &lt;
              </button>

              {Array.from({ length: totalPages }, (_, i) => i + 1).map(number => (
                <button
                  key={number}
                  className={`pagination-btn ${currentPage === number ? 'active' : ''}`}
                  onClick={() => setCurrentPage(number)}
                >
                  {number}
                </button>
              ))}

              <button
                className="pagination-btn"
                disabled={currentPage === totalPages}
                onClick={() => setCurrentPage(prev => prev + 1)}
              >
                &gt;
              </button>
            </div>
          )}

        </main>
      </div>
    </div>
  );
}

export default SanPham;