import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import '/src/style/main.css';
import { Link } from 'react-router-dom';
import { API_ENDPOINTS } from '../../config/api.config';
import { useFetch } from '../../components/useFetch';

const SLIDER_CONFIG = {
  TRANSITION_DURATION: 500,
  AUTO_SLIDE_INTERVAL: 3000,
};

const FEATURED_CATEGORIES = Object.freeze([
  { to: '/product?type=Giày', title: 'GIÀY', imgAlt: 'Giày' },
  { to: '/product?type=Áo', title: 'QUẦN ÁO', imgAlt: 'Quần áo' },
  { to: '/product', title: 'PHỤ KIỆN', imgAlt: 'Phụ kiện' }
]);

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

  if (timeLeft.expired) return <span className="fs-expired">Đã kết thúc</span>;

  return (
    <div className="fs-countdown">
      <span className="fs-time-box">{String(timeLeft.hours).padStart(2, '0')}</span>
      <span className="fs-colon">:</span>
      <span className="fs-time-box">{String(timeLeft.minutes).padStart(2, '0')}</span>
      <span className="fs-colon">:</span>
      <span className="fs-time-box">{String(timeLeft.seconds).padStart(2, '0')}</span>
    </div>
  );
};

const TrangChu = () => {
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const intervalRef = useRef(null);

  // Fetch Flash Sales data
  const { data: flashSales, loading: flashLoading } = useFetch(API_ENDPOINTS.FLASH_SALES.ACTIVE);

  const heroImages = useMemo(() => [
    'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=1600',
    'https://images.unsplash.com/photo-1483985988355-763728e1935b?w=1600',
    'https://images.unsplash.com/photo-1445205170230-053b83016050?w=1600',
    'https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=1600'
  ], []);

  const nextSlide = useCallback(() => {
    setCurrentImageIndex((prevIndex) => (prevIndex + 1) % heroImages.length);
  }, [heroImages.length]);

  const stopAutoSlide = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const startAutoSlide = useCallback(() => {
    stopAutoSlide();
    intervalRef.current = setInterval(() => {
      nextSlide();
    }, SLIDER_CONFIG.AUTO_SLIDE_INTERVAL);
  }, [nextSlide, stopAutoSlide]);

  useEffect(() => {
    startAutoSlide();
    return () => stopAutoSlide();
  }, [startAutoSlide, stopAutoSlide]);

  const handleDotClick = useCallback((index) => {
    stopAutoSlide();
    setCurrentImageIndex(index);
    startAutoSlide();
  }, [startAutoSlide, stopAutoSlide]);

  const formatPrice = (price) => {
    return new Intl.NumberFormat('vi-VN').format(price) + 'đ';
  };

  // Get first active flash sale
  const activeFlashSale = flashSales && flashSales.length > 0 ? flashSales[0] : null;

  return (
    <div className="homepage-container">
      <main>
        <section className="hero-section">
          <div className="hero-slider">
            <div
              className="hero-track"
              style={{ transform: `translateX(-${currentImageIndex * 100}%)` }}
            >
              {heroImages.map((image, index) => (
                <div
                  key={index}
                  className="hero-slide"
                  style={{ backgroundImage: `url(${image})` }}
                />
              ))}
            </div>
          </div>

          <div className="hero-overlay"></div>
          <div className="container hero-container">
            <div className="hero-content-box">
              <h1 className="hero-title">LIGHT THE BAY</h1>
              <p className="hero-subtitle">
                Sẵn sàng tăng tốc cùng bộ sưu tập Adidas x Mercedes-AMG PETRONAS F1 Team
              </p>
              <Link to="/product" className="hero-button">
                Mua ngay <span className="arrow">&#8594;</span>
              </Link>
            </div>
          </div>

          <div className="hero-indicators">
            {heroImages.map((_, index) => (
              <button
                key={index}
                className={`indicator-dot ${index === currentImageIndex ? 'active' : ''}`}
                onClick={() => handleDotClick(index)}
                aria-label={`Chuyển đến ảnh ${index + 1}`}
              />
            ))}
          </div>
        </section>

        {/* Flash Sale Section */}
        <section className="flash-sale-home-section">
          <div className="container">
            <div className="fs-header">
              <div className="fs-title-group">
                <h2 className="fs-title">
                  <span className="fs-icon">⚡</span>
                  Flash Sale
                </h2>
                {activeFlashSale && (
                  <span className="fs-badge">Giảm đến {activeFlashSale.discount_percent}%</span>
                )}
              </div>
              <div className="fs-timer-group">
                {activeFlashSale && <CountdownTimer endDate={activeFlashSale.end_time} />}
                <Link to="/flash-sales" className="fs-view-all">
                  Xem tất cả →
                </Link>
              </div>
            </div>

            {flashLoading ? (
              <div className="fs-loading">Đang tải...</div>
            ) : activeFlashSale && activeFlashSale.products && activeFlashSale.products.length > 0 ? (
              <div className="fs-products-grid">
                {activeFlashSale.products.slice(0, 4).map((product, index) => (
                  <Link
                    to={`/products/${product.slug || product.product_id}`}
                    key={product.product_id}
                    className="fs-product-card"
                  >
                    <div className="fs-product-image">
                      {product.image_url ? (
                        <img src={product.image_url} alt={product.product_name} />
                      ) : (
                        <div className="fs-no-image">📷</div>
                      )}
                      <span className="fs-discount-badge">{activeFlashSale.discount_percent}%</span>
                      {index === 0 && <span className="fs-hot-badge">Hot</span>}
                    </div>
                    <div className="fs-product-info">
                      <p className="fs-product-name">{product.product_name}</p>
                      <div className="fs-price-row">
                        <span className="fs-sale-price">
                          {formatPrice(product.base_price * (1 - activeFlashSale.discount_percent / 100))}
                        </span>
                        <span className="fs-original-price">
                          {formatPrice(product.base_price)}
                        </span>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="fs-empty">
                <p>🔥 Không có Flash Sale nào đang diễn ra</p>
                <Link to="/flash-sales" className="fs-empty-link">
                  Xem các chương trình sắp tới →
                </Link>
              </div>
            )}
          </div>
        </section>


        <section className="featured-section">
          <div className="container">
            <h2 className="section-title">Sản phẩm nổi bật</h2>
            <div className="featured-grid">
              {FEATURED_CATEGORIES.map(({ to, title, imgAlt }) => (
                <Link key={to} to={to} className="category-card group">
                  <img src="#" alt={imgAlt} className="category-image" />
                  <div className="category-overlay"></div>
                  <div className="category-content">
                    <h3 className="category-title">{title}</h3>
                    <div className="category-button">Mua ngay</div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </section>


        <section className="collection-section">
          <div className="club-container">
            <h2>BỘ SƯU TẬP</h2>
            <p>
              Khám phá các bộ sưu tập độc quyền, phong cách thời thượng và xu hướng mới nhất.
            </p>
            <Link to="/collections" className="join-btn">
              Xem ngay
              <span>&#8594;</span>
            </Link>
          </div>
        </section>

        <section className="club-section">
          <div className="club-container">
            <h2>TRỞ THÀNH HỘI VIÊN</h2>
            <p>
              Đăng ký ngay để nhận ưu đãi độc quyền, quyền truy cập sớm và những phần quà đặc biệt.
            </p>
            <Link to="/member" className="join-btn">
              Tham gia miễn phí
              <span>&#8594;</span>
            </Link>
          </div>
        </section>
      </main>
    </div>
  );
};

export default TrangChu;





