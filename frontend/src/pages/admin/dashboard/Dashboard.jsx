import React, { useState, useEffect } from 'react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer 
} from 'recharts';
import analyticsApi from '../../../api/analyticsApi';
import orderApi from '../../../api/orderApi'; //  Chuyển sang dùng orderApi để tính toán chuẩn
import './Dashboard.css';

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  
  // State bộ lọc thời gian: 'today' | '7days' | '30days'
  const [timeRange, setTimeRange] = useState('7days'); 

  const [stats, setStats] = useState({
    period_revenue: 0, revenue_growth: 0, all_time_revenue: 0,
    period_orders: 0, orders_growth: 0, pending_orders: 0,
    total_customers: 0, low_stock_products: 0
  });

  const [chartData, setChartData] = useState([]); 
  const [recentProducts, setRecentProducts] = useState([]);

  // --- HÀM LẤY DỮ LIỆU ---
  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // 1. Gọi API lấy dữ liệu
      const [resOrders, resProducts, resStats] = await Promise.all([
        orderApi.getAll({ page: 1, page_size: 1000 }), // Lấy 1000 đơn mới nhất
        analyticsApi.getMostViewedProducts({ limit: 5 }),
        analyticsApi.getDashboardStats() // Lấy số liệu tổng quan (tồn kho, khách hàng...)
      ]);

      // 2. Xử lý danh sách đơn hàng
      let orders = [];
      if (Array.isArray(resOrders)) orders = resOrders;
      else if (resOrders?.data) orders = Array.isArray(resOrders.data) ? resOrders.data : (resOrders.data.items || []);

      // Lọc đơn hợp lệ (không hủy)
      const validOrders = orders.filter(o => !['CANCELLED', 'FAILED', 'ĐÃ HỦY'].includes((o.order_status || o.status || '').toUpperCase()));

      // 3. Tính toán dữ liệu theo TimeRange
      processDataByTimeRange(validOrders, timeRange, resStats?.data || resStats);

      // 4. Xử lý List sản phẩm xem nhiều
      const prodList = Array.isArray(resProducts) ? resProducts : (resProducts.data || []);
      setRecentProducts(prodList);

    } catch (error) {
      console.error(" Lỗi tải Dashboard:", error);
    } finally {
      setLoading(false);
    }
  };

  // --- HÀM TÍNH TOÁN LOGIC (CORE) ---
  const processDataByTimeRange = (orders, range, backendStats) => {
    const now = new Date();
    let startDate = new Date();
    let dateFormat = 'DD/MM'; // Định dạng hiển thị trục hoành

    // Xác định ngày bắt đầu
    if (range === 'today') {
        startDate.setHours(0,0,0,0);
        dateFormat = 'HH:mm'; // Hôm nay thì hiện giờ
    } else if (range === '7days') {
        startDate.setDate(now.getDate() - 6);
    } else if (range === '30days') {
        startDate.setDate(now.getDate() - 29);
    }

    // 1. Lọc đơn hàng trong kỳ (Period)
    const periodOrders = orders.filter(o => new Date(o.created_at) >= startDate);
    
    // 2. Tính tổng doanh thu & số đơn kỳ này
    const periodRevenue = periodOrders.reduce((sum, o) => sum + Number(o.total_amount || o.subtotal || 0), 0);
    const periodOrderCount = periodOrders.length;

    // 3. Tính tổng doanh thu toàn thời gian (All Time)
    const allTimeRevenue = orders.reduce((sum, o) => sum + Number(o.total_amount || o.subtotal || 0), 0);
    const pendingCount = orders.filter(o => ['PENDING', 'CHỜ XỬ LÝ'].includes((o.order_status || o.status || '').toUpperCase())).length;

    // 4. Cập nhật State thống kê
    setStats({
        period_revenue: periodRevenue,
        revenue_growth: 0, // Cái này cần dữ liệu cũ để so sánh, tạm để 0
        all_time_revenue: allTimeRevenue,
        period_orders: periodOrderCount,
        orders_growth: 0,
        pending_orders: pendingCount,
        total_customers: Number(backendStats?.total_customers || 0), // Lấy từ API Dashboard
        low_stock_products: Number(backendStats?.low_stock_products || 0)
    });

    // 5. TẠO DỮ LIỆU BIỂU ĐỒ (Chart Data)
    // Tạo khung dữ liệu rỗng cho đủ các ngày/giờ trong range
    const chartMap = {};
    
    if (range === 'today') {
        // Nếu là 'today': Tạo các mốc giờ (0h -> 23h)
        for (let i = 0; i < 24; i++) {
            chartMap[`${i}:00`] = 0;
        }
        // Fill dữ liệu
        periodOrders.forEach(o => {
            const d = new Date(o.created_at);
            const hourKey = `${d.getHours()}:00`;
            chartMap[hourKey] = (chartMap[hourKey] || 0) + Number(o.total_amount || 0);
        });
    } else {
        // Nếu là 7 ngày hoặc 30 ngày: Tạo các mốc ngày
        const days = range === '7days' ? 7 : 30;
        for (let i = days - 1; i >= 0; i--) {
            const d = new Date();
            d.setDate(d.getDate() - i);
            const key = d.toISOString().split('T')[0]; // YYYY-MM-DD
            chartMap[key] = 0;
        }
        // Fill dữ liệu
        periodOrders.forEach(o => {
            const key = o.created_at.split('T')[0]; // YYYY-MM-DD
            if (chartMap[key] !== undefined) {
                chartMap[key] += Number(o.total_amount || 0);
            }
        });
    }

    // Chuyển object thành array cho Recharts
    const finalChartData = Object.keys(chartMap).map(key => {
        let label = key;
        // Format lại label ngày tháng cho đẹp (2025-12-30 -> 30/12)
        if (key.includes('-')) {
            const [y, m, d] = key.split('-');
            label = `${d}/${m}`;
        }
        return {
            name: label,
            revenue: chartMap[key]
        };
    });

    setChartData(finalChartData);
  };

  // Khi timeRange thay đổi -> Gọi lại API (hoặc chỉ cần tính lại nếu đã có data, nhưng gọi lại cho chắc)
  useEffect(() => {
    fetchDashboardData();
  }, [timeRange]);

  const formatMoney = (amount) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(amount);

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <h2>Dashboard Tổng quan</h2>
        
        <div className="header-actions">
            <div className="time-filter">
                <button className={timeRange === 'today' ? 'active' : ''} onClick={() => setTimeRange('today')}>Hôm nay</button>
                <button className={timeRange === '7days' ? 'active' : ''} onClick={() => setTimeRange('7days')}>7 ngày</button>
                <button className={timeRange === '30days' ? 'active' : ''} onClick={() => setTimeRange('30days')}>30 ngày</button>
            </div>
            
            <button className="btn-refresh" onClick={fetchDashboardData} title="Tải lại dữ liệu">🔄</button>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card blue-card">
          <div className="stat-header">
            <span>Doanh Thu ({timeRange === 'today' ? 'Hôm nay' : 'Kỳ này'})</span>
            <span className="icon-box blue-icon">$</span>
          </div>
          <div className="stat-number">{loading ? '...' : formatMoney(stats.period_revenue)}</div>
          <div className="stat-footer">Tổng tích lũy: {formatMoney(stats.all_time_revenue)}</div>
        </div>

        <div className="stat-card purple-card">
          <div className="stat-header">
            <span>Đơn Hàng ({timeRange === 'today' ? 'Hôm nay' : 'Kỳ này'})</span>
            <span className="icon-box purple-icon"></span>
          </div>
          <div className="stat-number">{loading ? '...' : stats.period_orders}</div>
          <div className="stat-footer status-highlight">Chờ xử lý: <strong>{stats.pending_orders}</strong></div>
        </div>

        <div className="stat-card green-card">
          <div className="stat-header">
            <span>Tổng Khách Hàng</span>
            <span className="icon-box green-icon"></span>
          </div>
          <div className="stat-number">{loading ? '...' : stats.total_customers}</div>
          <div className="stat-desc">Khách hàng toàn hệ thống</div>
        </div>

        <div className="stat-card red-card">
          <div className="stat-header">
            <span>Cảnh Báo Tồn Kho</span>
            <span className="icon-box red-icon"></span>
          </div>
          <div className="stat-number text-red">{loading ? '...' : stats.low_stock_products}</div>
          <div className="stat-footer link-red">Nhập hàng ngay →</div>
        </div>
      </div>

      <div className="main-content-grid">
        <div className="chart-section">
          <div className="chart-header">
            <h3>Biểu đồ doanh thu</h3>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={350}>
              <AreaChart data={chartData} margin={{ top: 10, right: 0, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#4361ee" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#4361ee" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#888', fontSize: 12}} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{fill: '#888', fontSize: 12}} tickFormatter={(val) => val >= 1000000 ? `${val/1000000}M` : val} />
                <Tooltip 
                    formatter={(value) => [formatMoney(value), 'Doanh thu']}
                    contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)'}}
                />
                <Area type="monotone" dataKey="revenue" stroke="#4361ee" strokeWidth={2} fillOpacity={1} fill="url(#colorRevenue)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="recent-section">
          <div className="recent-header">
            <h3>Top xem nhiều</h3>
            <span>{timeRange === 'today' ? 'Hôm nay' : 'Trong kỳ này'}</span>
          </div>
          <div className="recent-list">
            {recentProducts.map(prod => (
              <div key={prod.product_id} className="recent-item">
                <div className="prod-img">
                   <img src={prod.thumbnail || prod.image || 'https://via.placeholder.com/50'} alt="" />
                </div>
                <div className="prod-info">
                  <div className="prod-name">{prod.product_name}</div>
                  <div className="prod-time">Lượt xem: {prod.view_count || 0}</div>
                </div>
                <div className="prod-price">{formatMoney(prod.base_price || 0)}</div>
              </div>
            ))}
            {recentProducts.length === 0 && <p style={{color:'#999', textAlign:'center', marginTop: 20}}>Chưa có dữ liệu</p>}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;