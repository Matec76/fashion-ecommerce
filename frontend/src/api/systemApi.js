import axiosClient from './axiosClient';

const systemApi = {
  // --- SYSTEM SETTINGS ---
  getAll: () => axiosClient.get('/system/settings'),
  getByKey: (key) => axiosClient.get(`/system/settings/key/${key}`),
  setValue: (key, value) => axiosClient.post('/system/settings/set', null, { params: { key, value } }),
  getPublic: () => axiosClient.get('/system/settings/public'),

  // --- QUẢN LÝ VẬN CHUYỂN ---
  getShippingMethods: () => axiosClient.get(`/orders/shipping-methods/all?t=${new Date().getTime()}`),
  createShippingMethod: (data) => axiosClient.post('/orders/shipping-methods', data),
  updateShippingMethod: (id, data) => axiosClient.patch(`/orders/shipping-methods/${id}`, data),
  deleteShippingMethod: (id) => axiosClient.delete(`/orders/shipping-methods/${id}`),

  // --- QUẢN LÝ THANH TOÁN (ĐÃ FIX CACHE & ĐƯỜNG DẪN) ---
  
  // 1. Lấy danh sách (Thêm ?t=... để chống cache)
  // Endpoint: GET /api/v1/payment/methods
  getPaymentMethods: () => {
    return axiosClient.get(`/payment/methods?t=${new Date().getTime()}`);
  },

  // 2. Tạo mới (Dùng đường dẫn Admin)
  // Endpoint: POST /api/v1/payment_methods/admin
  createPaymentMethod: (data) => {
    return axiosClient.post('/payment_methods/admin', data);
  },

  // 3. Cập nhật (Dùng đường dẫn Admin)
  // Endpoint: PATCH /api/v1/payment_methods/admin/{method_id}
  updatePaymentMethod: (id, data) => {
    return axiosClient.patch(`/payment_methods/admin/${id}`, data);
  },

  // 4. Xóa (Dùng đường dẫn Admin)
  // Endpoint: DELETE /api/v1/payment_methods/admin/{method_id}
  deletePaymentMethod: (id) => {
    return axiosClient.delete(`/payment_methods/admin/${id}`);
  },
  getUsers: () => {
    return axiosClient.get(`/users?t=${new Date().getTime()}`);
  },
  create: (data) => {
    return axiosClient.post('/users', data);
  },
  // Cập nhật Role cho User
  updateUserRole: (userId, data) => {
    return axiosClient.patch(`/users/${userId}`, data);
  }
};

export default systemApi;