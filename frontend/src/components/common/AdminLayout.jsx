import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar'; //  Phải import từ './Sidebar'
import './Admin.css'; // File css layout nếu có

const AdminLayout = () => {
  return (
    <div className="admin-container" style={{display: 'flex'}}>
      {/* Sidebar nằm bên trái */}
      <Sidebar />
      
      {/* Nội dung chính nằm bên phải */}
      <div className="main-content" style={{flex: 1, marginLeft: '260px', padding: '20px', background: '#f8f9fa', minHeight: '100vh'}}>
        <Outlet />
      </div>
    </div>
  );
};

export default AdminLayout;