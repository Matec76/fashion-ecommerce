from sqlmodel import Session, create_engine, select

from app import crud
from app.core.config import settings
from app.models import User, UserCreate, Role, RoleCreate

# Tạo database engine
engine = create_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    echo=settings.ENVIRONMENT == "local",  # Hiển thị SQL queries trong môi trường local
    pool_pre_ping=True,  # Xác minh kết nối trước khi sử dụng
    pool_size=5,  # Số lượng kết nối duy trì trong pool
    max_overflow=10,  # Số lượng kết nối tối đa
    pool_recycle=3600,  # Tái kết nối sau 1 giờ
)

def init_db(session: Session) -> None:
    # Tạo các Role mặc định
    print("Đang tạo các role mặc định...")
    
    # Kiểm tra và tạo Admin role
    admin_role = session.exec(
        select(Role).where(Role.role_name == "Admin")
    ).first()
    if not admin_role:
        admin_role_in = RoleCreate(
            role_name="Admin",
            description="Quản trị viên có quyền truy cập đầy đủ tất cả chức năng"
        )
        admin_role = crud.create_role(session=session, role_create=admin_role_in)
        print("✓ Đã tạo role Admin")
    else:
        print("✓ Role Admin đã tồn tại")

    # Kiểm tra và tạo Customer role
    customer_role = session.exec(
        select(Role).where(Role.role_name == "Customer")
    ).first()
    if not customer_role:
        customer_role_in = RoleCreate(
            role_name="Customer",
            description="Khách hàng thông thường có quyền truy cập các chức năng mua sắm"
        )
        customer_role = crud.create_role(session=session, role_create=customer_role_in)
        print("✓ Đã tạo role Customer")
    else:
        print("✓ Role Customer đã tồn tại")

    # Kiểm tra và tạo Staff role
    staff_role = session.exec(
        select(Role).where(Role.role_name == "Staff")
    ).first()
    if not staff_role:
        staff_role_in = RoleCreate(
            role_name="Staff",
            description="Nhân viên có quyền quản lý đơn hàng và kho hàng"
        )
        staff_role = crud.create_role(session=session, role_create=staff_role_in)
        print("✓ Đã tạo role Staff")
    else:
        print("✓ Role Staff đã tồn tại")

    # Tạo Superuser đầu tiên
    print("\nĐang tạo tài khoản superuser...")
    
    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            first_name=settings.FIRST_SUPERUSER_FIRSTNAME,
            last_name=settings.FIRST_SUPERUSER_LASTNAME,
            is_superuser=True,
            is_active=True,
            is_email_verified=True,
            role_id=admin_role.role_id if admin_role else None,
        )
        user = crud.create_user(session=session, user_create=user_in)
        print(f"✓ Đã tạo superuser: {settings.FIRST_SUPERUSER}")
    else:
        print(f"✓ Superuser đã tồn tại: {settings.FIRST_SUPERUSER}")

    # Tạo các Permission mặc định
    print("\nĐang tạo các quyền hạn mặc định...")
    
    default_permissions = [
        # Quản lý người dùng
        {"name": "users:read", "description": "Xem người dùng", "module": "users"},
        {"name": "users:create", "description": "Tạo người dùng", "module": "users"},
        {"name": "users:update", "description": "Cập nhật người dùng", "module": "users"},
        {"name": "users:delete", "description": "Xóa người dùng", "module": "users"},
        
        # Quản lý sản phẩm
        {"name": "products:read", "description": "Xem sản phẩm", "module": "products"},
        {"name": "products:create", "description": "Tạo sản phẩm", "module": "products"},
        {"name": "products:update", "description": "Cập nhật sản phẩm", "module": "products"},
        {"name": "products:delete", "description": "Xóa sản phẩm", "module": "products"},
        
        # Quản lý đơn hàng
        {"name": "orders:read", "description": "Xem đơn hàng", "module": "orders"},
        {"name": "orders:read_all", "description": "Xem tất cả đơn hàng", "module": "orders"},
        {"name": "orders:update", "description": "Cập nhật đơn hàng", "module": "orders"},
        {"name": "orders:cancel", "description": "Hủy đơn hàng", "module": "orders"},
        
        # Quản lý kho hàng
        {"name": "inventory:read", "description": "Xem kho hàng", "module": "inventory"},
        {"name": "inventory:update", "description": "Cập nhật kho hàng", "module": "inventory"},
        
        # Quản lý danh mục
        {"name": "categories:read", "description": "Xem danh mục", "module": "categories"},
        {"name": "categories:create", "description": "Tạo danh mục", "module": "categories"},
        {"name": "categories:update", "description": "Cập nhật danh mục", "module": "categories"},
        {"name": "categories:delete", "description": "Xóa danh mục", "module": "categories"},
        
        # Quản lý mã giảm giá
        {"name": "coupons:read", "description": "Xem mã giảm giá", "module": "coupons"},
        {"name": "coupons:create", "description": "Tạo mã giảm giá", "module": "coupons"},
        {"name": "coupons:update", "description": "Cập nhật mã giảm giá", "module": "coupons"},
        {"name": "coupons:delete", "description": "Xóa mã giảm giá", "module": "coupons"},
        
        # Quản lý đánh giá
        {"name": "reviews:read", "description": "Xem đánh giá", "module": "reviews"},
        {"name": "reviews:moderate", "description": "Kiểm duyệt đánh giá", "module": "reviews"},
        {"name": "reviews:delete", "description": "Xóa đánh giá", "module": "reviews"},
        
        # Quản lý đổi trả/hoàn tiền
        {"name": "returns:read", "description": "Xem yêu cầu đổi trả", "module": "returns"},
        {"name": "returns:process", "description": "Xử lý đổi trả", "module": "returns"},
        
        # Báo cáo & Phân tích
        {"name": "reports:read", "description": "Xem báo cáo", "module": "reports"},
        {"name": "analytics:read", "description": "Xem phân tích", "module": "analytics"},
        
        # Cấu hình hệ thống
        {"name": "settings:read", "description": "Xem cấu hình", "module": "settings"},
        {"name": "settings:update", "description": "Cập nhật cấu hình", "module": "settings"},
    ]
    
    from app.models import Permission, PermissionCreate
    
    created_count = 0
    for perm_data in default_permissions:
        existing = session.exec(
            select(Permission).where(Permission.permission_name == perm_data["name"])
        ).first()
        
        if not existing:
            perm_in = PermissionCreate(
                permission_name=perm_data["name"],
                description=perm_data["description"],
                module=perm_data["module"]
            )
            crud.create_permission(session=session, permission_create=perm_in)
            created_count += 1
    
    if created_count > 0:
        print(f"✓ Đã tạo {created_count} quyền hạn")
    else:
        print("✓ Tất cả quyền hạn đã tồn tại")

    # Gán quyền cho Admin Role
    print("\nĐang gán quyền hạn cho role Admin...")
    
    if admin_role:
        # Lấy tất cả permissions
        all_permissions = session.exec(select(Permission)).all()
        
        from app.models import RolePermission, RolePermissionCreate
        
        assigned_count = 0
        for permission in all_permissions:
            # Kiểm tra permission đã được gán chưa
            existing = session.exec(
                select(RolePermission).where(
                    RolePermission.role_id == admin_role.role_id,
                    RolePermission.permission_id == permission.permission_id
                )
            ).first()
            
            if not existing:
                role_perm_in = RolePermissionCreate(
                    role_id=admin_role.role_id,
                    permission_id=permission.permission_id
                )
                crud.create_role_permission(session=session, role_permission_create=role_perm_in)
                assigned_count += 1
        
        if assigned_count > 0:
            print(f"✓ Đã gán {assigned_count} quyền hạn cho role Admin")
        else:
            print("✓ Tất cả quyền hạn đã được gán cho role Admin")

    # Tạo System Settings mặc định
    print("\nĐang tạo cấu hình hệ thống mặc định...")
    
    from app.models import SystemSetting, SystemSettingCreate
    
    default_settings = [
        {
            "key": "site_name",
            "value": settings.PROJECT_NAME,
            "type": "string",
            "description": "Tên website",
            "is_public": True
        },
        {
            "key": "site_email",
            "value": str(settings.EMAILS_FROM_EMAIL) if settings.EMAILS_FROM_EMAIL else "",
            "type": "string",
            "description": "Email liên hệ",
            "is_public": True
        },
        {
            "key": "currency_code",
            "value": settings.CURRENCY_CODE,
            "type": "string",
            "description": "Mã tiền tệ mặc định",
            "is_public": True
        },
        {
            "key": "tax_rate",
            "value": str(settings.TAX_RATE),
            "type": "number",
            "description": "Thuế VAT (thập phân)",
            "is_public": True
        },
        {
            "key": "free_shipping_threshold",
            "value": str(settings.FREE_SHIPPING_THRESHOLD),
            "type": "number",
            "description": "Giá trị đơn hàng tối thiểu để được miễn phí vận chuyển",
            "is_public": True
        },
        {
            "key": "enable_reviews",
            "value": str(settings.FEATURE_REVIEWS).lower(),
            "type": "boolean",
            "description": "Bật tính năng đánh giá sản phẩm",
            "is_public": True
        },
        {
            "key": "enable_loyalty_points",
            "value": str(settings.FEATURE_LOYALTY_POINTS).lower(),
            "type": "boolean",
            "description": "Bật chương trình điểm thưởng",
            "is_public": True
        },
        {
            "key": "maintenance_mode",
            "value": "false",
            "type": "boolean",
            "description": "Bật chế độ bảo trì",
            "is_public": False
        },
    ]
    
    settings_created = 0
    for setting_data in default_settings:
        existing = session.exec(
            select(SystemSetting).where(SystemSetting.setting_key == setting_data["key"])
        ).first()
        
        if not existing:
            setting_in = SystemSettingCreate(
                setting_key=setting_data["key"],
                setting_value=setting_data["value"],
                setting_type=setting_data["type"],
                description=setting_data["description"],
                is_public=setting_data["is_public"]
            )
            crud.create_system_setting(session=session, setting_create=setting_in)
            settings_created += 1
    
    if settings_created > 0:
        print(f"✓ Đã tạo {settings_created} cấu hình hệ thống")
    else:
        print("✓ Tất cả cấu hình hệ thống đã tồn tại")

    print("\n" + "="*50)
    print("Khởi tạo database hoàn tất!")
    print("="*50)
