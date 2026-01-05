import React, { useState, lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

// ✅ CRITICAL: Keep auth pages eager-loaded for immediate access
import Login from './pages/auth/Login';
import SignUp from './pages/auth/SignUp';

// ✅ OPTIMIZATION: Lazy-load all other pages for better initial load time
// Auth pages
const ForgotPassword = lazy(() => import('./pages/auth/ForgotPassword'));
const ResetPassword = lazy(() => import('./pages/auth/ResetPassword'));
const ChangePassword = lazy(() => import('./pages/auth/ChangePassword'));
const VerifyEmail = lazy(() => import('./pages/auth/VerifyEmail'));

// Home pages
const HomePage = lazy(() => import('./pages/home/TrangChu'));
const ProductPage = lazy(() => import('./pages/home/SanPham'));
const ProductDetail = lazy(() => import('./pages/home/ProductDetail'));
const Cart = lazy(() => import('./pages/home/Cart'));
const Checkout = lazy(() => import('./pages/home/Checkout'));
const PaymentQR = lazy(() => import('./pages/home/PaymentQR'));
const PaymentSuccess = lazy(() => import('./pages/home/PaymentSuccess'));
const PaymentFailure = lazy(() => import('./pages/home/PaymentFailure'));
const AddressManagement = lazy(() => import('./pages/home/AddressManagement'));
const OrderTracking = lazy(() => import('./pages/home/OrderTracking'));
const FlashSales = lazy(() => import('./pages/home/FlashSales'));
const Collections = lazy(() => import('./pages/home/Collections'));
const CollectionDetail = lazy(() => import('./pages/home/CollectionDetail'));

// User pages
const UserProfile = lazy(() => import('./pages/user/UserProfile'));
const Wishlist = lazy(() => import('./pages/user/Wishlist'));
const Loyalty = lazy(() => import('./pages/user/Loyalty'));
const Vouchers = lazy(() => import('./pages/user/Vouchers'));
const ReturnRefunds = lazy(() => import('./pages/user/ReturnRefunds'));
const ReturnRefundDetail = lazy(() => import('./pages/user/ReturnRefundDetail'));
const RedeemSuccess = lazy(() => import('./pages/user/RedeemSuccess'));

// Support & Info pages
const TrungTamHoTro = lazy(() => import('./pages/support/TrungTamHoTro'));
const ChinhSach = lazy(() => import('./pages/info/ChinhSach'));
const DieuKhoan = lazy(() => import('./pages/info/DieuKhoan'));
const CongTy = lazy(() => import('./pages/info/CongTy'));

// Components - keep these eager for layout
import Layout from './components/layout/Layout/Layout';
import ChatbotWidget from './components/common/ChatbotWidget';

// Context
import { CartProvider } from './pages/home/CartContext';
import { NotificationProvider } from './context/NotificationContext';

// ✅ Loading component for Suspense fallback
const LoadingFallback = () => (
  <div style={{
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100vh',
    fontSize: '18px',
    color: '#666'
  }}>
    <div className="spinner"></div>
  </div>
);

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
      <NotificationProvider>
        <Router>
          <Suspense fallback={<LoadingFallback />}>
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
              <Route path="/verify-email" element={<VerifyEmail />} />

              <Route element={<Layout user={user} onLogout={handleLogout} isSubPage={false} />}>
                <Route path="/" element={<HomePage />} />
                <Route path="/product" element={<ProductPage />} />
                <Route path="/products/:identifier" element={<ProductDetail />} />
              </Route>
              <Route element={<Layout user={user} onLogout={handleLogout} isSubPage={true} />}>

                {/* Các trang con phải nằm LỌT LÒNG bên trong */}
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
                <Route path="/loyalty" element={<Loyalty />} />
                <Route path="/loyalty/success" element={<RedeemSuccess />} />
                <Route path="/vouchers" element={<Vouchers />} />
                <Route path="/returns" element={<ReturnRefunds />} />
                <Route path="/returns/:returnId" element={<ReturnRefundDetail />} />
                <Route path="/flash-sales" element={<FlashSales />} />
                <Route path="/collections" element={<Collections />} />
                <Route path="/collections/:slug" element={<CollectionDetail />} />

              </Route>
              {/* 404 Route */}
              <Route path="*" element={<Navigate to="/" />} />
            </Routes>
          </Suspense>
          <ChatbotWidget />
        </Router>
      </NotificationProvider>
    </CartProvider >
  );
}

export default App;