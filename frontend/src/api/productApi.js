import axiosClient from './axiosClient';

const productApi = {
  // --- SẢN PHẨM ---
  getAll: (params) => axiosClient.get('/products', { params }),
  get: (id) => axiosClient.get(`/products/${id}`),
  add: (data) => axiosClient.post('/products', data),
  update: (id, data) => axiosClient.patch(`/products/${id}`, data),
  remove: (id) => axiosClient.delete(`/products/${id}`, { params: { permanent: true } }),

  // --- ẢNH (CHUẨN) ---
  getImages: (productId) => axiosClient.get(`/products/${productId}/images`),

  uploadFile: (file) => {
    const formData = new FormData();
    formData.append('file', file); 
    return axiosClient.post('/products/upload-image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  addImageToProduct: (productId, imageUrl) => {
    return axiosClient.post(`/products/${productId}/images`, {
      product_id: productId,
      image_url: imageUrl,
      alt_text: "Ảnh sản phẩm",
      display_order: 0,
      is_primary: false,
      variant_id: null 
    });
  },

  //  HÀM XÓA
  deleteImage: (imageId) => {
    return axiosClient.delete(`/products/images/${imageId}`);
  },

  setPrimaryImage: (imageId) => {
    return axiosClient.post(`/products/images/${imageId}/set-primary`);
  },


  getCategories: () => axiosClient.get('/categories'), // Lấy danh sách
  createCategory: (data) => axiosClient.post('/categories', data), // Tạo mới
  deleteCategory: (id) => axiosClient.delete(`/categories/${id}`), // Xóa


  getCollections: () => axiosClient.get(`/categories/collections/all?_t=${Date.now()}`),
  
  createCollection: (data) => axiosClient.post('/categories/collections', data),
  
  deleteCollection: (id) => axiosClient.delete(`/categories/collections/${id}`)
};

export default productApi;