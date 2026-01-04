import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import AdminLayout from './components/common/AdminLayout'; 
import Login from './pages/auth/Login';
import Products from './pages/admin/products/index';
import Orders from './pages/admin/orders/Orders';
import Customers from './pages/admin/customers/Customers';
import Marketing from './pages/admin/marketing/Marketing';
import Content from './pages/admin/content/Content';
import Reports from './pages/admin/Reports/Reports';
import Settings from './pages/admin/settings/Settings';
import Dashboard from './pages/admin/dashboard/Dashboard';

import Inventory from './pages/admin/inventory/inventory';

function App() {
  return (
    <div className="App">
      <Routes>
        {/* === PUBLIC ROUTES === */}
        <Route path="/admin/login" element={<Login />} />
        <Route path="/" element={<Navigate to="/admin/login" />} />

        {/* === ADMIN ROUTES === */}
        <Route path="/admin" element={<AdminLayout />}>
          
          {/* Mặc định vào Dashboard */}
          <Route index element={<Navigate to="dashboard" />} />

          {/* Danh sách các trang chức năng */}
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="products" element={<Products />} />

          {/*  ROUTE KHO HÀNG */}
          <Route path="inventory" element={<Inventory />} />

          <Route path="orders" element={<Orders />} />
          <Route path="customers" element={<Customers />} />
          
          <Route path="marketing" element={<Marketing />} />
          <Route path="content" element={<Content />} />

          {/* Các trang báo cáo & cấu hình */}
          <Route path="reports" element={<Reports />} />
          <Route path="settings" element={<Settings />} />

        </Route>

        {/* 404 Not Found */}
        <Route path="*" element={<div style={{padding: 50, textAlign: 'center'}}><h2>404 - Không tìm thấy trang</h2></div>} />
      </Routes>
    </div>
  );
}

export default App;