import React, { useState, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';
import orderApi from '../../../api/orderApi';
import './Reports.css';

const Reports = () => {
  const [loading, setLoading] = useState(false);
  const [revenueData, setRevenueData] = useState([]); 
  const [statusData, setStatusData] = useState([]);   
  const [summary, setSummary] = useState({ 
    totalRevenue: 0, 
    totalOrders: 0, 
    successRate: 0 
  });
  const STATUS_COLORS = {
      'warning': '#ff9800',  // Vàng cam rực (Thay vì nâu đất) -> Nhìn như đèn giao thông
      'info':    '#00b5e2',  // Xanh Cyan sáng (Thay vì xanh két tối)
      'primary': '#0066ff',  // Xanh dương điện (Thay vì xanh than) -> Sáng trưng
      'success': '#00b300',  // Xanh lá cây chuẩn (Thay vì xanh rêu già)
      'danger':  '#ff0000',  // Đỏ cờ (Thay vì đỏ rượu) -> Đỏ chót luôn
      'default': '#555555'   // Xám vừa phải (Thay vì xám đen kịt)
  };

  const getColorByStatus = (statusName) => {
      const s = statusName.toUpperCase();
      if (s === 'CHỜ XỬ LÝ' || s === 'PENDING') return STATUS_COLORS.warning;
      if (s === 'ĐANG XỬ LÝ' || s === 'PROCESSING') return STATUS_COLORS.info;
      if (s === 'ĐANG GIAO' || s.includes('SHIPPING')) return STATUS_COLORS.primary;
      if (s === 'HOÀN THÀNH' || s.includes('DELIVERED')) return STATUS_COLORS.success;
      if (s === 'ĐÃ HỦY' || s.includes('CANCEL')) return STATUS_COLORS.danger;
      return STATUS_COLORS.default;
  };

  const fetchData = async () => {
    try {
      setLoading(true);
      const res = await orderApi.getAll({ page: 1, page_size: 1000 });
      let orders = [];
      if (Array.isArray(res)) orders = res;
      else if (res.data) orders = Array.isArray(res.data) ? res.data : (res.data.items || []);
      processData(orders);
    } catch (error) {
      console.error("Lỗi tải dữ liệu:", error);
    } finally {
      setLoading(false);
    }
  };

  const processData = (orders) => {
    // 1. TỔNG QUAN
    const totalOrders = orders.length;
    const validOrders = orders.filter(o => !['CANCELLED', 'FAILED', 'ĐÃ HỦY'].includes((o.order_status || o.status || '').toUpperCase()));
    const totalRevenue = validOrders.reduce((sum, o) => sum + Number(o.total_amount || o.subtotal || 0), 0);
    const successCount = orders.filter(o => ['DELIVERED', 'COMPLETED', 'HOÀN THÀNH'].includes((o.order_status || o.status || '').toUpperCase())).length;
    const successRate = totalOrders > 0 ? ((successCount / totalOrders) * 100).toFixed(1) : 0;

    setSummary({ totalRevenue, totalOrders, successRate });

    // 2. BIỂU ĐỒ TRÒN
    const statusCount = {};
    orders.forEach(o => {
        let st = (o.order_status || o.status || 'UNKNOWN').toUpperCase();
        // Gom nhóm tên hiển thị
        if (st === 'PENDING') st = 'Chờ xử lý';
        else if (st === 'PROCESSING') st = 'Đang xử lý';
        else if (['SHIPPED', 'SHIPPING', 'ĐANG GIAO'].includes(st)) st = 'Đang giao';
        else if (['DELIVERED', 'COMPLETED', 'HOÀN THÀNH'].includes(st)) st = 'Hoàn thành';
        else if (['CANCELLED', 'FAILED', 'ĐÃ HỦY'].includes(st)) st = 'Đã hủy';
        
        statusCount[st] = (statusCount[st] || 0) + 1;
    });

    const pieData = Object.keys(statusCount).map(key => ({ name: key, value: statusCount[key] }));
    setStatusData(pieData);

    // 3. BIỂU ĐỒ CỘT (7 ngày)
    const last7Days = [];
    for (let i = 6; i >= 0; i--) {
        const d = new Date();
        d.setDate(d.getDate() - i);
        last7Days.push(d.toISOString().split('T')[0]);
    }

    const barData = last7Days.map(dateStr => {
        const dailyRevenue = validOrders
            .filter(o => o.created_at && o.created_at.startsWith(dateStr))
            .reduce((sum, o) => sum + Number(o.total_amount || o.subtotal || 0), 0);
        const [y, m, d] = dateStr.split('-');
        return { name: `${d}/${m}`, doanhThu: dailyRevenue };
    });
    setRevenueData(barData);
  };

  useEffect(() => { fetchData(); }, []);
  const formatMoney = (a) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(a || 0);

  // Custom Label %
  const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * Math.PI / 180);
    const y = cy + radius * Math.sin(-midAngle * Math.PI / 180);
    return percent > 0 ? (
      <text x={x} y={y} fill="white" textAnchor={x > cx ? 'start' : 'end'} dominantBaseline="central" fontSize={11} fontWeight="bold">
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    ) : null;
  };

  return (
    <div className="reports-page">
      <div className="page-header">
        <h2>Báo cáo Doanh thu & Hiệu suất</h2>
        <button className={`btn-refresh-modern ${loading ? 'spinning' : ''}`} onClick={fetchData} disabled={loading}>
            <span className="icon">↻</span> {loading ? 'Đang tải...' : 'Làm mới'}
        </button>
      </div>

      {/* Đã bỏ Icon, chỉ còn số liệu sạch sẽ */}
      <div className="summary-cards">
        <div className="card-stat">
             <div className="stat-title">Doanh thu thực tế</div>
             <div className="stat-value text-primary">{formatMoney(summary.totalRevenue)}</div>
             <div className="stat-desc">Tổng giá trị đơn hàng (trừ hủy)</div>
        </div>
        <div className="card-stat">
              <div className="stat-title">Tổng đơn hàng</div>
              <div className="stat-value text-dark">{summary.totalOrders}</div>
              <div className="stat-desc">Đơn hàng trong hệ thống</div>
        </div>
        <div className="card-stat">
              <div className="stat-title">Tỷ lệ thành công</div>
              <div className="stat-value text-success">{summary.successRate}%</div>
              <div className="stat-desc">Đơn hàng đã giao thành công</div>
        </div>
      </div>

      <div className="charts-container">
        <div className="chart-box big-chart">
          <h3>Doanh thu 7 ngày qua</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={revenueData} margin={{top: 20, right: 30, left: 20, bottom: 5}}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e0e0e0" />
              <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#666'}} dy={10} />
              <YAxis axisLine={false} tickLine={false} tick={{fill: '#666'}} tickFormatter={(val) => val >= 1000000 ? `${val/1000000}M` : val} />
              <Tooltip 
                cursor={{fill: 'rgba(0,0,0,0.05)'}}
                formatter={(val) => [formatMoney(val), 'Doanh thu']}
                contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)'}}
              />
              {/* Dùng màu Primary (xanh đậm) cho cột doanh thu */}
              <Bar dataKey="doanhThu" fill="#004085" radius={[4, 4, 0, 0]} barSize={40} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-box small-chart">
          <h3>Tỷ lệ trạng thái đơn</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={statusData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={renderCustomizedLabel}
                outerRadius={100}
                dataKey="value"
              >
                {statusData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getColorByStatus(entry.name)} stroke="#fff" strokeWidth={2} />
                ))}
              </Pie>
              <Tooltip formatter={(val) => [val + ' đơn', 'Số lượng']} />
              <Legend iconType="circle" layout="horizontal" verticalAlign="bottom" align="center" wrapperStyle={{paddingTop: '20px'}}/>
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default Reports;