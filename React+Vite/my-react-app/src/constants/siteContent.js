export const TOP_LINKS = Object.freeze([
  { to: '/support', label: 'TRỢ GIÚP' },
  { to: '/tracking', label: 'THEO DÕI ĐƠN HÀNG' },
  { to: '/member', label: 'ĐĂNG KÝ HỘI VIÊN' }
]);

export const MENU_LINKS = Object.freeze([
  { to: '/product?gender=Nam', label: 'Nam' },
  { to: '/product?gender=Nữ', label: 'Nữ' },
  { to: '/product?gender=Trẻ em', label: 'Trẻ em' },
  { to: '/product', label: 'PHỤ KIỆN' },
  { to: '/product?new=true', label: 'Outlet', className: 'outlet' }
]);

export const BRAND_INFO = Object.freeze({
  name: 'STYLEX',
  slogan: 'Nâng tầm phong cách, định hình cá tính.'
});

export const FOOTER_SECTIONS = Object.freeze([
  {
    heading: 'Sản phẩm',
    links: [
      { to: '/product?type=Giày', label: 'Giày' },
      { to: '/product?type=Áo', label: 'Quần áo' },
      { to: '/product', label: 'Phụ kiện' },
      { to: '/product?new=true', label: 'Hàng mới về' }
    ]
  },
  {
    heading: 'Hỗ trợ',
    links: [
      { to: '#', label: 'Liên hệ' },
      { to: '/support', label: 'Câu hỏi thường gặp' },
      { to: '#', label: 'Chính sách đổi trả' },
      { to: '/tracking', label: 'Tra cứu đơn hàng' }
    ]
  },
  {
    heading: 'Về chúng tôi',
    links: [
      { to: '/company', label: 'Câu chuyện' },
      { to: '/company', label: 'Tuyển dụng' },
      { to: '/company', label: 'Báo chí' }
    ]
  }
]);

export const SOCIAL_LINKS = Object.freeze([
  { type: 'facebook', href: 'https://www.facebook.com/profile.php?id=61577069013431' },
  { type: 'instagram', href: '#' },
  { type: 'twitter', href: '#' }
]);




