import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

// Auth pages
import Login from './pages/auth/Login';
import SignUp from './pages/auth/SignUp';
import ForgotPassword from './pages/auth/ForgotPassword';
import ResetPassword from './pages/auth/ResetPassword';
import ChangePassword from './pages/auth/ChangePassword';

// Home
import HomePage from './pages/home/TrangChu';
import ProductPage from './pages/home/SanPham';
import ProductDetail from './pages/home/ProductDetail';
import Cart from './pages/home/Cart';
import Checkout from './pages/home/Checkout';
import PaymentQR from './pages/home/PaymentQR';
import PaymentSuccess from './pages/home/PaymentSuccess';
import PaymentFailure from './pages/home/PaymentFailure';
import UserProfile from './pages/user/UserProfile';
import Wishlist from './pages/user/Wishlist';
import AddressManagement from './pages/home/AddressManagement';
import OrderTracking from './pages/home/OrderTracking';
import FlashSales from './pages/home/FlashSales';
import Collections from './pages/home/Collections';
import CollectionDetail from './pages/home/CollectionDetail';

// Support pages
import TrungTamHoTro from './pages/support/TrungTamHoTro';

import HoiVien from './pages/support/HoiVien';

// Info pages
import ChinhSach from './pages/info/ChinhSach';
import DieuKhoan from './pages/info/DieuKhoan';
import CongTy from './pages/info/CongTy';
import Layout from './components/Layout';

// Context
import { CartProvider } from './pages/home/CartContext';

function App() {
  // Lazy state initializer - chỉ chạy 1 lần khi component mount
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    const token = localStorage.getItem('authToken');
    const savedUser = localStorage.getItem('user');
    return !!(token && savedUser);
  });

  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
      try {
        return JSON.parse(savedUser);
      } catch {
        return null;
      }
    }
    return null;
  });

  const handleLoginSuccess = (userData) => {
    setIsAuthenticated(true);
    setUser(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
    setIsAuthenticated(false);
    setUser(null);
  };

  return (
    <CartProvider>
      <Router>
        <Routes>
          {/* Auth Routes */}
          <Route
            path="/login"
            element={
              isAuthenticated ?
                <Navigate to="/" /> :
                <Login onLoginSuccess={handleLoginSuccess} />
            }
          />
          <Route
            path="/signup"
            element={
              isAuthenticated ?
                <Navigate to="/" /> :
                <SignUp />
            }
          />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/change-password" element={<ChangePassword />} />

          <Route element={<Layout user={user} onLogout={handleLogout} isSubPage={false} />}>
            <Route path="/" element={<HomePage />} />
            <Route path="/product" element={<ProductPage />} />
            <Route path="/products/:identifier" element={<ProductDetail />} />
          </Route>
          <Route element={<Layout user={user} onLogout={handleLogout} isSubPage={true} />}>

            {/* Các trang con phải nằm LỌT LÒNG bên trong */}
            <Route path="/member" element={<HoiVien />} />
            <Route path="/privacy" element={<ChinhSach />} />  {/* <-- Trang bị lỗi của bạn đây */}
            <Route path="/terms" element={<DieuKhoan />} />
            <Route path="/support" element={<TrungTamHoTro />} />

            <Route path="/company" element={<CongTy />} />
            <Route path="/cart" element={<Cart />} />
            <Route path="/checkout" element={<Checkout />} />
            <Route path="/payment-qr" element={<PaymentQR />} />
            <Route path="/payment/success" element={<PaymentSuccess />} />
            <Route path="/payment/failure" element={<PaymentFailure />} />
            <Route path="/profile" element={<UserProfile />} />
            <Route path="/addresses" element={<AddressManagement />} />
            <Route path="/orders" element={<OrderTracking />} />
            <Route path="/order/:orderId" element={<OrderTracking />} />
            <Route path="/wishlist" element={<Wishlist />} />
            <Route path="/flash-sales" element={<FlashSales />} />
            <Route path="/collections" element={<Collections />} />
            <Route path="/collections/:slug" element={<CollectionDetail />} />

          </Route>
          {/* 404 Route */}
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </Router>
    </CartProvider>
  );
}

export default App;