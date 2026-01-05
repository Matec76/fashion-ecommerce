from collections.abc import AsyncGenerator
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine,
)
from sqlmodel import SQLModel, text

from app.core.config import settings


def get_engine_config() -> dict:
    base_config = {
        "echo": settings.ENVIRONMENT == "local",
        "future": True,
        "pool_pre_ping": True,
    }
    
    if settings.ENVIRONMENT == "production":
        base_config.update({
            "pool_size": 20,
            "max_overflow": 10,
            "pool_timeout": 30,
            "pool_recycle": 1800,
        })
    elif settings.ENVIRONMENT == "staging":
        base_config.update({
            "pool_size": 10,
            "max_overflow": 20,
            "pool_timeout": 20,
            "pool_recycle": 3600,
        })
    else:
        base_config.update({
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout": 10,
        })
    return base_config


engine: AsyncEngine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    **get_engine_config()
)


async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db() -> None:
    if settings.ENVIRONMENT in ["local"]:
        print(f"Ket noi database: {settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
        print("Dang tai tat ca models...")

        import app.models
        
        async with engine.begin() as conn:
            print("Dang tao tat ca bang...")
            await conn.run_sync(SQLModel.metadata.create_all)
            print("Tao tat ca bang thanh cong")
    else:
        print("Bo qua tao bang trong moi truong production/staging.")
        print("Su dung Alembic migrations: alembic upgrade head")
    
    
    await seed_roles_and_permissions()
    await seed_payment_methods()
    await seed_system_settings()
    await seed_loyalty_tiers()
    await create_first_superuser()


async def drop_all_tables() -> None:
    if settings.ENVIRONMENT == "production":
        raise RuntimeError("Khong the xoa bang trong moi truong production!")
    
    print("CANH BAO: Dang xoa tat ca bang...")
    import app.models  
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        print("Da xoa tat ca bang!")


async def check_db_connection() -> bool:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print("Ket noi database thanh cong")
        return True
    except Exception as e:
        print(f"Ket noi database that bai: {e}")
        return False


async def close_db() -> None:
    print("Dang dong ket noi database...")
    await engine.dispose()
    print("Da dong ket noi database")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_context() -> AsyncIterator[AsyncSession]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_table_names() -> list[str]:
    async with engine.begin() as conn:
        result = await conn.execute(
            text("""
                SELECT tablename 
                FROM pg_catalog.pg_tables 
                WHERE schemaname = 'public'
                ORDER BY tablename
            """)
        )
        return [row[0] for row in result.fetchall()]


async def get_database_info() -> dict:
    async with get_db_context() as db:
        result = await db.execute(text("SELECT version()"))
        version = result.scalar()
        
        result = await db.execute(
            text(f"SELECT pg_size_pretty(pg_database_size('{settings.POSTGRES_DB}'))")
        )
        size = result.scalar()
        
        result = await db.execute(
            text("SELECT count(*) FROM pg_stat_activity WHERE datname = :db"),
            {"db": settings.POSTGRES_DB}
        )
        connections = result.scalar()
        
        pool_size = engine.pool.size() if hasattr(engine.pool, 'size') else 0
        pool_overflow = engine.pool.overflow() if hasattr(engine.pool, 'overflow') else 0
        
        return {
            "database": settings.POSTGRES_DB,
            "host": settings.POSTGRES_SERVER,
            "port": settings.POSTGRES_PORT,
            "version": version,
            "size": size,
            "active_connections": connections,
            "pool_size": pool_size,
            "pool_overflow": pool_overflow,
        }


async def health_check() -> dict:
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1 as health"))
            health = result.scalar()
            
            if health == 1:
                return {
                    "status": "healthy",
                    "database": settings.POSTGRES_DB,
                    "message": "Ket noi database dang hoat dong"
                }
        return {
            "status": "unhealthy",
            "database": settings.POSTGRES_DB,
            "message": "Truy van database that bai"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": settings.POSTGRES_DB,
            "message": f"Ket noi database that bai: {str(e)}"
        }
    
    
async def seed_roles_and_permissions() -> None:
    print("Dang seed roles va permissions...")
    
    async for db in get_db():
        try:
            from app.models.user import Permission, Role, RolePermission
            from sqlalchemy import select
            
            roles_data = [
                {"role_id" : 1,"role_name": "Super Admin", "description": "Quyen truy cap toan bo he thong", "is_active": True},
                {"role_id" : 2,"role_name": "Admin", "description": "Quyen quan tri", "is_active": True},
                {"role_id" : 3,"role_name": "Warehouse Staff", "description": "Nhan vien Kho", "is_active": True},
                {"role_id" : 4,"role_name": "Marketing Staff", "description": "Nhan vien Marketing", "is_active": True},
                {"role_id" : 5,"role_name": "Support Staff", "description": "Nhan vien CSKH", "is_active": True},
                {"role_id" : 2176,"role_name": "Customer", "description": "Khach hang thuong", "is_active": True},
            ]

            for role_data in roles_data:
                result = await db.execute(
                    select(Role).where(Role.role_id == role_data["role_id"])
                )
                existing_role = result.scalar_one_or_none()
                
                if not existing_role:
                    role = Role(**role_data)
                    db.add(role)
                    print(f"  Da tao role: {role_data['role_name']} (ID: {role_data['role_id']})")

            await db.commit()
            
            permissions_data = [
                # --- SẢN PHẨM & KHO (Core) ---
                {"permission_code": "product.view", "permission_name": "Xem sản phẩm", "resource": "product", "action": "view"},
                {"permission_code": "product.create", "permission_name": "Tạo sản phẩm", "resource": "product", "action": "create"},
                {"permission_code": "product.update", "permission_name": "Sửa sản phẩm", "resource": "product", "action": "update"},
                {"permission_code": "product.delete", "permission_name": "Xóa/Ẩn sản phẩm", "resource": "product", "action": "delete"},
                
                {"permission_code": "attribute.manage", "permission_name": "Quản lý Màu/Size", "resource": "attribute", "action": "manage"},
                {"permission_code": "category.manage", "permission_name": "Quản lý Danh mục", "resource": "category", "action": "manage"},
                {"permission_code": "collection.manage", "permission_name": "Quản lý Bộ sưu tập", "resource": "collection", "action": "manage"},
                
                {"permission_code": "inventory.view", "permission_name": "Xem tồn kho", "resource": "inventory", "action": "view"},
                {"permission_code": "inventory.update", "permission_name": "Nhập/Xuất kho", "resource": "inventory", "action": "update"},
                {"permission_code": "warehouse.manage", "permission_name": "Cấu hình Kho bãi", "resource": "warehouse", "action": "manage"},

                # --- ĐƠN HÀNG & VẬN CHUYỂN ---
                {"permission_code": "order.view", "permission_name": "Xem đơn hàng", "resource": "order", "action": "view"},
                {"permission_code": "order.create", "permission_name": "Tạo đơn (POS)", "resource": "order", "action": "create"},
                {"permission_code": "order.update", "permission_name": "Xử lý đơn hàng", "resource": "order", "action": "update"},
                {"permission_code": "order.cancel", "permission_name": "Hủy đơn hàng", "resource": "order", "action": "cancel"},
                {"permission_code": "shipping.manage", "permission_name": "Quản lý Phí/Đơn vị vận chuyển", "resource": "shipping", "action": "manage"},

                # --- TÀI CHÍNH (Payments) ---
                {"permission_code": "payment.view", "permission_name": "Xem giao dịch", "resource": "payment", "action": "view"},
                {"permission_code": "payment.update", "permission_name": "Cập nhật trạng thái thanh toán", "resource": "payment", "action": "update"},
                {"permission_code": "payment.refund", "permission_name": "Hoàn tiền (Refund)", "resource": "payment", "action": "refund"},
                {"permission_code": "payment.config", "permission_name": "Cấu hình cổng thanh toán", "resource": "payment", "action": "config"}, # Mới thêm cho payment_methods.py

                {"permission_code": "return.view", "permission_name": "Xem yêu cầu trả hàng", "resource": "return", "action": "view"},
                {"permission_code": "return.manage", "permission_name": "Xử lý trả hàng", "resource": "return", "action": "manage"},

                # --- USER & KHÁCH HÀNG ---
                {"permission_code": "user.view", "permission_name": "Xem danh sách User", "resource": "user", "action": "view"},
                {"permission_code": "user.create", "permission_name": "Tạo nhân viên", "resource": "user", "action": "create"},
                {"permission_code": "user.update", "permission_name": "Sửa thông tin User", "resource": "user", "action": "update"},
                {"permission_code": "user.delete", "permission_name": "Xóa/Khóa User", "resource": "user", "action": "delete"}, # Đã bổ sung theo yêu cầu

                # --- MARKETING & CMS ---
                {"permission_code": "marketing.view", "permission_name": "Xem chiến dịch Marketing", "resource": "marketing", "action": "view"},
                {"permission_code": "marketing.manage", "permission_name": "Quản lý Coupon/FlashSale", "resource": "marketing", "action": "manage"},
                {"permission_code": "marketing.abandoned_cart", "permission_name": "Xem giỏ hàng quên", "resource": "marketing", "action": "view_abandoned"},
                {"permission_code": "loyalty.manage", "permission_name": "Quản lý Điểm thưởng", "resource": "loyalty", "action": "manage"},
                
                {"permission_code": "review.manage", "permission_name": "Quản lý Đánh giá & Hỏi đáp", "resource": "review", "action": "manage"},
                {"permission_code": "cms.manage", "permission_name": "Quản lý Banner/Menu/Blog", "resource": "cms", "action": "manage"},

                # --- HỆ THỐNG (System) ---
                {"permission_code": "analytics.view", "permission_name": "Xem báo cáo thống kê", "resource": "analytics", "action": "view"},
                {"permission_code": "system.manage", "permission_name": "Cấu hình hệ thống (Settings)", "resource": "system", "action": "manage"},
                {"permission_code": "system.log", "permission_name": "Xem nhật ký hoạt động (Audit)", "resource": "system", "action": "log"},
                {"permission_code": "notification.manage", "permission_name": "Quản lý Email/Thông báo", "resource": "notification", "action": "manage"},
            ]
            
            all_perm_codes = []
            
            for perm_data in permissions_data:
                all_perm_codes.append(perm_data["permission_code"])
                result = await db.execute(
                    select(Permission).where(Permission.permission_code == perm_data["permission_code"])
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    perm = Permission(**perm_data)
                    db.add(perm)
                    print(f"  Da tao permission: {perm_data['permission_code']}")
            
            await db.commit()


            ROLE_POLICIES = {
                1: all_perm_codes,

                2: [
                    c for c in all_perm_codes 
                    if c not in ["system.manage", "system.log"] 
                ],

                3: [
                    "product.view", 
                    "inventory.view", "inventory.update", 
                    "order.view", "order.update", 
                    "return.view", "return.manage"
                ],

                4: [
                    "product.view", "product.update",
                    "category.manage", "collection.manage",
                    "marketing.view", "marketing.manage", "marketing.abandoned_cart", "loyalty.manage",
                    "cms.manage", "review.manage", "analytics.view"
                ],

                5: [
                    "user.view", "user.update",
                    "order.view", "order.create", "order.update", "order.cancel",
                    "product.view", "inventory.view",
                    "payment.view", "return.view", "return.manage", "review.manage"
                ]
            }

            print("  Dang phan quyen cho cac Role...")
            for role_id, perm_codes in ROLE_POLICIES.items():
                stmt = select(Permission).where(Permission.permission_code.in_(perm_codes))
                perms_to_assign = (await db.execute(stmt)).scalars().all()
                
                count = 0
                for perm in perms_to_assign:
                    check = await db.execute(select(RolePermission).where(
                        RolePermission.role_id == role_id,
                        RolePermission.permission_id == perm.permission_id
                    ))
                    if not check.scalar_one_or_none():
                        db.add(RolePermission(role_id=role_id, permission_id=perm.permission_id))
                        count += 1
                
                if count > 0:
                    print(f"    -> Role ID {role_id}: +{count} permissions")

            await db.commit()
            print("Seed roles va permissions thanh cong")
            
        except Exception as e:
            await db.rollback()
            print(f"Loi khi seed roles: {e}")
            import traceback
            traceback.print_exc()
        finally:
            break


async def seed_payment_methods() -> None:
    print("Dang seed payment methods...")
    
    async for db in get_db():
        try:
            from app.models.payment_method import PaymentMethod
            from app.models.enums import ProcessingFeeType
            from sqlalchemy import select
            from decimal import Decimal
            
            payment_methods_data = [
                {
                    "method_code": "COD",
                    "method_name": "Thanh toan khi nhan hang",
                    "description": "Thanh toan bang tien mat khi nhan hang (Cash on Delivery)",
                    "processing_fee": Decimal("0.00"),
                    "processing_fee_type": ProcessingFeeType.FIXED,
                    "is_active": True,
                    "display_order": 1,
                },
                {
                    "method_code": "BANK_TRANSFER",
                    "method_name": "Chuyen khoan Ngan hang (VietQR)",
                    "description": "Thanh toan quet ma QR tu dong qua VietQR (PayOS)",
                    "processing_fee": Decimal("0.00"),
                    "processing_fee_type": ProcessingFeeType.FIXED, 
                    "is_active": True,
                    "display_order": 2,
                },
            ]
            
            for pm_data in payment_methods_data:
                result = await db.execute(
                    select(PaymentMethod).where(PaymentMethod.method_code == pm_data["method_code"])
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    payment_method = PaymentMethod(**pm_data)
                    db.add(payment_method)
                    print(f"  Da tao payment method: {pm_data['method_code']}")
                
            await db.commit()
            print("Seed payment methods thanh cong")
            
        except Exception as e:
            await db.rollback()
            print(f"Loi khi seed payment methods: {e}")
            import traceback
            traceback.print_exc()
        finally:
            break


async def seed_system_settings() -> None:
    print("Dang seed system settings...")
    
    async for db in get_db():
        try:
            from app.models.system import SystemSetting
            from app.models.enums import SettingTypeEnum 
            from sqlalchemy import select
            
            settings_data = [
                # --- Loyalty & Rewards ---
                {"setting_key": "point_expiration_days", "setting_value": "365", "setting_type": SettingTypeEnum.NUMBER, "description": "Thời hạn điểm (ngày)", "is_public": True},
                {"setting_key": "referral_reward_points", "setting_value": "10000", "setting_type": SettingTypeEnum.NUMBER, "description": "Điểm thưởng giới thiệu", "is_public": True},
                {"setting_key": "referee_reward_points", "setting_value": "20000", "setting_type": SettingTypeEnum.NUMBER, "description": "Điểm thưởng người mới", "is_public": True},
                {"setting_key": "loyalty_exchange_rate", "setting_value": "100", "setting_type": SettingTypeEnum.NUMBER, "description": "Tỷ lệ đổi điểm thưởng (100 VNĐ = 1 điểm)", "is_public": True},
                
                {"setting_key": "redeem_limit_bronze", "setting_value": "100000", "setting_type": SettingTypeEnum.NUMBER, "description": "Mức đổi tối đa cho hạng Bronze (VNĐ)", "is_public": True},
                {"setting_key": "redeem_limit_silver", "setting_value": "500000", "setting_type": SettingTypeEnum.NUMBER, "description": "Mức đổi tối đa cho hạng Silver (VNĐ)", "is_public": True},
                {"setting_key": "redeem_limit_gold", "setting_value": "1000000", "setting_type": SettingTypeEnum.NUMBER, "description": "Mức đổi tối đa cho hạng Gold (VNĐ)", "is_public": True},
                {"setting_key": "redeem_limit_diamond", "setting_value": "5000000", "setting_type": SettingTypeEnum.NUMBER, "description": "Mức đổi tối đa cho hạng Diamond (VNĐ)", "is_public": True},
                
                {"setting_key": "redeem_coupon_validity_days", "setting_value": "30", "setting_type": SettingTypeEnum.NUMBER, "description": "Thời hạn sử dụng của mã coupon sau khi đổi (ngày)", "is_public": True},
                {"setting_key": "redeem_point_exchange_rate", "setting_value": "1", "setting_type": SettingTypeEnum.NUMBER, "description": "Giá trị quy đổi: 1 điểm = 1 VNĐ", "is_public": True},

                # --- Shipping & Return ---
                {"setting_key": "free_shipping_threshold", "setting_value": "500000", "setting_type": SettingTypeEnum.NUMBER, "description": "Ngưỡng miễn phí vận chuyển", "is_public": True},
                {"setting_key": "return_window_days", "setting_value": "7", "setting_type": SettingTypeEnum.NUMBER, "description": "Số ngày cho phép đổi trả hàng", "is_public": True},

                # --- Payments ---
                {"setting_key": "payment_method_cod_enabled", "setting_value": "true", "setting_type": SettingTypeEnum.BOOLEAN, "description": "Bật/Tắt thanh toán khi nhận hàng (COD)", "is_public": True},
                {"setting_key": "payment_method_payos_enabled", "setting_value": "true", "setting_type": SettingTypeEnum.BOOLEAN, "description": "Bật/Tắt thanh toán qua PayOS", "is_public": True},

                # --- Cart & Coupon ---
                {"setting_key": "cart_max_item_qty", "setting_value": "99", "setting_type": SettingTypeEnum.NUMBER, "description": "Số lượng tối đa cho 1 sản phẩm trong giỏ hàng", "is_public": False},
                {"setting_key": "max_coupon_usage_per_user", "setting_value": "1", "setting_type": SettingTypeEnum.NUMBER, "description": "Số lần tối đa 1 người được dùng mã giảm giá", "is_public": False},

                # --- Inventory & Product ---
                {"setting_key": "low_stock_threshold", "setting_value": "5", "setting_type": SettingTypeEnum.NUMBER, "description": "Ngưỡng cảnh báo sắp hết hàng", "is_public": False},
                {"setting_key": "featured_products_limit", "setting_value": "12", "setting_type": SettingTypeEnum.NUMBER, "description": "Số lượng sản phẩm nổi bật hiển thị", "is_public": True},
                {"setting_key": "search_min_query_length", "setting_value": "2", "setting_type": SettingTypeEnum.NUMBER, "description": "Độ dài từ khóa tối thiểu để tìm kiếm", "is_public": True},
                {"setting_key": "related_products_limit", "setting_value": "8", "setting_type": SettingTypeEnum.NUMBER, "description": "Số lượng sản phẩm liên quan hiển thị", "is_public": True},

                # --- Marketing / Abandoned Cart ---
                {"setting_key": "abandoned_cart_delay_hours", "setting_value": "2", "setting_type": SettingTypeEnum.NUMBER, "description": "Số giờ sau khi bỏ giỏ hàng để gửi email nhắc nhở", "is_public": False},
                {"setting_key": "max_abandoned_cart_emails", "setting_value": "3", "setting_type": SettingTypeEnum.NUMBER, "description": "Số email nhắc nhở tối đa cho giỏ hàng bị bỏ quên", "is_public": False},

                # --- Contact & Social ---
                {"setting_key": "contact_hotline", "setting_value": "1900 1234", "setting_type": SettingTypeEnum.STRING, "description": "Hotline hỗ trợ khách hàng", "is_public": True},
                {"setting_key": "contact_email", "setting_value": "support@stylex.com.vn", "setting_type": SettingTypeEnum.STRING, "description": "Email hỗ trợ kỹ thuật", "is_public": True},
                {"setting_key": "contact_address", "setting_value": "Tầng 10, Tòa nhà STYLEX, 123 Đường Thời Trang, Hà Nội", "setting_type": SettingTypeEnum.STRING, "description": "Địa chỉ văn phòng", "is_public": True},
                {"setting_key": "social_facebook", "setting_value": "https://facebook.com/yourpage", "setting_type": SettingTypeEnum.STRING, "description": "Link Fanpage Facebook", "is_public": True},
                {"setting_key": "social_instagram", "setting_value": "https://instagram.com/yourpage", "setting_type": SettingTypeEnum.STRING, "description": "Link Instagram", "is_public": True},
                {"setting_key": "social_twitter", "setting_value": "https://twitter.com/yourpage", "setting_type": SettingTypeEnum.STRING, "description": "Link Twitter", "is_public": True},

                # --- System ---
                {"setting_key": "chatbot_enabled", "setting_value": "true", "setting_type": SettingTypeEnum.BOOLEAN, "description": "Bật/Tắt tính năng Chatbot AI", "is_public": True},
                {"setting_key": "maintenance_mode", "setting_value": "false", "setting_type": SettingTypeEnum.BOOLEAN, "description": "Bật chế độ bảo trì (Tắt web)", "is_public": True},
            ]
            
            count_new = 0
            for setting in settings_data:
                stmt = select(SystemSetting).where(SystemSetting.setting_key == setting["setting_key"])
                existing = (await db.execute(stmt)).scalar_one_or_none()
                
                if not existing:
                    new_setting = SystemSetting(**setting)
                    db.add(new_setting)
                    count_new += 1
            
            if count_new > 0:
                await db.commit()
                print(f"Seed system settings thanh cong: +{count_new} keys moi")
            else:
                print("System settings da day du, khong can seed them.")
            
        except Exception as e:
            await db.rollback()
            print(f"Loi khi seed settings: {e}")
        finally:
            break


async def seed_loyalty_tiers() -> None:
    print("Dang seed loyalty tiers...")
    
    async for db in get_db():
        try:
            from app.models.loyalty import LoyaltyTier
            from sqlalchemy import select
            from decimal import Decimal
            
            tiers_data = [
                {
                    "tier_name": "Bronze",
                    "min_points": 0,
                    "discount_percentage": Decimal("0.00"),
                    "benefits": "Thành viên mới. Tích điểm đổi quà.",
                    "is_active": True
                },
                {
                    "tier_name": "Silver",
                    "min_points": 100000,
                    "discount_percentage": Decimal("2.00"),
                    "benefits": "Giảm 2% trực tiếp. Ưu tiên hỗ trợ.",
                    "is_active": True
                },
                {
                    "tier_name": "Gold",
                    "min_points": 500000,
                    "discount_percentage": Decimal("5.00"),
                    "benefits": "Giảm 5% trực tiếp. Quà sinh nhật. Freeship.",
                    "is_active": True
                },
                {
                    "tier_name": "Diamond",
                    "min_points": 1000000,
                    "discount_percentage": Decimal("10.00"),
                    "benefits": "Giảm 10% trực tiếp. Hotline riêng. Quà đặc biệt.",
                    "is_active": True
                }
            ]
            
            for tier_data in tiers_data:
                stmt = select(LoyaltyTier).where(LoyaltyTier.tier_name == tier_data["tier_name"])
                existing = (await db.execute(stmt)).scalar_one_or_none()
                
                if not existing:
                    tier = LoyaltyTier(**tier_data)
                    db.add(tier)
                    print(f"  Da tao tier: {tier_data['tier_name']}")
            
            await db.commit()
            print("Seed loyalty tiers thanh cong")
            
        except Exception as e:
            await db.rollback()
            print(f"Loi khi seed loyalty tiers: {e}")
        finally:
            break


async def create_first_superuser() -> None:
    print(f"Kiem tra superuser ton tai: {settings.FIRST_SUPERUSER}")
    
    async for db in get_db():
        try:
            from app.models.user import User
            from app.core.security import get_password_hash
            from sqlalchemy import select
            
            result = await db.execute(
                select(User).where(User.email == settings.FIRST_SUPERUSER)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"  Superuser da ton tai: {existing_user.email}")
                return
            
            SUPER_ADMIN_ROLE_ID = 1
            
            print(f"  Dang tao superuser dau tien: {settings.FIRST_SUPERUSER}")
            
            superuser = User(
                email=settings.FIRST_SUPERUSER,
                hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
                first_name=settings.FIRST_SUPERUSER_FIRSTNAME,
                last_name=settings.FIRST_SUPERUSER_LASTNAME,
                role_id=SUPER_ADMIN_ROLE_ID,
                is_active=True,
                is_superuser=True,
                is_email_verified=True,
            )
            
            db.add(superuser)
            await db.commit()
            await db.refresh(superuser)
            
            print(f"Tao superuser thanh cong")
            print(f"  Email: {superuser.email}")
            print(f"  Role ID: {superuser.role_id}")
            
        except Exception as e:
            print(f"Loi khi tao superuser: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
        finally:
            break
    
    
__all__ = [
    "engine",
    "async_session_maker",
    "get_db",
    "get_db_context",
    "init_db",
    "drop_all_tables",
    "check_db_connection",
    "close_db",
    "get_table_names",
    "get_database_info",
    "health_check",
    "seed_roles_and_permissions",
    "seed_payment_methods",
    "seed_system_settings",
    "seed_loyalty_tiers",
    "create_first_superuser",
]