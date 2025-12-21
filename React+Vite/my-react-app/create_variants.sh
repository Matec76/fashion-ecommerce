# Script to create product variants for "Áo Thun 3 Sọc" (product_id = 2)
# Màu: 1=Đen, 2=Trắng, 3=Xám
# Size: 1=S, 2=M, 3=L, 4=XL

# Màu Đen + Size S
curl -X POST "http://localhost:8000/api/v1/products/2/variants" -H "Content-Type: application/json" -d "{\"product_id\":2,\"sku\":\"AO-THUN-BLACK-S\",\"color_id\":1,\"size_id\":1,\"stock_quantity\":20,\"price_adjustment\":0,\"is_available\":true}"

# Màu Đen + Size M
curl -X POST "http://localhost:8000/api/v1/products/2/variants" -H "Content-Type: application/json" -d "{\"product_id\":2,\"sku\":\"AO-THUN-BLACK-M\",\"color_id\":1,\"size_id\":2,\"stock_quantity\":25,\"price_adjustment\":0,\"is_available\":true}"

# Màu Đen + Size L
curl -X POST "http://localhost:8000/api/v1/products/2/variants" -H "Content-Type: application/json" -d "{\"product_id\":2,\"sku\":\"AO-THUN-BLACK-L\",\"color_id\":1,\"size_id\":3,\"stock_quantity\":30,\"price_adjustment\":0,\"is_available\":true}"

# Màu Đen + Size XL
curl -X POST "http://localhost:8000/api/v1/products/2/variants" -H "Content-Type: application/json" -d "{\"product_id\":2,\"sku\":\"AO-THUN-BLACK-XL\",\"color_id\":1,\"size_id\":4,\"stock_quantity\":15,\"price_adjustment\":0,\"is_available\":true}"

# Màu Trắng + Size S
curl -X POST "http://localhost:8000/api/v1/products/2/variants" -H "Content-Type: application/json" -d "{\"product_id\":2,\"sku\":\"AO-THUN-WHITE-S\",\"color_id\":2,\"size_id\":1,\"stock_quantity\":18,\"price_adjustment\":0,\"is_available\":true}"

# Màu Trắng + Size M
curl -X POST "http://localhost:8000/api/v1/products/2/variants" -H "Content-Type: application/json" -d "{\"product_id\":2,\"sku\":\"AO-THUN-WHITE-M\",\"color_id\":2,\"size_id\":2,\"stock_quantity\":22,\"price_adjustment\":0,\"is_available\":true}"

# Màu Trắng + Size L
curl -X POST "http://localhost:8000/api/v1/products/2/variants" -H "Content-Type: application/json" -d "{\"product_id\":2,\"sku\":\"AO-THUN-WHITE-L\",\"color_id\":2,\"size_id\":3,\"stock_quantity\":28,\"price_adjustment\":0,\"is_available\":true}"

# Màu Trắng + Size XL
curl -X POST "http://localhost:8000/api/v1/products/2/variants" -H "Content-Type: application/json" -d "{\"product_id\":2,\"sku\":\"AO-THUN-WHITE-XL\",\"color_id\":2,\"size_id\":4,\"stock_quantity\":12,\"price_adjustment\":0,\"is_available\":true}"

# Verify
echo "Checking created variants..."
curl "http://localhost:8000/api/v1/products/2/variants"
