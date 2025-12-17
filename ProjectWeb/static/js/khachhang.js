document.addEventListener('DOMContentLoaded', function () {
    // --- 1. MODAL THÊM ---
    const modalAdd = document.getElementById('customerModal'); // ID khớp với HTML đã sửa
    const btnAdd = document.getElementById('btnAddCustomer');
    const btnCloseAdd = document.getElementById('btnCloseModal');
    const formAdd = document.getElementById('createCustomerForm');

    if (btnAdd) btnAdd.onclick = () => modalAdd.style.display = 'block';
    if (btnCloseAdd) btnCloseAdd.onclick = () => modalAdd.style.display = 'none';

    // --- 2. MODAL SỬA (Nếu anh có thêm tính năng sửa) ---
    const modalEdit = document.getElementById('editCustomerModal');
    const btnCloseEdit = document.getElementById('btnCloseEditModal');
    const formEdit = document.getElementById('editCustomerForm');
    const editButtons = document.querySelectorAll('.btn-edit');

    editButtons.forEach(btn => {
        btn.onclick = function(e) {
            e.preventDefault();
            document.getElementById('edit_id').value = this.getAttribute('data-id');
            document.getElementById('edit_ten').value = this.getAttribute('data-ten');
            document.getElementById('edit_email').value = this.getAttribute('data-email');
            document.getElementById('edit_sdt').value = this.getAttribute('data-sdt');
            if (modalEdit) modalEdit.style.display = 'block';
        };
    });

    if (btnCloseEdit) btnCloseEdit.onclick = () => modalEdit.style.display = 'none';

    // Đóng modal khi click ra ngoài
    window.onclick = (e) => {
        if (e.target == modalAdd) modalAdd.style.display = 'none';
        if (e.target == modalEdit) modalEdit.style.display = 'none';
    };

    // --- 3. HIỆU ỨNG LOADING ---
    function handleFormSubmit(form, title) {
        if (form) {
            form.addEventListener('submit', function (e) {
                e.preventDefault();
                Swal.fire({
                    title: title,
                    text: 'Hệ thống đang xử lý...',
                    allowOutsideClick: false,
                    didOpen: () => Swal.showLoading()
                });
                setTimeout(() => form.submit(), 500);
            });
        }
    }
    handleFormSubmit(formAdd, 'Đang thêm khách hàng...');
    handleFormSubmit(formEdit, 'Đang cập nhật thông tin...');

    // --- 4. XỬ LÝ XÓA (Sửa lại để nhận URL từ Blueprint) ---
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const name = this.getAttribute('data-name');
            const url = this.getAttribute('data-url'); // Lấy link từ Flask sinh ra
            
            Swal.fire({
                title: 'Xóa khách hàng?',
                text: `Dữ liệu của "${name}" sẽ bị xóa vĩnh viễn!`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#94a3b8',
                confirmButtonText: 'Xác nhận xóa',
                cancelButtonText: 'Hủy'
            }).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = url;
                }
            });
        });
    });
});