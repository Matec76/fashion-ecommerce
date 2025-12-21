import { useState, useCallback } from 'react';

/**
 * useMutation Hook - Xử lý POST, PUT, PATCH, DELETE requests
 * @returns {Object} { mutate, loading, error, data, reset }
 * 
 * @example
 * const { mutate, loading, error } = useMutation();
 * 
 * const handleSubmit = async () => {
 *   const result = await mutate('/api/users', {
 *     method: 'POST',
 *     body: { name: 'John' }
 *   });
 *   if (result.success) {
 *     console.log('Created:', result.data);
 *   }
 * };
 */
const useMutation = () => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [data, setData] = useState(null);

    /**
     * Thực hiện mutation request
     * @param {string} url - API endpoint
     * @param {Object} options - Request options
     * @param {string} options.method - HTTP method (POST, PUT, PATCH, DELETE)
     * @param {Object} options.body - Request body (will be JSON stringified)
     * @param {Object} options.headers - Additional headers
     * @param {boolean} options.auth - Include auth token (default: true)
     * @returns {Promise<{success: boolean, data?: any, error?: string}>}
     */
    const mutate = useCallback(async (url, options = {}) => {
        const {
            method = 'POST',
            body,
            headers = {},
            auth = true
        } = options;

        setLoading(true);
        setError(null);

        try {
            // Build headers
            const requestHeaders = {
                'Content-Type': 'application/json',
                ...headers
            };

            // Add auth token if needed
            if (auth) {
                const token = localStorage.getItem('authToken');
                if (token) {
                    requestHeaders['Authorization'] = `Bearer ${token}`;
                }
            }

            console.log(`🚀 ${method}:`, url);

            const response = await fetch(url, {
                method,
                headers: requestHeaders,
                body: body ? JSON.stringify(body) : undefined
            });

            // Handle 401 Unauthorized
            if (response.status === 401) {
                localStorage.removeItem('authToken');
                setError('Phiên đăng nhập hết hạn');
                return { success: false, error: 'Phiên đăng nhập hết hạn', status: 401 };
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

                console.error(`❌ ${method} failed:`, errorMessage);
                setError(errorMessage);
                return { success: false, error: errorMessage, status: response.status };
            }

            console.log(`✅ ${method} success:`, url);
            setData(responseData);
            return { success: true, data: responseData, status: response.status };

        } catch (err) {
            console.error(`💥 ${method} error:`, err);
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
