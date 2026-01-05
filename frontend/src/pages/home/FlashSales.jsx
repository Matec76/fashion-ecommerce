import { useState, useEffect, useCallback } from 'react';
import logger from '../../utils/logger';
import { Link } from 'react-router-dom';
import { API_ENDPOINTS, getAuthHeaders } from '../../config/api.config';
import '../../style/FlashSales.css';

const PRODUCTS_PER_PAGE = 18;

const FlashSales = () => {
    const [activeTab, setActiveTab] = useState('active');
    const [currentPage, setCurrentPage] = useState(1);
    const [flashSales, setFlashSales] = useState([]);
    const [upcomingFlashSales, setUpcomingFlashSales] = useState([]);
    const [loading, setLoading] = useState(true);

    // Fetch flash sales data using ACTIVE and UPCOMING APIs
    useEffect(() => {
        const fetchFlashSales = async () => {
            setLoading(true);

            try {
                // Fetch ACTIVE flash sales from API
                try {
                    const activeResponse = await fetch(API_ENDPOINTS.FLASH_SALES.ACTIVE, {
                        headers: getAuthHeaders()
                    });
                    if (activeResponse.ok) {
                        const activeData = await activeResponse.json();
                        const activeSales = Array.isArray(activeData) ? activeData : (activeData ? [activeData] : []);

                        // Fetch detail for each active sale to get products
                        const detailedActiveSales = await Promise.all(
                            activeSales.map(async (sale) => {
                                if (sale.flash_sale_id) {
                                    try {
                                        const detailResponse = await fetch(API_ENDPOINTS.FLASH_SALES.DETAIL(sale.flash_sale_id), {
                                            headers: getAuthHeaders()
                                        });
                                        if (detailResponse.ok) {
                                            return await detailResponse.json();
                                        }
                                    } catch (err) {
                                        logger.error(`Error fetching detail for flash sale ${sale.flash_sale_id}:`, err);
                                    }
                                }
                                return sale;
                            })
                        );

                        // Separate into truly active vs upcoming based on current time
                        const now = new Date();
                        const trulyActive = detailedActiveSales.filter(sale => {
                            const startTime = new Date(sale.start_time);
                            const endTime = new Date(sale.end_time);
                            return startTime <= now && now <= endTime;
                        });
                        const upcomingFromActive = detailedActiveSales.filter(sale => {
                            const startTime = new Date(sale.start_time);
                            return startTime > now;
                        });

                        setFlashSales(trulyActive);

                        // Fetch from /upcoming API (for is_active=false sales)
                        try {
                            const upcomingResponse = await fetch(API_ENDPOINTS.FLASH_SALES.UPCOMING, {
                                headers: getAuthHeaders()
                            });

                            if (upcomingResponse.ok) {
                                const upcomingData = await upcomingResponse.json();
                                const upcomingSales = Array.isArray(upcomingData) ? upcomingData : (upcomingData ? [upcomingData] : []);

                                const detailedUpcomingSales = await Promise.all(
                                    upcomingSales.map(async (sale) => {
                                        if (sale.flash_sale_id) {
                                            try {
                                                const detailResponse = await fetch(API_ENDPOINTS.FLASH_SALES.DETAIL(sale.flash_sale_id), {
                                                    headers: getAuthHeaders()
                                                });
                                                if (detailResponse.ok) {
                                                    return await detailResponse.json();
                                                }
                                            } catch (err) {
                                                logger.error(`Error fetching detail for upcoming flash sale ${sale.flash_sale_id}:`, err);
                                            }
                                        }
                                        return sale;
                                    })
                                );

                                // Merge: upcoming from active (is_active=true but start_time>now) + upcoming API (is_active=false)
                                const allUpcoming = [...upcomingFromActive];
                                detailedUpcomingSales.forEach(sale => {
                                    if (!allUpcoming.find(s => s.flash_sale_id === sale.flash_sale_id)) {
                                        allUpcoming.push(sale);
                                    }
                                });

                                setUpcomingFlashSales(allUpcoming);
                            } else {
                                setUpcomingFlashSales(upcomingFromActive);
                            }
                        } catch (err) {
                            logger.error('Error fetching upcoming flash sales:', err);
                            setUpcomingFlashSales(upcomingFromActive);
                        }
                    }
                } catch (err) {
                    logger.error('Error fetching active flash sales:', err);
                }
            } catch (error) {
                logger.error('Error fetching flash sales:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchFlashSales();
    }, []);

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
    const ProductCard = ({ product, discountPercent, isUpcoming = false }) => {
        const originalPrice = parseFloat(product.price) || 0;
        const salePrice = originalPrice * (1 - discountPercent / 100);
        const soldPercent = product.quantity_sold && product.quantity_limit
            ? Math.min(Math.round((product.quantity_sold / product.quantity_limit) * 100), 100)
            : Math.floor(Math.random() * 60) + 40;
        const productImage = product.images && product.images.length > 0 ? product.images[0].image_url : null;

        // Mystery price masking function for upcoming sales
        const maskPrice = (price) => {
            const priceStr = Math.round(price).toString();
            if (priceStr.length <= 3) return priceStr; // Too short to mask

            // Mask 2nd and 3rd digits: "1234567" -> "1??4567"
            const first = priceStr[0];
            const rest = priceStr.substring(3);

            return first + '??' + rest;
        };

        const formatMaskedPrice = (price) => {
            const masked = maskPrice(price);
            // Format with dots: "382??000" -> "38.2??.000đ"
            let result = '';
            let count = 0;
            for (let i = masked.length - 1; i >= 0; i--) {
                if (count === 3 && masked[i] !== '?') {
                    result = '.' + result;
                    count = 0;
                }
                result = masked[i] + result;
                if (masked[i] !== '?') count++;
            }
            return result + 'đ';
        };

        return (
            <Link
                to={`/products/${product.product_slug || product.product_id}`}
                className="fsp-product-card"
            >
                <div className="fsp-product-image">
                    {productImage ? (
                        <img src={productImage} alt={product.product_name} />
                    ) : (
                        <div className="fsp-no-image"></div>
                    )}
                    <span className="fsp-discount-tag">
                        {isUpcoming ? 'X%' : `-${discountPercent}%`}
                    </span>
                </div>

                <div className="fsp-product-content">
                    <h3 className="fsp-product-name">{product.product_name}</h3>

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
                            <span className="fsp-sale-price">
                                {isUpcoming ? formatMaskedPrice(salePrice) : formatPrice(salePrice)}
                            </span>
                            <span className="fsp-original-price">{formatPrice(originalPrice)}</span>
                        </div>
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
                discountPercent: parseFloat(sale.discount_value) || 0,
                flashSaleName: sale.sale_name,
                endTime: sale.end_time
            }))
        );
    };

    // Filter flash sales by active based on current time
    const now = new Date();
    const activeFlashSales = flashSales.filter(sale => {
        const startTime = new Date(sale.start_time);
        const endTime = new Date(sale.end_time);
        return startTime <= now && now <= endTime;
    });

    const currentSales = activeTab === 'active'
        ? (activeFlashSales.length > 0 ? activeFlashSales : flashSales)
        : upcomingFlashSales;
    const allProducts = getAllProducts(currentSales);
    const firstSale = flashSales.length > 0 ? flashSales[0] : null;

    return (
        <div className="fsp-page">
            {/* Hero Header */}
            <div className="fsp-hero">
                <div className="fsp-hero-content">
                    <h1 className="fsp-hero-title">
                        {firstSale ? firstSale.sale_name : 'Flash Sale'}
                    </h1>
                    <p className="fsp-hero-subtitle">Săn deal khủng - Giá sốc mỗi ngày!</p>
                </div>
            </div>

            {/* Timer Bar */}
            {firstSale && (
                <div className="fsp-timer-bar">
                    <div className="fsp-timer-info">
                        <span className="fsp-timer-text">
                            Giảm đến <strong>{parseFloat(firstSale.discount_value) || 0}%</strong>
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
                    onClick={() => { setActiveTab('active'); setCurrentPage(1); }}
                >
                    <span className="fsp-tab-label">Đang diễn ra</span>
                    {flashSales.length > 0 && flashSales[0].start_time && (
                        <div className="fsp-tab-times">
                            <span className="fsp-tab-time">
                                Bắt đầu: {new Date(flashSales[0].start_time).toLocaleString('vi-VN', {
                                    day: '2-digit', month: '2-digit', year: 'numeric',
                                    hour: '2-digit', minute: '2-digit'
                                })}
                            </span>
                            <span className="fsp-tab-time">
                                Kết thúc: {new Date(flashSales[0].end_time).toLocaleString('vi-VN', {
                                    day: '2-digit', month: '2-digit', year: 'numeric',
                                    hour: '2-digit', minute: '2-digit'
                                })}
                            </span>
                        </div>
                    )}
                </button>
                <button
                    className={`fsp-time-tab ${activeTab === 'upcoming' ? 'active' : ''}`}
                    onClick={() => { setActiveTab('upcoming'); setCurrentPage(1); }}
                >
                    <span className="fsp-tab-label">Sắp tới</span>
                    {upcomingFlashSales.length > 0 && (
                        <div className="fsp-tab-times">
                            <span className="fsp-tab-time">
                                Bắt đầu: {new Date(upcomingFlashSales[0].start_time).toLocaleString('vi-VN', {
                                    day: '2-digit', month: '2-digit', year: 'numeric',
                                    hour: '2-digit', minute: '2-digit'
                                })}
                            </span>
                            <span className="fsp-tab-time">
                                Kết thúc: {new Date(upcomingFlashSales[0].end_time).toLocaleString('vi-VN', {
                                    day: '2-digit', month: '2-digit', year: 'numeric',
                                    hour: '2-digit', minute: '2-digit'
                                })}
                            </span>
                        </div>
                    )}
                </button>
            </div>

            {/* Products List */}
            <div className="fsp-content">
                {loading ? (
                    <div className="fsp-loading">
                        <div className="fsp-spinner"></div>
                        <p>Đang tải Flash Sale...</p>
                    </div>
                ) : allProducts.length > 0 ? (
                    <>
                        <div className="fsp-products-list">
                            {allProducts
                                .slice((currentPage - 1) * PRODUCTS_PER_PAGE, currentPage * PRODUCTS_PER_PAGE)
                                .map((product, index) => (
                                    <ProductCard
                                        key={`${product.product_id}-${index}`}
                                        product={product}
                                        discountPercent={product.discountPercent}
                                        isUpcoming={activeTab === 'upcoming'}
                                    />
                                ))}
                        </div>

                        {/* Pagination */}
                        {allProducts.length > PRODUCTS_PER_PAGE && (
                            <div className="fsp-pagination">
                                <button
                                    className="fsp-page-btn"
                                    onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                                    disabled={currentPage === 1}
                                >
                                    ← Trước
                                </button>

                                <div className="fsp-page-numbers">
                                    {Array.from({ length: Math.ceil(allProducts.length / PRODUCTS_PER_PAGE) }, (_, i) => i + 1).map(page => (
                                        <button
                                            key={page}
                                            className={`fsp-page-number ${currentPage === page ? 'active' : ''}`}
                                            onClick={() => setCurrentPage(page)}
                                        >
                                            {page}
                                        </button>
                                    ))}
                                </div>

                                <button
                                    className="fsp-page-btn"
                                    onClick={() => setCurrentPage(prev => Math.min(prev + 1, Math.ceil(allProducts.length / PRODUCTS_PER_PAGE)))}
                                    disabled={currentPage === Math.ceil(allProducts.length / PRODUCTS_PER_PAGE)}
                                >
                                    Sau →
                                </button>
                            </div>
                        )}
                    </>
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
