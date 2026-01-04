import React, { useEffect, useState } from 'react';
import orderApi from '../../../api/orderApi';
import './Orders.css';

const OrderDetailModal = ({ orderId, onClose }) => {
  const [order, setOrder] = useState(null);
  const [user, setUser] = useState(null);
  const [userAddress, setUserAddress] = useState(''); 
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [selectedStatus, setSelectedStatus] = useState('');

  const ORDER_STATUSES = [
      { value: 'PENDING', label: 'Chờ xử lý' },
      { value: 'PROCESSING', label: 'Đang xử lý' },
      { value: 'CONFIRMED', label: 'Đã xác nhận' },
      { value: 'SHIPPED', label: 'Đang giao hàng' },
      { value: 'DELIVERED', label: 'Hoàn thành' },
      { value: 'CANCELLED', label: 'Đã hủy' },
      { value: 'FAILED', label: 'Thất bại' }
  ];

  useEffect(() => {
    const fetchDetail = async () => {
      try {
        setLoading(true);
        // 1. Lấy chi tiết đơn hàng
        const res = await orderApi.getDetail(orderId);
        const orderData = res.data || res;
        setOrder(orderData);
        setSelectedStatus(orderData.order_status || orderData.status);

        // 2. Lấy địa chỉ dựa trên user_id bằng hàm getAddresses có sẵn của anh
        if (orderData.user_id) {
            try {
                // Lấy info User để hiện tên (Sử dụng hàm get trong orderApi của anh)
                const userRes = await orderApi.get(orderData.user_id);
                const userData = userRes.data || userRes;
                setUser(userData);

                //  Lấy địa chỉ bằng hàm getAddresses của anh
                const addrRes = await orderApi.getAddresses(orderData.user_id);
                const addresses = addrRes.data || addrRes;
                
                if (Array.isArray(addresses) && addresses.length > 0) {
                    // Ưu tiên địa chỉ mặc định (is_default)
                    const activeAddr = addresses.find(a => a.is_default) || addresses[0];
                    
                    // Gộp chuỗi theo cấu trúc bảng: street_address, ward, city
                    const fullAddr = `${activeAddr.street_address}${activeAddr.ward ? ', ' + activeAddr.ward : ''}, ${activeAddr.city}`;
                    setUserAddress(fullAddr);
                }
            } catch (err) {
                console.warn("Không lấy được địa chỉ từ user_id:", orderData.user_id);
            }
        }
      } catch (error) {
        alert("Lỗi tải đơn hàng: " + error.message);
        onClose();
      } finally {
        setLoading(false);
      }
    };
    if (orderId) fetchDetail();
  }, [orderId]);

  const handleSaveStatus = async () => {
    if (!selectedStatus || selectedStatus === (order.order_status || order.status)) return;
    if(!window.confirm(`Xác nhận đổi trạng thái sang "${selectedStatus}"?`)) return;

    try {
      setProcessing(true);
      await orderApi.updateStatus(orderId, selectedStatus); //
      alert(" Cập nhật thành công!");
      onClose();
    } catch (error) {
      alert(" Lỗi: " + (error.response?.data?.detail || error.message));
    } finally {
      setProcessing(false);
    }
  };

  const formatMoney = (v) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(v || 0);
  const formatDate = (d) => d ? new Date(d).toLocaleString('vi-VN') : '---';

  const getDisplayData = () => {
    if (!order) return {};
    let snap = {};
    if (order.shipping_snapshot) {
        try { snap = typeof order.shipping_snapshot === 'string' ? JSON.parse(order.shipping_snapshot) : order.shipping_snapshot; } catch(e){}
    }

    // Hiển thị địa chỉ: Ưu tiên Địa chỉ từ bảng vừa lấy -> Snapshot -> Mặc định đơn
    const finalAddress = userAddress || snap.address || snap.full_address || order.shipping_address || 'Chưa có địa chỉ';

    return {
        ...order,
        display_name: snap.full_name || (user ? `${user.last_name || ''} ${user.first_name || ''}`.trim() : 'Khách lẻ'),
        display_phone: snap.phone_number || (user ? user.phone_number : 'Trống'),
        display_address: finalAddress,
        status: order.order_status || order.status,
        subtotal: Number(order.subtotal || order.total_amount || 0),
        shipping_fee: Number(order.shipping_fee || 0),
        discount: Number(order.discount_amount || 0),
        total: Number(order.total_amount || 0)
    };
  };

  if (!order) return null;
  const data = getDisplayData();

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content order-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
            <div style={{display:'flex', alignItems:'center', gap:'10px'}}>
                <h3>Chi tiết đơn #{data.order_number || data.order_id}</h3>
                <span className={`status-badge badge-${data.status === 'CANCELLED' ? 'danger' : 'success'}`}>
                    {data.status}
                </span>
            </div>
            <button className="close-btn" onClick={onClose}>&times;</button>
        </div>

        <div className="modal-body">
            {loading ? <div className="text-center">Đang đồng bộ địa chỉ khách hàng...</div> : (
                <>
                    <div className="order-info-grid">
                        <div className="info-box">
                            <h4 style={{borderBottom:'1px solid #ddd', paddingBottom:'5px', marginBottom:'10px'}}>👤 Khách hàng</h4>
                            <p><strong>Họ tên:</strong> {data.display_name}</p>
                            <p><strong>SĐT:</strong> <span style={{color:'#0056b3', fontWeight:'bold'}}>{data.display_phone}</span></p>
                            <p><strong>User ID:</strong> {data.user_id || 'Guest'}</p>
                        </div>

                        <div className="info-box">
                            <h4 style={{borderBottom:'1px solid #ddd', paddingBottom:'5px', marginBottom:'10px'}}>📦 Đơn hàng</h4>
                            <p><strong>Ngày đặt:</strong> {formatDate(data.created_at)}</p>
                            <p><strong>Thanh toán:</strong> {data.payment_method_id === 1 ? 'COD' : 'Chuyển khoản'}</p>
                            {/*  HIỂN THỊ ĐỊA CHỈ TỪ HÀM GETADDRESSES CỦA ANH */}
                             <p><strong>Địa chỉ:</strong> {data.display_address}</p>
                        </div>
                    </div>

                    <div className="order-items-table" style={{marginTop:'20px'}}>
                        <h4 style={{marginBottom:'10px'}}>🛒 Sản phẩm</h4>
                        <table>
                            <thead>
                                <tr>
                                    <th>Tên sản phẩm</th>
                                    <th>Phân loại</th>
                                    <th className="text-right">Đơn giá</th>
                                    <th className="text-center">SL</th>
                                    <th className="text-right">Thành tiền</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.order_details?.length > 0 ? (
                                    data.order_details.map((item, idx) => (
                                        <tr key={idx}>
                                            <td>{item.product_name}</td>
                                            <td><small className="text-muted">{item.color} - {item.size}</small></td>
                                            <td className="text-right">{formatMoney(item.unit_price)}</td>
                                            <td className="text-center">x{item.quantity}</td>
                                            <td className="text-right"><strong>{formatMoney(item.total_price)}</strong></td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr><td colSpan="5" className="text-center" style={{padding:'20px', color:'#888'}}>Không có sản phẩm nào.</td></tr>
                                )}
                            </tbody>
                        </table>
                    </div>

                    <div style={{display:'flex', justifyContent:'flex-end', marginTop:'15px'}}>
                        <div style={{width:'300px', textAlign:'right'}}>
                            <p>Tạm tính: <strong>{formatMoney(data.subtotal)}</strong></p>
                            <p>Phí vận chuyển: <strong>+ {formatMoney(data.shipping_fee)}</strong></p>
                            <p>Giảm giá: <strong>- {formatMoney(data.discount)}</strong></p>
                            <hr style={{margin:'10px 0'}}/>
                            <p style={{fontSize:'18px', color:'#d00000'}}>
                                Tổng cộng: <strong>{formatMoney(data.total)}</strong>
                            </p>
                        </div>
                    </div>
                </>
            )}
        </div>

        <div className="modal-footer">
            <div style={{display:'flex', alignItems:'center', gap:'10px', flex:1}}>
                <strong>Trạng thái:</strong>
                {data.status !== 'CANCELLED' && (
                    <>
                        <select 
                            value={selectedStatus} 
                            onChange={e => setSelectedStatus(e.target.value)}
                            style={{padding:'8px', borderRadius:'4px', border:'1px solid #ccc'}}
                        >
                            {ORDER_STATUSES.map(st => <option key={st.value} value={st.value}>{st.label}</option>)}
                        </select>
                        <button className="btn-primary" onClick={handleSaveStatus} disabled={processing || selectedStatus === data.status}>
                            {processing ? 'Đang lưu...' : 'Lưu'}
                        </button>
                    </>
                )}
            </div>
            <button className="btn-secondary" onClick={onClose}>Đóng</button>
        </div>
      </div>
    </div>
  );
};

export default OrderDetailModal;