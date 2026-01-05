import React from 'react';
import '/src/style/SubPages.css';
import { Link } from 'react-router-dom';

const FOOTER_LINKS = [
  { to: '/privacy', label: 'Chính sách Bảo mật' },
  { to: '/terms', label: 'Các Điều Khoản' },
  { to: '/company', label: 'Thông tin công ty' },
];

const Footer_2 = ({ contactHotline = '+84 28 44581937' }) => {
  return (
    <footer className="site-footer1">
      <div className="container1">
        <div className="footer-grid1">
          <span>
            <i className="fa-solid fa-phone"></i> Questions? {contactHotline} |
            Thứ Hai đến Thứ Bảy: từ 9 giờ sáng đến 9 giờ tối.
          </span>
          <div className="footer-links1">
            {FOOTER_LINKS.map(({ to, label }) => (
              <Link key={to} to={to}>{label}</Link>
            ))}
          </div>
        </div>
        <div className="footer-bottom1">
          <p>&copy; 2025 STYLEX Vietnam. Mọi quyền được bảo lưu.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer_2;