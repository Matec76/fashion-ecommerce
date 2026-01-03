import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import logger from '../utils/logger';

// Cache bên ngoài hook - persist khi component unmount
const cache = new Map();

/**
 * useFetch Hook - AbortController, Caching, Auth, TTL
 * @param {string} url - API endpoint
 * @param {Object} options - { auth, skipCache, cacheTime, ...fetchOptions }
 *   - auth: boolean - Require authentication token
 *   - skipCache: boolean - Always fetch fresh data, never use cache
 *   - cacheTime: number - Cache TTL in milliseconds (default: infinite, 0 = no cache)
 * @returns {Object} { data, loading, error, refetch }
 */
const useFetch = (url, options = {}) => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const abortControllerRef = useRef(null);

    // ✅ OPTIMIZATION: Serialize options to prevent unnecessary re-fetches
    const optionsKey = useMemo(() => JSON.stringify(options), [
        options.auth,
        options.skipCache,
        options.cacheTime,
        JSON.stringify(options.headers || {}),
        options.method
    ]);

    const fetchData = useCallback(async (forceUpdate = false) => {
        if (!url) {
            setLoading(false);
            return;
        }

        const opts = JSON.parse(optionsKey);
        const { auth = false, skipCache = false, cacheTime, ...fetchOptions } = opts;

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

        // 1. Cache key và kiểm tra cache với TTL
        const cacheKey = auth ? `${url}:auth` : url;

        // Clear cache if force update is requested or skipCache is enabled
        if ((forceUpdate || skipCache) && cache.has(cacheKey)) {
            cache.delete(cacheKey);
            logger.log('Cache cleared for:', url);
        }

        // Check cache with TTL support
        if (cache.has(cacheKey) && !forceUpdate && !skipCache) {
            const cachedEntry = cache.get(cacheKey);
            const now = Date.now();

            // Check if cache has expired based on cacheTime
            if (cacheTime !== undefined && cacheTime > 0) {
                const isCacheValid = (now - cachedEntry.timestamp) < cacheTime;
                if (isCacheValid) {
                    setData(cachedEntry.data);
                    setLoading(false);
                    logger.log('Load from TTL Cache:', url, `(age: ${now - cachedEntry.timestamp}ms)`);
                    return;
                } else {
                    // Cache expired, delete it
                    cache.delete(cacheKey);
                    logger.log('Cache expired for:', url);
                }
            } else if (cacheTime === 0) {
                // cacheTime = 0 means no cache
                cache.delete(cacheKey);
            } else {
                // No cacheTime specified, use cache indefinitely (backward compatibility)
                const data = cachedEntry.data !== undefined ? cachedEntry.data : cachedEntry;
                setData(data);
                setLoading(false);
                logger.log('Load from Infinite Cache:', url);
                return;
            }
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

            // 3. Lưu vào Cache với timestamp (chỉ khi không skipCache)
            if (!skipCache) {
                cache.set(cacheKey, {
                    data: result,
                    timestamp: Date.now()
                });
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
    }, [url, optionsKey]);

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