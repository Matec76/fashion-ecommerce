import React, { useEffect, useState } from 'react';
import orderApi from '../../../api/orderApi';
import userApi from '../../../api/userApi';
import OrderDetailModal from './OrderDetailModal';
import './Orders.css';

const Orders = () => {
  const [orders, setOrders] = useState([]);
  const [users, setUsers] = useState([]); 
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedOrderId, setSelectedOrderId] = useState(null);

  // --- HÀM TẢI DỮ LIỆU ---
  const fetchData = async () => {
    try {
      setLoading(true);
      
      const [resOrders, resUsers] = await Promise.all([
        orderApi.getAll({ page: 1, page_size: 100, status: statusFilter || undefined, search: searchTerm || undefined }),
        userApi.getAll({ page: 1, page_size: 1000 }) // Lấy 1000 user để tra cứu
      ]);

      // 1. Xử lý List Đơn hàng (Tìm mọi ngóc ngách để lấy mảng)
      let orderList = [];
      if (Array.isArray(resOrders)) orderList = resOrders;
      else if (resOrders?.data) orderList = Array.isArray(resOrders.data) ? resOrders.data : (resOrders.data.items || []);
      
      // 2. Xử lý List User (Quan trọng: Log ra để kiểm tra)
      console.log(" API Users trả về:", resUsers); // Soi log này nếu vẫn lỗi
      
      let userList = [];
      if (Array.isArray(resUsers)) userList = resUsers;
      else if (Array.isArray(resUsers?.data)) userList = resUsers.data; // Trường hợp data: [...]
      else if (Array.isArray(resUsers?.data?.items)) userList = resUsers.data.items; // Trường hợp data: { items: [...] }
      else if (Array.isArray(resUsers?.items)) userList = resUsers.items; // Trường hợp items: [...]

      console.log(` Đã tải được ${userList.length} user để ghép tên.`);
      
      setOrders(orderList);
      setUsers(userList);

    } catch (error) {
      console.error(" Lỗi tải dữ liệu:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => fetchData(), 500);
    return () => clearTimeout(timer);
  }, [statusFilter, searchTerm]);

  // --- HÀM TRA CỨU TÊN KHÁCH (UPDATE V3: Chấp hết các loại ID) ---
  const getCustomerInfo = (order) => {
    // 1. Nếu có Snapshot lịch sử thì lấy luôn (Dù trong ảnh đại ca gửi đang NULL, nhưng cứ để phòng hờ)
    if (order.shipping_snapshot) {
        let snap = order.shipping_snapshot;
        if (typeof snap === 'string') { try { snap = JSON.parse(snap); } catch(e) {} }
        const snapName = snap.full_name || snap.name || snap.shipping_name;
        if (snapName) return { name: snapName, phone: snap.phone_number || snap.phone };
    }

    // 2. Tra cứu từ danh sách Users
    if (order.user_id && users.length > 0) {
        //  QUAN TRỌNG: Tìm theo cả 'user_id' VÀ 'id' (phòng trường hợp API đổi tên biến)
        const user = users.find(u => {
            const uId = u.user_id || u.id; // Lấy ID của user trong list
            return String(uId) === String(order.user_id); // Ép kiểu String để so sánh
        });

        if (user) {
            const firstName = user.first_name || '';
            const lastName = user.last_name || '';
            const fullName = `${lastName} ${firstName}`.trim();
            
            return { 
                name: fullName || user.email || user.username || 'Không tên', 
                phone: user.phone_number 
            };
        }
    }

    // 3. Fallback cuối cùng
    return { name: fullName, phone: order.shipping_phone || order.phone_number };
  };

  const formatMoney = (a) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(a || 0);
  const formatDate = (d) => d ? new Date(d).toLocaleDateString('vi-VN', {day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit'}) : '-';

  const getStatusBadge = (status) => {
      const s = status ? String(status).toUpperCase() : '';
      let cls = 'badge-default';
      if (['PENDING', 'CHỜ XỬ LÝ', 'PROCESSING'].includes(s)) cls = 'badge-warning';
      else if (['CONFIRMED', 'ĐÃ XÁC NHẬN'].includes(s)) cls = 'badge-info';
      else if (['SHIPPING', 'SHIPPED', 'ĐANG GIAO'].includes(s)) cls = 'badge-primary';
      else if (['COMPLETED', 'HOÀN THÀNH', 'DELIVERED', 'PAID'].includes(s)) cls = 'badge-success';
      else if (['CANCELLED', 'ĐÃ HỦY', 'FAILED'].includes(s)) cls = 'badge-danger';
      return <span className={`status-badge ${cls}`}>{status || 'Mới'}</span>;
  };

  return (
    <div className="orders-page">
      <div className="page-header">
        <h2>Quản lý Đơn hàng</h2>
        <div className="toolbar">
             {/* Giữ nguyên phần lọc như cũ */}
             <button className="btn-reload" onClick={fetchData} style={{marginRight:'10px', cursor:'pointer'}}>🔄 Tải lại</button>
        </div>
      </div>

      <div className="table-container">
        <table>
            <thead>
                <tr>
                    <th>Mã đơn</th>
                    <th>Ngày đặt</th>
                    <th>Khách hàng</th>
                    <th>Tổng tiền</th>
                    <th>Trạng thái</th>
                    <th className="text-right">Hành động</th>
                </tr>
            </thead>
            <tbody>
                {loading ? (
                   <tr><td colSpan="6" className="text-center">⏳ Đang tải dữ liệu...</td></tr>
                ) : (orders && orders.length > 0) ? (
                   orders.map((order, index) => {
                        const orderId = order.order_number || order.order_id || `ID-${index}`;
                        
                        //  GỌI HÀM TRA CỨU MỚI
                        const customer = getCustomerInfo(order);

                        return (
                            <tr key={order.order_id || index}>
                                <td><b>#{orderId}</b></td>
                                <td>{formatDate(order.created_at)}</td>
                                <td>
                                    <div className="customer-info">
                                        {/* Tên Khách Hàng (Màu đậm) */}
                                        <span style={{fontWeight:'bold', color:'#2b2d42', fontSize:'14px'}}>
                                            {customer.name}
                                        </span>
                                        {/* Email hoặc SĐT (Màu nhạt) */}
                                        <small style={{display:'block', color:'#888', marginTop:'2px'}}>
                                            {customer.phone || (order.user_id ? `ID: ${order.user_id}` : '')}
                                        </small>
                                    </div>
                                </td>
                                <td style={{color:'#d00000', fontWeight:'bold'}}>
                                    {formatMoney(order.total_amount || order.subtotal)}
                                </td>
                                <td>{getStatusBadge(order.order_status || order.status)}</td>
                                <td className="text-right">
                                    <button className="btn-view" onClick={() => setSelectedOrderId(order.order_id)}>Xem chi tiết</button>
                                </td>
                            </tr>
                        );
                   })
                ) : (
                   <tr><td colSpan="6" className="text-center">📭 Không có dữ liệu.</td></tr>
                )}
            </tbody>
        </table>
      </div>

      {selectedOrderId && (
        <OrderDetailModal orderId={selectedOrderId} onClose={() => { setSelectedOrderId(null); fetchData(); }} />
      )}
    </div>
  );
};

export default Orders;