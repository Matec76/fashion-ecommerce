import React, { useState, useEffect, useMemo, memo } from 'react';
import logger from '../../utils/logger';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { API_ENDPOINTS, API_CONFIG } from '../../config/api.config';
import useFetch from '../../hooks/useFetch';
import useMutation from '../../hooks/useMutation';
import useDelete from '../../hooks/useDelete';
import '../../style/SanPham.css';
import '../../style/Collections.css';

// ==========================================
// SUB-COMPONENT: PRODUCT CARD (giống SanPham.jsx)
// ==========================================
const ProductCard = memo(({ product }) => {
    const navigate = useNavigate();
    const [isInWishlist, setIsInWishlist] = useState(false);
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

    useEffect(() => {
        setImgError(false);
    }, [imageUrl]);

    const displayImage = (imageUrl && !imgError) ? imageUrl : 'https://placehold.co/600x600?text=No+Image';
    const isPlaceholder = !imageUrl || imgError;

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
            const result = await mutate(`${API_CONFIG.BASE_URL}/wishlist/add-to-default`, {
                method: 'POST',
                body: { product_id: product.id }
            });
            if (result.success) {
                setIsInWishlist(true);
            }
        }
    };

    return (
        <Link to={`/products/${product.slug || product.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
            <div className="product-card">
                {product.isNew && <span className="new-badge">NEW</span>}

                <button
                    className={`wishlist-icon-btn ${isInWishlist ? 'active' : ''}`}
                    onClick={handleWishlistClick}
                    disabled={wishlistLoading}
                    title={isInWishlist ? 'Xóa khỏi yêu thích' : 'Thêm vào yêu thích'}
                >
                    {wishlistLoading ? (
                        <span className="loading-dot">•</span>
                    ) : isInWishlist ? (
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="#e74c3c" stroke="#e74c3c">
                            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
                        </svg>
                    ) : (
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#666" strokeWidth="2">
                            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
                        </svg>
                    )}
                </button>

                <div className="product-image">
                    {loading ? (
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
// MAIN COMPONENT: COLLECTION DETAIL
// ==========================================
function CollectionDetail() {
    const { slug } = useParams();
    // Fetch collection data with 5-minute cache
    const { data: collection, loading, error } = useFetch(
        API_ENDPOINTS.COLLECTIONS.BY_SLUG(slug),
        { cacheTime: 300000 } // 5 minutes cache
    );

    // Pagination
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 18;

    // Chuẩn hóa sản phẩm
    const normalizedProducts = useMemo(() => {
        if (!collection?.products) return [];
        return collection.products.map(p => ({
            id: p.id || p.product_id,
            name: p.product_name || p.name,
            slug: p.slug,
            basePrice: typeof p.base_price === 'string' ? parseFloat(p.base_price) : (p.base_price || 0),
            salePrice: p.sale_price ? (typeof p.sale_price === 'string' ? parseFloat(p.sale_price) : p.sale_price) : null,
            isNew: p.is_new_arrival || false,
            type: p.category_name || 'Sản phẩm',
            primary_image_url: p.primary_image_url,
            image_url: p.image_url
        }));
    }, [collection]);

    // Pagination logic
    const indexOfLastItem = currentPage * itemsPerPage;
    const indexOfFirstItem = indexOfLastItem - itemsPerPage;
    const currentProducts = normalizedProducts.slice(indexOfFirstItem, indexOfLastItem);
    const totalPages = Math.ceil(normalizedProducts.length / itemsPerPage);

    useEffect(() => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }, [currentPage]);

    if (loading) {
        return (
            <div className="loading-container">
                <div className="loading-spinner"></div>
                <p>Đang tải bộ sưu tập...</p>
            </div>
        );
    }

    if (error || !collection) {
        return (
            <div className="error-container">
                <p style={{ fontSize: '16px' }}>Không tìm thấy bộ sưu tập này.</p>
                <Link to="/collections" style={{ color: '#000', marginTop: '1rem', display: 'inline-block', fontSize: '14px' }}>
                    ← Quay lại danh sách
                </Link>
            </div>
        );
    }

    return (
        <div className="san-pham-page">
            {/* Hero Header */}
            <header className="collection-hero-section" style={{
                backgroundImage: collection.image_url
                    ? `linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url(${collection.image_url})`
                    : 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)'
            }}>
                <div className="collection-hero-content">
                    <h1 className="collection-hero-title">{collection.collection_name}</h1>
                    {collection.description && (
                        <p className="collection-hero-description">{collection.description}</p>
                    )}
                </div>
            </header>

            <div className="content-wrapper">
                {/* SIDEBAR - Collection Info */}
                <aside className="sidebar-filters">
                    <div className="filter-section">
                        <h3 className="sidebar-title">THÔNG TIN</h3>

                        <div className="filter-group">
                            <h4 className="collection-sidebar-name">{collection.collection_name}</h4>
                            {collection.description && (
                                <p className="collection-sidebar-desc">
                                    {collection.description}
                                </p>
                            )}
                        </div>

                        {collection.start_date && (
                            <div className="filter-group">
                                <h4 className="sidebar-info-label">Thời gian</h4>
                                <div className="date-info">
                                    <p className="date-item">
                                        <span className="dot start"></span>
                                        Bắt đầu: {new Date(collection.start_date).toLocaleDateString('vi-VN')}
                                    </p>
                                    {collection.end_date && (
                                        <p className="date-item">
                                            <span className="dot end"></span>
                                            Kết thúc: {new Date(collection.end_date).toLocaleDateString('vi-VN')}
                                        </p>
                                    )}
                                </div>
                            </div>
                        )}

                        <Link to="/collections" className="clear-filters-btn" style={{ textDecoration: 'none', display: 'block', textAlign: 'center' }}>
                            ← Xem tất cả bộ sưu tập
                        </Link>
                    </div>
                </aside>

                {/* MAIN CONTENT */}
                <main className="main-content">
                    <div className="product-count">
                        <p>Hiển thị {normalizedProducts.length} sản phẩm trong bộ sưu tập</p>
                    </div>

                    {normalizedProducts.length === 0 ? (
                        <div className="no-products">
                            <p>Chưa có sản phẩm nào trong bộ sưu tập này.</p>
                        </div>
                    ) : (
                        <div className="products-grid">
                            {currentProducts.map(p => (
                                <ProductCard key={p.id} product={p} />
                            ))}
                        </div>
                    )}

                    {/* Pagination */}
                    {normalizedProducts.length > itemsPerPage && (
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

export default CollectionDetail;
