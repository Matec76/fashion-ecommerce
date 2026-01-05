import React, { useState } from 'react';
import { API_ENDPOINTS } from '../../../config/api.config';
import useMutation from '../../../hooks/useMutation';
import '/src/style/modal.css';

const ChangePasswordModal = ({ isOpen, onClose }) => {
    const [formData, setFormData] = useState({
        currentPassword: '',
        newPassword: ''
    });
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);

    const { mutate, loading } = useMutation();

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
        if (error) setError('');
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        const token = localStorage.getItem('authToken');
        if (!token) {
            setError('Vui lòng đăng nhập để đổi mật khẩu!');
            return;
        }

        if (!formData.currentPassword || !formData.newPassword) {
            setError('Vui lòng nhập đầy đủ thông tin!');
            return;
        }

        if (formData.newPassword.length < 8) {
            setError('Mật khẩu mới phải có ít nhất 8 ký tự!');
            return;
        }

        if (formData.currentPassword === formData.newPassword) {
            setError('Mật khẩu mới phải khác mật khẩu hiện tại!');
            return;
        }

        setError('');

        const result = await mutate(API_ENDPOINTS.AUTH.PASSWORD_CHANGE, {
            method: 'POST',
            body: {
                current_password: formData.currentPassword,
                new_password: formData.newPassword
            }
        });

        if (result.success) {
            setSuccess(true);
            setFormData({
                currentPassword: '',
                newPassword: ''
            });
            setTimeout(() => {
                setSuccess(false);
                onClose();
            }, 2000);
        } else {
            setError(result.error || 'Không thể đổi mật khẩu. Vui lòng thử lại!');
        }
    };

    const handleClose = () => {
        setFormData({
            currentPassword: '',
            newPassword: ''
        });
        setError('');
        setSuccess(false);
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay" onClick={handleClose}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <button className="modal-close" onClick={handleClose}>×</button>

                <div className="modal-header">
                    <h1 className="modal-main-title">ĐỔI MẬT KHẨU</h1>
                </div>

                {success ? (
                    <div className="modal-success">
                        <div className="success-icon">✓</div>
                        <p>Mật khẩu đã được thay đổi thành công!</p>
                    </div>
                ) : (
                    <form onSubmit={handleSubmit} className="modal-form">
                        <div className="modal-input-group">
                            <input
                                type="password"
                                name="currentPassword"
                                value={formData.currentPassword}
                                onChange={handleChange}
                                required
                                placeholder=" "
                            />
                            <label>Mật Khẩu Cũ *</label>
                        </div>

                        <div className="modal-input-group">
                            <input
                                type="password"
                                name="newPassword"
                                value={formData.newPassword}
                                onChange={handleChange}
                                required
                                placeholder=" "
                            />
                            <label>Mật Khẩu Mới *</label>
                        </div>

                        {error && (
                            <div className="modal-error">
                                {error}
                            </div>
                        )}

                        <div className="modal-buttons">
                            <button
                                type="submit"
                                className="modal-btn modal-btn-primary"
                                disabled={loading}
                            >
                                {loading ? 'Đang xử lý...' : 'LƯU CÁC THAY ĐỔI'}
                                <span className="btn-arrow">→</span>
                            </button>
                        </div>
                    </form>
                )}
            </div>
        </div>
    );
};

export default ChangePasswordModal;
