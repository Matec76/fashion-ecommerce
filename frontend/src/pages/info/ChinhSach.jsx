import React from 'react';
import '/src/style/SubPages.css';

const ChinhSach = () => {
  return (
    <div className="sub-page-container">
      {/* Header */}

      {/* 2. QUAN TRỌNG: Thêm div container bao quanh nội dung chính */}
      <main className="sub4">
        <div className="container">
        
            <h2>Chính sách Bảo mật</h2>
            
            <div className="sub4__update">
              <p>Cập nhật lần cuối: 10/15/2025</p>
              <p>
                STYLEX cam kết sẽ bảo vệ quyền riêng tư của bạn. Chính sách Bảo mật của chúng tôi 
                sẽ giải thích cách chúng tôi thu thập, sử dụng và bảo vệ thông tin của bạn khi bạn 
                truy cập vào trang web của chúng tôi.
              </p>
            </div>

            <ol className="sub4__list">
              <li>
                <h4>Thu thập thông tin</h4>
                <p>
                  Chúng tôi có thể thu thập các loại thông tin cá nhân như: Họ và Tên, Địa chỉ email, 
                  Số điện thoại, Thông tin thanh toán.
                </p>
              </li>
              <li>
                <h4>Sử dụng thông tin</h4>
                <p>
                  Thông tin chúng tôi thu thập được để: Cung cấp, vận hành và duy trì trang web của 
                  chúng tôi; Cải thiện trải nghiệm của người dùng.
                </p>
              </li>
              <li>
                 <h4>Bảo mật thông tin</h4>
                 <p>Chúng tôi thực hiện nhiều biện pháp an ninh bao gồm mã hóa và tường lửa để đảm bảo an toàn cho dữ liệu của bạn.</p>
              </li>
            </ol>

        </div>
      </main>
    </div>
  );
};

export default ChinhSach;