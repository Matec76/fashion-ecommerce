import React from 'react';
import '/src/style/SubPages.css'; 

const HoiVien = () => {
  return (
    <div className="membership-page">

      <main className="sub3">
            <div className="help-center">
                <h1>THAM GIA CÂU LẠC BỘ</h1>
                <p className="subtitle">Nhận quyền truy cập tức thì vào các bản giới hạn,giảm giá đặc biệt và nhiều đặc quyền khác.</p>
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

          <form className="form-order1">
            <div>
              <label htmlFor="email">Email</label>
              <input type="email" id="email" name="email" placeholder="email@example.com" required />
            </div>
            <button type="submit">ĐĂNG KÍ NGAY</button>
          </form>
        </div>
      </main>
    </div>
  );
};

export default HoiVien;