import React, { useEffect, useState } from 'react';
import orderApi from '../../../api/orderApi';
import userApi from '../../../api/userApi';
import OrderDetailModal from './OrderDetailModal';
import ReturnRequestsModal from './ReturnRequestsModal'; 
import './Orders.css';

const Orders = () => {
  const [orders, setOrders] = useState([]);
  const [users, setUsers] = useState([]); 
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  
  // State Modal
  const [selectedOrderId, setSelectedOrderId] = useState(null);
  const [showReturnModal, setShowReturnModal] = useState(false);
  const [pendingReturnCount, setPendingReturnCount] = useState(0); 

  // --- HÀM TẢI DỮ LIỆU ---
  const fetchData = async () => {
    try {
      setLoading(true);
      // Gọi song song các API cần thiết
      const [resOrders, resUsers, resCount] = await Promise.all([
        orderApi.getAll({ page: 1, page_size: 100, status: statusFilter || undefined, search: searchTerm || undefined, _t: Date.now() }),
        userApi.getAll({ page: 1, page_size: 1000 }),
        orderApi.getPendingReturnCount().catch(() => ({ count: 0 }))
      ]);

      // Xử lý list Orders
      let orderList = [];
      if (Array.isArray(resOrders)) orderList = resOrders;
      else if (resOrders?.data) orderList = Array.isArray(resOrders.data) ? resOrders.data : (resOrders.data.items || []);
      
      // Xử lý list Users
      let userList = [];
      if (Array.isArray(resUsers)) userList = resUsers;
      else if (resUsers?.data) userList = Array.isArray(resUsers.data) ? resUsers.data : (resUsers.data.items || []);

      setOrders(orderList);
      setUsers(userList);
      
      // Cập nhật số lượng pending returns
      const count = (typeof resCount === 'number') ? resCount : (resCount?.count || 0);
      setPendingReturnCount(count);

    } catch (error) {
      console.error("Lỗi tải dữ liệu:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => fetchData(), 500);
    return () => clearTimeout(timer);
  }, [statusFilter, searchTerm]);

  // --- HÀM TÌM TÊN KHÁCH (Giữ nguyên) ---
  const getCustomerInfo = (order) => {
    if (order.shipping_snapshot) {
        let snap = order.shipping_snapshot;
        if (typeof snap === 'string') { try { snap = JSON.parse(snap); } catch(e) {} }
        const snapName = snap.full_name || snap.name || snap.shipping_name;
        if (snapName) return { name: snapName, phone: snap.phone_number || snap.phone };
    }
    if (order.user_id && users.length > 0) {
        const user = users.find(u => String(u.user_id || u.id) === String(order.user_id));
        if (user) {
            const fullName = `${user.last_name || ''} ${user.first_name || ''}`.trim();
            return { name: fullName || user.email || `User #${user.user_id}`, phone: user.phone_number };
        }
    }
    return { name: 'Khách lẻ', phone: order.shipping_phone || order.phone_number };
  };

  const getStatusBadge = (statusRaw) => { /* Giữ nguyên hàm cũ */ 
      const s = statusRaw ? String(statusRaw).toUpperCase() : '';
      let cls = 'badge-default';
      if (['PENDING'].includes(s)) cls = 'badge-warning';
      else if (['CONFIRMED'].includes(s)) cls = 'badge-info';
      else if (['SHIPPING', 'SHIPPED'].includes(s)) cls = 'badge-primary';
      else if (['COMPLETED', 'DELIVERED'].includes(s)) cls = 'badge-success';
      else if (['CANCELLED'].includes(s)) cls = 'badge-danger';
      return <span className={`status-badge ${cls}`}>{s}</span>;
  };
  const formatMoney = (a) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(a || 0);
  const formatDate = (d) => d ? new Date(d).toLocaleDateString('vi-VN', {day:'2-digit', month:'2-digit'}) : '-';

  return (
    <div className="orders-page">
      <div className="page-header">
        <h2>Quản lý Đơn hàng</h2>
        <div className="toolbar" style={{display:'flex', gap:'10px', alignItems:'center'}}>
             
             {/*  NÚT MỚI: QUẢN LÝ HOÀN TIỀN */}
             <button 
                className="btn-return-request"
                onClick={() => setShowReturnModal(true)}
                style={{
                    background: '#f97316', color: 'white', border: 'none', 
                    padding: '8px 15px', borderRadius: '6px', cursor: 'pointer',
                    fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '8px'
                }}
             >
                 Yêu cầu Trả hàng
                {pendingReturnCount > 0 && (
                    <span style={{background:'white', color:'#f97316', padding:'2px 6px', borderRadius:'10px', fontSize:'11px'}}>
                        {pendingReturnCount}
                    </span>
                )}
             </button>

             <div style={{height:'30px', width:'1px', background:'#ddd', margin:'0 5px'}}></div>

             <button className="btn-reload" onClick={fetchData} style={{cursor:'pointer', border:'1px solid #ddd', background:'white', padding:'8px', borderRadius:'6px'}}>🔄</button>
        </div>
      </div>
      <div className="table-container">
        <table>
            <thead>
                <tr><th>Mã đơn</th><th>Ngày đặt</th><th>Khách hàng</th><th>Tổng tiền</th><th>Trạng thái</th><th className="text-right">Hành động</th></tr>
            </thead>
            <tbody>
                {loading ? (<tr><td colSpan="6" className="text-center"> Đang tải...</td></tr>) : 
                 (orders && orders.length > 0) ? orders.map((order, index) => {
                        const customer = getCustomerInfo(order);
                        return (
                            <tr key={order.order_id || index}>
                                <td><b>#{order.order_id}</b></td>
                                <td>{formatDate(order.created_at)}</td>
                                <td>
                                    <div className="customer-info">
                                        <span style={{fontWeight:'bold', color:'#2b2d42', fontSize:'14px'}}>{customer.name}</span>
                                        <small style={{display:'block', color:'#888', marginTop:'2px'}}>{customer.phone}</small>
                                    </div>
                                </td>
                                <td style={{color:'#d00000', fontWeight:'bold'}}>{formatMoney(order.total_amount)}</td>
                                <td>{getStatusBadge(order.order_status || order.status)}</td>
                                <td className="text-right">
                                    <button className="btn-view" onClick={() => setSelectedOrderId(order.order_id)}>Xem</button>
                                </td>
                            </tr>
                        );
                    }) : (<tr><td colSpan="6" className="text-center">📭 Không có dữ liệu.</td></tr>)
                }
            </tbody>
        </table>
      </div>

      {/* CÁC MODAL */}
      {selectedOrderId && <OrderDetailModal orderId={selectedOrderId} onClose={() => { setSelectedOrderId(null); fetchData(); }} />}
      
      {/*  MODAL HOÀN TIỀN VỪA THÊM */}
      {showReturnModal && <ReturnRequestsModal onClose={() => setShowReturnModal(false)} />}
    </div>
  );
};

export default Orders;