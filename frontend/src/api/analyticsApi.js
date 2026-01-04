import axiosClient from './axiosClient';

const analyticsApi = {

  getDashboardStats: () => {
    return axiosClient.get('/analytics/dashboard');
  },

  getSalesReport: (params) => {
    return axiosClient.get('/analytics/sales', { params });
  },


  getMostViewedProducts: () => {
    return axiosClient.get('/analytics/most-viewed-products');
  }
};

export default analyticsApi;