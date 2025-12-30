import React, { useState, useEffect } from 'react';
import logger from '../../../utils/logger';
import { Outlet } from 'react-router-dom';
import Header from '../Header/Header';
import Footer_1 from '../Footer/Footer_1';
import Footer_2 from '../Footer/Footer_2';

import {
  TOP_LINKS,
  MENU_LINKS,
  BRAND_INFO,
  FOOTER_SECTIONS,
  SOCIAL_LINKS,
} from '../../../constants/siteContent';

const Layout = ({ user, onLogout, isSubPage = false }) => {
  const [socialLinks, setSocialLinks] = useState([]);
  const [contactHotline, setContactHotline] = useState('+84 28 44581937');

  useEffect(() => {
    const fetchSocialLinks = async () => {
      try {
        const response = await fetch('/api/v1/system/settings/public');
        if (response.ok) {
          const data = await response.json();
          logger.log('🔍 API Response:', data);

          // Build social links từ API data
          const apiSocialLinks = [];
          if (data.social_facebook) {
            apiSocialLinks.push({ type: 'facebook', href: data.social_facebook });
          }
          if (data.social_instagram) {
            apiSocialLinks.push({ type: 'instagram', href: data.social_instagram });
          }
          if (data.social_twitter) {
            apiSocialLinks.push({ type: 'twitter', href: data.social_twitter });
          }

          logger.log('📱 Social Links:', apiSocialLinks);

          // Always update với API data
          setSocialLinks(apiSocialLinks);

          // Update contact hotline nếu có
          if (data.contact_hotline) {
            setContactHotline(data.contact_hotline);
          }
        }
      } catch (error) {
        logger.error('Error fetching social links:', error);
        // Giữ nguyên default SOCIAL_LINKS nếu lỗi
      }
    };

    fetchSocialLinks();
  }, []);

  return (
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

      {isSubPage ? (
        <Footer_2 contactHotline={contactHotline} />
      ) : (
        <Footer_1
          brandInfo={BRAND_INFO}
          footerSections={FOOTER_SECTIONS}
          socialLinks={socialLinks}
          contactHotline={contactHotline}
        />
      )}
    </>
  );
};

export default Layout;

