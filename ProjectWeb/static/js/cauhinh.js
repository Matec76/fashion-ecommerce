document.addEventListener('DOMContentLoaded', function () {
    // 1. Hiệu ứng thông báo khi nhấn vào các mục chưa phát triển (Thanh toán, Vận chuyển)
    const settingsCards = document.querySelectorAll('.setting-card');

    settingsCards.forEach(card => {
        card.addEventListener('click', function (e) {
            const title = this.querySelector('h3').innerText;
            
            // Nếu anh chưa viết xong giao diện cho Thanh toán hoặc Vận chuyển
            // Anh có thể dùng thông báo này để nhắc nhở
            if (this.getAttribute('href') === '#' || this.getAttribute('href').includes('thanhtoan')) {
                // e.preventDefault(); // Chặn chuyển trang nếu muốn
                // Swal.fire('Thông báo', `Tính năng ${title} đang được bảo trì`, 'info');
            }
        });
    });

    // 2. Xác nhận khi vào khu vực Phân quyền (Khu vực nhạy cảm)
    const phanQuyenLink = document.querySelector('a[href*="phanquyen"]');
    if (phanQuyenLink) {
        phanQuyenLink.addEventListener('click', function(e) {
            console.log("Truy cập khu vực quản lý nhân viên");
            // Anh có thể thêm logic kiểm tra quyền ở đây nếu cần
        });
    }
});