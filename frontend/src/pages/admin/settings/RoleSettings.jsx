import React, { useState, useEffect } from 'react';
import systemApi from '../../../api/systemApi';
import './RoleSettings.css';

const RoleSettings = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [currentId, setCurrentId] = useState(null);

  const ROLE_CONFIG = {
    1: { label: 'SUPER USER', class: 'badge-super-user' },
    2: { label: 'ADMIN', class: 'badge-admin' },
    3: { label: 'NHÂN VIÊN KHO', class: 'badge-warehouse' },
    4: { label: 'MARKETING', class: 'badge-marketing' },
    5: { label: 'CSKH', class: 'badge-cskh' }
  };

  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    phone_number: '',
    gender: 'MALE',
    date_of_birth: '',
    role_id: 2,
    is_active: true
  });

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const res = await systemApi.getUsers();
      const allUsers = Array.isArray(res) ? res : (res.data || []);
      const staffs = allUsers.filter(u => u.role_id >= 1 && u.role_id <= 5);
      setUsers(staffs);
    } catch (error) {
      console.error("Lỗi tải người dùng:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchUsers(); }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (isEditing) {
        const updateData = { 
            first_name: formData.first_name,
            last_name: formData.last_name,
            phone_number: formData.phone_number,
            gender: formData.gender,
            date_of_birth: formData.date_of_birth,
            role_id: Number(formData.role_id), 
            is_active: formData.is_active ? 1 : 0 
        };
        await systemApi.updateUserRole(currentId, updateData);
        alert(" Cập nhật nhân viên thành công!");
      } else {
        const newUserPayload = {
            email: formData.email,
            password: formData.password,
            first_name: formData.first_name,
            last_name: formData.last_name,
            phone_number: formData.phone_number,
            gender: formData.gender,
            date_of_birth: formData.date_of_birth || null,
            role_id: Number(formData.role_id),
            is_active: 1,
            is_superuser: Number(formData.role_id) === 1 ? 1 : 0,
            is_email_verified: 1
        };

        await systemApi.create(newUserPayload);
        alert(" Thêm nhân viên mới thành công!");
      }
      setShowModal(false);
      fetchUsers();
    } catch (error) {
      const msg = error.response?.data?.detail;
      alert(" Lỗi: " + (typeof msg === 'object' ? JSON.stringify(msg) : (msg || "Thao tác thất bại")));
    }
  };

  const openEditModal = (user) => {
    setIsEditing(true);
    setCurrentId(user.user_id || user.id);
    setFormData({
      first_name: user.first_name || '',
      last_name: user.last_name || '',
      email: user.email,
      phone_number: user.phone_number || '',
      gender: user.gender || 'MALE',
      date_of_birth: user.date_of_birth ? user.date_of_birth.split('T')[0] : '',
      role_id: user.role_id,
      is_active: Number(user.is_active) === 1
    });
    setShowModal(true);
  };

  return (
    <div className="settings-card">
      <div className="card-header" style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
        <div>
          <h3>Quản lý Quyền nhân viên</h3>
          <p className="text-muted">Danh sách tài khoản quản trị hệ thống.</p>
        </div>
        <button className="btn-primary" onClick={() => { 
          setIsEditing(false); 
          setFormData({ first_name:'', last_name:'', email:'', password:'', phone_number:'', gender:'MALE', date_of_birth:'', role_id: 2, is_active: true });
          setShowModal(true); 
        }}>+ Thêm nhân viên</button>
      </div>

      <div className="card-body">
        {loading ? <p>⏳ Đang đồng bộ...</p> : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Họ và tên</th>
                <th>Liên hệ</th>
                <th>Chức vụ</th>
                <th>Trạng thái</th>
                <th style={{ textAlign: 'right' }}>Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.user_id || user.id}>
                  <td>
                    <div className="staff-name" style={{fontWeight: 600}}>
                        {user.first_name} {user.last_name}
                    </div>
                    <div style={{fontSize:'11px', color:'#9ca3af'}}>
                        {user.gender === 'MALE' ? 'Nam' : 'Nữ'} {user.date_of_birth ? `| ${new Date(user.date_of_birth).toLocaleDateString('vi-VN')}` : ''}
                    </div>
                  </td>
                  <td>
                    <div style={{fontSize:'13px'}}>{user.email}</div>
                    <div style={{fontSize:'12px', color:'#666'}}>{user.phone_number || 'Chưa có SĐT'}</div>
                  </td>
                  <td>
                    <span className={`role-badge ${ROLE_CONFIG[user.role_id]?.class || 'badge-cskh'}`}>
                      {ROLE_CONFIG[user.role_id]?.label || 'THÀNH VIÊN'}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${Number(user.is_active) === 1 ? 'badge-success' : 'badge-default'}`}>
                      {Number(user.is_active) === 1 ? 'Hoạt động' : 'Đã khóa'}
                    </span>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <button className="btn-icon" onClick={() => openEditModal(user)}>✏️</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content" style={{maxWidth: '600px'}}>
            <div className="modal-header">
              <h4>{isEditing ? 'Sửa thông tin' : 'Thêm nhân viên mới'}</h4>
              <button className="close-btn" onClick={() => setShowModal(false)}>×</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="form-row">
                <div className="form-group half">
                    <label>Họ</label>
                    <input required className="form-control" value={formData.first_name} onChange={(e) => setFormData({...formData, first_name: e.target.value})} />
                </div>
                <div className="form-group half">
                    <label>Tên</label>
                    <input required className="form-control" value={formData.last_name} onChange={(e) => setFormData({...formData, last_name: e.target.value})} />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group half">
                    <label>Số điện thoại</label>
                    <input className="form-control" value={formData.phone_number} onChange={(e) => setFormData({...formData, phone_number: e.target.value})} placeholder="0987..." />
                </div>
                <div className="form-group half">
                    <label>Giới tính</label>
                    <select className="form-control" value={formData.gender} onChange={(e) => setFormData({...formData, gender: e.target.value})}>
                        <option value="MALE">Nam</option>
                        <option value="FEMALE">Nữ</option>
                        <option value="OTHER">Khác</option>
                    </select>
                </div>
              </div>

              <div className="form-group">
                <label>Ngày sinh</label>
                <input type="date" className="form-control" value={formData.date_of_birth} onChange={(e) => setFormData({...formData, date_of_birth: e.target.value})} />
              </div>

              <div className="form-group">
                <label>Email (Tên đăng nhập)</label>
                <input required type="email" className="form-control" value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})} disabled={isEditing} />
              </div>

              {!isEditing && (
                <div className="form-group">
                  <label>Mật khẩu khởi tạo</label>
                  <input required type="password" className="form-control" value={formData.password} onChange={(e) => setFormData({...formData, password: e.target.value})} />
                </div>
              )}

              <div className="form-group">
                <label>Chức vụ</label>
                <select className="form-control" value={formData.role_id} onChange={(e) => setFormData({...formData, role_id: Number(e.target.value)})}>
                  <option value={2}>ADMIN</option>
                  <option value={3}>NHÂN VIÊN KHO</option>
                  <option value={4}>MARKETING</option>
                  <option value={5}>CSKH</option>
                </select>
              </div>

              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>Hủy</button>
                <button type="submit" className="btn-primary">Lưu lại</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default RoleSettings;