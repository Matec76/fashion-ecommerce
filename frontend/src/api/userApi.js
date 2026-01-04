import axiosClient from './axiosClient';

const userApi = {
  // 1. Lấy danh sách Users
  getAll: (params) => {
    return axiosClient.get('/users', { params });
  },

  // 2. Lấy chi tiết 1 User
  get: (id) => {
    return axiosClient.get(`/users/${id}`);
  },

  // 3. Tạo mới User
  create: (data) => {
    return axiosClient.post('/users', data);
  },

  // 4. Cập nhật User (QUAN TRỌNG: Dùng PATCH theo Swagger)
  update: (id, data) => {
    return axiosClient.patch(`/users/${id}`, data);
  },
  delete: (id, params) => {
    // - Endpoint DELETE /users/{user_id}
    return axiosClient.delete(`/users/${id}`, { params });
  }
};

export default userApi;