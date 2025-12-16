import { useState, useEffect, useMemo } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import useFetch from '../../components/useFetch';
import { API_ENDPOINTS } from '../../config/api.config';
import { useCart } from '../../context/useCart';
import '../../style/ProductDetail.css';

// ==========================================
// SUB-COMPONENT: IMAGE GALLERY
// ==========================================
const ImageGallery = ({ images, loading, productName }) => {
    // Tính initial index từ useMemo thay vì useEffect
    const initialIndex = useMemo(() => {
        if (images && images.length > 0) {
            const primaryIndex = images.findIndex(img => img.is_primary);
            return primaryIndex >= 0 ? primaryIndex : 0;
        }
        return 0;
    }, [images]);

    const [selectedIndex, setSelectedIndex] = useState(initialIndex);

    // Loading state
    if (loading) {
        return (
            <div className="image-gallery">
                <div className="main-image skeleton-image">
                    <div className="loading-spinner"></div>
                </div>
            </div>
        );
    }

    if (!images || images.length === 0) {
        return (
            <div className="image-gallery">
                <div className="main-image">
                    <img src="https://placehold.co/600x600?text=No+Image" alt={productName} />
                </div>
            </div>
        );
    }

    return (
        <div className="image-gallery">
            <div className="main-image">
                <img
                    src={images[selectedIndex]?.image_url}
                    alt={`${productName} - ${selectedIndex + 1}`}
                />
            </div>
            {images.length > 1 && (
                <div className="thumbnail-list">
                    {images.map((img, index) => (
                        <button
                            key={img.id || index}
                            className={`thumbnail ${index === selectedIndex ? 'active' : ''}`}
                            onClick={() => setSelectedIndex(index)}
                        >
                            <img src={img.image_url} alt={`Thumbnail ${index + 1}`} />
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
};

// ==========================================
// SUB-COMPONENT: VARIANT SELECTOR
// ==========================================
const VariantSelector = ({ variants, selectedVariant, onSelect }) => {
    if (!variants || variants.length === 0) return null;

    // Group variants by color and size
    const colors = [...new Set(variants.map(v => v.color?.name).filter(Boolean))];
    const sizes = [...new Set(variants.map(v => v.size?.name).filter(Boolean))];

    return (
        <div className="variant-selector">
            {colors.length > 0 && (
                <div className="variant-group">
                    <h4>Màu sắc</h4>
                    <div className="variant-options">
                        {colors.map(color => (
                            <button
                                key={color}
                                className={`variant-btn color-btn ${selectedVariant?.color?.name === color ? 'active' : ''}`}
                                onClick={() => {
                                    const variant = variants.find(v => v.color?.name === color);
                                    onSelect(variant);
                                }}
                            >
                                {color}
                            </button>
                        ))}
                    </div>
                </div>
            )}
            {sizes.length > 0 && (
                <div className="variant-group">
                    <h4>Kích cỡ</h4>
                    <div className="variant-options">
                        {sizes.map(size => (
                            <button
                                key={size}
                                className={`variant-btn size-btn ${selectedVariant?.size?.name === size ? 'active' : ''}`}
                                onClick={() => {
                                    const variant = variants.find(v => v.size?.name === size);
                                    onSelect(variant);
                                }}
                            >
                                {size}
                            </button>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

// ==========================================
// SUB-COMPONENT: RELATED PRODUCT CARD
// ==========================================
const RelatedProductCard = ({ product }) => {
    const { data: imagesData } = useFetch(API_ENDPOINTS.PRODUCTS.IMAGES(product.id));

    const imageUrl = useMemo(() => {
        if (!imagesData || imagesData.length === 0) return 'https://placehold.co/300x300?text=No+Image';
        const primary = imagesData.find(img => img.is_primary) || imagesData[0];
        return primary.image_url;
    }, [imagesData]);

    return (
        <Link to={`/products/${product.slug || product.id}`} className="related-card">
            <div className="related-image">
                <img src={imageUrl} alt={product.product_name} />
            </div>
            <div className="related-info">
                <h4>{product.product_name}</h4>
                <p className="related-price">
                    {Number(product.base_price)?.toLocaleString('vi-VN')}₫
                </p>
            </div>
        </Link>
    );
};

// ==========================================
// SUB-COMPONENT: STAR RATING
// ==========================================
const StarRating = ({ rating, size = 'md', interactive = false, onChange }) => {
    const [hoverRating, setHoverRating] = useState(0);

    const stars = [1, 2, 3, 4, 5];
    const sizeClass = size === 'sm' ? 'star-sm' : size === 'lg' ? 'star-lg' : '';

    return (
        <div className={`star-rating ${sizeClass}`}>
            {stars.map(star => (
                <span
                    key={star}
                    className={`star ${star <= (hoverRating || rating) ? 'filled' : ''} ${interactive ? 'interactive' : ''}`}
                    onClick={() => interactive && onChange?.(star)}
                    onMouseEnter={() => interactive && setHoverRating(star)}
                    onMouseLeave={() => interactive && setHoverRating(0)}
                >
                    ★
                </span>
            ))}
        </div>
    );
};

// ==========================================
// SUB-COMPONENT: REVIEW SECTION
// ==========================================
const ReviewSection = ({ reviews, reviewSummary, productRating, reviewCount, productId }) => {
    const [showReviewForm, setShowReviewForm] = useState(true);
    const [newRating, setNewRating] = useState(5);
    const [newComment, setNewComment] = useState('');
    const [submitting, setSubmitting] = useState(false);

    // Sử dụng dữ liệu từ API summary hoặc tính từ reviews
    const ratingStats = useMemo(() => {
        // Nếu có reviewSummary từ API, ưu tiên sử dụng
        if (reviewSummary) {
            const dist = reviewSummary.rating_distribution || {};
            return {
                avg: reviewSummary.average_rating?.toFixed(1) || '0',
                total: reviewSummary.total_reviews || 0,
                counts: [dist['5'] || 0, dist['4'] || 0, dist['3'] || 0, dist['2'] || 0, dist['1'] || 0]
            };
        }

        // Fallback: tính từ reviews array
        if (!reviews || reviews.length === 0) return { avg: '0', total: 0, counts: [0, 0, 0, 0, 0] };

        const counts = [0, 0, 0, 0, 0]; // 5, 4, 3, 2, 1 stars
        reviews.forEach(r => {
            const idx = 5 - Math.round(r.rating);
            if (idx >= 0 && idx < 5) counts[idx]++;
        });

        const avg = (reviews.reduce((sum, r) => sum + Number(r.rating), 0) / reviews.length).toFixed(1);
        return { avg, total: reviews.length, counts };
    }, [reviews, reviewSummary]);

    const handleSubmitReview = async (e) => {
        e.preventDefault();
        setSubmitting(true);

        // Kiểm tra đăng nhập
        const token = localStorage.getItem('authToken');
        if (!token) {
            alert('Vui lòng đăng nhập để đánh giá sản phẩm!');
            setSubmitting(false);
            return;
        }

        try {
            const response = await fetch(API_ENDPOINTS.REVIEWS.CREATE, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    product_id: productId,
                    rating: newRating,
                    comment: newComment
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP Error: ${response.status}`);
            }

            alert('Cảm ơn bạn đã đánh giá sản phẩm! 🎉');
            setNewRating(5);
            setNewComment('');
            // Reload trang để hiển thị review mới
            window.location.reload();
        } catch (error) {
            console.error('Error submitting review:', error);
            alert(`Có lỗi xảy ra: ${error.message}`);
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="review-section">
            <h2>Đánh giá sản phẩm</h2>

            {/* Summary */}
            <div className="review-summary">
                <div className="review-score">
                    <span className="score-number">{ratingStats.avg || productRating || '0'}</span>
                    <StarRating rating={Number(ratingStats.avg) || Number(productRating) || 0} size="lg" />
                    <span className="review-total">({ratingStats.total || reviewCount || 0} đánh giá)</span>
                </div>

                <div className="rating-bars">
                    {[5, 4, 3, 2, 1].map((star, idx) => {
                        const count = ratingStats.counts[idx];
                        const total = ratingStats.total || 0;
                        const percent = total > 0 ? Math.round((count / total) * 100) : 0;

                        return (
                            <div key={star} className="rating-bar-row">
                                <span className="star-label">{star} ★</span>
                                <div className="rating-bar">
                                    <div
                                        className="rating-bar-fill"
                                        style={{ width: `${percent}%` }}
                                    />
                                </div>
                                <span className="bar-stats">
                                    {count}
                                    <span className="bar-percent">({percent}%)</span>
                                </span>
                            </div>
                        );
                    })}
                </div>

                <button
                    className="write-review-btn"
                    onClick={() => setShowReviewForm(!showReviewForm)}
                >
                    ✏️ Viết đánh giá
                </button>
            </div>

            {/* Review Form */}
            {
                showReviewForm && (
                    <form className="review-form" onSubmit={handleSubmitReview}>
                        <h3>Đánh giá của bạn</h3>

                        <div className="form-group">
                            <label>Số sao:</label>
                            <StarRating
                                rating={newRating}
                                interactive
                                onChange={setNewRating}
                                size="lg"
                            />
                        </div>

                        <div className="form-group">
                            <label>Nhận xét:</label>
                            <textarea
                                value={newComment}
                                onChange={(e) => setNewComment(e.target.value)}
                                placeholder="Chia sẻ trải nghiệm của bạn về sản phẩm này..."
                                rows={4}
                                required
                            />
                        </div>

                        <div className="form-actions">
                            <button type="button" className="cancel-btn" onClick={() => setShowReviewForm(false)}>
                                Hủy
                            </button>
                            <button type="submit" className="submit-btn" disabled={submitting}>
                                {submitting ? 'Đang gửi...' : 'Gửi đánh giá'}
                            </button>
                        </div>
                    </form>
                )
            }

            {/* Reviews List */}
            <div className="reviews-list">
                {(!reviews || reviews.length === 0) ? (
                    <p className="no-reviews">Chưa có đánh giá nào cho sản phẩm này.</p>
                ) : (
                    reviews.map((review, index) => (
                        <div key={review.id || index} className="review-item">
                            <div className="review-header">
                                <div className="reviewer-info">
                                    <div className="reviewer-avatar">
                                        {review.user?.full_name?.[0] || review.user?.email?.[0] || 'U'}
                                    </div>
                                    <div>
                                        <span className="reviewer-name">
                                            {review.user?.full_name || review.user?.email || 'Người dùng ẩn danh'}
                                        </span>
                                        <StarRating rating={review.rating} size="sm" />
                                    </div>
                                </div>
                                <span className="review-date">
                                    {new Date(review.created_at).toLocaleDateString('vi-VN')}
                                </span>
                            </div>
                            <p className="review-comment">{review.comment}</p>
                        </div>
                    ))
                )}
            </div>
        </div >
    );
};

// ==========================================
// MAIN COMPONENT: PRODUCT DETAIL
// ==========================================
const ProductDetail = () => {
    const { identifier } = useParams();
    const navigate = useNavigate();
    const { addToCart } = useCart();
    const [selectedVariant, setSelectedVariant] = useState(null);
    const [quantity, setQuantity] = useState(1);

    // Xác định API endpoint dựa trên identifier là số (ID) hay chuỗi (slug)
    const isNumericId = /^\d+$/.test(identifier);
    const productUrl = isNumericId
        ? API_ENDPOINTS.PRODUCTS.DETAIL(identifier)
        : API_ENDPOINTS.PRODUCTS.BY_SLUG(identifier);

    // Fetch product data
    const { data: product, loading: productLoading, error: productError } = useFetch(productUrl);

    // Lấy product ID từ data để fetch thêm thông tin (API trả về product_id)
    const productId = product?.product_id || product?.id;

    // Sử dụng images từ product response nếu có
    const productImages = product?.images;

    // Fetch variants, related products, reviews
    const variantsUrl = productId ? API_ENDPOINTS.PRODUCTS.VARIANTS(productId) : '';
    const relatedUrl = productId ? API_ENDPOINTS.PRODUCTS.RELATED(productId) : '';
    const reviewsUrl = productId ? API_ENDPOINTS.REVIEWS.BY_PRODUCT(productId) : '';
    const reviewSummaryUrl = productId ? API_ENDPOINTS.REVIEWS.SUMMARY(productId) : '';

    // Fetch images riêng nếu product không có images
    const imagesUrl = (!productImages || productImages.length === 0) && productId
        ? API_ENDPOINTS.PRODUCTS.IMAGES(productId)
        : '';

    const { data: fetchedImages, loading: imagesLoading } = useFetch(imagesUrl || null);
    const { data: variants } = useFetch(variantsUrl || null);
    const { data: relatedProducts } = useFetch(relatedUrl || null);
    const { data: reviews } = useFetch(reviewsUrl || null);
    const { data: reviewSummary } = useFetch(reviewSummaryUrl || null);

    // Ưu tiên images từ product response
    const images = productImages && productImages.length > 0 ? productImages : fetchedImages;

    // Set default variant
    useEffect(() => {
        if (variants && variants.length > 0 && !selectedVariant) {
            setSelectedVariant(variants[0]);
        }
    }, [variants, selectedVariant]);

    // Loading state
    if (productLoading) {
        return (
            <div className="product-detail-page">
                <div className="loading-container">
                    <div className="loading-spinner"></div>
                    <p>Đang tải thông tin sản phẩm...</p>
                </div>
            </div>
        );
    }

    // Error state
    if (productError || !product) {
        return (
            <div className="product-detail-page">
                <div className="error-container">
                    <h2>😕 Không tìm thấy sản phẩm</h2>
                    <p>Sản phẩm bạn tìm kiếm không tồn tại hoặc đã bị xóa.</p>
                    <button className="back-btn" onClick={() => navigate('/product')}>
                        ← Quay lại trang sản phẩm
                    </button>
                </div>
            </div>
        );
    }

    // Tính giá hiển thị (có thể khác theo variant)
    const displayPrice = selectedVariant?.price_adjustment
        ? Number(product.base_price) + Number(selectedVariant.price_adjustment)
        : Number(product.base_price);

    // Handler thêm giỏ hàng
    const handleAddToCart = async () => {
        const variantId = selectedVariant?.variant_id || selectedVariant?.id || null;
        const success = await addToCart(productId, quantity, variantId);
        if (success) {
            alert(`Đã thêm ${quantity} sản phẩm "${product.product_name}" vào giỏ hàng!`);
        }
    };

    return (
        <div className="product-detail-page">
            {/* Breadcrumb */}
            <nav className="breadcrumb">
                <Link to="/">Trang chủ</Link>
                <span>/</span>
                <Link to="/product">Sản phẩm</Link>
                <span>/</span>
                <span className="current">{product.product_name}</span>
            </nav>

            {/* Main Content */}
            <div className="product-detail-content">
                {/* Left: Image Gallery */}
                <div className="product-gallery-section">
                    <ImageGallery
                        images={images}
                        loading={!images && imagesLoading}
                        productName={product.product_name}
                    />
                </div>

                {/* Right: Product Info */}
                <div className="product-info-section">
                    {product.is_new && <span className="new-tag">MỚI</span>}

                    <h1 className="product-title">{product.product_name}</h1>

                    <div className="product-meta">
                        {product.category && (
                            <span className="category-tag">{product.category.name}</span>
                        )}
                        {product.gender && (
                            <span className="gender-tag">
                                {product.gender === 'male' ? 'Nam' : product.gender === 'female' ? 'Nữ' : 'Unisex'}
                            </span>
                        )}
                    </div>

                    <div className="product-price-section">
                        <span className="current-price">
                            {displayPrice?.toLocaleString('vi-VN')}₫
                        </span>
                        {selectedVariant?.price_adjustment > 0 && (
                            <span className="original-price">
                                {Number(product.base_price)?.toLocaleString('vi-VN')}₫
                            </span>
                        )}
                    </div>

                    {/* Description */}
                    {product.description && (
                        <div className="product-description">
                            <h3>Mô tả sản phẩm</h3>
                            <p>{product.description}</p>
                        </div>
                    )}

                    {/* Variant Selector */}
                    <VariantSelector
                        variants={variants}
                        selectedVariant={selectedVariant}
                        onSelect={setSelectedVariant}
                    />

                    {/* Quantity & Add to Cart */}
                    <div className="purchase-section">
                        <div className="quantity-selector">
                            <button
                                onClick={() => setQuantity(q => Math.max(1, q - 1))}
                                disabled={quantity <= 1}
                            >
                                −
                            </button>
                            <span>{quantity}</span>
                            <button onClick={() => setQuantity(q => q + 1)}>+</button>
                        </div>

                        <button className="add-to-cart-btn" onClick={handleAddToCart}>
                            🛒 Thêm vào giỏ hàng
                        </button>
                    </div>

                    {/* Stock Status */}
                    {selectedVariant && (
                        <div className="stock-status">
                            {selectedVariant.stock_quantity > 0 ? (
                                <span className="in-stock">✓ Còn hàng ({selectedVariant.stock_quantity} sản phẩm)</span>
                            ) : (
                                <span className="out-of-stock">✗ Hết hàng</span>
                            )}
                        </div>
                    )}
                </div>
            </div>

            {/* Related Products */}
            {relatedProducts && relatedProducts.length > 0 && (
                <div className="related-products-section">
                    <h2>Sản phẩm liên quan</h2>
                    <div className="related-products-grid">
                        {relatedProducts.slice(0, 4).map(prod => (
                            <RelatedProductCard key={prod.id} product={prod} />
                        ))}
                    </div>
                </div>
            )}

            {/* Reviews Section */}
            <ReviewSection
                reviews={reviews}
                reviewSummary={reviewSummary}
                productRating={product.rating}
                reviewCount={product.review_count}
                productId={productId}
            />
        </div>
    );
};

export default ProductDetail;
