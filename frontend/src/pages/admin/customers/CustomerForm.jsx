import React, { useState, useEffect } from 'react';
import userApi from '../../../api/userApi';
import './Customers.css';

const CustomerForm = ({ onClose, initialData, onSuccess }) => {
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone_number: '',
    password: '',
    role_id: 2176,
    is_active: true
  });
  
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (initialData) {
      setFormData({
        first_name: initialData.first_name || '',
        last_name: initialData.last_name || '',
        email: initialData.email || '',
        phone_number: initialData.phone_number || '',
        is_active: initialData.is_active,
        role_id: initialData.role_id,
        password: ''
      });
    }
  }, [initialData]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (initialData) {
        // Cập nhật
        const { password, ...updateData } = formData;
        if (!password) delete updateData.password;
        await userApi.update(initialData.user_id || initialData.id, updateData);
        alert("Cập nhật thành công!");
      } else {
        // Tạo mới
        await userApi.create(formData);
        alert("Thêm khách hàng mới thành công!");
      }
      onSuccess();
    } catch (error) {
      alert("Lỗi: " + (error.response?.data?.detail || "Có lỗi xảy ra"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content customer-modal animate-pop-in" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{initialData ? 'Sửa thông tin' : 'Thêm khách hàng mới'}</h3>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </div>

        <div className="modal-body">
          <form id="custForm" onSubmit={handleSubmit}>
            <div className="form-grid-2">
              <div className="form-group">
                <label>Họ (Last Name)</label>
                <input type="text" name="last_name" value={formData.last_name} onChange={handleChange} placeholder="Nguyễn" required />
              </div>
              <div className="form-group">
                <label>Tên (First Name)</label>
                <input type="text" name="first_name" value={formData.first_name} onChange={handleChange} placeholder="Văn A" required />
              </div>
            </div>

            <div className="form-group">
              <label>Email (Tài khoản) <span style={{color:'red'}}>*</span></label>
              <input type="email" name="email" value={formData.email} onChange={handleChange} required disabled={!!initialData} />
            </div>

            <div className="form-group">
              <label>Số điện thoại</label>
              <input type="text" name="phone_number" value={formData.phone_number} onChange={handleChange} placeholder="0988..." />
            </div>

            <div className="form-group">
              <label>{initialData ? 'Mật khẩu mới (Để trống nếu không đổi)' : 'Mật khẩu đăng nhập *'}</label>
              <input 
                type="password" name="password" 
                value={formData.password} onChange={handleChange} 
                required={!initialData}
                placeholder="••••••••" 
              />
            </div>

            <div className="form-group">
              <label>Trạng thái hoạt động</label>
              <select name="is_active" value={formData.is_active} onChange={(e) => setFormData({...formData, is_active: e.target.value === 'true'})}>
                <option value="true">Hoạt động (Active)</option>
                <option value="false">Đã khóa (Inactive)</option>
              </select>
            </div>
          </form>
        </div>

        <div className="modal-footer">
          <button type="button" className="btn-cancel" onClick={onClose}>Hủy</button>
          <button type="submit" form="custForm" className="btn-save" disabled={loading}>
            {loading ? 'Đang lưu...' : 'Lưu khách hàng'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default CustomerForm;