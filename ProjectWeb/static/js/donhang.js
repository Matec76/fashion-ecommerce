document.addEventListener('DOMContentLoaded', function () {
    // --- XỬ LÝ MODAL TẠO ĐƠN ---
    const modal = document.getElementById('orderModal');
    const btnAdd = document.getElementById('btnAddOrder');
    const btnClose = document.getElementById('btnCloseOrder');
    const form = document.getElementById('createOrderForm');

    if (btnAdd) btnAdd.onclick = () => modal.style.display = 'block';
    if (btnClose) btnClose.onclick = () => modal.style.display = 'none';

    window.onclick = (e) => {
        if (e.target == modal) modal.style.display = 'none';
    };

    // Xử lý gửi Form (Thêm hiệu ứng Loading)
    if (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            Swal.fire({
                title: 'Đang lưu đơn hàng...',
                text: 'Hệ thống đang xử lý, vui lòng đợi.',
                allowOutsideClick: false,
                didOpen: () => Swal.showLoading()
            });
            setTimeout(() => form.submit(), 500);
        });
    }

    // --- XỬ LÝ NÚT XÓA ĐƠN HÀNG ---
    const deleteButtons = document.querySelectorAll('.btn-delete-order');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            
            // Lấy URL an toàn từ data-url thay vì href
            const deleteUrl = this.getAttribute('data-url');
            const maDon = this.getAttribute('data-ma') || "đơn hàng này";

            Swal.fire({
                title: `Xóa đơn hàng ${maDon}?`,
                text: "Dữ liệu đơn hàng sẽ bị mất và không thể khôi phục!",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#94a3b8',
                confirmButtonText: 'Xác nhận xóa',
                cancelButtonText: 'Quay lại'
            }).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = deleteUrl;
                }
            });
        });
    });

    // --- XỬ LÝ CẬP NHẬT TRẠNG THÁI (GIAO/HỦY) ---
    // Anh có thể thêm SweetAlert confirm cho các nút "Giao" và "Hủy" 
    // để tránh bấm nhầm làm thay đổi doanh thu khách hàng.
    const actionLinks = document.querySelectorAll('.action-link');
    actionLinks.forEach(link => {
        if (link.classList.contains('btn-delete-order')) return; // Bỏ qua nút xóa

        link.addEventListener('click', function(e) {
            const actionText = this.innerText.includes('Giao') ? 'hoàn tất giao' : 'hủy';
            const color = this.innerText.includes('Giao') ? '#27ae60' : '#e74c3c';
            
            e.preventDefault();
            const url = this.getAttribute('href');

            Swal.fire({
                title: 'Xác nhận thay đổi?',
                text: `Bạn có chắc muốn ${actionText} đơn hàng này không?`,
                icon: 'question',
                showCancelButton: true,
                confirmButtonColor: color,
                confirmButtonText: 'Đồng ý',
                cancelButtonText: 'Hủy'
            }).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = url;
                }
            });
        });
    });
});