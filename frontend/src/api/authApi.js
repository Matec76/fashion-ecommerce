import axiosClient from './axiosClient';

/**
 * Authentication API
 * ------------------
 * Module chuyên xử lý các tác vụ xác thực và định danh người dùng.
 */
const authApi = {
  /**
   * Gửi yêu cầu đăng nhập lên hệ thống.
   * * @param {Object} data - Payload chứa thông tin đăng nhập.
   * @param {string} data.username - Tên đăng nhập hoặc Email (bắt buộc).
   * @param {string} data.password - Mật khẩu (bắt buộc).
   * @returns {Promise} - Trả về Promise chứa Access Token và thông tin User từ Server.
   */
  login: ({ username, password }) => {
    // Endpoint chuẩn theo cấu hình backend của đại ca
    const url = '/auth/login';
    
    // Chuẩn bị dữ liệu dạng application/x-www-form-urlencoded
    // (Chuẩn bắt buộc của OAuth2PasswordRequestForm trong FastAPI)
    const params = new URLSearchParams();
    params.append('username', username); 
    params.append('password', password);

    return axiosClient.post(url, params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });
  }
};

export default authApi;