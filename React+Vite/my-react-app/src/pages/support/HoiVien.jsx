import React, { useState, useEffect } from 'react';
import { API_ENDPOINTS } from '../../config/api.config';
import '/src/style/SubPages.css';
import '/src/style/Loyalty.css';

const TIER_ICONS = {
  'bronze': '🥉',
  'silver': '🥈',
  'gold': '🥇',
  'platinum': '💎',
  'diamond': '👑',
};

const HoiVien = () => {
  const [tiers, setTiers] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [userLoyalty, setUserLoyalty] = useState(null);
  const [loading, setLoading] = useState(true);

  const isLoggedIn = !!localStorage.getItem('authToken');

  useEffect(() => {
    fetchTiers();
    fetchLeaderboard();
    if (isLoggedIn) {
      fetchUserLoyalty();
    }
  }, [isLoggedIn]);

  const fetchTiers = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.LOYALTY.TIERS);
      if (response.ok) {
        const data = await response.json();
        setTiers(data);
      }
    } catch (error) {
      console.error('Error fetching tiers:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchLeaderboard = async () => {
    try {
      const response = await fetch(`${API_ENDPOINTS.LOYALTY.LEADERBOARD}?limit=10`);
      if (response.ok) {
        const data = await response.json();
        setLeaderboard(data);
      }
    } catch (error) {
      console.error('Error fetching leaderboard:', error);
    }
  };

  const fetchUserLoyalty = async () => {
    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch(API_ENDPOINTS.LOYALTY.ME, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setUserLoyalty(data);
      }
    } catch (error) {
      console.error('Error fetching user loyalty:', error);
    }
  };

  const formatPoints = (points) => {
    return new Intl.NumberFormat('vi-VN').format(points || 0);
  };

  return (
    <div className="membership-page">
      <main className="sub3">
        <div className="help-center">
          <h1>THAM GIA CÂU LẠC BỘ</h1>
          <p className="subtitle">
            Nhận quyền truy cập tức thì vào các bản giới hạn, giảm giá đặc biệt và nhiều đặc quyền khác.
          </p>

          {/* Current Status (if logged in) */}
          {isLoggedIn && userLoyalty && (
            <div className="user-loyalty-status">
              <div className="loyalty-card compact">
                <div className="loyalty-main">
                  <div className="points-display">
                    <span className="points-value">{formatPoints(userLoyalty.points_balance)}</span>
                    <span className="points-label">điểm</span>
                  </div>
                  <div className="tier-info">
                    <span className="tier-badge" data-tier={userLoyalty.tier?.tier_name?.toLowerCase()}>
                      {TIER_ICONS[userLoyalty.tier?.tier_name?.toLowerCase()] || '🎖️'} {userLoyalty.tier?.tier_name || 'Bronze'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tier Cards */}
          <div className="tiers-container">
            {loading ? (
              <p>Đang tải thông tin hạng thành viên...</p>
            ) : tiers.length === 0 ? (
              // Fallback static content
              <div className="sub3__container">
                <div className="dac_quyen">
                  <h6>Ưu Đãi Độc Quyền</h6>
                  <p>Giảm giá cho các thành viên và quyền truy cập sớm vào đợt giảm giá.</p>
                </div>
                <div className="dac_quyen">
                  <h6>Sản Phẩm Giới Hạn</h6>
                  <p>Cơ hội mua các mặt hàng độc quyền và giới hạn.</p>
                </div>
                <div className="dac_quyen">
                  <h6>Miễn phí vận chuyển</h6>
                  <p>Tận hưởng giao hàng miễn phí cho tất cả các đơn hàng</p>
                </div>
              </div>
            ) : (
              tiers.filter(t => t.is_active).map(tier => (
                <div
                  key={tier.tier_id}
                  className={`tier-card ${userLoyalty?.tier_id === tier.tier_id ? 'current' : ''}`}
                >
                  <div className="tier-icon">
                    {TIER_ICONS[tier.tier_name?.toLowerCase()] || '🎖️'}
                  </div>
                  <h3>{tier.tier_name}</h3>
                  <p className="tier-points">
                    Từ {formatPoints(tier.min_points)} điểm
                  </p>
                  {parseFloat(tier.discount_percentage) > 0 && (
                    <p className="tier-discount-text">
                      🎁 Giảm {tier.discount_percentage}% mọi đơn hàng
                    </p>
                  )}
                  {tier.benefits && (
                    <div className="tier-benefits">
                      {tier.benefits}
                    </div>
                  )}
                  {userLoyalty?.tier_id === tier.tier_id && (
                    <span className="current-tier-label">✓ Hạng hiện tại</span>
                  )}
                </div>
              ))
            )}
          </div>

          {/* Leaderboard */}
          {leaderboard.length > 0 && (
            <div className="leaderboard-section">
              <h2>🏆 Bảng xếp hạng</h2>
              <table className="leaderboard-table">
                <thead>
                  <tr>
                    <th>Hạng</th>
                    <th>Thành viên</th>
                    <th>Điểm</th>
                  </tr>
                </thead>
                <tbody>
                  {leaderboard.map((user, index) => (
                    <tr key={user.user_id || index}>
                      <td className={`leaderboard-rank ${index < 3 ? `top-${index + 1}` : ''}`}>
                        {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : index + 1}
                      </td>
                      <td className="leaderboard-name">
                        {user.full_name || user.email?.split('@')[0] || `User ${user.user_id}`}
                      </td>
                      <td className="leaderboard-points">
                        {formatPoints(user.total_points || user.points_balance)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Sign up CTA for non-logged in users */}
          {!isLoggedIn && (
            <form className="form-order1">
              <div>
                <label htmlFor="email">Email</label>
                <input type="email" id="email" name="email" placeholder="email@example.com" required />
              </div>
              <button type="submit">ĐĂNG KÍ NGAY</button>
            </form>
          )}
        </div>
      </main>
    </div>
  );
};

export default HoiVien;