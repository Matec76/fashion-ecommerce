import { useState, useCallback } from 'react';

/**
 * useDelete Hook - Chuyên xử lý DELETE requests (xóa dữ liệu)
 * @returns {Object} { remove, loading, error, reset }
 * 
 * @example
 * const { remove, loading, error } = useDelete();
 * 
 * const handleDelete = async () => {
 *   const result = await remove('/api/users/1');
 *   if (result.success) {
 *     console.log('Deleted successfully');
 *   }
 * };
 */
const useDelete = () => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    /**
     * Thực hiện DELETE request
     * @param {string} url - API endpoint
     * @param {Object} options - Additional options
     * @returns {Promise<{success: boolean, error?: string}>}
     */
    const remove = useCallback(async (url, options = {}) => {
        const { headers = {}, auth = true } = options;

        setLoading(true);
        setError(null);

        try {
            const requestHeaders = { ...headers };

            if (auth) {
                const token = localStorage.getItem('authToken');
                if (token) {
                    requestHeaders['Authorization'] = `Bearer ${token}`;
                }
            }

            console.log('🗑️ DELETE:', url);

            const response = await fetch(url, {
                method: 'DELETE',
                headers: requestHeaders
            });

            if (response.status === 401) {
                localStorage.removeItem('authToken');
                setError('Phiên đăng nhập hết hạn');
                return { success: false, error: 'Phiên đăng nhập hết hạn', status: 401 };
            }

            // DELETE thường trả về 204 No Content
            if (response.status === 204 || response.ok) {
                console.log('✅ DELETE success:', url);
                return { success: true, status: response.status };
            }

            // Parse error response
            let responseData = null;
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                responseData = await response.json();
            }

            let errorMessage = 'Không thể xóa';
            if (responseData) {
                if (typeof responseData.detail === 'string') {
                    errorMessage = responseData.detail;
                } else if (Array.isArray(responseData.detail)) {
                    errorMessage = responseData.detail.map(e => e.msg).join(', ');
                }
            }

            console.error('❌ DELETE failed:', errorMessage);
            setError(errorMessage);
            return { success: false, error: errorMessage, status: response.status };

        } catch (err) {
            console.error('💥 DELETE error:', err);
            const errorMessage = err.message || 'Lỗi kết nối server';
            setError(errorMessage);
            return { success: false, error: errorMessage };
        } finally {
            setLoading(false);
        }
    }, []);

    const reset = useCallback(() => {
        setLoading(false);
        setError(null);
    }, []);

    return { remove, loading, error, reset };
};

export default useDelete;
