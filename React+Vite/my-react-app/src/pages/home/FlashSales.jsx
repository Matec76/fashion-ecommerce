import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { API_ENDPOINTS } from '../../config/api.config';
import { useFetch } from '../../components/useFetch';
import '../../style/FlashSales.css';

const FlashSales = () => {
    const [activeTab, setActiveTab] = useState('active');

    // Fetch flash sales data
    const {
        data: activeFlashSales,
        loading: activeLoading
    } = useFetch(API_ENDPOINTS.FLASH_SALES.ACTIVE);

    const {
        data: upcomingFlashSales,
        loading: upcomingLoading
    } = useFetch(API_ENDPOINTS.FLASH_SALES.UPCOMING);

    const formatPrice = (price) => {
        return new Intl.NumberFormat('vi-VN').format(price) + 'đ';
    };

    // Countdown Timer Component
    const CountdownTimer = ({ endDate }) => {
        const calculateTimeLeft = useCallback(() => {
            const difference = new Date(endDate) - new Date();
            if (difference <= 0) return { expired: true };
            return {
                hours: Math.floor(difference / (1000 * 60 * 60)),
                minutes: Math.floor((difference / 1000 / 60) % 60),
                seconds: Math.floor((difference / 1000) % 60),
                expired: false
            };
        }, [endDate]);

        const [timeLeft, setTimeLeft] = useState(calculateTimeLeft());

        useEffect(() => {
            const timer = setInterval(() => {
                setTimeLeft(calculateTimeLeft());
            }, 1000);
            return () => clearInterval(timer);
        }, [calculateTimeLeft]);

        if (timeLeft.expired) {
            return <span className="fsp-expired">Đã kết thúc</span>;
        }

        return (
            <div className="fsp-countdown">
                <span className="fsp-time-box">{String(timeLeft.hours).padStart(2, '0')}</span>
                <span className="fsp-colon">:</span>
                <span className="fsp-time-box">{String(timeLeft.minutes).padStart(2, '0')}</span>
                <span className="fsp-colon">:</span>
                <span className="fsp-time-box">{String(timeLeft.seconds).padStart(2, '0')}</span>
            </div>
        );
    };

    // Product Card Component
    const ProductCard = ({ product, discountPercent }) => {
        const salePrice = product.base_price * (1 - discountPercent / 100);
        const soldPercent = product.sold_quantity && product.stock_quantity
            ? Math.min(Math.round((product.sold_quantity / (product.sold_quantity + product.stock_quantity)) * 100), 100)
            : Math.floor(Math.random() * 60) + 40; // Mock data for demo

        return (
            <Link
                to={`/products/${product.slug || product.product_id}`}
                className="fsp-product-card"
            >
                <div className="fsp-product-image">
                    {product.image_url ? (
                        <img src={product.image_url} alt={product.product_name} />
                    ) : (
                        <div className="fsp-no-image">📷</div>
                    )}
                    <span className="fsp-discount-tag">-{discountPercent}%</span>
                </div>

                <div className="fsp-product-content">
                    <h3 className="fsp-product-name">{product.product_name}</h3>

                    <div className="fsp-product-tags">
                        <span className="fsp-tag fsp-tag-freeship">🚚 Freeship</span>
                        <span className="fsp-tag fsp-tag-cod">COD</span>
                    </div>

                    <div className="fsp-progress-container">
                        <div className="fsp-progress-bar">
                            <div
                                className="fsp-progress-fill"
                                style={{ width: `${soldPercent}%` }}
                            ></div>
                        </div>
                        <span className="fsp-sold-text">Đã bán {soldPercent}%</span>
                    </div>

                    <div className="fsp-price-row">
                        <div className="fsp-prices">
                            <span className="fsp-sale-price">{formatPrice(salePrice)}</span>
                            <span className="fsp-original-price">{formatPrice(product.base_price)}</span>
                        </div>
                        <button className="fsp-buy-btn">
                            <span className="fsp-discount-badge">{discountPercent}%</span>
                            Mua ngay
                        </button>
                    </div>
                </div>
            </Link>
        );
    };

    // Get all products from all flash sales
    const getAllProducts = (sales) => {
        if (!sales || sales.length === 0) return [];
        return sales.flatMap(sale =>
            (sale.products || []).map(product => ({
                ...product,
                discountPercent: sale.discount_percent || 0,
                flashSaleName: sale.name,
                endTime: sale.end_time
            }))
        );
    };

    const currentSales = activeTab === 'active' ? activeFlashSales : upcomingFlashSales;
    const isLoading = activeTab === 'active' ? activeLoading : upcomingLoading;
    const allProducts = getAllProducts(currentSales);
    const firstSale = currentSales && currentSales.length > 0 ? currentSales[0] : null;

    return (
        <div className="fsp-page">
            {/* Hero Header */}
            <div className="fsp-hero">
                <div className="fsp-hero-content">
                    <h1 className="fsp-hero-title">
                        Flash Sale
                    </h1>
                    <p className="fsp-hero-subtitle">Săn deal khủng - Giá sốc mỗi ngày!</p>
                </div>
            </div>

            {/* Timer Bar */}
            {firstSale && (
                <div className="fsp-timer-bar">
                    <div className="fsp-timer-info">
                        <span className="fsp-timer-text">
                            Giảm đến <strong>{firstSale.discount_percent}%</strong>
                        </span>
                    </div>
                    <div className="fsp-timer-countdown">
                        <span className="fsp-timer-label">Kết thúc sau:</span>
                        <CountdownTimer endDate={firstSale.end_time} />
                    </div>
                </div>
            )}

            {/* Time Tabs */}
            <div className="fsp-tabs-container">
                <button
                    className={`fsp-time-tab ${activeTab === 'active' ? 'active' : ''}`}
                    onClick={() => setActiveTab('active')}
                >
                    <span className="fsp-tab-label">Đang diễn ra</span>
                </button>
                <button
                    className={`fsp-time-tab ${activeTab === 'upcoming' ? 'active' : ''}`}
                    onClick={() => setActiveTab('upcoming')}
                >
                    <span className="fsp-tab-label">Sắp tới</span>
                </button>
            </div>

            {/* Products List */}
            <div className="fsp-content">
                {isLoading ? (
                    <div className="fsp-loading">
                        <div className="fsp-spinner"></div>
                        <p>Đang tải Flash Sale...</p>
                    </div>
                ) : allProducts.length > 0 ? (
                    <div className="fsp-products-list">
                        {allProducts.map((product, index) => (
                            <ProductCard
                                key={`${product.product_id}-${index}`}
                                product={product}
                                discountPercent={product.discountPercent}
                            />
                        ))}
                    </div>
                ) : (
                    <div className="fsp-empty">
                        <h3>
                            {activeTab === 'active'
                                ? 'Không có Flash Sale nào đang diễn ra'
                                : 'Chưa có Flash Sale nào sắp tới'
                            }
                        </h3>
                        <p>Hãy quay lại sau nhé!</p>
                        <Link to="/" className="fsp-back-home">
                            ← Về trang chủ
                        </Link>
                    </div>
                )}
            </div>
        </div>
    );
};

export default FlashSales;
