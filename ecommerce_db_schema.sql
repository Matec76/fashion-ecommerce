-- ECMOMMERCE DATABASE SCHEMA

-- CUSTOM DATA TYPES
CREATE TYPE gender_enum AS ENUM ('male', 'female', 'other');
CREATE TYPE address_type_enum AS ENUM ('shipping', 'billing', 'both');
CREATE TYPE size_type_enum AS ENUM ('shoes', 'clothing', 'accessories');
CREATE TYPE product_gender_enum AS ENUM ('men', 'women', 'unisex', 'kids');
CREATE TYPE order_status_enum AS ENUM ('pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded');
CREATE TYPE payment_status_enum AS ENUM ('pending', 'paid', 'failed', 'refunded');
CREATE TYPE discount_type_enum AS ENUM ('percentage', 'fixed_amount');
CREATE TYPE inventory_change_enum AS ENUM ('import', 'sale', 'return', 'adjustment', 'damaged');
CREATE TYPE return_reason_enum AS ENUM ('defective', 'wrong_item', 'size_issue', 'changed_mind', 'other');
CREATE TYPE return_status_enum AS ENUM ('pending', 'approved', 'rejected', 'processing', 'completed');
CREATE TYPE refund_method_enum AS ENUM ('original_payment', 'store_credit', 'bank_transfer');
CREATE TYPE item_condition_enum AS ENUM ('unopened', 'used', 'damaged');
CREATE TYPE loyalty_transaction_enum AS ENUM ('earn_purchase', 'earn_review', 'earn_referral', 'redeem', 'expire', 'adjustment');
CREATE TYPE notification_type_enum AS ENUM ('order', 'promotion', 'system', 'review');
CREATE TYPE email_type_enum AS ENUM ('welcome', 'order_confirmation', 'shipping', 'promotion', 'password_reset');
CREATE TYPE email_status_enum AS ENUM ('pending', 'sent', 'failed');
CREATE TYPE setting_type_enum AS ENUM ('string', 'number', 'boolean', 'json');
CREATE TYPE admin_action_enum AS ENUM ('create', 'update', 'delete', 'login', 'logout', 'export');


-- TABLE DEFINITIONS


-- 1. AUTHENTICATION & AUTHORIZATION

-- Bảng Roles (Vai trò)
CREATE TABLE roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bảng Permissions (Quyền hạn)
CREATE TABLE permissions (
    permission_id SERIAL PRIMARY KEY,
    permission_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    module VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bảng Role_Permissions (Quyền của từng vai trò)
CREATE TABLE role_permissions (
    role_permission_id SERIAL PRIMARY KEY,
    role_id INT NOT NULL REFERENCES roles(role_id) ON DELETE CASCADE,
    permission_id INT NOT NULL REFERENCES permissions(permission_id) ON DELETE CASCADE,
    UNIQUE (role_id, permission_id)
);

-- Bảng Users (Người dùng)
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    date_of_birth DATE,
    gender gender_enum,
    role_id INT DEFAULT 1 REFERENCES roles(role_id),
    is_active BOOLEAN DEFAULT true,
    is_email_verified BOOLEAN DEFAULT false,
    email_verification_token VARCHAR(255),
    password_reset_token VARCHAR(255),
    password_reset_expires TIMESTAMPTZ,
    loyalty_points INT DEFAULT 0,
    last_login TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bảng Addresses (Địa chỉ)
CREATE TABLE addresses (
    address_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    address_type address_type_enum DEFAULT 'shipping',
    street_address VARCHAR(255) NOT NULL,
    ward VARCHAR(100),
    district VARCHAR(100),
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) DEFAULT 'Vietnam',
    postal_code VARCHAR(20),
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. PRODUCT CATALOG

-- Bảng Categories (Danh mục sản phẩm)
CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL,
    parent_category_id INT REFERENCES categories(category_id) ON DELETE SET NULL,
    slug VARCHAR(100) UNIQUE,
    description TEXT,
    image_url VARCHAR(255),
    display_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bảng Colors (Màu sắc)
CREATE TABLE colors (
    color_id SERIAL PRIMARY KEY,
    color_name VARCHAR(50) UNIQUE NOT NULL,
    color_code VARCHAR(7) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bảng Sizes (Kích cỡ)
CREATE TABLE sizes (
    size_id SERIAL PRIMARY KEY,
    size_value VARCHAR(20) UNIQUE NOT NULL,
    size_type size_type_enum NOT NULL,
    display_order INT DEFAULT 0
);

-- Bảng Products (Sản phẩm)
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE,
    description TEXT,
    category_id INT REFERENCES categories(category_id) ON DELETE SET NULL,
    brand VARCHAR(100) DEFAULT 'Adidas',
    collection VARCHAR(100),
    gender product_gender_enum,
    base_price DECIMAL(10, 2) NOT NULL,
    sale_price DECIMAL(10, 2),
    cost_price DECIMAL(10, 2),
    is_featured BOOLEAN DEFAULT false,
    is_new_arrival BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    view_count INT DEFAULT 0,
    sold_count INT DEFAULT 0,
    meta_title VARCHAR(255),
    meta_description TEXT,
    meta_keywords VARCHAR(255),
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bảng Product_Variants (Biến thể sản phẩm)
CREATE TABLE product_variants (
    variant_id SERIAL PRIMARY KEY,
    product_id INT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    sku VARCHAR(100) UNIQUE NOT NULL,
    color_id INT REFERENCES colors(color_id) ON DELETE SET NULL,
    size_id INT REFERENCES sizes(size_id) ON DELETE SET NULL,
    stock_quantity INT DEFAULT 0,
    low_stock_threshold INT DEFAULT 5,
    weight DECIMAL(8, 2),
    is_available BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bảng Product_Images (Hình ảnh sản phẩm)
CREATE TABLE product_images (
    image_id SERIAL PRIMARY KEY,
    product_id INT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    variant_id INT REFERENCES product_variants(variant_id) ON DELETE CASCADE,
    image_url VARCHAR(255) NOT NULL,
    alt_text VARCHAR(255),
    display_order INT DEFAULT 0,
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bảng Product_Collections (Bộ sưu tập sản phẩm)
CREATE TABLE product_collections (
    collection_id SERIAL PRIMARY KEY,
    collection_name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE,
    description TEXT,
    image_url VARCHAR(255),
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT true,
    display_order INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bảng Collection_Products (Sản phẩm trong bộ sưu tập)
CREATE TABLE collection_products (
    collection_product_id SERIAL PRIMARY KEY,
    collection_id INT NOT NULL REFERENCES product_collections(collection_id) ON DELETE CASCADE,
    product_id INT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    display_order INT DEFAULT 0,
    UNIQUE (collection_id, product_id)
);

-- 3. SHOPPING CART

-- Bảng Cart (Giỏ hàng)
CREATE TABLE cart (
    cart_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    session_id VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bảng Cart_Items (Sản phẩm trong giỏ hàng)
CREATE TABLE cart_items (
    cart_item_id SERIAL PRIMARY KEY,
    cart_id INT NOT NULL REFERENCES cart(cart_id) ON DELETE CASCADE,
    variant_id INT NOT NULL REFERENCES product_variants(variant_id) ON DELETE CASCADE,
    quantity INT NOT NULL DEFAULT 1,
    added_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bảng Abandoned_Carts (Giỏ hàng bỏ quên)
CREATE TABLE abandoned_carts (
    abandoned_id SERIAL PRIMARY KEY,
    cart_id INT NOT NULL REFERENCES cart(cart_id) ON DELETE CASCADE,
    user_id INT REFERENCES users(user_id) ON DELETE SET NULL,
    email VARCHAR(255),
    total_items INT,
    total_value DECIMAL(10, 2),
    email_sent_count INT DEFAULT 0,
    last_email_sent TIMESTAMPTZ,
    recovered BOOLEAN DEFAULT false,
    recovered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. ORDERS & PAYMENTS

-- Bảng Shipping_Methods (Phương thức vận chuyển)
CREATE TABLE shipping_methods (
    shipping_method_id SERIAL PRIMARY KEY,
    method_name VARCHAR(100) NOT NULL,
    description TEXT,
    base_cost DECIMAL(10, 2) NOT NULL,
    estimated_days VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bảng Orders (Đơn hàng)
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id),
    order_number VARCHAR(50) UNIQUE NOT NULL,
    order_status order_status_enum DEFAULT 'pending',
    payment_status payment_status_enum DEFAULT 'pending',
    payment_method VARCHAR(50),
    subtotal DECIMAL(10, 2) NOT NULL,
    shipping_fee DECIMAL(10, 2) DEFAULT 0,
    discount_amount DECIMAL(10, 2) DEFAULT 0,
    tax_amount DECIMAL(10, 2) DEFAULT 0,
    total_amount DECIMAL(10, 2) NOT NULL,
    shipping_address_id INT REFERENCES addresses(address_id),
    billing_address_id INT REFERENCES addresses(address_id),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bảng Order_Items (Sản phẩm trong đơn hàng)
CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    variant_id INT NOT NULL REFERENCES product_variants(variant_id),
    product_name VARCHAR(255) NOT NULL,
    sku VARCHAR(100),
    color VARCHAR(50),
    size VARCHAR(20),
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL
);

-- Bảng Payment_Transactions (Giao dịch thanh toán)
CREATE TABLE payment_transactions (
    transaction_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    transaction_code VARCHAR(100) UNIQUE,
    payment_method VARCHAR(50) NOT NULL,
    payment_gateway VARCHAR(50),
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'VND',
    status payment_status_enum DEFAULT 'pending',
    gateway_response TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bảng Order_Status_History (Lịch sử trạng thái đơn hàng)
CREATE TABLE order_status_history (
    history_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    old_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    comment TEXT,
    changed_by INT REFERENCES users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. PROMOTIONS & COUPONS

-- Bảng Coupons (Mã giảm giá)
CREATE TABLE coupons (
    coupon_id SERIAL PRIMARY KEY,
    coupon_code VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255),
    discount_type discount_type_enum NOT NULL,
    discount_value DECIMAL(10, 2) NOT NULL,
    min_purchase_amount DECIMAL(10, 2) DEFAULT 0,
    max_discount_amount DECIMAL(10, 2),
    usage_limit INT,
    used_count INT DEFAULT 0,
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bảng Order_Coupons (Mã giảm giá đã sử dụng)
CREATE TABLE order_coupons (
    order_coupon_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    coupon_id INT NOT NULL REFERENCES coupons(coupon_id)
);

-- Bảng Flash_Sales (Flash sale)
CREATE TABLE flash_sales (
    flash_sale_id SERIAL PRIMARY KEY,
    sale_name VARCHAR(100) NOT NULL,
    description TEXT,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    discount_type discount_type_enum NOT NULL,
    discount_value DECIMAL(10, 2) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bảng Flash_Sale_Products (Sản phẩm trong flash sale)
CREATE TABLE flash_sale_products (
    flash_sale_product_id SERIAL PRIMARY KEY,
    flash_sale_id INT NOT NULL REFERENCES flash_sales(flash_sale_id) ON DELETE CASCADE,
    product_id INT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    quantity_limit INT,
    quantity_sold INT DEFAULT 0,
    UNIQUE (flash_sale_id, product_id)
);

-- 6. REVIEWS & RATINGS

-- Bảng Reviews (Đánh giá sản phẩm)
CREATE TABLE reviews (
    review_id SERIAL PRIMARY KEY,
    product_id INT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    order_id INT REFERENCES orders(order_id) ON DELETE SET NULL,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    title VARCHAR(255),
    comment TEXT,
    is_verified_purchase BOOLEAN DEFAULT false,
    is_approved BOOLEAN DEFAULT false,
    helpful_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bảng Review_Images (Hình ảnh đánh giá)
CREATE TABLE review_images (
    review_image_id SERIAL PRIMARY KEY,
    review_id INT NOT NULL REFERENCES reviews(review_id) ON DELETE CASCADE,
    image_url VARCHAR(255) NOT NULL,
    display_order INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bảng Review_Helpful (Đánh dấu review hữu ích)
CREATE TABLE review_helpful (
    review_helpful_id SERIAL PRIMARY KEY,
    review_id INT NOT NULL REFERENCES reviews(review_id) ON DELETE CASCADE,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, review_id)
);

-- Bảng Product_Questions (Hỏi đáp sản phẩm)
CREATE TABLE product_questions (
    question_id SERIAL PRIMARY KEY,
    product_id INT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    answer TEXT,
    answered_by INT REFERENCES users(user_id) ON DELETE SET NULL,
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    answered_at TIMESTAMPTZ
);

-- 7. WISHLIST & FAVORITES

-- Bảng Wishlist (Danh sách yêu thích)
CREATE TABLE wishlist (
    wishlist_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    product_id INT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    added_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, product_id)
);

-- 8. INVENTORY MANAGEMENT

-- Bảng Inventory_Logs (Lịch sử thay đổi tồn kho)
CREATE TABLE inventory_logs (
    log_id SERIAL PRIMARY KEY,
    variant_id INT NOT NULL REFERENCES product_variants(variant_id) ON DELETE CASCADE,
    change_type inventory_change_enum NOT NULL,
    quantity_change INT NOT NULL,
    quantity_before INT NOT NULL,
    quantity_after INT NOT NULL,
    reference_type VARCHAR(50),
    reference_id INT,
    note TEXT,
    created_by INT REFERENCES users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 9. RETURNS & REFUNDS

-- Bảng Return_Requests (Yêu cầu đổi/trả hàng)
CREATE TABLE return_requests (
    return_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    return_reason return_reason_enum NOT NULL,
    reason_detail TEXT,
    images TEXT,
    status return_status_enum DEFAULT 'pending',
    refund_amount DECIMAL(10, 2),
    refund_method refund_method_enum,
    admin_note TEXT,
    processed_by INT REFERENCES users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bảng Return_Items (Sản phẩm trong yêu cầu đổi/trả)
CREATE TABLE return_items (
    return_item_id SERIAL PRIMARY KEY,
    return_id INT NOT NULL REFERENCES return_requests(return_id) ON DELETE CASCADE,
    order_item_id INT NOT NULL REFERENCES order_items(order_item_id) ON DELETE CASCADE,
    quantity INT NOT NULL,
    condition_received item_condition_enum DEFAULT 'unopened'
);

-- 10. LOYALTY & REWARDS

-- Bảng Loyalty_Transactions (Lịch sử điểm thưởng)
CREATE TABLE loyalty_transactions (
    transaction_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    points_change INT NOT NULL,
    transaction_type loyalty_transaction_enum NOT NULL,
    reference_type VARCHAR(50),
    reference_id INT,
    description VARCHAR(255),
    balance_before INT NOT NULL,
    balance_after INT NOT NULL,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 11. ANALYTICS & TRACKING

-- Bảng Product_Views (Lịch sử xem sản phẩm)
CREATE TABLE product_views (
    view_id BIGSERIAL PRIMARY KEY,
    product_id INT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    user_id INT REFERENCES users(user_id) ON DELETE SET NULL,
    session_id VARCHAR(255),
    ip_address VARCHAR(45),
    user_agent TEXT,
    viewed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bảng Search_History (Lịch sử tìm kiếm)
CREATE TABLE search_history (
    search_id BIGSERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE SET NULL,
    session_id VARCHAR(255),
    search_query VARCHAR(255) NOT NULL,
    result_count INT DEFAULT 0,
    clicked_product_id INT REFERENCES products(product_id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 12. NOTIFICATIONS & COMMUNICATIONS

-- Bảng Notifications (Thông báo)
CREATE TABLE notifications (
    notification_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    notification_type notification_type_enum NOT NULL,
    reference_id INT,
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bảng Email_Queue (Hàng đợi email)
CREATE TABLE email_queue (
    email_id SERIAL PRIMARY KEY,
    recipient_email VARCHAR(255) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    email_type email_type_enum NOT NULL,
    status email_status_enum DEFAULT 'pending',
    attempts INT DEFAULT 0,
    error_message TEXT,
    scheduled_at TIMESTAMPTZ DEFAULT NOW(),
    sent_at TIMESTAMPTZ
);

-- 13. CMS & MARKETING

-- Bảng Banner_Slides (Banner quảng cáo)
CREATE TABLE banner_slides (
    banner_id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    subtitle VARCHAR(255),
    image_url VARCHAR(255) NOT NULL,
    mobile_image_url VARCHAR(255),
    link_url VARCHAR(255),
    link_text VARCHAR(100),
    display_order INT DEFAULT 0,
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true,
    click_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 14. SYSTEM & ADMINISTRATION

-- Bảng System_Settings (Cấu hình hệ thống)
CREATE TABLE system_settings (
    setting_id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type setting_type_enum DEFAULT 'string',
    description TEXT,
    is_public BOOLEAN DEFAULT false,
    updated_by INT REFERENCES users(user_id) ON DELETE SET NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bảng Admin_Activity_Logs (Lịch sử hoạt động admin)
CREATE TABLE admin_activity_logs (
    log_id BIGSERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    action_type admin_action_enum NOT NULL,
    table_name VARCHAR(50),
    record_id INT,
    old_value TEXT,
    new_value TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);