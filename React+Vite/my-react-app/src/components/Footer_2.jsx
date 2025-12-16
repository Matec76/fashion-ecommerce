import React from 'react';
import '/src/style/SubPages.css';
import { Link } from 'react-router-dom'; 

const Footer_2 = () => {
    return (
        <footer className="site-footer1">
        <div className="container1">
          <div className="footer-grid1">
            <span>
              <i className="fa-solid fa-phone"></i> Questions? +84 28 44581937 | 
              Thứ Hai đến Thứ Bảy: từ 9 giờ sáng đến 9 giờ tối.
            </span>
            <div className="footer-links1">
              <Link to="/privacy">Chính sách Bảo mật</Link>
              <Link to="/terms">Các Điều Khoản</Link>
              <Link to="/company">Thông tin công ty</Link>
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