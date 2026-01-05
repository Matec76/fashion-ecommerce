import React from 'react';
import { Link } from 'react-router-dom';
import '/src/style/SubPages.css';

const DieuKhoan = () => {
  return (
    <div className="sub-page-container">
      {/* Main Content */}
      <main className="sub4">
            <h2>Các Điều kiện & Điều khoản</h2>
            <div className="sub4__update">
                <p>Chào mừng bạn đến với STYLEX! Các điều khoản và điều kiện này nêu ra các quy tắc và quy định cho việc sử dụng Trang web của STYLEX.</p>
                <p>Bằng cách truy cập trang web này, chúng tôi cho rằng bạn chấp nhận các điều khoản và điều kiện này. Đừng tiếp tục sử dụng STYLEX nếu bạn không đồng ý với tất cả các điều khoản và điều kiện được nêu trên trang này.</p>
            </div>

            <ol className="sub4__list">
                <li>
                    <h4>Giấy phép</h4>
                    <p>Trừ khi có quy định khác, STYLEX và/hoặc người cấp phép của nó sở hữu quyền sở hữu trí tuệ đối với tất cả tài liệu trên STYLEX.</p>
                </li>
                
            </ol>
        </main>
    </div>
  );
};

export default DieuKhoan;