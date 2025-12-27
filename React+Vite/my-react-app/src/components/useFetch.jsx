import { useState, useEffect, useRef, useCallback } from 'react';

// Tạo cache bên ngoài hook để dữ liệu vẫn còn khi component unmount
const cache = new Map();

/**
 * useFetch Hook - Có xử lý AbortController, Caching và Auth
 * @param {string} url - API endpoint URL
 * @param {Object} options - Fetch options
 * @param {boolean} options.auth - Tự động thêm Authorization header
 * @returns {Object} { data, loading, error, refetch }
 * 
 * @example
 * // Không cần auth
 * const { data, loading } = useFetch('/api/products');
 * 
 * // Cần auth token
 * const { data, refetch } = useFetch('/api/wishlist/me', { auth: true });
 */
const useFetch = (url, options = {}) => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Dùng useRef để lưu abortController, giúp hủy request cũ
    const abortControllerRef = useRef(null);

    const fetchData = useCallback(async (forceUpdate = false) => {
        if (!url) {
            setLoading(false);
            return;
        }

        const { auth = false, ...fetchOptions } = options;

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
        if (cache.has(cacheKey) && !forceUpdate) {
            setData(cache.get(cacheKey));
            setLoading(false);
            console.log('📦 Load from Cache:', url);
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
            console.log('🚀 Fetching:', url);
            const response = await fetch(url, {
                ...fetchOptions,
                signal: controller.signal // Gắn tín hiệu hủy vào fetch
            });

            if (response.status === 401) {
                // Không xóa token ở đây - chỉ báo lỗi
                // Token chỉ nên bị xóa khi đăng xuất hoặc khi endpoint /auth/me trả về 401
                console.warn('401 Unauthorized for:', url);
                setError('Không có quyền truy cập');
                setData(null);
                setLoading(false);
                return;
            }

            if (!response.ok) {
                throw new Error(`HTTP Error: ${response.status}`);
            }

            const result = await response.json();

            // 3. Lưu vào Cache
            cache.set(cacheKey, result);

            setData(result);
        } catch (err) {
            if (err.name === 'AbortError') {
                console.log('🛑 Request cancelled:', url);
            } else {
                console.error(' Fetch error:', err);
                setError(err.message || 'An error occurred');
                setData(null);
            }
        } finally {
            // Chỉ tắt loading nếu request không bị hủy
            if (!controller.signal.aborted) {
                setLoading(false);
            }
        }
    }, [url, options.auth]);

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
        fetchData(true);
    }, [fetchData]);

    return { data, loading, error, refetch };
};

export { useFetch };
export default useFetch;