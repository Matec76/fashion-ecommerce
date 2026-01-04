import axios from 'axios';

const axiosClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL, 
  
  headers: {
    'Content-Type': 'application/json',
  },
});

// --- INTERCEPTOR REQUEST (Giữ nguyên) ---
axiosClient.interceptors.request.use(async (config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// --- INTERCEPTOR RESPONSE ---
axiosClient.interceptors.response.use((response) => {
  return response.data; 
}, (error) => {
  if (error.response && error.response.status === 401) {
      console.warn("Token hết hạn hoặc không hợp lệ. Đang đăng xuất...");
      localStorage.clear();
      window.location.href = '/admin/login';
  }
  throw error;
});

export default axiosClient;