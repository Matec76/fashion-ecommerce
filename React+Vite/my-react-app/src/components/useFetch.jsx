import { useState, useEffect, useRef } from 'react';

// Tạo cache bên ngoài hook để dữ liệu vẫn còn khi component unmount
const cache = new Map();

/**
 * useFetch Hook - Có xử lý AbortController và Caching
 * @param {string} url - API endpoint URL
 * @param {Object} options - Fetch options
 * @returns {Object} { data, loading, error, refetch }
 */
const useFetch = (url, options = {}) => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Dùng useRef để lưu abortController, giúp hủy request cũ
    const abortControllerRef = useRef(null);

    const fetchData = async (forceUpdate = false) => {
        if (!url) return;

        // 1. Nếu có trong cache và không bắt buộc tải lại -> Lấy từ cache ngay lập tức
        if (cache.has(url) && !forceUpdate) {
            setData(cache.get(url));
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
                ...options,
                signal: controller.signal // Gắn tín hiệu hủy vào fetch
            });

            if (!response.ok) {
                throw new Error(`HTTP Error: ${response.status}`);
            }

            const result = await response.json();

            // 3. Lưu vào Cache
            cache.set(url, result);

            setData(result);
        } catch (err) {
            if (err.name === 'AbortError') {
                console.log('🛑 Request cancelled:', url);
            } else {
                console.error('❌ Fetch error:', err);
                setError(err.message || 'An error occurred');
                setData(null);
            }
        } finally {
            // Chỉ tắt loading nếu request không bị hủy
            if (!controller.signal.aborted) {
                setLoading(false);
            }
        }
    };

    useEffect(() => {
        fetchData();

        // Cleanup: Khi component unmount hoặc url đổi, hủy request đang chạy
        return () => {
            if (abortControllerRef.current) {
                abortControllerRef.current.abort();
            }
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [url]);

    // Hàm reload cưỡng ép (bỏ qua cache)
    const refetch = () => {
        fetchData(true);
    };

    return { data, loading, error, refetch };
};

export default useFetch;