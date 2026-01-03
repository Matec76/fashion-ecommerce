import { useState, useCallback } from 'react';
import logger from '../utils/logger';

/**
 * useDelete Hook - DELETE requests
 * @returns {Object} { remove, loading, error, reset }
 */
const useDelete = () => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

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

            logger.log('DELETE:', url);

            const response = await fetch(url, {
                method: 'DELETE',
                headers: requestHeaders
            });

            if (response.status === 401) {
                logger.warn('401 Unauthorized for:', url);
                setError('Không có quyền truy cập');
                return { success: false, error: 'Không có quyền truy cập', status: 401 };
            }

            // DELETE thường trả về 204 No Content
            // 404 cũng được coi là thành công vì item đã không tồn tại
            if (response.status === 204 || response.status === 404 || response.ok) {
                logger.log('DELETE success:', url, '(status:', response.status + ')');
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

            logger.error('DELETE failed:', errorMessage);
            setError(errorMessage);
            return { success: false, error: errorMessage, status: response.status };

        } catch (err) {
            logger.error('DELETE error:', err);
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
