import axiosClient from './axiosClient';

const marketingApi = {
  // PHẦN 1: COUPONS
  getPublicCoupons: () => {
    return axiosClient.get('/coupons/public');
  },

  getAvailableCoupons: (params) => {
    return axiosClient.get('/coupons/available', { params });
  },

  validateCoupon: (data) => {
    return axiosClient.post('/coupons/validate', data);
  },

  getAllCoupons: (params) => {
    return axiosClient.get('/coupons', { params });
  },

  createCoupon: (data) => {
    return axiosClient.post('/coupons', data);
  },

  getCouponById: (id) => {
    return axiosClient.get(`/coupons/${id}`);
  },

  updateCoupon: (id, data) => {
    return axiosClient.patch(`/coupons/${id}`, data);
  },

  deleteCoupon: (id) => {
    return axiosClient.delete(`/coupons/${id}`);
  },

  getCouponByCode: (code) => {
    return axiosClient.get(`/coupons/code/${code}`);
  },
  // PHẦN 2: FLASH SALES

  getActiveFlashSales: () => {
    return axiosClient.get('/coupons/flash-sales/active');
  },

  getUpcomingFlashSales: () => {
    return axiosClient.get('/coupons/flash-sales/upcoming');
  },

  getAllFlashSales: (params) => {
    return axiosClient.get('/coupons/flash-sales/all', { params });
  },

  getFlashSaleById: (id) => {
    return axiosClient.get(`/coupons/flash-sales/${id}`);
  },

  updateFlashSale: (id, data) => {
    return axiosClient.patch(`/coupons/flash-sales/${id}`, data);
  },

  deleteFlashSale: (id) => {
    return axiosClient.delete(`/coupons/flash-sales/${id}`);
  },

  createFlashSale: (data) => {
    return axiosClient.post('/coupons/flash-sales', data);
  },

  addProductToFlashSale: (flashSaleId, data) => {
    return axiosClient.post(`/coupons/flash-sales/${flashSaleId}/products`, data);
  },

  removeProductFromFlashSale: (flashSaleId, productId) => {
    return axiosClient.delete(`/coupons/flash-sales/${flashSaleId}/products/${productId}`);
  },

  checkProductInFlashSale: (productId) => {
    return axiosClient.get(`/coupons/flash-sales/product/${productId}/check`);
  },
  getProductsForSelection: () => {
    // Giả sử API lấy sản phẩm là /products. Đại ca sửa lại endpoint nếu khác nhé.
    return axiosClient.get('/products?limit=100'); 
  }
};

export default marketingApi;