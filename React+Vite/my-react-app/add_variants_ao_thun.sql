-- BƯỚC 1: Kiểm tra variant_id hiện tại cao nhất
-- Đảm bảo sequence bắt đầu từ ID đúng

-- BƯỚC 2: Reset sequence để tránh conflict
SELECT setval('product_variants_variant_id_seq', (SELECT COALESCE(MAX(variant_id), 0) FROM product_variants));

-- BƯỚC 3: Thêm variants cho "Áo Thun 3 Sọc" (product_id = 2)
-- Màu: Đen (1), Trắng (2), Xanh Navy (3)
-- Size: S (1), M (2), L (3), XL (4)

INSERT INTO product_variants 
(product_id, sku, color_id, size_id, stock_quantity, low_stock_threshold, weight, is_available, created_at, updated_at) 
VALUES
-- Màu Đen
(2, 'AO-THUN-3SOC-BLACK-S',  1, 1, 20, 5, 0.30, true, NOW(), NOW()),
(2, 'AO-THUN-3SOC-BLACK-M',  1, 2, 25, 5, 0.30, true, NOW(), NOW()),
(2, 'AO-THUN-3SOC-BLACK-L',  1, 3, 30, 5, 0.30, true, NOW(), NOW()),
(2, 'AO-THUN-3SOC-BLACK-XL', 1, 4, 15, 5, 0.30, true, NOW(), NOW()),

-- Màu Trắng
(2, 'AO-THUN-3SOC-WHITE-S',  2, 1, 18, 5, 0.30, true, NOW(), NOW()),
(2, 'AO-THUN-3SOC-WHITE-M',  2, 2, 22, 5, 0.30, true, NOW(), NOW()),
(2, 'AO-THUN-3SOC-WHITE-L',  2, 3, 28, 5, 0.30, true, NOW(), NOW()),
(2, 'AO-THUN-3SOC-WHITE-XL', 2, 4, 12, 5, 0.30, true, NOW(), NOW()),

-- Màu Xanh Navy
(2, 'AO-THUN-3SOC-NAVY-S',   3, 1, 15, 5, 0.30, true, NOW(), NOW()),
(2, 'AO-THUN-3SOC-NAVY-M',   3, 2, 20, 5, 0.30, true, NOW(), NOW()),
(2, 'AO-THUN-3SOC-NAVY-L',   3, 3, 25, 5, 0.30, true, NOW(), NOW()),
(2, 'AO-THUN-3SOC-NAVY-XL',  3, 4, 10, 5, 0.30, true, NOW(), NOW());

-- BƯỚC 4: Kiểm tra kết quả
SELECT 
    pv.variant_id,
    pv.sku,
    c.color_name,
    s.size_name,
    pv.stock_quantity
FROM product_variants pv
LEFT JOIN colors c ON pv.color_id = c.color_id
LEFT JOIN sizes s ON pv.size_id = s.size_id
WHERE pv.product_id = 2
ORDER BY c.color_id, s.size_id;
