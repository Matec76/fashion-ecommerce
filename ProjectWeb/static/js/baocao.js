document.addEventListener('DOMContentLoaded', function () {
    
    // 1. BIỂU ĐỒ TRÒN (Trạng thái đơn hàng)
    const ctxTrangThai = document.getElementById('chartTrangThai');
    if (ctxTrangThai) {
        new Chart(ctxTrangThai, {
            type: 'doughnut',
            data: {
                labels: ['Đang xử lý', 'Đã giao thành công', 'Đã hủy'],
                datasets: [{
                    data: dataTrangThai,
                    backgroundColor: ['#f39c12', '#27ae60', '#e74c3c'],
                    borderWidth: 0,
                    hoverOffset: 10 // Hiệu ứng nổi bật khi rê chuột vào
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { 
                        position: 'bottom',
                        labels: { padding: 20, usePointStyle: true }
                    }
                }
            }
        });
    }

    // 2. BIỂU ĐỒ CỘT (Top Khách Hàng)
    const ctxKhachHang = document.getElementById('chartKhachHang');
    if (ctxKhachHang) {
        new Chart(ctxKhachHang, {
            type: 'bar',
            data: {
                labels: labelKhachHang,
                datasets: [{
                    label: 'Tổng chi tiêu',
                    data: dataKhachHang,
                    backgroundColor: '#1e293b',
                    borderRadius: 5,
                    barThickness: 35 // Giúp cột trông gọn gàng hơn
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { 
                        beginAtZero: true,
                        ticks: {
                            // Format: 1,000,000₫
                            callback: function(value) {
                                return value.toLocaleString('vi-VN') + '₫';
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) label += ': ';
                                label += context.parsed.y.toLocaleString('vi-VN') + '₫';
                                return label;
                            }
                        }
                    },
                    legend: { display: false } // Ẩn legend vì đã có label trên trục Y
                }
            }
        });
    }
});