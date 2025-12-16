import React from 'react';
import { Outlet } from 'react-router-dom';
import Header from './Header';
import Footer_1 from './Footer_1'; // 1. Đổi tên import này cho rõ
import Footer_2 from './Footer_2'; // 2. Import thêm Footer_2

import {
  TOP_LINKS,
  MENU_LINKS,
  BRAND_INFO,
  FOOTER_SECTIONS,
  SOCIAL_LINKS,
} from '../constants/siteContent';

// 3. Thêm prop "isSubPage" (mặc định là false)
const Layout = ({ user, onLogout, isSubPage = false }) => (
  <>
    <Header
      topLinks={TOP_LINKS}
      menuLinks={MENU_LINKS}
      user={user}
      onLogout={onLogout}
    />

    <main>
      <Outlet />
    </main>

    {/* 4. Logic chọn Footer: */}
    {/* Nếu là trang phụ (isSubPage = true) -> Hiện Footer 2 */}
    {/* Nếu là trang chủ (isSubPage = false) -> Hiện Footer 1 */}
    {isSubPage ? (
      <Footer_2 />
    ) : (
      <Footer_1
        brandInfo={BRAND_INFO}
        footerSections={FOOTER_SECTIONS}
        socialLinks={SOCIAL_LINKS}
      />
    )}
  </>
);

export default Layout;

