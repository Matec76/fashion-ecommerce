document.addEventListener('DOMContentLoaded', function () {
    const modal = document.getElementById('couponModal');
    const btnAdd = document.getElementById('btnAddCoupon');
    const btnClose = document.getElementById('btnCloseModal');
    const form = document.getElementById('createCouponForm');

    // Mở Modal khi bấm nút đen
    if (btnAdd) {
        btnAdd.onclick = () => modal.style.display = 'block';
    }

    // Đóng Modal
    if (btnClose) {
        btnClose.onclick = () => modal.style.display = 'none';
    }

    // Click ra ngoài khoảng trắng cũng đóng
    window.onclick = (e) => {
        if (e.target == modal) modal.style.display = 'none';
    }

    // Xử lý gửi Form (Thêm mới)
    if (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            Swal.fire({
                title: 'Đang tạo mã...',
                text: 'Vui lòng chờ trong giây lát',
                allowOutsideClick: false,
                didOpen: () => { Swal.showLoading(); }
            });
            setTimeout(() => { form.submit(); }, 500);
        });
    }

    // Xử lý nút Xóa (Cập nhật để khớp với Blueprint)
    const deleteButtons = document.querySelectorAll('.btn-delete-coupon');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            
            // Lấy thông tin từ data-attributes đã sửa trong HTML
            const url = this.getAttribute('data-url');
            const code = this.getAttribute('data-code');

            Swal.fire({
                title: 'Xóa mã giảm giá?',
                text: `Bạn có chắc muốn xóa mã "${code}" không?`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#1e293b', 
                cancelButtonColor: '#94a3b8',
                confirmButtonText: 'Xóa ngay',
                cancelButtonText: 'Quay lại',
            }).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = url;
                }
            });
        });
    });
});