import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom'; 
import { hasPermission } from '../../utils/roles'; 
import './Sidebar.css';

const Sidebar = () => {
  const navigate = useNavigate(); 

  const userString = localStorage.getItem('user');
  const user = userString ? JSON.parse(userString) : {};
  const roleId = user.role_id; 
  const userName = user.full_name || "Admin";

  // ... (Phần menuItems GIỮ NGUYÊN KHÔNG CẦN SỬA) ...
  const menuItems = [
    { path: '/admin/dashboard', name: 'Tổng quan', permission: 'dashboard.view', icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg> },
    { path: '/admin/orders', name: 'Đơn hàng', permission: 'order.view', icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"></path><rect x="9" y="3" width="6" height="4" rx="1"></rect><path d="M9 14l2 2 4-4"></path></svg> },
    { path: '/admin/customers', name: 'Khách hàng', permission: 'user.view', icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg> },
    { path: '/admin/products', name: 'Sản phẩm', permission: 'product.view', icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 7.5L12 3 4 7.5 4 16.5 12 21 20 16.5z"></path><path d="M12 21L12 12"></path><path d="M20 7.5L12 12 4 7.5"></path></svg> },
    { path: '/admin/inventory', name: 'Kho hàng', permission: 'inventory.view', icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="21 8 21 21 3 21 3 8"></polyline><rect x="1" y="3" width="22" height="5"></rect><line x1="10" y1="12" x2="14" y2="12"></line></svg> },
    { path: '/admin/marketing', name: 'Marketing', permission: 'marketing.view', icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path><line x1="7" y1="7" x2="7.01" y2="7"></line></svg> },
    { path: '/admin/content', name: 'Nội dung', permission: 'cms.manage', icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg> },
    { path: '/admin/reports', name: 'Báo cáo', permission: 'analytics.view', icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg> },
    { path: '/admin/settings', name: 'Cấu hình', permission: 'system.manage', icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg> }
  ];

  const handleLogout = () => {
    if (window.confirm("Đại ca có chắc muốn đăng xuất không?")) {
        localStorage.clear();
        window.location.href = '/admin/login'; 
    }
  };

  return (
    <div className="sidebar">
      {/* ... (Phần render giữ nguyên) ... */}
      <div className="sidebar-logo">
        <h2>STYLEX</h2>
        <small style={{display:'block', fontSize:'11px', color:'#9ca3af', marginTop:'4px'}}>
            Xin chào, {userName}
        </small>
      </div>
      
      <div className="sidebar-menu">
        {menuItems.map((item, index) => {
            if (item.permission && !hasPermission(roleId, item.permission)) {
                return null;
            }
            return (
              <NavLink 
                to={item.path} 
                key={index} 
                className={({ isActive }) => isActive ? "menu-item active" : "menu-item"}
              >
                <span className="icon">{item.icon}</span>
                <span className="text">{item.name}</span>
              </NavLink>
            );
        })}
      </div>

      <div className="sidebar-footer">
          <div className="menu-item logout-btn" onClick={handleLogout}>
            <span className="icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
            </span>
            <span className="text">Đăng xuất</span>
          </div>
      </div>
    </div>
  );
};

export default Sidebar;