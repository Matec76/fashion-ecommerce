import React from 'react';
import '/src/style/SubPages.css'; 

const TrungTamHoTro = () => {
  return (
    <div className="sub-page-container">
      <main className="sub1">
        <div className="help-center">
            <h1>Trung tâm trợ giúp</h1>
            <p className="subtitle">Chúng tôi ở đây để trả lời các câu hỏi của bạn.</p>

            <div className="faq-list">
                <div class="faq-item">
                    <h3>Làm cách nào để theo dõi đơn hàng của tôi?</h3>
                    <p>Bạn có thể theo dõi đơn hàng của mình bằng cách truy cập trang "Theo dõi đơn hàng" và nhập mã đơn hàng cùng với email của bạn.</p>
                </div>
                <div class="faq-item">
                    <h3>Chính sách đổi trả là gì?</h3>
                    <p>Chúng tôi chấp nhận đổi trả trong vòng 30 ngày kể từ ngày mua hàng đối với các sản phẩm chưa qua sử dụng và còn nguyên tem mác.</p>
                </div>
                <div class="faq-item">
                    <h3>Mất bao lâu để nhận được hàng?</h3>
                    <p>Thời gian giao hàng tiêu chuẩn là 2-5 ngày làm việc, tùy thuộc vào địa điểm của bạn.</p>
                </div>
            </div>
        </div>
      </main>
    </div>
  );
};

export default TrungTamHoTro;