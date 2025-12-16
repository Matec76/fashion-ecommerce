import React from 'react';
import '/src/style/SubPages.css';

const CongTy = () => {
  return (
    <div className="sub-page-container">
      {/* Main Content */}
      <main className="sub4">
        <h2 style={{marginBottom:'40px'}}>Các thông tin về Công ty</h2>
        <ul className="sub4__list" style={{fontSize:'18px'}}>
          <li>
            <h4>Tên công ty: <span style={{ fontWeight: 400 }}>Công ty TNHH STYLEX Việt Nam</span></h4>
          </li>
          <li>
            <h4>Mã số doanh nghiệp: <span style={{ fontWeight: 400 }}>0123456789</span></h4>
          </li>
          <li>
            <h4>Địa chỉ: <span style={{ fontWeight: 400 }}>Tầng 10, Tòa nhà STYLEX, 123 Đường Thời Trang, Quận 1, Thành phố Hồ Chí Minh, Việt Nam</span></h4>
          </li>
          <li>
            <h4>Email: <span style={{ fontWeight: 400 }}>support@stylex.com.vn</span></h4>
          </li>
          <li>
            <h4>Điện thoại: <span style={{ fontWeight: 400 }}>+84 28 44581037</span></h4>
          </li>
        </ul>
      </main>
    </div>
  );
};

export default CongTy;