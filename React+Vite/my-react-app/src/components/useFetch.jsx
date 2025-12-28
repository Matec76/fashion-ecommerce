import { useState, useEffect, useRef, useCallback } from 'react';
import logger from '../utils/logger';

// Cache bên ngoài hook - persist khi component unmount
const cache = new Map();

/**
 * useFetch Hook - AbortController, Caching, Auth
 * @param {string} url - API endpoint
 * @param {Object} options - { auth, skipCache, ...fetchOptions }
 * @returns {Object} { data, loading, error, refetch }
 */
const useFetch = (url, options = {}) => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const abortControllerRef = useRef(null);

    const fetchData = useCallback(async (forceUpdate = false) => {
        if (!url) {
            setLoading(false);
            return;
        }

        const { auth = false, skipCache = false, ...fetchOptions } = options;

        // Kiểm tra auth
        if (auth) {
            const token = localStorage.getItem('authToken');
            if (!token) {
                setError('Chưa đăng nhập');
                setLoading(false);
                return;
            }
            fetchOptions.headers = {
                ...fetchOptions.headers,
                'Authorization': `Bearer ${token}`
            };
        }

        // 1. Nếu có trong cache và không bắt buộc tải lại -> Lấy từ cache ngay lập tức
        const cacheKey = auth ? `${url}:auth` : url;

        // Clear cache if force update is requested or skipCache is enabled
        if ((forceUpdate || skipCache) && cache.has(cacheKey)) {
            cache.delete(cacheKey);
            logger.log('Cache cleared for:', url);
        }

        // Skip cache check entirely if skipCache is enabled
        if (cache.has(cacheKey) && !forceUpdate && !skipCache) {
            setData(cache.get(cacheKey));
            setLoading(false);
            logger.log('Load from Cache:', url);
            return;
        }

        // 2. Hủy request cũ nếu đang chạy (Tránh Race Condition)
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }

        // Tạo controller mới cho request này
        const controller = new AbortController();
        abortControllerRef.current = controller;

        setLoading(true);
        setError(null);

        try {
            logger.log('Fetching:', url);

            // Build headers - add cache control only when skipCache is enabled
            const headers = {
                ...fetchOptions.headers,
                ...(skipCache && {
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                })
            };

            const response = await fetch(url, {
                ...fetchOptions,
                headers,
                signal: controller.signal // Gắn tín hiệu hủy vào fetch
            });

            if (response.status === 401) {
                // Không xóa token ở đây - chỉ báo lỗi
                // Token chỉ nên bị xóa khi đăng xuất hoặc khi endpoint /auth/me trả về 401
                logger.warn('401 Unauthorized for:', url);
                setError('Không có quyền truy cập');
                setData(null);
                setLoading(false);
                return;
            }

            if (!response.ok) {
                throw new Error(`HTTP Error: ${response.status}`);
            }

            const result = await response.json();

            // 3. Lưu vào Cache (chỉ khi không skipCache)
            if (!skipCache) {
                cache.set(cacheKey, result);
            }

            setData(result);
        } catch (err) {
            if (err.name === 'AbortError') {
                logger.log('Request cancelled:', url);
            } else {
                logger.error('Fetch error:', err);
                setError(err.message || 'An error occurred');
                setData(null);
            }
        } finally {
            // Chỉ tắt loading nếu request không bị hủy
            if (!controller.signal.aborted) {
                setLoading(false);
            }
        }
    }, [url, options.auth, options.skipCache]);

    useEffect(() => {
        fetchData();

        // Cleanup: Khi component unmount hoặc url đổi, hủy request đang chạy
        return () => {
            if (abortControllerRef.current) {
                abortControllerRef.current.abort();
            }
        };
    }, [url, fetchData]);

    // Hàm reload cưỡng ép (bỏ qua cache)
    const refetch = useCallback(() => {
        return fetchData(true);
    }, [fetchData]);

    return { data, loading, error, refetch };
};

export { useFetch };
export default useFetch;