import { useState, useEffect, useMemo, memo, useRef } from 'react';
import logger from '../../utils/logger';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import useFetch from '../../hooks/useFetch';
import useMutation from '../../hooks/useMutation';
import useDelete from '../../hooks/useDelete';
import { API_ENDPOINTS, API_CONFIG } from '/src/config/api.config';
import '../../style/SanPham.css';
import { getFeaturedWithHierarchy } from '../../utils/category.utils';

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

  // Fetch images with error handling for 422 errors
  // Use product_id (correct field from API) instead of id
  const productId = product.product_id || product.id;
  const { data: imagesData, loading, error } = useFetch(
    API_ENDPOINTS.PRODUCTS.IMAGES(productId),
    { cacheTime: 300000 } // 5 minutes cache
  );

  const imageUrl = useMemo(() => {
    // If API returns 422 error or no data, use placeholder
    if (error || !imagesData || !Array.isArray(imagesData) || imagesData.length === 0) {
      return null;
    }
    const primary = imagesData.find(img => img.is_primary) || imagesData[0];
    return primary.image_url;
  }, [imagesData, error]);

  const [imgError, setImgError] = useState(false);

  // Reset error khi đổi sản phẩm/ảnh
  useEffect(() => {
    setImgError(false);
  }, [imageUrl]);

  // Ảnh hiển thị (Fallback nếu chưa có hoặc lỗi)
  const displayImage = (imageUrl && !imgError) ? imageUrl : 'https://placehold.co/600x600?text=No+Image';
  const isPlaceholder = !imageUrl || imgError;

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
        logger.error('Error removing from wishlist:', err);
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
        logger.error('Error adding to wishlist:', result.error);
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
  const navigate = useNavigate();

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
  const [activeTab, setActiveTab] = useState(() => {
    const params = new URLSearchParams(location.search);
    if (params.get('featured') === 'true') return 'featured';
    if (params.get('new') === 'true') return 'new';
    return 'all';
  });
  const [priceSort, setPriceSort] = useState('none'); // 'none', 'asc', 'desc'
  const [selectedPriceRanges, setSelectedPriceRanges] = useState([]);

  // CONSTANT: KHOẢNG GIÁ
  const PRICE_RANGES = [
    { id: 'range1', label: '0đ - 10.000.000đ', min: 0, max: 10000000 },
    { id: 'range2', label: '10.000.000đ - 50.000.000đ', min: 10000000, max: 50000000 },
    { id: 'range3', label: '50.000.000đ - 100.000.000đ', min: 50000000, max: 100000000 },
    { id: 'range4', label: 'Trên 100.000.000đ', min: 100000000, max: 500000000 },
  ];

  // 🔍 DEBUG: Track selectedTypes changes
  useEffect(() => {
    logger.log('📊 selectedTypes changed:', selectedTypes);
  }, [selectedTypes]);

  // ❌ REMOVED: This useEffect was overwriting user selections
  // Filters are already initialized from URL in state (lines 169-181)
  // No need to sync continuously - it was causing all filters/tabs to fail

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
      } catch (e) { logger.error("Lỗi tải danh mục", e); }
    };
    fetchCats();
  }, []);

  // --- AUTO-SELECT FILTER WHEN COMING FROM HOMEPAGE ---
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const categoryId = params.get('category_id');
    const isFeatured = params.get('featured') === 'true';

    logger.log('=== AUTO-FILTER DEBUG ===');
    logger.log('categoryId:', categoryId);
    logger.log('isFeatured:', isFeatured);
    logger.log('categories.length:', categories.length);

    // Only apply when coming from homepage (category_id + featured)
    if (categoryId && isFeatured && categories.length > 0) {
      const category = categories.find(cat =>
        String(cat.category_id) === String(categoryId) ||
        String(cat.id) === String(categoryId)
      );

      logger.log('Found category:', category);

      if (category) {
        // Remove suffix (Nam/Nữ) to get base category name
        const baseName = category.category_name.replace(/\s*(Nam|Nữ)$/i, '').trim();

        logger.log('baseName after removing suffix:', baseName);
        logger.log('Setting selectedTypes to:', [baseName]);

        // REPLACE filter (not append) when from homepage
        setSelectedTypes([baseName]);
        logger.log(`Auto-selected filter (replaced): ${baseName}`);
      } else {
        logger.log('❌ Category not found in categories array');
        logger.log('Categories count:', categories.length);
      }
    }
    // If not from homepage, keep existing filters (user can manually select)
  }, [categories, location.search]);

  // --- API 2: LẤY DANH SÁCH SẢN PHẨM ---
  const apiUrl = useMemo(() => {
    const params = new URLSearchParams(location.search);
    const searchKeyword = params.get('search');
    const categoryId = params.get('category_id');
    const isFeatured = params.get('featured') === 'true';

    // Nếu có từ khóa tìm kiếm, luôn gọi API search
    if (searchKeyword) {
      return `${API_ENDPOINTS.PRODUCTS.LIST}?search=${encodeURIComponent(searchKeyword)}&page_size=1000`;
    }

    // Nếu có category_id và featured=true → Lấy sản phẩm nổi bật theo category
    if (categoryId && isFeatured) {
      return `${API_ENDPOINTS.PRODUCTS.FEATURED}?category_id=${categoryId}&limit=50`;
    }

    // Chọn API dựa trên tab đang active
    switch (activeTab) {
      case 'featured':
        // Nếu có category_id trong URL, lọc theo category
        return categoryId
          ? `${API_ENDPOINTS.PRODUCTS.FEATURED}?category_id=${categoryId}&limit=50`
          : `${API_ENDPOINTS.PRODUCTS.FEATURED}?limit=50`;
      case 'best-sellers':
        return `${API_ENDPOINTS.PRODUCTS.BEST_SELLERS}?limit=50`;
      case 'new':
        return `${API_ENDPOINTS.PRODUCTS.NEW_ARRIVALS}?limit=50`;
      default:
        // Tab "Tất cả" - Lấy tất cả sản phẩm (thêm page_size lớn để không bị giới hạn)
        if (params.get('new') === 'true') {
          return `${API_ENDPOINTS.PRODUCTS.NEW_ARRIVALS}?limit=50`;
        }
        return `${API_ENDPOINTS.PRODUCTS.LIST}?page_size=1000`;
    }
  }, [activeTab, location.search]);

  // Fetch products with 2-minute cache
  const { data, loading, error, refetch } = useFetch(apiUrl, { cacheTime: 120000 });

  // --- CUSTOM FETCH FOR HIERARCHY-BASED FEATURED PRODUCTS ---
  const [hierarchyProducts, setHierarchyProducts] = useState(null);
  const [hierarchyLoading, setHierarchyLoading] = useState(false);
  const prevCategoryIdRef = useRef(null);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const categoryId = params.get('category_id');
    const isFeatured = params.get('featured') === 'true';

    // Only fetch hierarchy if both params present AND categoryId changed
    if (categoryId && isFeatured) {
      // Only fetch if categoryId actually changed
      if (prevCategoryIdRef.current !== categoryId) {
        prevCategoryIdRef.current = categoryId;
        setHierarchyLoading(true);
        getFeaturedWithHierarchy(parseInt(categoryId), 50)
          .then(products => {
            setHierarchyProducts(products);
            setHierarchyLoading(false);
          })
          .catch(err => {
            logger.error('Error fetching hierarchy products:', err);
            setHierarchyProducts(null);
            setHierarchyLoading(false);
          });
      }
    } else {
      // Reset when not from homepage
      prevCategoryIdRef.current = null;
      if (hierarchyProducts !== null) {
        setHierarchyProducts(null);
      }
    }
  }, [location.search]); // Only depend on location.search

  // Use hierarchy products if available, otherwise use regular fetch
  const finalData = hierarchyProducts !== null ? hierarchyProducts : data;
  const finalLoading = hierarchyProducts !== null ? hierarchyLoading : loading;

  // --- LOGIC LỌC SẢN PHẨM (Dùng useMemo để tối ưu hiệu năng) ---
  const filteredProducts = useMemo(() => {
    // Safety check: return empty array if data is null/undefined
    if (!finalData) return [];

    let rawProducts = [];
    if (Array.isArray(finalData)) rawProducts = finalData;
    else if (finalData?.items) rawProducts = finalData.items;
    else if (finalData?.data) rawProducts = finalData.data;

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
          const g = (p.gender || '').trim().toUpperCase();
          if (g === 'MEN' || g === 'MALE') return 'Nam';
          if (g === 'WOMEN' || g === 'FEMALE') return 'Nữ';
          if (g === 'KIDS' || g === 'CHILD' || g === 'KID') return 'Trẻ em';
          if (g === 'ALL' || g === 'UNISEX') return 'Unisex';
          return 'Unisex'; // Default
        })(),
        // Lấy tên loại (Ưu tiên tên tìm được trong bảng Category)
        type: catObj?.category_name || p.category_name || 'Khác',
        // Add category hierarchy info
        categoryId: p.category_id,
        parentCategoryId: catObj?.parent_category_id || null,
        sizes: p.variants ? p.variants.map(v => v.size) : [],
        // Add image URLs from API response
        primary_image_url: p.primary_image_url,
        image_url: p.image_url
      };
    });

    // 2. Thực hiện lọc
    let filtered = normalized.filter(product => {
      // Lọc Giới tính
      if (selectedGenders.length > 0 && !selectedGenders.includes(product.gender)) return false;

      // Lọc Loại sản phẩm (dùng parent_category_id hierarchy)
      if (selectedTypes.length > 0) {
        // Build map: filterName -> parent category IDs
        const filterCategoryMap = {};

        selectedTypes.forEach(filterName => {
          // Find parent category by name
          const parentCat = categories.find(cat =>
            cat.category_name === filterName && cat.parent_category_id === null
          );

          if (parentCat) {
            filterCategoryMap[filterName] = parentCat.category_id;
          }
        });

        // Check if product matches any selected filter
        const isMatch = selectedTypes.some(filterName => {
          const parentId = filterCategoryMap[filterName];
          if (!parentId) return false;

          // Match if:
          // 1. Product's category_id == parent category ID
          // 2. Product's parent_category_id == parent category ID (child of selected category)
          return product.categoryId === parentId || product.parentCategoryId === parentId;
        });

        if (!isMatch) return false;
      }

      // Lọc Size 
      // (Thêm check length để tránh ẩn hết sản phẩm khi API thiếu data size)
      if (selectedSizes.length > 0 && product.sizes.length > 0) {
        if (!product.sizes.some(s => selectedSizes.includes(s))) return false;
      }

      return true;
    });

    // Lọc theo Khoảng giá (Filter by Price Range)
    if (selectedPriceRanges.length > 0) {
      filtered = filtered.filter(product => {
        const price = product.salePrice || product.basePrice;
        // Check if price matches ANY of the selected ranges
        return selectedPriceRanges.some(rangeId => {
          const range = PRICE_RANGES.find(r => r.id === rangeId);
          return range && price >= range.min && price < range.max;
        });
      });
    }

    // 3. Sắp xếp theo giá (nếu có)
    if (priceSort === 'asc') {
      filtered = [...filtered].sort((a, b) => {
        const priceA = a.salePrice || a.basePrice;
        const priceB = b.salePrice || b.basePrice;
        return priceA - priceB;
      });
    } else if (priceSort === 'desc') {
      filtered = [...filtered].sort((a, b) => {
        const priceA = a.salePrice || a.basePrice;
        const priceB = b.salePrice || b.basePrice;
        return priceB - priceA;
      });
    }

    return filtered;
  }, [finalData, categories, selectedGenders, selectedTypes, selectedSizes, priceSort, location.search, selectedPriceRanges]);

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

  // Helper: Clear category_id and featured from URL
  const clearFeaturedParams = () => {
    const params = new URLSearchParams(location.search);
    if (params.has('category_id') || params.has('featured')) {
      const newParams = new URLSearchParams(location.search);
      newParams.delete('category_id');
      newParams.delete('featured');
      navigate(`/product?${newParams.toString()}`, { replace: true });
    }
  };

  // Helper toggle - Clear URL params when user manually changes filters
  const toggleFilter = (state, setState, value) => {
    clearFeaturedParams();
    setState(prev => prev.includes(value) ? prev.filter(i => i !== value) : [...prev, value]);
  };

  // Toggle price sort: none -> asc -> desc -> none
  const togglePriceSort = () => {
    clearFeaturedParams(); // Clear URL params when user sorts
    setPriceSort(prev => {
      if (prev === 'none') return 'asc';
      if (prev === 'asc') return 'desc';
      return 'none';
    });
  };

  // Handle tab change - clear URL params
  const handleTabChange = (tab) => {
    clearFeaturedParams(); // Clear URL params when user clicks tab
    setActiveTab(tab);
  };

  // --- RENDER UI ---
  if (finalLoading && !finalData) return <div className="loading-container"><div className="loading-spinner"></div><p>Đang tải dữ liệu...</p></div>;
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
              {['Nam', 'Nữ', 'Trẻ em', 'Unisex'].map(g => (
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
                  // 1. Lấy child categories (có parent)
                  // 2. Tìm parent category của chúng
                  // 3. Hiển thị unique parent names
                  [...new Set(
                    categories
                      .filter(cat => cat.parent_category_id !== null) // Child categories
                      .map(child => {
                        // Tìm parent category
                        const parent = categories.find(c =>
                          c.category_id === child.parent_category_id
                        );
                        return parent?.category_name; // Lấy tên parent
                      })
                      .filter(Boolean) // Loại bỏ undefined
                  )].map(parentName => (
                    <label key={parentName} className="filter-checkbox">
                      <input
                        type="checkbox"
                        checked={selectedTypes.includes(parentName)}
                        onChange={() => toggleFilter(selectedTypes, setSelectedTypes, parentName)}
                      />
                      <span>{parentName}</span>
                    </label>
                  ))
                ) : (
                  <span className="loading-text">Đang tải...</span>
                )}
              </div>
            </div>

            {/* Khoảng giá */}
            <div className="filter-group">
              <h4>Khoảng giá</h4>
              {PRICE_RANGES.map(range => (
                <label key={range.id} className="filter-checkbox">
                  <input
                    type="checkbox"
                    checked={selectedPriceRanges.includes(range.id)}
                    onChange={() => toggleFilter(selectedPriceRanges, setSelectedPriceRanges, range.id)}
                  />
                  <span>{range.label}</span>
                </label>
              ))}
            </div>

            {/* Nút xóa */}
            {(selectedGenders.length > 0 || selectedSizes.length > 0 || selectedTypes.length > 0 || selectedPriceRanges.length > 0) && (
              <button
                className="clear-filters-btn"
                onClick={() => {
                  setSelectedGenders([]);
                  setSelectedSizes([]);
                  setSelectedTypes([]);
                  setSelectedPriceRanges([]);
                }}
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
              onClick={() => handleTabChange('all')}
            >
              Tất cả
            </button>
            <button
              className={`product-tab-btn ${activeTab === 'featured' ? 'active' : ''}`}
              onClick={() => handleTabChange('featured')}
            >
              Nổi bật
            </button>
            <button
              className={`product-tab-btn ${activeTab === 'best-sellers' ? 'active' : ''}`}
              onClick={() => handleTabChange('best-sellers')}
            >
              Bán chạy
            </button>
            <button
              className={`product-tab-btn ${activeTab === 'new' ? 'active' : ''}`}
              onClick={() => handleTabChange('new')}
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