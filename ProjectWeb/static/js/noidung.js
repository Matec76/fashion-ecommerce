document.addEventListener('DOMContentLoaded', function () {
    const modal = document.getElementById('postModal');
    const btnAdd = document.getElementById('btnAddPost');
    const btnClose = document.getElementById('btnCloseModal');
    const form = document.getElementById('createPostForm');

    // --- ĐÓNG/MỞ MODAL ---
    if (btnAdd) btnAdd.onclick = () => modal.style.display = 'block';
    if (btnClose) btnClose.onclick = () => modal.style.display = 'none';
    
    window.onclick = (e) => { 
        if (e.target == modal) modal.style.display = 'none'; 
    }

    // --- XỬ LÝ ĐĂNG BÀI ---
    if (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            Swal.fire({ 
                title: 'Đang đăng bài...', 
                text: 'Vui lòng chờ trong giây lát',
                allowOutsideClick: false,
                didOpen: () => Swal.showLoading() 
            });
            // Giả lập delay 500ms để người dùng thấy hiệu ứng loading mượt hơn
            setTimeout(() => form.submit(), 500);
        });
    }

    // --- XỬ LÝ XÓA BÀI VIẾT ---
    // Đổi selector thành .btn-delete-post cho khớp với HTML mới
    const deleteButtons = document.querySelectorAll('.btn-delete-post');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            
            // Lấy thông tin từ data attributes
            const url = this.getAttribute('data-url');
            const postName = this.getAttribute('data-name') || "bài viết này";

            Swal.fire({
                title: 'Xóa bài viết?',
                text: `Bạn có chắc muốn xóa "${postName}"? Hành động này không thể hoàn tác.`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6',
                confirmButtonText: 'Xóa ngay',
                cancelButtonText: 'Hủy'
            }).then((result) => { 
                if (result.isConfirmed) {
                    window.location.href = url; 
                }
            });
        });
    });
});