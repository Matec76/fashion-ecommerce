import { useState, useEffect, useMemo } from 'react';
import logger from '../../utils/logger';
import { useParams, Link, useNavigate } from 'react-router-dom';
import useFetch from '../../hooks/useFetch';
import { API_ENDPOINTS } from '../../config/api.config';
import { authFetch } from '../../utils/authInterceptor';
import { useCart } from './CartContext';
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
const VariantSelector = ({ variants, selectedColor, selectedSize, onColorChange, onSizeChange }) => {
    if (!variants || variants.length === 0) return null;

    // Group variants by color and size
    const colors = [...new Set(variants.map(v => v.color?.name).filter(Boolean))];
    const sizes = [...new Set(variants.map(v => v.size?.name).filter(Boolean))];

    // Get available sizes for selected color (or all sizes if no color selected)
    const availableSizes = selectedColor
        ? [...new Set(variants.filter(v => v.color?.name === selectedColor).map(v => v.size?.name).filter(Boolean))]
        : sizes;

    // Get available colors for selected size (or all colors if no size selected)
    const availableColors = selectedSize
        ? [...new Set(variants.filter(v => v.size?.name === selectedSize).map(v => v.color?.name).filter(Boolean))]
        : colors;

    return (
        <div className="variant-selector">
            {colors.length > 0 && (
                <div className="variant-group">
                    <h4>Màu sắc</h4>
                    <div className="variant-options">
                        {colors.map(color => {
                            const isAvailable = availableColors.includes(color);
                            const isSelected = selectedColor === color;
                            return (
                                <button
                                    key={color}
                                    className={`variant-btn color-btn ${isSelected ? 'active' : ''} ${!isAvailable ? 'disabled' : ''}`}
                                    onClick={() => onColorChange(color)}
                                    disabled={!isAvailable}
                                >
                                    {color}
                                </button>
                            );
                        })}
                    </div>
                </div>
            )}
            {sizes.length > 0 && (
                <div className="variant-group">
                    <h4>Kích cỡ</h4>
                    <div className="variant-options">
                        {sizes.map(size => {
                            const isAvailable = availableSizes.includes(size);
                            const isSelected = selectedSize === size;
                            return (
                                <button
                                    key={size}
                                    className={`variant-btn size-btn ${isSelected ? 'active' : ''} ${!isAvailable ? 'disabled' : ''}`}
                                    onClick={() => onSizeChange(size)}
                                    disabled={!isAvailable}
                                >
                                    {size}
                                </button>
                            );
                        })}
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
    // Fetch images with error handling for 422 errors
    // Use product_id (correct field from API) instead of id
    const productId = product.product_id || product.id;
    const { data: imagesData, error } = useFetch(
        API_ENDPOINTS.PRODUCTS.IMAGES(productId),
        { cacheTime: 300000 }
    );

    const imageUrl = useMemo(() => {
        // If API returns error or no data, use placeholder
        if (error || !imagesData || !Array.isArray(imagesData) || imagesData.length === 0) {
            return 'https://placehold.co/300x300?text=No+Image';
        }
        const primary = imagesData.find(img => img.is_primary) || imagesData[0];
        return primary.image_url;
    }, [imagesData, error]);

    const [imgError, setImgError] = useState(false);
    const displayImage = imgError ? 'https://placehold.co/300x300?text=No+Image' : imageUrl;

    return (
        <Link to={`/products/${product.slug || product.id}`} className="related-card">
            <div className="related-image">
                <img
                    src={displayImage}
                    alt={product.product_name}
                    onError={() => setImgError(true)}
                />
            </div>
            <div className="related-info">
                <h4>{product.product_name}</h4>
                <div className="related-price-wrapper">
                    {product.sale_price ? (
                        <>
                            <span className="related-sale-price">
                                {Number(product.sale_price).toLocaleString('vi-VN')}₫
                            </span>
                            <span className="related-base-price-strikethrough">
                                {Number(product.base_price).toLocaleString('vi-VN')}₫
                            </span>
                        </>
                    ) : (
                        <span className="related-price">
                            {Number(product.base_price).toLocaleString('vi-VN')}₫
                        </span>
                    )}
                </div>
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
    const [selectedImages, setSelectedImages] = useState([]);
    const [uploadedImageUrls, setUploadedImageUrls] = useState([]);
    const [uploadingImages, setUploadingImages] = useState(false);
    const [currentUserId, setCurrentUserId] = useState(null);

    // Fetch current user ID
    useEffect(() => {
        const fetchCurrentUser = async () => {
            const token = localStorage.getItem('authToken');
            if (!token) return;
            try {
                const response = await fetch(API_ENDPOINTS.USERS.ME, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (response.ok) {
                    const user = await response.json();
                    setCurrentUserId(user.user_id || user.id);
                }
            } catch (err) {
                logger.error('Error fetching user:', err);
            }
        };
        fetchCurrentUser();
    }, []);

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

    // Handle image selection
    const handleImageSelect = (e) => {
        const files = Array.from(e.target.files);
        if (files.length + selectedImages.length > 5) {
            alert('Bạn chỉ có thể tải lên tối đa 5 ảnh!');
            return;
        }
        setSelectedImages(prev => [...prev, ...files]);
    };

    // Remove selected image
    const removeImage = (index) => {
        setSelectedImages(prev => prev.filter((_, i) => i !== index));
        setUploadedImageUrls(prev => prev.filter((_, i) => i !== index));
    };

    // Upload images to server
    const uploadImages = async () => {
        const token = localStorage.getItem('authToken');
        if (!token || selectedImages.length === 0) return [];

        setUploadingImages(true);
        const urls = [];

        try {
            for (const file of selectedImages) {
                const formData = new FormData();
                formData.append('file', file);

                const response = await fetch(API_ENDPOINTS.REVIEWS.UPLOAD_IMAGE, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    },
                    body: formData
                });

                if (response.ok) {
                    const data = await response.json();
                    // API có thể trả về URL trong các trường khác nhau
                    const imageUrl = data.url || data.image_url || data.file_url || Object.values(data)[0];
                    if (imageUrl) urls.push(imageUrl);
                }
            }
        } catch (error) {
            logger.error('Error uploading images:', error);
        }

        setUploadingImages(false);
        return urls;
    };

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
            // Upload images first if any
            let imageUrls = [];
            if (selectedImages.length > 0) {
                imageUrls = await uploadImages();
            }

            const response = await fetch(API_ENDPOINTS.REVIEWS.CREATE, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    product_id: productId,
                    rating: newRating,
                    title: `Đánh giá ${newRating} sao`,
                    comment: newComment,
                    image_urls: imageUrls
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP Error: ${response.status}`);
            }

            alert('Cảm ơn bạn đã đánh giá sản phẩm! 🎉');
            setNewRating(5);
            setNewComment('');
            setSelectedImages([]);
            setUploadedImageUrls([]);
            // Reload trang để hiển thị review mới
            window.location.reload();
        } catch (error) {
            logger.error('Error submitting review:', error);
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

                        {/* Image Upload Section */}
                        <div className="form-group">
                            <label>Thêm hình ảnh (tối đa 5 ảnh):</label>
                            <div className="image-upload-section">
                                <input
                                    type="file"
                                    accept="image/*"
                                    multiple
                                    onChange={handleImageSelect}
                                    id="review-images"
                                    style={{ display: 'none' }}
                                />
                                <label htmlFor="review-images" className="upload-btn">
                                    📷 Chọn ảnh
                                </label>

                                {selectedImages.length > 0 && (
                                    <div className="image-preview-list">
                                        {selectedImages.map((file, index) => (
                                            <div key={index} className="image-preview-item">
                                                <img src={URL.createObjectURL(file)} alt={`Preview ${index + 1}`} />
                                                <button
                                                    type="button"
                                                    className="remove-image-btn"
                                                    onClick={() => removeImage(index)}
                                                >
                                                    ✕
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="form-actions">
                            <button type="button" className="cancel-btn" onClick={() => setShowReviewForm(false)}>
                                Hủy
                            </button>
                            <button type="submit" className="submit-btn" disabled={submitting || uploadingImages}>
                                {uploadingImages ? 'Đang tải ảnh...' : submitting ? 'Đang gửi...' : 'Gửi đánh giá'}
                            </button>
                        </div>
                    </form>
                )
            }

            {/* Reviews List */}
            <div className="reviews-list chat-style">
                {(!reviews || reviews.length === 0) ? (
                    <p className="no-reviews">Chưa có đánh giá nào cho sản phẩm này.</p>
                ) : (
                    reviews.map((review, index) => {
                        const isCurrentUser = currentUserId &&
                            (review.user?.user_id === currentUserId || review.user?.id === currentUserId);

                        return (
                            <div
                                key={review.id || index}
                                className={`review-item ${isCurrentUser ? 'own-review' : 'other-review'}`}
                            >
                                <div className="review-bubble">
                                    <div className="review-header">
                                        <div className="reviewer-info">
                                            <div className="reviewer-avatar">
                                                {review.user?.full_name?.[0] || review.user?.email?.[0] || 'U'}
                                            </div>
                                            <div>
                                                <span className="reviewer-name">
                                                    {review.user?.full_name || review.user?.email || 'Người dùng ẩn danh'}
                                                    {isCurrentUser && <span className="you-badge">Bạn</span>}
                                                </span>
                                                <StarRating rating={review.rating} size="sm" />
                                            </div>
                                        </div>
                                        <span className="review-date">
                                            {new Date(review.created_at).toLocaleDateString('vi-VN')}
                                        </span>
                                    </div>
                                    <p className="review-comment">{review.comment}</p>

                                    {/* Review Images */}
                                    {((review.images && review.images.length > 0) || (review.image_urls && review.image_urls.length > 0)) && (
                                        <div className="review-images">
                                            {(review.images || review.image_urls).map((img, i) => {
                                                const url = typeof img === 'string' ? img : img.image_url;
                                                return (
                                                    <div key={i} className="review-image-item">
                                                        <img
                                                            src={url}
                                                            alt={`Đánh giá từ ${review.user?.full_name || 'khách hàng'}`}
                                                            onClick={() => window.open(url, '_blank')}
                                                        />
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    )}
                                </div>
                            </div>
                        );
                    })
                )}
            </div>
        </div >
    );
};

// ==========================================
// SUB-COMPONENT: Q&A SECTION
// ==========================================
const QASection = ({ productId }) => {
    const [questions, setQuestions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showQuestionForm, setShowQuestionForm] = useState(false);
    const [newQuestion, setNewQuestion] = useState('');
    const [submitting, setSubmitting] = useState(false);

    // Fetch questions when productId changes
    useEffect(() => {
        logger.log('QASection - productId:', productId);
        if (!productId) return;

        const fetchQuestions = async () => {
            setLoading(true);
            try {
                const url = API_ENDPOINTS.QUESTIONS.BY_PRODUCT(productId);
                logger.log('Fetching questions from:', url);
                const response = await fetch(url);
                logger.log('Questions response status:', response.status);
                if (response.ok) {
                    const data = await response.json();
                    logger.log('Questions data:', data);
                    setQuestions(data || []);
                }
            } catch (error) {
                logger.error('Error fetching questions:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchQuestions();
    }, [productId]);

    const handleSubmitQuestion = async (e) => {
        e.preventDefault();

        const token = localStorage.getItem('authToken');
        if (!token) {
            alert('Vui lòng đăng nhập để đặt câu hỏi!');
            return;
        }

        if (!newQuestion.trim()) {
            alert('Vui lòng nhập câu hỏi!');
            return;
        }

        setSubmitting(true);

        try {
            const response = await fetch(API_ENDPOINTS.QUESTIONS.CREATE, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    product_id: parseInt(productId, 10),
                    question: newQuestion.trim()
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                // Handle different error formats
                let errorMessage = 'Có lỗi xảy ra';
                if (typeof errorData.detail === 'string') {
                    errorMessage = errorData.detail;
                } else if (Array.isArray(errorData.detail)) {
                    // FastAPI validation errors are usually in this format
                    errorMessage = errorData.detail.map(err => err.msg || err.message).join(', ');
                } else if (errorData.message) {
                    errorMessage = errorData.message;
                } else {
                    errorMessage = `HTTP Error: ${response.status}`;
                }
                throw new Error(errorMessage);
            }

            const newQ = await response.json();
            setQuestions(prev => [newQ, ...prev]);
            setNewQuestion('');
            setShowQuestionForm(false);
            alert('Câu hỏi của bạn đã được gửi! 🎉');
        } catch (error) {
            logger.error('Error submitting question:', error);
            alert(`Có lỗi xảy ra: ${error.message}`);
        } finally {
            setSubmitting(false);
        }
    };

    const formatDate = (dateString) => {
        if (!dateString) return '';
        return new Date(dateString).toLocaleDateString('vi-VN', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    };

    return (
        <div className="qa-section">
            <div className="qa-header">
                <h2>❓ Hỏi & Đáp về sản phẩm</h2>
                <button
                    className="ask-question-btn"
                    onClick={() => setShowQuestionForm(!showQuestionForm)}
                >
                    ✍️ Đặt câu hỏi
                </button>
            </div>

            {/* Question Form */}
            {showQuestionForm && (
                <form className="question-form" onSubmit={handleSubmitQuestion}>
                    <textarea
                        value={newQuestion}
                        onChange={(e) => setNewQuestion(e.target.value)}
                        placeholder="Bạn có thắc mắc gì về sản phẩm này? Hãy đặt câu hỏi..."
                        rows={3}
                        required
                    />
                    <div className="form-actions">
                        <button
                            type="button"
                            className="cancel-btn"
                            onClick={() => {
                                setShowQuestionForm(false);
                                setNewQuestion('');
                            }}
                        >
                            Hủy
                        </button>
                        <button
                            type="submit"
                            className="submit-btn"
                            disabled={submitting}
                        >
                            {submitting ? 'Đang gửi...' : 'Gửi câu hỏi'}
                        </button>
                    </div>
                </form>
            )}

            {/* Questions List */}
            <div className="questions-list">
                {loading ? (
                    <div className="loading-questions">
                        <div className="loading-spinner"></div>
                        <p>Đang tải câu hỏi...</p>
                    </div>
                ) : questions.length === 0 ? (
                    <div className="no-questions">
                        <p>💬 Chưa có câu hỏi nào cho sản phẩm này.</p>
                        <p>Hãy là người đầu tiên đặt câu hỏi!</p>
                    </div>
                ) : (
                    questions.map((q) => (
                        <div key={q.question_id} className="question-item chat-style">
                            {/* User Question - Right Side */}
                            <div className="question-content user-side">
                                <div className="question-body">
                                    <p className="question-text">{q.question}</p>
                                    <div className="question-meta">
                                        <span className="question-author">
                                            {q.user?.full_name || q.user?.email || 'Người dùng'}
                                        </span>
                                        <span className="question-date">
                                            {formatDate(q.created_at)}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* Admin Answer - Left Side */}
                            {q.answer && (
                                <div className="answer-content admin-side">
                                    <div className="answer-body">
                                        <div className="answer-label">🏪 Shop trả lời:</div>
                                        <p className="answer-text">{q.answer}</p>
                                        <div className="answer-meta">
                                            <span className="answer-author">
                                                {q.answerer?.full_name || 'Shop'}
                                            </span>
                                            <span className="answer-date">
                                                {formatDate(q.answered_at)}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {!q.answer && (
                                <div className="no-answer admin-side">
                                    <span>⏳ Đang chờ trả lời...</span>
                                </div>
                            )}
                        </div>
                    ))
                )}
            </div>
        </div>
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
    const [selectedColor, setSelectedColor] = useState(null);
    const [selectedSize, setSelectedSize] = useState(null);
    const [quantity, setQuantity] = useState(1);
    const [isInWishlist, setIsInWishlist] = useState(false);
    const [wishlistLoading, setWishlistLoading] = useState(false);

    // Flash sale state
    const [flashSaleInfo, setFlashSaleInfo] = useState(null);
    const [flashSaleTimeLeft, setFlashSaleTimeLeft] = useState(null);

    // Xác định API endpoint dựa trên identifier là số (ID) hay chuỗi (slug)
    const isNumericId = /^\d+$/.test(identifier);
    const productUrl = isNumericId
        ? API_ENDPOINTS.PRODUCTS.DETAIL(identifier)
        : API_ENDPOINTS.PRODUCTS.BY_SLUG(identifier);

    // Fetch product data with 3-minute cache
    const { data: product, loading: productLoading, error: productError } = useFetch(
        productUrl,
        { cacheTime: 180000 } // 3 minutes cache
    );

    // Lấy product ID từ data để fetch thêm thông tin (API trả về product_id)
    const productId = product?.product_id || product?.id;

    // Sử dụng images từ product response nếu có
    const productImages = product?.images;

    // Fetch variants, related products, reviews
    const variantsUrl = productId ? API_ENDPOINTS.PRODUCTS.VARIANTS(productId) : '';
    const relatedUrl = productId ? API_ENDPOINTS.PRODUCTS.RELATED(productId) : '';
    const reviewsUrl = productId ? API_ENDPOINTS.REVIEWS.BY_PRODUCT(productId) : '';
    const reviewSummaryUrl = productId ? API_ENDPOINTS.REVIEWS.SUMMARY(productId) : '';

    // Fetch colors and sizes for mapping
    const colorsUrl = API_ENDPOINTS.ATTRIBUTES.COLORS.LIST;
    const sizesUrl = API_ENDPOINTS.ATTRIBUTES.SIZES.LIST;

    // Track product view
    useEffect(() => {
        const trackView = async () => {
            if (productId) {
                try {
                    const token = localStorage.getItem('authToken');
                    await fetch(API_ENDPOINTS.ANALYTICS.TRACK_PRODUCT(productId), {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
                        }
                    });
                } catch (error) {
                    logger.error('Error tracking product view:', error);
                }
            }
        };
        trackView();
    }, [productId]);

    // Fetch images riêng nếu product không có images
    const imagesUrl = (!productImages || productImages.length === 0) && productId
        ? API_ENDPOINTS.PRODUCTS.IMAGES(productId)
        : '';

    const { data: fetchedImages, loading: imagesLoading } = useFetch(imagesUrl || null, { cacheTime: 300000 });
    const { data: variantsData } = useFetch(variantsUrl || null, { cacheTime: 300000 });
    const { data: colorsData } = useFetch(colorsUrl, { cacheTime: 300000 });
    const { data: sizesData } = useFetch(sizesUrl, { cacheTime: 300000 });
    const { data: relatedProducts } = useFetch(relatedUrl || null, { cacheTime: 180000 });
    const { data: reviews } = useFetch(reviewsUrl || null);
    const { data: reviewSummary } = useFetch(reviewSummaryUrl || null);

    // Map colors and sizes to variants
    const variants = useMemo(() => {
        if (!variantsData || !colorsData || !sizesData) return variantsData;

        return variantsData.map(variant => {
            const color = colorsData.find(c => c.color_id === variant.color_id);
            const size = sizesData.find(s => s.size_id === variant.size_id);

            return {
                ...variant,
                color: color ? { name: color.color_name, code: color.color_code } : null,
                size: size ? { name: size.size_name } : null
            };
        });
    }, [variantsData, colorsData, sizesData]);

    // Ưu tiên images từ product response
    const images = productImages && productImages.length > 0 ? productImages : fetchedImages;

    // Set default color and size from first variant
    useEffect(() => {
        if (variants && variants.length > 0) {
            if (!selectedColor && variants[0]?.color) {
                setSelectedColor(variants[0].color.name);
            }
            if (!selectedSize && variants[0]?.size) {
                setSelectedSize(variants[0].size.name);
            }
        }
    }, [variants, selectedColor, selectedSize]);

    // Find matching variant based on selected color and size
    useEffect(() => {
        if (variants && variants.length > 0) {
            const matchingVariant = variants.find(v => {
                const colorMatch = !selectedColor || v.color?.name === selectedColor;
                const sizeMatch = !selectedSize || v.size?.name === selectedSize;
                return colorMatch && sizeMatch;
            });
            setSelectedVariant(matchingVariant || variants[0]);
        }
    }, [variants, selectedColor, selectedSize]);

    // Check wishlist status khi có productId
    useEffect(() => {
        if (!productId) return;
        const token = localStorage.getItem('authToken');
        if (!token) {
            setIsInWishlist(false);
            return;
        }

        const checkWishlistStatus = async () => {
            try {
                const response = await fetch(`${API_ENDPOINTS.PRODUCTS.LIST.split('/products')[0]}/wishlist/check/${productId}`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (response.ok) {
                    const data = await response.json();
                    // Kiểm tra xem có item_id trong response không
                    const hasItem = data && typeof data === 'object' && Object.keys(data).length > 0 &&
                        Object.values(data).some(item => item && item.item_id);
                    setIsInWishlist(hasItem);
                } else {
                    setIsInWishlist(false);
                }
            } catch (err) {
                logger.error('Error checking wishlist:', err);
                setIsInWishlist(false);
            }
        };
        checkWishlistStatus();
    }, [productId]);

    // Check flash sale status
    useEffect(() => {
        if (!productId) return;

        const checkFlashSale = async () => {
            try {
                const response = await fetch(API_ENDPOINTS.FLASH_SALES.CHECK_PRODUCT(productId));
                if (response.ok) {
                    const data = await response.json();
                    if (data.in_flash_sale && data.flash_sale) {
                        setFlashSaleInfo(data.flash_sale);
                    } else {
                        setFlashSaleInfo(null);
                    }
                }
            } catch (err) {
                logger.error('Error checking flash sale:', err);
                setFlashSaleInfo(null);
            }
        };
        checkFlashSale();
    }, [productId]);

    // Countdown timer for flash sale
    useEffect(() => {
        if (!flashSaleInfo?.end_time) {
            setFlashSaleTimeLeft(null);
            return;
        }

        const calculateTimeLeft = () => {
            const difference = new Date(flashSaleInfo.end_time) - new Date();
            if (difference <= 0) {
                setFlashSaleTimeLeft(null);
                setFlashSaleInfo(null);
                return;
            }
            setFlashSaleTimeLeft({
                hours: Math.floor(difference / (1000 * 60 * 60)),
                minutes: Math.floor((difference / 1000 / 60) % 60),
                seconds: Math.floor((difference / 1000) % 60)
            });
        };

        calculateTimeLeft();
        const timer = setInterval(calculateTimeLeft, 1000);
        return () => clearInterval(timer);
    }, [flashSaleInfo]);

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
    const getProductRawPrice = () => {
        return product.sale_price || product.base_price || 0;
    };

    const baseDisplayPrice = selectedVariant?.price_adjustment
        ? Number(getProductRawPrice()) + Number(selectedVariant.price_adjustment)
        : Number(getProductRawPrice());

    // Calculate flash sale price if applicable
    const discountPercent = flashSaleInfo ? parseFloat(flashSaleInfo.discount_value) || 0 : 0;
    const flashSalePrice = flashSaleInfo ? baseDisplayPrice * (1 - discountPercent / 100) : null;
    const displayPrice = flashSalePrice || baseDisplayPrice;

    // Handler thêm giỏ hàng
    const handleAddToCart = async () => {
        const variantId = selectedVariant?.variant_id || selectedVariant?.id || null;
        const success = await addToCart(productId, quantity, variantId);
        if (success) {
            alert(`Đã thêm ${quantity} sản phẩm "${product.product_name}" vào giỏ hàng!`);
        }
    };

    // Handler thêm/xóa khỏi wishlist
    const handleToggleWishlist = async () => {
        const token = localStorage.getItem('authToken');
        if (!token) {
            alert('Vui lòng đăng nhập để thêm vào yêu thích!');
            navigate('/login');
            return;
        }

        setWishlistLoading(true);
        try {
            if (isInWishlist) {
                // Xóa khỏi wishlist - cần tìm item_id trước
                const checkResponse = await fetch(`${API_ENDPOINTS.PRODUCTS.LIST.split('/products')[0]}/wishlist/check/${productId}`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (checkResponse.ok) {
                    const wishlistData = await checkResponse.json();
                    const itemId = Object.values(wishlistData)[0]?.item_id;
                    if (itemId) {
                        await fetch(`${API_ENDPOINTS.PRODUCTS.LIST.split('/products')[0]}/wishlist/items/${itemId}`, {
                            method: 'DELETE',
                            headers: { 'Authorization': `Bearer ${token}` }
                        });
                        setIsInWishlist(false);
                    }
                }
            } else {
                // Thêm vào wishlist mặc định
                const variantId = selectedVariant?.variant_id || selectedVariant?.id || null;
                const response = await fetch(`${API_ENDPOINTS.PRODUCTS.LIST.split('/products')[0]}/wishlist/add-to-default`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        product_id: productId,
                        variant_id: variantId
                    })
                });
                if (response.ok) {
                    setIsInWishlist(true);
                    alert('Đã thêm vào danh sách yêu thích! ❤️');
                }
            }
        } catch (err) {
            logger.error('Error toggling wishlist:', err);
            alert('Có lỗi xảy ra!');
        } finally {
            setWishlistLoading(false);
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
                                {(() => {
                                    const g = product.gender.toUpperCase();
                                    if (g === 'MEN' || g === 'MALE') return 'Nam';
                                    if (g === 'WOMEN' || g === 'FEMALE') return 'Nữ';
                                    if (g === 'KIDS' || g === 'CHILD' || g === 'KID') return 'Trẻ em';
                                    return 'Unisex';
                                })()}
                            </span>
                        )}
                    </div>

                    {/* Flash Sale Banner */}
                    {flashSaleInfo && flashSaleTimeLeft && (
                        <div className="flash-sale-banner">
                            <div className="flash-sale-header">
                                <span className="flash-sale-title">{flashSaleInfo.sale_name}</span>
                                <span className="flash-sale-discount">-{discountPercent}%</span>
                            </div>
                            <div className="flash-sale-countdown">
                                <span className="countdown-label">Kết thúc sau:</span>
                                <div className="countdown-timer">
                                    <span className="time-box">{String(flashSaleTimeLeft.hours).padStart(2, '0')}</span>
                                    <span className="time-colon">:</span>
                                    <span className="time-box">{String(flashSaleTimeLeft.minutes).padStart(2, '0')}</span>
                                    <span className="time-colon">:</span>
                                    <span className="time-box">{String(flashSaleTimeLeft.seconds).padStart(2, '0')}</span>
                                </div>
                            </div>
                        </div>
                    )}

                    <div className="product-price-section">
                        <span className={`current-price ${flashSaleInfo ? 'sale-price' : ''}`}>
                            {displayPrice?.toLocaleString('vi-VN')}₫
                        </span>
                        {flashSaleInfo && (
                            <span className="original-price">
                                {baseDisplayPrice?.toLocaleString('vi-VN')}₫
                            </span>
                        )}
                        {!flashSaleInfo && selectedVariant?.price_adjustment > 0 && (
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
                        selectedColor={selectedColor}
                        selectedSize={selectedSize}
                        onColorChange={setSelectedColor}
                        onSizeChange={setSelectedSize}
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

                        <button
                            className={`wishlist-btn ${isInWishlist ? 'active' : ''}`}
                            onClick={handleToggleWishlist}
                            disabled={wishlistLoading}
                        >
                            {wishlistLoading ? '...' : isInWishlist ? (
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="#e74c3c" stroke="#e74c3c" strokeWidth="1.5">
                                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
                                </svg>
                            ) : (
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#999" strokeWidth="1.5">
                                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
                                </svg>
                            )}
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
                        {relatedProducts.slice(0, 4).map((prod, index) => (
                            <RelatedProductCard key={prod.product_id || prod.id || index} product={prod} />
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

            {/* Q&A Section */}
            <QASection productId={productId} />
        </div>
    );
};

export default ProductDetail;
