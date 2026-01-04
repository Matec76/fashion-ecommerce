import React, { useState, useMemo } from 'react';
import './Settings.css';

// Import tất cả các trang con
import StoreInfo from './StoreInfo';
import ShippingSettings from './ShippingSettings';
import PaymentSettings from './PaymentSettings'; 
import RoleSettings from './RoleSettings';
import InventoryProduct from './InventoryProduct';
import MarketingContact from './MarketingContact'; 
import LoyaltyConfig from './LoyaltyConfig';       
import SystemControl from './SystemControl';       

const Settings = () => {
  // 1. Lấy thông tin Role hiện tại
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const roleId = parseInt(user.role_id);

  // 2. Định nghĩa danh sách gốc
  const allTabs = [
    { id: 'info', label: 'Thông tin cửa hàng' },
    { id: 'shipping', label: 'Vận chuyển & Đổi trả' },
    { id: 'payment', label: 'Thanh toán' },
    { id: 'inventory', label: 'Sản phẩm & Kho hàng' },
    { id: 'marketing', label: 'Marketing & KH' },
    { id: 'loyalty', label: 'Điểm thưởng (Loyalty)' },
    { id: 'system', label: 'Hệ thống' },
    { id: 'roles', label: 'Phân quyền nhân viên' },
  ];

  // 3. Lọc Tab theo Role (Logic phân quyền nằm ở đây)
  const visibleTabs = useMemo(() => {
    return allTabs.filter(tab => {
        // 🔥 Role 1 (Admin) & Role 2 (Quản lý): Xem HẾT
        if (roleId === 1 || roleId === 2) return true;

        // 🔥 Role 4 (Marketing): Chỉ xem Loyalty
        if (roleId === 4) return tab.id === 'loyalty';

        // 🔥 Role 5 (CSKH): Chỉ xem Payment (Thanh toán)
        if (roleId === 5) return tab.id === 'payment';

        return false; // Các role khác (nếu có) không thấy gì
    });
  }, [roleId]);

  // 4. Chọn tab mặc định là tab đầu tiên trong danh sách được phép
  // (Ví dụ Role 4 vào thì tự nhảy sang 'loyalty' chứ không ở 'info' nữa)
  const [activeTab, setActiveTab] = useState(visibleTabs.length > 0 ? visibleTabs[0].id : '');

  const renderContent = () => {
    switch (activeTab) {
        case 'info': return <StoreInfo />;
        case 'shipping': return <ShippingSettings />;
        case 'payment': return <PaymentSettings />;
        case 'roles': return <RoleSettings />;
        case 'inventory': return <InventoryProduct />;
        case 'marketing': return <MarketingContact />;
        case 'loyalty': return <LoyaltyConfig />;
        case 'system': return <SystemControl />;
        default: return <div style={{padding:'20px'}}>Chọn mục cấu hình để xem chi tiết</div>;
    }
  };

  return (
    <div className="settings-page">
      <div className="page-header-box">
        <h2>Cấu hình hệ thống</h2>
      </div>

      <div className="settings-layout">
        <div className="settings-sidebar">
            <div className="sidebar-header">Danh mục</div>
            <ul className="sidebar-menu">
                {/* Render danh sách đã lọc */}
                {visibleTabs.map(tab => (
                    <li 
                        key={tab.id}
                        className={`settings-nav-item ${activeTab === tab.id ? 'active' : ''}`}
                        onClick={() => setActiveTab(tab.id)}
                    >
                        {tab.label}
                    </li>
                ))}
            </ul>
        </div>

        <div className="settings-content-area">
            {/* Chỉ render nội dung nếu có tab hợp lệ */}
            {visibleTabs.length > 0 ? renderContent() : (
                <div style={{padding: '20px', color: 'red'}}>
                    Bạn không có quyền truy cập mục Cấu hình nào.
                </div>
            )}
        </div>
      </div>
    </div>
  );
};

export default Settings;