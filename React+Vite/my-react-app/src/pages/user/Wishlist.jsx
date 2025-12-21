import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { API_CONFIG } from '../../config/api.config';
import useFetch from '../../components/useFetch';
import useMutation from '../../components/useMutation';
import useDelete from '../../components/useDelete';
import '../../style/Wishlist.css';

const API_BASE_URL = API_CONFIG.BASE_URL;

const Wishlist = () => {
    const navigate = useNavigate();
    const [activeWishlistId, setActiveWishlistId] = useState(null);

    // Modal states
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [showMoveModal, setShowMoveModal] = useState(false);
    const [selectedItem, setSelectedItem] = useState(null);
    const [newWishlistName, setNewWishlistName] = useState('');
    const [newWishlistDescription, setNewWishlistDescription] = useState('');

    const token = localStorage.getItem('authToken');

    // Hooks cho API calls
    const { mutate } = useMutation();
    const { remove } = useDelete();

    // Fetch all wishlists với useFetch
    const {
        data: wishlists,
        loading,
        error,
        refetch: refetchWishlists
    } = useFetch(`${API_BASE_URL}/wishlist/me`, { auth: true });

    // Fetch wishlist details với useFetch
    const {
        data: activeWishlist,
        refetch: refetchDetails
    } = useFetch(
        activeWishlistId ? `${API_BASE_URL}/wishlist/${activeWishlistId}` : null,
        { auth: true }
    );

    // Redirect nếu chưa đăng nhập
    useEffect(() => {
        if (!token) {
            navigate('/login');
        }
    }, [token, navigate]);

    // Tự động chọn wishlist mặc định khi wishlists load xong
    useEffect(() => {
        if (wishlists && wishlists.length > 0 && !activeWishlistId) {
            const defaultWL = wishlists.find(w => w.is_default) || wishlists[0];
            if (defaultWL) {
                setActiveWishlistId(defaultWL.wishlist_id);
            }
        }
    }, [wishlists, activeWishlistId]);

    // Create new wishlist
    const handleCreateWishlist = async (e) => {
        e.preventDefault();
        if (!newWishlistName.trim()) return;

        const result = await mutate(`${API_BASE_URL}/wishlist`, {
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

    // Remove item from wishlist
    const handleRemoveItem = async (itemId) => {
        if (!window.confirm('Bạn có chắc muốn xóa sản phẩm này khỏi danh sách yêu thích?')) return;

        const result = await remove(`${API_BASE_URL}/wishlist/items/${itemId}`);

        if (result.success) {
            refetchDetails();
            refetchWishlists();
        }
    };

    // Move item to another wishlist
    const handleMoveItem = async (targetWishlistId) => {
        if (!selectedItem) return;

        const result = await mutate(`${API_BASE_URL}/wishlist/items/${selectedItem.item_id}/move`, {
            method: 'POST',
            body: { target_wishlist_id: targetWishlistId }
        });

        if (result.success) {
            setShowMoveModal(false);
            setSelectedItem(null);
            refetchDetails();
            refetchWishlists();
        }
    };

    // Set wishlist as default
    const handleSetDefault = async (wishlistId) => {
        const result = await mutate(`${API_BASE_URL}/wishlist/${wishlistId}/set-default`, {
            method: 'POST'
        });

        if (result.success) {
            refetchWishlists();
        }
    };

    // Delete wishlist
    const handleDeleteWishlist = async (wishlistId) => {
        const wishlist = wishlists.find(w => w.wishlist_id === wishlistId);
        if (wishlist?.is_default) {
            alert('Không thể xóa danh sách yêu thích mặc định!');
            return;
        }

        if (!window.confirm('Bạn có chắc muốn xóa danh sách này?')) return;

        const result = await remove(`${API_BASE_URL}/wishlist/${wishlistId}`);

        if (result.success) {
            refetchWishlists();
        }
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
            <div className="wishlist-container">
                {/* Header */}
                <div className="wishlist-header">
                    <h1>❤️ Danh sách yêu thích</h1>
                    <button
                        className="create-wishlist-btn"
                        onClick={() => setShowCreateModal(true)}
                    >
                        + Tạo danh sách mới
                    </button>
                </div>

                {error && <div className="error-message">{error}</div>}

                <div className="wishlist-content">
                    {/* Wishlist tabs */}
                    <div className="wishlist-tabs">
                        {wishlists && wishlists.map(wishlist => (
                            <div
                                key={wishlist.wishlist_id}
                                className={`wishlist-tab ${activeWishlistId === wishlist.wishlist_id ? 'active' : ''}`}
                                onClick={() => setActiveWishlistId(wishlist.wishlist_id)}
                            >
                                <span className="tab-name">
                                    {wishlist.name}
                                    {wishlist.is_default && <span className="default-badge">Mặc định</span>}
                                </span>
                                <span className="tab-count">{wishlist.item_count}</span>

                                <div className="tab-actions">
                                    {!wishlist.is_default && (
                                        <>
                                            <button
                                                className="set-default-btn"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleSetDefault(wishlist.wishlist_id);
                                                }}
                                                title="Đặt làm mặc định"
                                            >
                                                ⭐
                                            </button>
                                            <button
                                                className="delete-wishlist-btn"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleDeleteWishlist(wishlist.wishlist_id);
                                                }}
                                                title="Xóa danh sách"
                                            >
                                                🗑️
                                            </button>
                                        </>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Wishlist items */}
                    <div className="wishlist-items">
                        {activeWishlist?.items?.length > 0 ? (
                            <div className="items-grid">
                                {activeWishlist.items.map(item => (
                                    <div key={item.item_id} className="wishlist-item">
                                        <div className="item-image">
                                            <img
                                                src={item.product?.images?.[0]?.image_url || '/placeholder.jpg'}
                                                alt={item.product?.product_name}
                                                onClick={() => navigate(`/products/${item.product_id}`)}
                                            />
                                        </div>
                                        <div className="item-info">
                                            <h3
                                                className="item-name"
                                                onClick={() => navigate(`/products/${item.product_id}`)}
                                            >
                                                {item.product?.product_name || 'Sản phẩm'}
                                            </h3>
                                            <p className="item-price">
                                                {formatPrice(item.product?.base_price || 0)}
                                            </p>
                                            {item.variant && (
                                                <p className="item-variant">
                                                    Phân loại: {item.variant.color?.name} - {item.variant.size?.name}
                                                </p>
                                            )}
                                            {item.note && (
                                                <p className="item-note">📝 {item.note}</p>
                                            )}
                                        </div>
                                        <div className="item-actions">
                                            <button
                                                className="add-to-cart-btn"
                                                onClick={() => navigate(`/products/${item.product_id}`)}
                                            >
                                                🛒 Thêm vào giỏ
                                            </button>
                                            {wishlists.length > 1 && (
                                                <button
                                                    className="move-btn"
                                                    onClick={() => {
                                                        setSelectedItem(item);
                                                        setShowMoveModal(true);
                                                    }}
                                                >
                                                    📁 Di chuyển
                                                </button>
                                            )}
                                            <button
                                                className="remove-btn"
                                                onClick={() => handleRemoveItem(item.item_id)}
                                            >
                                                🗑️ Xóa
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="empty-wishlist">
                                <div className="empty-icon">💔</div>
                                <h3>Danh sách trống</h3>
                                <p>Chưa có sản phẩm nào trong danh sách yêu thích này</p>
                                <Link to="/product" className="browse-btn">
                                    Khám phá sản phẩm
                                </Link>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Create Wishlist Modal */}
            {showCreateModal && (
                <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()}>
                        <h2>Tạo danh sách yêu thích mới</h2>
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
                                    placeholder="Mô tả ngắn về danh sách này..."
                                />
                            </div>
                            <div className="modal-actions">
                                <button type="button" onClick={() => setShowCreateModal(false)}>
                                    Hủy
                                </button>
                                <button type="submit" className="primary">
                                    Tạo
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Move Item Modal */}
            {showMoveModal && (
                <div className="modal-overlay" onClick={() => setShowMoveModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()}>
                        <h2>Di chuyển đến danh sách khác</h2>
                        <div className="move-options">
                            {wishlists
                                .filter(w => w.wishlist_id !== activeWishlist?.wishlist_id)
                                .map(wishlist => (
                                    <button
                                        key={wishlist.wishlist_id}
                                        className="move-option"
                                        onClick={() => handleMoveItem(wishlist.wishlist_id)}
                                    >
                                        {wishlist.name}
                                        {wishlist.is_default && ' (Mặc định)'}
                                    </button>
                                ))
                            }
                        </div>
                        <button
                            className="cancel-btn"
                            onClick={() => setShowMoveModal(false)}
                        >
                            Hủy
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Wishlist;
