import axiosClient from './axiosClient';

const orderApi = {
  // 1. Lấy danh sách
  getAll: (params) => {
    return axiosClient.get('/orders', { params });
  },

  // 2. Lấy chi tiết
  getDetail: (id) => {
    return axiosClient.get(`/orders/${id}`);
  },

  // 3. Cập nhật trạng thái (SỬA LẠI ĐOẠN NÀY)

  updateStatus: (id, status) => {
    return axiosClient.patch(`/orders/${id}`, { order_status: status });
  },

  // 4. Các hàm tiện ích khác
  confirmCod: (id) => axiosClient.post(`/orders/${id}/payment/confirm-cod`),
  cancelOrder: (id, reason) => axiosClient.post(`/orders/${id}/cancel`, { reason }),
  getHistory: (id) => axiosClient.get(`/orders/${id}/history`),
  getStats: () => axiosClient.get('/orders/stats/overview'),



  getAlluser: (params) => {
    // URL này nối đuôi vào axiosClient.
    // Nếu axiosClient đã set base là '/api/v1' thì ở đây chỉ cần '/users'
    // Nếu GET hoạt động rồi thì giữ nguyên, không cần sửa đường dẫn này.
    return axiosClient.get('/users', { params });
  },

  // 2. Lấy chi tiết 1 User
  get: (id) => {
    return axiosClient.get(`/users/${id}`);
  },
  getAddresses: (userId) => {
    return axiosClient.get(`/users/${userId}/addresses`);
  },



  getAllReturns: (params) => axiosClient.get('/return_refunds/admin/returns', { params }),
  
  // 2. Đếm số yêu cầu đang chờ xử lý (để hiện số đỏ đỏ trên nút bấm)
  getPendingReturnCount: () => axiosClient.get('/return_refunds/admin/returns/pending/count'),
  
  // 3. Lấy chi tiết 1 yêu cầu (kèm danh sách món hàng trả)
  getReturnDetail: (returnId) => axiosClient.get(`/return_refunds/returns/${returnId}`),
  
  // 4. Duyệt yêu cầu (Approve)
  approveReturn: (returnId) => axiosClient.post(`/return_refunds/admin/returns/${returnId}/approve`),
  
  // 5. Từ chối yêu cầu (Reject) -> Cần lý do
  rejectReturn: (returnId, reason) => axiosClient.post(`/return_refunds/admin/returns/${returnId}/reject`, { reason }),
  
  // 6. Xử lý hoàn tiền (Process Refund) -> Bước cuối cùng sau khi nhận được hàng trả
  processRefund: (refundId) => axiosClient.post(`/return_refunds/admin/refunds/${refundId}/process`),
};

export default orderApi;