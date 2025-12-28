import { useState, useCallback } from 'react';
import logger from '../utils/logger';

/**
 * usePatch Hook - PATCH requests
 * @returns {Object} { patch, loading, error, data, reset }
 */
const usePatch = () => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [data, setData] = useState(null);

    const patch = useCallback(async (url, body, options = {}) => {
        const { headers = {}, auth = true } = options;

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

            logger.log('PATCH:', url);

            const response = await fetch(url, {
                method: 'PATCH',
                headers: requestHeaders,
                body: body ? JSON.stringify(body) : undefined
            });

            if (response.status === 401) {
                logger.warn('401 Unauthorized for:', url);
                setError('Không có quyền truy cập');
                return { success: false, error: 'Không có quyền truy cập', status: 401 };
            }

            let responseData = null;
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                responseData = await response.json();
            }

            if (!response.ok) {
                let errorMessage = 'Không thể cập nhật';
                if (responseData) {
                    if (typeof responseData.detail === 'string') {
                        errorMessage = responseData.detail;
                    } else if (Array.isArray(responseData.detail)) {
                        errorMessage = responseData.detail.map(e => e.msg).join(', ');
                    }
                }
                logger.error('PATCH failed:', errorMessage);
                setError(errorMessage);
                return { success: false, error: errorMessage, status: response.status };
            }

            logger.log('PATCH success:', url);
            setData(responseData);
            return { success: true, data: responseData, status: response.status };

        } catch (err) {
            logger.error('PATCH error:', err);
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
        setData(null);
    }, []);

    return { patch, loading, error, data, reset };
};

export default usePatch;
