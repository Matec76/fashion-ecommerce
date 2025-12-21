import React from 'react';
import { Link } from 'react-router-dom';
import { API_ENDPOINTS } from '../../config/api.config';
import useFetch from '../../components/useFetch';
import '../../style/SanPham.css';
import '../../style/Collections.css';

const Collections = () => {
    const { data: collections, loading, error } = useFetch(API_ENDPOINTS.COLLECTIONS.LIST);

    if (loading) {
        return (
            <div className="loading-container">
                <div className="loading-spinner"></div>
                <p>Đang tải bộ sưu tập...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="error-container">
                <p>Không thể tải bộ sưu tập. Vui lòng thử lại sau.</p>
            </div>
        );
    }

    const activeCollections = collections?.filter(c => c.is_active) || [];

    return (
        <div className="san-pham-page">
            {/* Hero Header */}
            <div className="hero-header">
                <div className="hero-product-image" style={{ backgroundColor: '#1a1a2e' }}>
                    <div className="hero-overlay"></div>
                    <h1 style={{ position: 'absolute', color: 'white', bottom: 20, left: 40 }}>BỘ SƯU TẬP</h1>
                </div>
            </div>

            <div className="content-wrapper">
                {/* SIDEBAR */}
                <aside className="sidebar-filters">
                    <div className="filter-section">
                        <h3>BỘ SƯU TẬP</h3>

                        <div className="filter-group">
                            <h4>Danh sách</h4>
                            <div className="collection-sidebar-list">
                                {activeCollections.map(collection => (
                                    <Link
                                        key={collection.collection_id}
                                        to={`/collections/${collection.slug}`}
                                        className="collection-sidebar-item"
                                    >
                                        {collection.collection_name}
                                    </Link>
                                ))}
                            </div>
                        </div>

                        <Link to="/product" className="clear-filters-btn" style={{ textDecoration: 'none', display: 'block', textAlign: 'center' }}>
                            Xem tất cả sản phẩm →
                        </Link>
                    </div>
                </aside>

                {/* MAIN CONTENT */}
                <main className="main-content">
                    <div className="product-count">
                        <p>Hiển thị {activeCollections.length} bộ sưu tập</p>
                    </div>

                    {activeCollections.length === 0 ? (
                        <div className="no-products">
                            <p>Chưa có bộ sưu tập nào.</p>
                        </div>
                    ) : (
                        <div className="collections-grid">
                            {activeCollections.map(collection => (
                                <Link
                                    to={`/collections/${collection.slug}`}
                                    key={collection.collection_id}
                                    className="collection-card"
                                >
                                    <div className="collection-image-wrapper">
                                        {collection.image_url ? (
                                            <img
                                                src={collection.image_url}
                                                alt={collection.collection_name}
                                                className="collection-image"
                                            />
                                        ) : (
                                            <div className="collection-no-image">
                                                <span>🎨</span>
                                            </div>
                                        )}
                                        <div className="collection-overlay">
                                            <span className="collection-view-btn">Xem bộ sưu tập</span>
                                        </div>
                                    </div>
                                    <div className="collection-info">
                                        <h3 className="collection-name">{collection.collection_name}</h3>
                                        {collection.description && (
                                            <p className="collection-description">{collection.description}</p>
                                        )}
                                        {collection.end_date && (
                                            <p className="collection-date">
                                                Kết thúc: {new Date(collection.end_date).toLocaleDateString('vi-VN')}
                                            </p>
                                        )}
                                    </div>
                                </Link>
                            ))}
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
};

export default Collections;
