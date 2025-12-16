import React from 'react';
import '/src/style/SubPages.css'; 


const TheoDoi = () => {
  return (
    <div className="tracking-page">

      <main>
        <div className="sub2">
          <div className="follow-container">
            <h2>THEO DÕI ĐƠN HÀNG</h2>
            <p>Vui lòng nhập thông tin chi tiết của bạn để xem trạng thái đơn hàng.</p>
            <form className="form-order">
              <div>
                <label htmlFor="order-id">Mã đơn hàng</label>
                <input type="text" id="order-id" name="order-id" placeholder="STYLEX12345" required />
              </div>
              <div>
                <label htmlFor="email">Email đặt hàng</label>
                <input type="email" id="email" name="email" placeholder="email@example.com" required />
              </div>
              <button type="submit">XEM TRẠNG THÁI</button>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
};

export default TheoDoi;