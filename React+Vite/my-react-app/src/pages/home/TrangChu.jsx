import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import '/src/style/main.css';
import { Link } from 'react-router-dom';

const SLIDER_CONFIG = {
  TRANSITION_DURATION: 500,
  AUTO_SLIDE_INTERVAL: 3000,
};

const FEATURED_CATEGORIES = Object.freeze([
  { to: '/product?type=Giày', title: 'GIÀY', imgAlt: 'Giày' },
  { to: '/product?type=Áo', title: 'QUẦN ÁO', imgAlt: 'Quần áo' },
  { to: '/product', title: 'PHỤ KIỆN', imgAlt: 'Phụ kiện' }
]);

const TrangChu = () => {
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const intervalRef = useRef(null);

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




