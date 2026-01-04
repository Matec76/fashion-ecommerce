// src/api/inventoryApi.js
import axiosClient from './axiosClient';

const inventoryApi = {
  // --- 1. QUẢN LÝ KHO (CRUD) ---
  // (Khớp với ảnh Swagger Warehouse đại ca gửi)
  
  getAll: (params) => {
    return axiosClient.get('/warehouse', { params });
  },

  create: (data) => {
    return axiosClient.post('/warehouse', data);
  },

  get: (id) => {
    return axiosClient.get(`/warehouse/${id}`);
  },

  update: (id, data) => {
    // Swagger ghi là PATCH, nên mình dùng PATCH
    return axiosClient.patch(`/warehouse/${id}`, data);
  },

  delete: (id) => {
    return axiosClient.delete(`/warehouse/${id}`);
  },

  setAsDefault: (id) => {
    return axiosClient.post(`/warehouse/${id}/set-default`);
  },

  // --- 2. QUẢN LÝ GIAO DỊCH (NHẬP/XUẤT) ---
  
  getTransactions: (params) => {
    return axiosClient.get('/inventory/transactions', { params });
  },


  createTransaction: (data) => {
    return axiosClient.post('/inventory/adjust', data);
  }
};

export default inventoryApi;