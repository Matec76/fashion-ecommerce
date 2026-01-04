import axiosClient from './axiosClient';

const contentApi = {
  //  QUẢN LÝ TRANG (PAGES)
  getAll: (params) => axiosClient.get('/cms/pages', { params }),
  get: (id) => axiosClient.get(`/cms/pages/${id}`),
  create: (data) => axiosClient.post('/cms/pages', data),
  update: (id, data) => axiosClient.patch(`/cms/pages/${id}`, data),
  remove: (id) => axiosClient.delete(`/cms/pages/${id}`),
  publish: (id) => axiosClient.post(`/cms/pages/${id}/publish`),
  unpublish: (id) => axiosClient.post(`/cms/pages/${id}/unpublish`),

  // BANNER & UPLOAD 
  
  // Upload ảnh (Giữ nguyên header như bên Product cho chắc ăn)
  uploadFile: (file) => {
      const formData = new FormData();
      formData.append('file', file); 
      return axiosClient.post('/cms/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
      });
  },

  //  QUAN TRỌNG: Thêm ?_t=... để ép trình duyệt không dùng Cache cũ
  getBanners: () => axiosClient.get(`/cms/banners?_t=${Date.now()}`),
  
  createBanner: (data) => axiosClient.post('/cms/banners', data),
  updateBanner: (id, data) => axiosClient.patch(`/cms/banners/${id}`, data),
  deleteBanner: (id) => axiosClient.delete(`/cms/banners/${id}`),
};

export default contentApi;