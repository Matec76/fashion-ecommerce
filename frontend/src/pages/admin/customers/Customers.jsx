import React, { useState, useEffect } from 'react';
import userApi from '../../../api/userApi';
import orderApi from '../../../api/orderApi';
import CustomerForm from './CustomerForm';
import './Customers.css';

const Customers = () => {
  const [users, setUsers] = useState([]);
  const [filteredUsers, setFilteredUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  
  const [showModal, setShowModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);

  // Format tiền tệ
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('vi-VN', {
      style: 'currency',
      currency: 'VND'
    }).format(amount || 0);
  };

  // Tải dữ liệu
  const fetchData = async () => {
    try {
      setLoading(true);
      
      // 1. Gọi API
      const [resUsers, resOrders] = await Promise.all([
        userApi.getAll({ limit: 500, role_id: 2176, _t: Date.now() }), 
        orderApi.getAll({ limit: 1000, _t: Date.now() })
      ]);

      // 2. Lọc User (Role 2176)
      let userList = [];
      if (Array.isArray(resUsers)) userList = resUsers;
      else if (resUsers.data) userList = resUsers.data.items || resUsers.data || [];
      
      userList = userList.filter(u => parseInt(u.role_id) === 2176);

      // 3. Tính tổng tiền
      let orderList = [];
      if (Array.isArray(resOrders)) orderList = resOrders;
      else if (resOrders.data) orderList = resOrders.data.items || resOrders.data || [];

      const spendingMap = {};
      orderList.forEach(order => {
        if (order.user_id) {
          if (!spendingMap[order.user_id]) spendingMap[order.user_id] = 0;
          spendingMap[order.user_id] += parseFloat(order.total_amount || 0);
        }
      });

      // 4. Ghép data
      const finalUsers = userList.map(user => {
        const uid = user.user_id || user.id;
        return {
          ...user,
          total_spending: spendingMap[uid] || 0
        };
      });

      setUsers(finalUsers);
      setFilteredUsers(finalUsers);

    } catch (error) {
      console.error("Lỗi tải dữ liệu:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const results = users.filter(user => {
      const fullName = `${user.last_name || ''} ${user.first_name || ''}`.trim().toLowerCase();
      const email = (user.email || '').toLowerCase();
      const phone = (user.phone_number || '');
      const search = searchTerm.toLowerCase();
      return fullName.includes(search) || email.includes(search) || phone.includes(search);
    });
    setFilteredUsers(results);
  }, [searchTerm, users]);

  useEffect(() => { fetchData(); }, []);

  const handleAdd = () => {
    setSelectedUser(null);
    setShowModal(true);
  };

  const handleEdit = (user) => {
    const editData = { ...user, id: user.user_id || user.id }; 
    setSelectedUser(editData);
    setShowModal(true);
  };
  const handleDelete = async (user) => {
    const userId = user.user_id || user.id;
    const userName = `${user.last_name || ''} ${user.first_name || ''}`;
    
    if (window.confirm(`CẢNH BÁO:\nBạn có chắc chắn muốn XÓA VĨNH VIỄN khách hàng: ${userName}?`)) {
        try {
            // - Thêm tham số permanent: true để xóa cứng
            await userApi.delete(userId, { permanent: true }); 
            
            alert("Đã xóa vĩnh viễn thành công!");
            
            // Tải lại bảng dữ liệu
            fetchData(); 
        } catch (error) {
            console.error("Lỗi xóa:", error);
            alert("Lỗi: " + (error.response?.data?.detail || error.message));
        }
    }
  };

  const handleModalSuccess = () => {
    setShowModal(false);
    fetchData();
  };

  return (
    <div className="customers-page">
      <div className="page-header">
        <div className="page-title">
          <h2>Quản lý Khách hàng</h2>
          <span>Danh sách & Lịch sử chi tiêu</span>
        </div>
        
        <div className="toolbar">
          <div className="search-box">
            <span className="search-icon"></span>
            <input 
              type="text" 
              placeholder="Tìm khách hàng..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <button className="btn-add" onClick={handleAdd}>
            <span>+</span> Thêm khách
          </button>
        </div>
      </div>

      <div className="table-card">
        {loading ? (
          <div style={{padding: '40px', textAlign: 'center'}}>Đang tải dữ liệu... </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th style={{width: '30%'}}>Khách hàng</th>
                <th style={{width: '20%'}}>Liên hệ</th>
                <th style={{width: '20%', textAlign: 'right'}}>Tổng chi tiêu</th>
                <th style={{width: '15%'}}>Trạng thái</th>
                <th style={{width: '15%', textAlign:'right'}}>Hành động</th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.length > 0 ? (
                filteredUsers.map(user => {
                  let displayName = `${user.last_name || ''} ${user.first_name || ''}`.trim();
                  if (!displayName) displayName = user.email ? user.email.split('@')[0] : 'No Name';
                  const uniqueKey = user.user_id || user.id || Math.random();

                  return (
                    <tr key={uniqueKey}>
                      <td>
                        <div className="user-info">
                          <div className="user-avatar-placeholder">
                             {displayName.charAt(0).toUpperCase()}
                          </div>
                          <div className="user-details">
                            <div style={{fontWeight: '600', color: '#2b2d42'}}>
                              {displayName}
                            </div>
                            <div style={{fontSize: '13px', color: '#8d99ae'}}>
                              {user.email}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td>
                        {user.phone_number || <span style={{color:'#ccc'}}>--</span>}
                      </td>
                      <td style={{textAlign: 'right'}}>
                        <div style={{fontWeight: '700', color: '#2a9d8f'}}>
                          {formatCurrency(user.total_spending)}
                        </div>
                      </td>
                      <td>
                        <span className={`status-badge ${user.is_active ? 'status-active' : 'status-blocked'}`}>
                          {user.is_active ? 'Active' : 'Locked'}
                        </span>
                      </td>
                      <td style={{textAlign:'right'}}>
                        <div className="action-buttons" style={{justifyContent: 'flex-end', gap: '8px'}}>
                          <button 
                            className="btn-icon btn-edit" 
                            title="Sửa thông tin"
                            onClick={() => handleEdit(user)}
                          >
                            ✏️
                          </button>
                          <button 
                            className="btn-icon btn-delete" 
                            title="Xóa khách hàng"
                            onClick={() => handleDelete(user)}
                          >
                            🗑️
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan="5" style={{textAlign:'center', padding:'40px', color:'#888'}}>
                    Không tìm thấy khách hàng nào (Role 2176)!
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {showModal && (
        <CustomerForm 
          onClose={() => setShowModal(false)}
          initialData={selectedUser}
          onSuccess={handleModalSuccess}
        />
      )}
    </div>
  );
};

export default Customers;