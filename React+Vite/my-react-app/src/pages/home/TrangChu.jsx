import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import logger from '../../utils/logger';
import '/src/style/main.css';
import { Link } from 'react-router-dom';
import { API_ENDPOINTS } from '../../config/api.config';
import { useFetch } from '../../hooks/useFetch';

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
  const [isEmailVerified, setIsEmailVerified] = useState(true); // Default true to hide section initially
  const intervalRef = useRef(null);
  const [flashSales, setFlashSales] = useState([]);
  const [flashLoading, setFlashLoading] = useState(true);

  // Banner state
  const [banners, setBanners] = useState([]);
  const [bannersLoading, setBannersLoading] = useState(true);

  // Default fallback banners
  const defaultBanners = useMemo(() => [
    {
      image_url: 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=1600',
      title: 'LIGHT THE BAY',
      description: 'Sẵn sàng tăng tốc cùng bộ sưu tập thời trang mới nhất',
      link_url: '/product',
      button_text: 'Mua ngay'
    },
    {
      image_url: 'https://images.unsplash.com/photo-1483985988355-763728e1935b?w=1600',
      title: 'NEW ARRIVALS',
      description: 'Khám phá xu hướng thời trang mới nhất mùa xuân hè',
      link_url: '/product',
      button_text: 'Khám phá'
    },
    {
      image_url: 'https://images.unsplash.com/photo-1445205170230-053b83016050?w=1600',
      title: 'SUMMER COLLECTION',
      description: 'Bộ sưu tập hè 2026 đã có mặt',
      link_url: '/collections',
      button_text: 'Xem ngay'
    },
    {
      image_url: 'https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=1600',
      title: 'FLASH SALE',
      description: 'Giảm giá đến 50% - Chỉ trong tuần này',
      link_url: '/flash-sales',
      button_text: 'Săn deal'
    }
  ], []);

  // Fetch Banners from CMS API
  useEffect(() => {
    const fetchBanners = async () => {
      setBannersLoading(true);
      try {
        const response = await fetch(API_ENDPOINTS.CMS.BANNERS.ACTIVE);
        if (response.ok) {
          const data = await response.json();
          // Sort by display_order and filter active banners
          const sortedBanners = Array.isArray(data)
            ? data.sort((a, b) => (a.display_order || 0) - (b.display_order || 0))
            : [];
          setBanners(sortedBanners.length > 0 ? sortedBanners : defaultBanners);
        } else {
          setBanners(defaultBanners);
        }
      } catch (error) {
        logger.error('Error fetching banners:', error);
        setBanners(defaultBanners);
      } finally {
        setBannersLoading(false);
      }
    };

    fetchBanners();
  }, [defaultBanners]);

  // Fetch Flash Sales data using ACTIVE API then DETAIL API
  useEffect(() => {
    const fetchFlashSales = async () => {
      setFlashLoading(true);

      try {
        // Step 1: Get active flash sale
        const activeResponse = await fetch(API_ENDPOINTS.FLASH_SALES.ACTIVE);
        if (activeResponse.ok) {
          const activeData = await activeResponse.json();

          // API returns an array, get the first active sale
          const firstActiveSale = Array.isArray(activeData) && activeData.length > 0 ? activeData[0] : null;

          if (firstActiveSale && firstActiveSale.flash_sale_id) {
            // Step 2: Get detailed info with products using the ID
            const detailResponse = await fetch(API_ENDPOINTS.FLASH_SALES.DETAIL(firstActiveSale.flash_sale_id));
            if (detailResponse.ok) {
              const detailData = await detailResponse.json();
              // Wrap in array for consistent handling
              setFlashSales([detailData]);
            } else {
              // Fallback to active data if detail fails
              setFlashSales([firstActiveSale]);
            }
          } else {
            setFlashSales([]);
          }
        } else {
          setFlashSales([]);
        }
      } catch (error) {
        logger.error('Error fetching flash sales:', error);
        setFlashSales([]);
      } finally {
        setFlashLoading(false);
      }
    };

    fetchFlashSales();
  }, []);

  // Check email verification status
  useEffect(() => {
    const checkVerification = async () => {
      const token = localStorage.getItem('authToken');
      if (!token) {
        setIsEmailVerified(true); // Hide for non-logged in users
        return;
      }

      try {
        const response = await fetch(API_ENDPOINTS.AUTH.ME, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (response.ok) {
          const data = await response.json();
          setIsEmailVerified(data.is_email_verified || false);
        }
      } catch (error) {
        logger.error('Error checking verification:', error);
      }
    };

    checkVerification();
  }, []);

  // Use banners for slider (from API or fallback)
  const slideBanners = banners.length > 0 ? banners : defaultBanners;

  const nextSlide = useCallback(() => {
    setCurrentImageIndex((prevIndex) => (prevIndex + 1) % slideBanners.length);
  }, [slideBanners.length]);

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

  // Get first flash sale with products
  const activeFlashSale = flashSales.length > 0 ? flashSales[0] : null;

  return (
    <div className="homepage-container">
      <main>
        <section className="hero-section">
          <div className="hero-slider">
            <div
              className="hero-track"
              style={{ transform: `translateX(-${currentImageIndex * 100}%)` }}
            >
              {slideBanners.map((banner, index) => (
                <div
                  key={banner.banner_id || index}
                  className="hero-slide"
                  style={{ backgroundImage: `url(${banner.image_url})` }}
                />
              ))}
            </div>
          </div>

          <div className="hero-overlay"></div>
          <div className="container hero-container">
            {slideBanners[currentImageIndex] && (
              <div className="hero-content-box">
                <h1 className="hero-title">{slideBanners[currentImageIndex].title}</h1>
                <p className="hero-subtitle">
                  {slideBanners[currentImageIndex].description}
                </p>
                <Link to={slideBanners[currentImageIndex].link_url || '/product'} className="hero-button">
                  {slideBanners[currentImageIndex].button_text || 'Mua ngay'} <span className="arrow">&#8594;</span>
                </Link>
              </div>
            )}
          </div>

          <div className="hero-indicators">
            {slideBanners.map((_, index) => (
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
                  Flash Sale
                </h2>
                {activeFlashSale && (
                  <span className="fs-badge">Giảm đến {parseFloat(activeFlashSale.discount_value) || 0}%</span>
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
                {activeFlashSale.products.slice(0, 4).map((product, index) => {
                  const originalPrice = parseFloat(product.price) || 0;
                  const discountValue = parseFloat(activeFlashSale.discount_value) || 0;
                  const salePrice = originalPrice * (1 - discountValue / 100);
                  const productImage = product.images && product.images.length > 0 ? product.images[0].image_url : null;

                  return (
                    <Link
                      to={`/products/${product.product_slug || product.product_id}`}
                      key={product.product_id}
                      className="fs-product-card"
                    >
                      <div className="fs-product-image">
                        {productImage ? (
                          <img src={productImage} alt={product.product_name} />
                        ) : (
                          <div className="fs-no-image"></div>
                        )}
                        <span className="fs-discount-badge">{discountValue}%</span>
                        {index === 0 && <span className="fs-hot-badge">Hot</span>}
                      </div>
                      <div className="fs-product-info">
                        <p className="fs-product-name">{product.product_name}</p>
                        <div className="fs-price-row">
                          <span className="fs-sale-price">
                            {formatPrice(salePrice)}
                          </span>
                          <span className="fs-original-price">
                            {formatPrice(originalPrice)}
                          </span>
                        </div>
                      </div>
                    </Link>
                  );
                })}
              </div>
            ) : (
              <div className="fs-empty">
                <p>Không có Flash Sale nào đang diễn ra</p>
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

        {/* Only show for unverified users */}
        {!isEmailVerified && (
          <section className="club-section">
            <div className="club-container">
              <h2>TRỞ THÀNH HỘI VIÊN</h2>
              <p>
                Đăng ký ngay để nhận ưu đãi độc quyền, quyền truy cập sớm và những phần quà đặc biệt.
              </p>
              <Link to="/loyalty" className="join-btn">
                Tham gia miễn phí
                <span>&#8594;</span>
              </Link>
            </div>
          </section>
        )}
      </main>
    </div>
  );
};

export default TrangChu;





