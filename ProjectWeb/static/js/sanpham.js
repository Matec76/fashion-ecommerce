document.addEventListener('DOMContentLoaded', function () {
    // --- MODAL THÊM ---
    const modalAdd = document.getElementById('productModal');
    const btnAdd = document.getElementById('btnAddProduct');
    const btnCloseAdd = document.getElementById('btnCloseModal');
    const formAdd = document.getElementById('createProductForm');

    if (btnAdd) btnAdd.addEventListener('click', () => modalAdd.style.display = 'block');
    if (btnCloseAdd) btnCloseAdd.addEventListener('click', () => modalAdd.style.display = 'none');

    // --- MODAL SỬA ---
    const modalEdit = document.getElementById('editProductModal');
    const btnCloseEdit = document.getElementById('btnCloseEditModal');
    const formEdit = document.getElementById('editProductForm');
    const editButtons = document.querySelectorAll('.btn-edit');

    editButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            document.getElementById('edit_id').value = this.getAttribute('data-id');
            document.getElementById('edit_ten').value = this.getAttribute('data-ten');
            document.getElementById('edit_sku').value = this.getAttribute('data-sku');
            document.getElementById('edit_gia').value = this.getAttribute('data-gia');
            document.getElementById('edit_ton_kho').value = this.getAttribute('data-tonkho');
            document.getElementById('edit_hinh_anh').value = this.getAttribute('data-anh');
            modalEdit.style.display = 'block';
        });
    });

    if (btnCloseEdit) btnCloseEdit.addEventListener('click', () => modalEdit.style.display = 'none');

    window.addEventListener('click', function (e) {
        if (e.target == modalAdd) modalAdd.style.display = 'none';
        if (e.target == modalEdit) modalEdit.style.display = 'none';
    });

    // --- HIỆU ỨNG LOADING ---
    function handleFormSubmit(form, title) {
        if (form) {
            form.addEventListener('submit', function (e) {
                e.preventDefault();
                Swal.fire({
                    title: title,
                    text: 'Vui lòng chờ...',
                    allowOutsideClick: false,
                    didOpen: () => Swal.showLoading()
                });
                // Submit form thực tế sau một khoảng chờ ngắn để hiện hiệu ứng
                setTimeout(() => form.submit(), 500);
            });
        }
    }
    
    handleFormSubmit(formAdd, 'Đang thêm mới...');
    handleFormSubmit(formEdit, 'Đang cập nhật...');

    // --- XỬ LÝ XÓA (Đã sửa để nhận URL chuẩn từ Flask) ---
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const productName = this.getAttribute('data-name');
            // Lấy URL từ thuộc tính data-url mà em đã thêm trong HTML
            const deleteUrl = this.getAttribute('data-url'); 

            Swal.fire({
                title: 'Xóa sản phẩm?',
                text: `Bạn có chắc chắn muốn xóa: "${productName}"?`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6',
                confirmButtonText: 'Xóa luôn!',
                cancelButtonText: 'Hủy'
            }).then((result) => {
                // Nếu nhấn xác nhận, chuyển hướng đến URL xóa đã chuẩn hóa
                if (result.isConfirmed) {
                    window.location.href = deleteUrl;
                }
            });
        });
    });
});