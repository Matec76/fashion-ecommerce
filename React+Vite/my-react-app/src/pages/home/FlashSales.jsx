import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { API_ENDPOINTS } from '../../config/api.config';
import { useFetch } from '../../components/useFetch';
import Header from '../../components/Header';
import Footer from '../../components/Footer_1';
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

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleString('vi-VN', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const calculateTimeLeft = (endDate) => {
        const difference = new Date(endDate) - new Date();
        if (difference <= 0) return { expired: true };

        return {
            days: Math.floor(difference / (1000 * 60 * 60 * 24)),
            hours: Math.floor((difference / (1000 * 60 * 60)) % 24),
            minutes: Math.floor((difference / 1000 / 60) % 60),
            seconds: Math.floor((difference / 1000) % 60),
            expired: false
        };
    };

    const CountdownTimer = ({ endDate }) => {
        const [timeLeft, setTimeLeft] = useState(calculateTimeLeft(endDate));

        useEffect(() => {
            const timer = setInterval(() => {
                setTimeLeft(calculateTimeLeft(endDate));
            }, 1000);

            return () => clearInterval(timer);
        }, [endDate]);

        if (timeLeft.expired) {
            return <span className="countdown-expired">Đã kết thúc</span>;
        }

        return (
            <div className="countdown-timer">
                <div className="countdown-item">
                    <span className="countdown-value">{timeLeft.days}</span>
                    <span className="countdown-label">Ngày</span>
                </div>
                <span className="countdown-separator">:</span>
                <div className="countdown-item">
                    <span className="countdown-value">{String(timeLeft.hours).padStart(2, '0')}</span>
                    <span className="countdown-label">Giờ</span>
                </div>
                <span className="countdown-separator">:</span>
                <div className="countdown-item">
                    <span className="countdown-value">{String(timeLeft.minutes).padStart(2, '0')}</span>
                    <span className="countdown-label">Phút</span>
                </div>
                <span className="countdown-separator">:</span>
                <div className="countdown-item">
                    <span className="countdown-value">{String(timeLeft.seconds).padStart(2, '0')}</span>
                    <span className="countdown-label">Giây</span>
                </div>
            </div>
        );
    };

    const FlashSaleCard = ({ sale }) => {
        const discountPercent = sale.discount_percent || 0;

        return (
            <div className="flash-sale-card">
                <div className="flash-sale-header">
                    <div className="flash-sale-badge">
                        <span className="flash-icon">⚡</span>
                        <span>-{discountPercent}%</span>
                    </div>
                    <h3 className="flash-sale-name">{sale.name}</h3>
                </div>

                <div className="flash-sale-time">
                    <p className="time-label">
                        {activeTab === 'active' ? 'Kết thúc sau:' : 'Bắt đầu lúc:'}
                    </p>
                    {activeTab === 'active' ? (
                        <CountdownTimer endDate={sale.end_time} />
                    ) : (
                        <p className="start-time">{formatDate(sale.start_time)}</p>
                    )}
                </div>

                {sale.products && sale.products.length > 0 && (
                    <div className="flash-sale-products">
                        <h4>Sản phẩm giảm giá:</h4>
                        <div className="products-grid">
                            {sale.products.slice(0, 4).map((product) => (
                                <Link
                                    to={`/products/${product.slug || product.product_id}`}
                                    key={product.product_id}
                                    className="flash-product-item"
                                >
                                    <div className="product-image">
                                        {product.image_url ? (
                                            <img src={product.image_url} alt={product.product_name} />
                                        ) : (
                                            <div className="no-image">📷</div>
                                        )}
                                        <span className="discount-badge">-{discountPercent}%</span>
                                    </div>
                                    <div className="product-info">
                                        <p className="product-name">{product.product_name}</p>
                                        <div className="price-row">
                                            <span className="original-price">
                                                {formatPrice(product.base_price)}
                                            </span>
                                            <span className="sale-price">
                                                {formatPrice(product.base_price * (1 - discountPercent / 100))}
                                            </span>
                                        </div>
                                    </div>
                                </Link>
                            ))}
                        </div>
                        {sale.products.length > 4 && (
                            <p className="more-products">
                                +{sale.products.length - 4} sản phẩm khác
                            </p>
                        )}
                    </div>
                )}
            </div>
        );
    };

    const currentSales = activeTab === 'active' ? activeFlashSales : upcomingFlashSales;
    const isLoading = activeTab === 'active' ? activeLoading : upcomingLoading;

    return (
        <>
            <Header />
            <div className="flash-sales-page">
                <div className="flash-sales-hero">
                    <div className="hero-content">
                        <h1>
                            <span className="flash-icon-large">⚡</span>
                            Flash Sale
                            <span className="flash-icon-large">⚡</span>
                        </h1>
                        <p>Săn deal khủng - Giá sốc mỗi ngày!</p>
                    </div>
                </div>

                <div className="flash-sales-container">
                    <div className="tabs-container">
                        <button
                            className={`tab-btn ${activeTab === 'active' ? 'active' : ''}`}
                            onClick={() => setActiveTab('active')}
                        >
                            🔥 Đang diễn ra
                        </button>
                        <button
                            className={`tab-btn ${activeTab === 'upcoming' ? 'active' : ''}`}
                            onClick={() => setActiveTab('upcoming')}
                        >
                            ⏰ Sắp tới
                        </button>
                    </div>

                    <div className="flash-sales-content">
                        {isLoading ? (
                            <div className="loading-container">
                                <div className="loading-spinner"></div>
                                <p>Đang tải...</p>
                            </div>
                        ) : currentSales && currentSales.length > 0 ? (
                            <div className="flash-sales-grid">
                                {currentSales.map((sale) => (
                                    <FlashSaleCard key={sale.flash_sale_id} sale={sale} />
                                ))}
                            </div>
                        ) : (
                            <div className="no-sales">
                                <span className="no-sales-icon">📭</span>
                                <h3>
                                    {activeTab === 'active'
                                        ? 'Không có Flash Sale nào đang diễn ra'
                                        : 'Chưa có Flash Sale nào sắp tới'
                                    }
                                </h3>
                                <p>Hãy quay lại sau nhé!</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
            <Footer />
        </>
    );
};

export default FlashSales;
