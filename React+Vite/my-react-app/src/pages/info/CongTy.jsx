import React, { useState, useEffect } from 'react';
import logger from '../../utils/logger';
import '/src/style/SubPages.css';

const CongTy = () => {
  const [companyInfo, setCompanyInfo] = useState({
    name: 'Công ty TNHH STYLEX Việt Nam',
    taxId: '0123456789',
    address: 'Tầng 10, Tòa nhà STYLEX, 123 Đường Thời Trang, Quận 1, Thành phố Hồ Chí Minh, Việt Nam',
    email: 'support@stylex.com.vn',
    phone: '+84 28 44581037'
  });

  useEffect(() => {
    const fetchCompanyInfo = async () => {
      try {
        const response = await fetch('/api/v1/system/settings/public');
        if (response.ok) {
          const data = await response.json();

          setCompanyInfo(prev => ({
            ...prev,
            address: data.contact_address || prev.address,
            email: data.contact_email || prev.email,
            phone: data.contact_hotline || prev.phone
          }));
        }
      } catch (error) {
        logger.error('Error fetching company info:', error);
      }
    };

    fetchCompanyInfo();
  }, []);

  return (
    <div className="sub-page-container">
      {/* Main Content */}
      <main className="sub4">
        <h2 style={{ marginBottom: '40px' }}>Các thông tin về Công ty</h2>
        <ul className="sub4__list" style={{ fontSize: '18px' }}>
          <li>
            <h4>Tên công ty: <span style={{ fontWeight: 400 }}>{companyInfo.name}</span></h4>
          </li>
          <li>
            <h4>Mã số doanh nghiệp: <span style={{ fontWeight: 400 }}>{companyInfo.taxId}</span></h4>
          </li>
          <li>
            <h4>Địa chỉ: <span style={{ fontWeight: 400 }}>{companyInfo.address}</span></h4>
          </li>
          <li>
            <h4>Email: <span style={{ fontWeight: 400 }}>{companyInfo.email}</span></h4>
          </li>
          <li>
            <h4>Điện thoại: <span style={{ fontWeight: 400 }}>{companyInfo.phone}</span></h4>
          </li>
        </ul>
      </main>
    </div>
  );
};

export default CongTy;