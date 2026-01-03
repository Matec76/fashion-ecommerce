import React, { useState, useEffect, useMemo } from 'react';
import logger from '../../utils/logger';
import { useNavigate, Link } from 'react-router-dom';
import { API_ENDPOINTS, API_CONFIG } from '../../config/api.config';
import useFetch from '../../hooks/useFetch';
import useMutation from '../../hooks/useMutation';
import useDelete from '../../hooks/useDelete';
import '../../style/Wishlist.css';

const Wishlist = () => {
    const navigate = useNavigate();
    const [activeSection, setActiveSection] = useState('favorites'); // 'favorites' or wishlist_id
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [showAddProductModal, setShowAddProductModal] = useState(false);
    const [newWishlistName, setNewWishlistName] = useState('');
    const [newWishlistDescription, setNewWishlistDescription] = useState('');
    const [selectedProducts, setSelectedProducts] = useState([]);
    const [productDetails, setProductDetails] = useState({}); // Cache product details
    const [removingItems, setRemovingItems] = useState([]); // Track items being removed for optimistic update

    const token = localStorage.getItem('authToken');
    const { mutate, loading: mutateLoading } = useMutation();
    const { remove } = useDelete();

    // Fetch all wishlists - always fresh data
    const { data: wishlists, loading, refetch: refetchWishlists } = useFetch(
        API_ENDPOINTS.WISHLIST.LIST,
        { auth: true, skipCache: true }
    );

    // Fetch default wishlist (all favorites) - always fresh data
    const { data: defaultWishlist, refetch: refetchDefault } = useFetch(
        API_ENDPOINTS.WISHLIST.DEFAULT,
        { auth: true, skipCache: true }
    );

    // Fetch active wishlist details
    const activeWishlistId = activeSection !== 'favorites' ? activeSection : null;
    const { data: activeWishlistData, refetch: refetchActive } = useFetch(
        activeWishlistId ? API_ENDPOINTS.WISHLIST.DETAIL(activeWishlistId) : null,
        { auth: true, skipCache: true }
    );

    // Redirect if not logged in
    useEffect(() => {
        if (!token) {
            navigate('/login');
        }
    }, [token, navigate]);

    // Force refetch when component mounts to ensure fresh data
    useEffect(() => {
        if (token && refetchWishlists && refetchDefault) {
            // Small delay to ensure hooks are fully initialized
            const timer = setTimeout(() => {
                logger.log('Force refetching wishlist data...');
                refetchWishlists();
                refetchDefault();
            }, 100);
            return () => clearTimeout(timer);
        }
    }, [token, refetchWishlists, refetchDefault]);

    // Fetch product details for wishlist items
    useEffect(() => {
        const items = activeSection === 'favorites'
            ? (defaultWishlist?.items || [])
            : (activeWishlistData?.items || []);

        const fetchProductDetails = async () => {
            for (const item of items) {
                if (item.product_id && !productDetails[item.product_id] && !item.product?.product_name) {
                    try {
                        const response = await fetch(API_ENDPOINTS.PRODUCTS.DETAIL(item.product_id));
                        if (response.ok) {
                            const product = await response.json();
                            setProductDetails(prev => ({
                                ...prev,
                                [item.product_id]: product
                            }));
                        }
                    } catch (err) {
                        logger.error('Error fetching product:', err);
                    }
                }
            }
        };

        if (items.length > 0) {
            fetchProductDetails();
        }
    }, [defaultWishlist, activeWishlistData, activeSection]);

    // Get current items to display with enriched product data
    const displayItems = useMemo(() => {
        const items = activeSection === 'favorites'
            ? (defaultWishlist?.items || [])
            : (activeWishlistData?.items || []);

        // Filter out items that are being removed (optimistic update)
        const filteredItems = items.filter(item => !removingItems.includes(item.wishlist_item_id));

        // Enrich items with fetched product details
        return filteredItems.map(item => ({
            ...item,
            product: item.product?.product_name
                ? item.product
                : productDetails[item.product_id] || item.product
        }));
    }, [activeSection, defaultWishlist, activeWishlistData, productDetails, removingItems]);

    // Filter wishlists (exclude default)
    const customWishlists = useMemo(() => {
        if (!wishlists) return [];
        return wishlists.filter(w => !w.is_default);
    }, [wishlists]);

    // Create new wishlist
    const handleCreateWishlist = async (e) => {
        e.preventDefault();
        if (!newWishlistName.trim()) return;

        const result = await mutate(API_ENDPOINTS.WISHLIST.CREATE, {
            method: 'POST',
            body: {
                name: newWishlistName,
                description: newWishlistDescription,
                is_default: false
            }
        });

        if (result.success) {
            setShowCreateModal(false);
            setNewWishlistName('');
            setNewWishlistDescription('');
            refetchWishlists();
        }
    };

    // Remove item from wishlist (with optimistic update)
    const handleRemoveItem = async (itemId) => {
        if (!window.confirm('Bạn có chắc muốn xóa sản phẩm này?')) return;

        // Debug log
        logger.log('Removing item with ID:', itemId);
        logger.log('DELETE URL:', API_ENDPOINTS.WISHLIST.REMOVE_ITEM(itemId));

        // Optimistic update: immediately hide the item from UI
        setRemovingItems(prev => [...prev, itemId]);

        try {
            const result = await remove(API_ENDPOINTS.WISHLIST.REMOVE_ITEM(itemId));

            if (result.success) {
                // Refetch in background - keep item hidden via removingItems
                // Don't cleanup removingItems here, item stays hidden
                refetchDefault();
                refetchActive();
                refetchWishlists();
            } else {
                // Only revert if API explicitly failed (not 404)
                setRemovingItems(prev => prev.filter(id => id !== itemId));
            }
        } catch (error) {
            logger.error('Error removing item:', error);
            // Revert optimistic update if network error
            setRemovingItems(prev => prev.filter(id => id !== itemId));
        }
    };

    // Delete wishlist
    const handleDeleteWishlist = async (wishlistId) => {
        if (!window.confirm('Bạn có chắc muốn xóa danh sách này?')) return;

        const result = await remove(API_ENDPOINTS.WISHLIST.DELETE(wishlistId));
        if (result.success) {
            setActiveSection('favorites');
            refetchWishlists();
        }
    };

    // Add products to custom wishlist
    const handleAddProductsToList = async () => {
        if (selectedProducts.length === 0 || !activeWishlistId) return;

        for (const productId of selectedProducts) {
            await mutate(API_ENDPOINTS.WISHLIST.ADD_ITEM(activeWishlistId), {
                method: 'POST',
                body: { product_id: productId }
            });
        }

        setShowAddProductModal(false);
        setSelectedProducts([]);
        refetchActive();
        refetchWishlists();
    };

    // Toggle product selection
    const toggleProductSelection = (productId) => {
        setSelectedProducts(prev =>
            prev.includes(productId)
                ? prev.filter(id => id !== productId)
                : [...prev, productId]
        );
    };

    // Format price
    const formatPrice = (price) => {
        return new Intl.NumberFormat('vi-VN', {
            style: 'currency',
            currency: 'VND'
        }).format(price);
    };

    if (!token) {
        return (
            <div className="wishlist-page">
                <div className="wishlist-login-prompt">
                    <h2>Vui lòng đăng nhập</h2>
                    <p>Bạn cần đăng nhập để xem danh sách yêu thích</p>
                    <Link to="/login" className="login-btn">Đăng nhập</Link>
                </div>
            </div>
        );
    }

    if (loading) {
        return (
            <div className="wishlist-page">
                <div className="wishlist-loading">
                    <div className="spinner"></div>
                    <p>Đang tải...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="wishlist-page">
            <div className="wishlist-content">
                {/* Sidebar */}
                <aside className="wishlist-sidebar">
                    {/* Section 1: Yêu thích */}
                    <div
                        className={`sidebar-item favorites ${activeSection === 'favorites' ? 'active' : ''}`}
                        onClick={() => setActiveSection('favorites')}
                    >
                        <span>Yêu thích</span>
                        <span className="item-count">({defaultWishlist?.item_count || 0})</span>
                    </div>

                    <div className="sidebar-divider"></div>

                    {/* Section 2: Wishlist đã tạo */}
                    <div className="sidebar-section-title">WISHLIST ĐÃ TẠO</div>

                    {customWishlists.map(wishlist => (
                        <div
                            key={wishlist.wishlist_id}
                            className={`sidebar-item ${activeSection === wishlist.wishlist_id ? 'active' : ''}`}
                        >
                            <span
                                className="list-name"
                                onClick={() => setActiveSection(wishlist.wishlist_id)}
                            >
                                {wishlist.name}
                            </span>
                            <span className="item-count">({wishlist.item_count})</span>
                            <button
                                className="delete-list-btn"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    handleDeleteWishlist(wishlist.wishlist_id);
                                }}
                                title="Xóa danh sách"
                            >
                                ×
                            </button>
                        </div>
                    ))}

                    <button
                        className="create-list-btn"
                        onClick={() => setShowCreateModal(true)}
                    >
                        + Tạo mới
                    </button>
                </aside>

                {/* Main Content */}
                <main className="wishlist-main">
                    <div className="wishlist-header">
                        <p className="product-count">Hiển thị {displayItems.length} sản phẩm</p>
                        {activeSection !== 'favorites' && (
                            <button
                                className="add-products-btn"
                                onClick={() => setShowAddProductModal(true)}
                            >
                                + Thêm sản phẩm yêu thích
                            </button>
                        )}
                    </div>

                    {displayItems.length === 0 ? (
                        <div className="empty-wishlist">
                            <h3>Danh sách trống</h3>
                            <p>Chưa có sản phẩm nào</p>
                            <Link to="/product" className="browse-btn">Khám phá sản phẩm</Link>
                        </div>
                    ) : (
                        <div className="products-grid">
                            {displayItems.map(item => {
                                const product = item.product;
                                const imageUrl = product?.images?.[0]?.image_url || 'https://placehold.co/300x300?text=No+Image';
                                const productName = product?.product_name || 'Đang tải...';
                                const productSlug = product?.slug || item.product_id;
                                const productPrice = product?.base_price;

                                return (
                                    <div key={item.wishlist_item_id} className="product-card">
                                        <div
                                            className="product-image"
                                            onClick={() => navigate(`/products/${productSlug}`)}
                                        >
                                            <img
                                                src={imageUrl}
                                                alt={productName}
                                            />
                                        </div>
                                        <div className="product-info">
                                            <h3
                                                className="product-name"
                                                onClick={() => navigate(`/products/${productSlug}`)}
                                            >
                                                {productName}
                                            </h3>
                                            {productPrice && (
                                                <p className="product-price">
                                                    {formatPrice(productPrice)}
                                                </p>
                                            )}
                                            <button
                                                className="remove-btn"
                                                onClick={() => handleRemoveItem(item.wishlist_item_id)}
                                            >
                                                Xóa
                                            </button>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </main>
            </div>

            {/* Create Wishlist Modal */}
            {showCreateModal && (
                <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()}>
                        <button className="modal-close" onClick={() => setShowCreateModal(false)}>×</button>
                        <h2>Tạo danh sách mới</h2>
                        <form onSubmit={handleCreateWishlist}>
                            <div className="form-group">
                                <label>Tên danh sách *</label>
                                <input
                                    type="text"
                                    value={newWishlistName}
                                    onChange={(e) => setNewWishlistName(e.target.value)}
                                    placeholder="VD: Đồ mùa hè"
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label>Mô tả</label>
                                <textarea
                                    value={newWishlistDescription}
                                    onChange={(e) => setNewWishlistDescription(e.target.value)}
                                    placeholder="Mô tả ngắn..."
                                />
                            </div>
                            <div className="modal-actions">
                                <button type="button" onClick={() => setShowCreateModal(false)}>Hủy</button>
                                <button type="submit" className="primary" disabled={mutateLoading}>
                                    {mutateLoading ? 'Đang tạo...' : 'Tạo'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Add Products Modal */}
            {showAddProductModal && (
                <div className="modal-overlay" onClick={() => setShowAddProductModal(false)}>
                    <div className="modal-content add-products-modal" onClick={e => e.stopPropagation()}>
                        <button className="modal-close" onClick={() => setShowAddProductModal(false)}>×</button>
                        <h2>Chọn sản phẩm để thêm vào list</h2>

                        <div className="products-select-list">
                            {(defaultWishlist?.items || [])
                                .filter(item => {
                                    // Filter out products already in the current list
                                    const currentListProductIds = (activeWishlistData?.items || []).map(i => i.product_id);
                                    return !currentListProductIds.includes(item.product_id);
                                })
                                .map(item => {
                                    // Get product from fetched details or fallback to item.product
                                    const product = productDetails[item.product_id] || item.product;
                                    return (
                                        <label key={item.wishlist_item_id} className="product-select-item">
                                            <input
                                                type="checkbox"
                                                checked={selectedProducts.includes(item.product_id)}
                                                onChange={() => toggleProductSelection(item.product_id)}
                                            />
                                            {product?.images?.[0]?.image_url ? (
                                                <img
                                                    src={product.images[0].image_url}
                                                    alt={product?.product_name}
                                                    onError={(e) => {
                                                        e.target.style.display = 'none';
                                                        e.target.parentElement.insertAdjacentHTML('afterbegin',
                                                            '<div style="width: 50px; height: 50px; background-color: #e0e0e0; border-radius: 6px;"></div>'
                                                        );
                                                    }}
                                                />
                                            ) : (
                                                <div className="no-image-placeholder" style={{ width: 50, height: 50, backgroundColor: '#e0e0e0', borderRadius: 6 }} />
                                            )}
                                            <span className="product-select-name">{product?.product_name || 'Đang tải...'}</span>
                                        </label>
                                    );
                                })}
                        </div>

                        <div className="modal-actions">
                            <button type="button" onClick={() => setShowAddProductModal(false)}>Hủy</button>
                            <button
                                type="button"
                                className="primary"
                                onClick={handleAddProductsToList}
                                disabled={selectedProducts.length === 0 || mutateLoading}
                            >
                                {mutateLoading ? 'Đang thêm...' : `Thêm (${selectedProducts.length})`}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Wishlist;
