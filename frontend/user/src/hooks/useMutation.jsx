import { useState, useCallback } from 'react';
import logger from '../utils/logger';

/**
 * useMutation Hook - POST, PUT, PATCH, DELETE requests
 * @returns {Object} { mutate, loading, error, data, reset }
 */
const useMutation = () => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [data, setData] = useState(null);

    const mutate = useCallback(async (url, options = {}) => {
        const { method = 'POST', body, headers = {}, auth = true } = options;

        setLoading(true);
        setError(null);

        try {
            const requestHeaders = {
                'Content-Type': 'application/json',
                ...headers
            };

            if (auth) {
                const token = localStorage.getItem('authToken');
                if (token) {
                    requestHeaders['Authorization'] = `Bearer ${token}`;
                }
            }

            logger.log(`${method}:`, url);

            const response = await fetch(url, {
                method,
                headers: requestHeaders,
                body: body ? JSON.stringify(body) : undefined
            });

            // Handle 401 Unauthorized - Chỉ báo lỗi, không xóa token
            if (response.status === 401) {
                logger.warn('401 Unauthorized for:', url);
                setError('Không có quyền truy cập');
                return { success: false, error: 'Không có quyền truy cập', status: 401 };
            }

            // Parse response
            let responseData = null;
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                responseData = await response.json();
            }

            if (!response.ok) {
                // Parse error message
                let errorMessage = 'Có lỗi xảy ra';
                if (responseData) {
                    if (typeof responseData.detail === 'string') {
                        errorMessage = responseData.detail;
                    } else if (Array.isArray(responseData.detail)) {
                        errorMessage = responseData.detail.map(e =>
                            `${e.loc?.join('→') || 'Field'}: ${e.msg}`
                        ).join(', ');
                    } else if (responseData.message) {
                        errorMessage = responseData.message;
                    }
                }

                logger.error(`${method} failed:`, errorMessage);
                setError(errorMessage);
                return { success: false, error: errorMessage, status: response.status };
            }

            logger.log(`${method} success:`, url);
            setData(responseData);
            return { success: true, data: responseData, status: response.status };

        } catch (err) {
            logger.error(`${method} error:`, err);
            const errorMessage = err.message || 'Lỗi kết nối server';
            setError(errorMessage);
            return { success: false, error: errorMessage };
        } finally {
            setLoading(false);
        }
    }, []);

    // Reset state
    const reset = useCallback(() => {
        setLoading(false);
        setError(null);
        setData(null);
    }, []);

    return { mutate, loading, error, data, reset };
};

export default useMutation;
