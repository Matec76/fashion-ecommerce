document.addEventListener('DOMContentLoaded', function () {
    const ctx = document.getElementById('bieuDoDoanhThu');

    if (ctx) {
        // Biểu đồ Doanh thu (Line Chart)
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartLabels, // Lấy từ biến Python
                datasets: [{
                    label: 'Doanh thu (Triệu VNĐ)',
                    data: chartData, // Lấy từ biến Python
                    borderColor: '#0f1b2c',
                    backgroundColor: 'rgba(15, 27, 44, 0.1)',
                    borderWidth: 2,
                    tension: 0.4, // Đường cong mềm mại
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { borderDash: [5, 5] }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    }
});