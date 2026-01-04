// src/utils/roles.js

export const ROLE_POLICIES = {
    1: ["*"], 
    2: ["*"], 
    // (Ẩn Tổng quan, Ẩn Khách hàng, Không Cấu hình)
    3: [
        "product.view", 
        "inventory.view", 
        "order.view", 
        // "user.view" <--- Đã XÓA dòng này để ẩn menu Khách hàng
    ],
    4: [
        "product.view", 
        "marketing.view", 
        "analytics.view", 
        "cms.manage",
        "system.manage"
    ],
    5: [
        "order.view", 
        "user.view",     // CSKH vẫn cần xem khách
        "product.view", 
        "inventory.view", 
        "system.manage"
    ]
};

export const hasPermission = (roleId, requiredPermission) => {
    // Menu không yêu cầu quyền thì luôn hiện
    if (!requiredPermission) return true;

    const id = parseInt(roleId);
    
    // Admin (1) và Quản lý (2) thấy TẤT CẢ
    if (id === 1 || id === 2) return true; 

    // 1. Kiểm tra quyền từ Server (LocalStorage)
    try {
        const storedPerms = localStorage.getItem('permissions');
        if (storedPerms) {
            const dynamicPermissions = JSON.parse(storedPerms);
            if (Array.isArray(dynamicPermissions) && dynamicPermissions.length > 0) {
                if (dynamicPermissions.includes(requiredPermission)) return true;
            }
        }
    } catch (e) { console.error("RBAC Error:", e); }

    // 2. Dùng bảng quyền cứng ROLE_POLICIES
    const allowedPermissions = ROLE_POLICIES[id] || [];
    return allowedPermissions.includes(requiredPermission);
};