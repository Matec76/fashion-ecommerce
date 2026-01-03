from app.crud.base import CRUDBase

from app.crud.user import CRUDUser, user
from app.crud.role import (
    CRUDRole,
    CRUDPermission,
    CRUDRolePermission,
    role,
    permission,
    role_permission,
)
from app.crud.address import CRUDAddress, address

from app.crud.attribute import (
    CRUDColor,
    CRUDSize,
    color,
    size,
)

from app.crud.category import (
    CRUDCategory,
    CRUDProductCollection,
    CRUDCollectionProduct,
    category,
    product_collection,
    collection_product,
)

from app.crud.product import (
    CRUDProduct,
    CRUDProductVariant,
    CRUDProductImage,
    product,
    product_variant,
    product_image,
)

from app.crud.cart import (
    CRUDCart,
    CRUDCartItem,
    CRUDAbandonedCart,
    cart,
    cart_item,
    abandoned_cart,
)

from app.crud.order import (
    CRUDOrder,
    CRUDOrderItem,
    CRUDOrderStatusHistory,
    CRUDShippingMethod,
    order,
    order_item,
    order_status_history,
    shipping_method,
)

from app.crud.payment import (
    CRUDPaymentTransaction,
    payment_transaction,
)

from app.crud.payment_method import (
    CRUDPaymentMethod,
    payment_method,
)

from app.crud.coupon import (
    CRUDCoupon,
    CRUDOrderCoupon,
    CRUDFlashSale,
    CRUDFlashSaleProduct,
    coupon,
    order_coupon,
    flash_sale,
    flash_sale_product,
)

from app.crud.review import (
    CRUDProductQuestion,
    product_question,
)

from app.crud.wishlist import (
    CRUDWishlist,
    CRUDWishlistItem,
    wishlist,
    wishlist_item,
)

from app.crud.notification import (
    CRUDNotification,
    CRUDEmailQueue,
    notification,
    email_queue,
)

from app.crud.cms import (
    CRUDBannerSlide,
    CRUDPage,
    CRUDMenu,
    CRUDMenuItem,
    banner_slide,
    page,
    menu,
    menu_item,
)

from app.crud.system import (
    CRUDSystemSetting,
    system_setting,
)

from app.crud.inventory import (
    CRUDInventoryTransaction,
    CRUDVariantStock,
    CRUDStockAlert,
    inventory_transaction,
    variant_stock,
    stock_alert,
)

from app.crud.loyalty import (
    CRUDLoyaltyTier,
    CRUDLoyaltyPoint,
    CRUDPointTransaction,
    CRUDReferral,
    loyalty_tier_crud,
    loyalty_point_crud,
    point_transaction_crud,
    referral_crud,
)

from app.crud.return_refund import (
    CRUDReturnRequest,
    CRUDReturnItem,
    CRUDRefundTransaction,
    return_request_crud,
    return_item_crud,
    refund_transaction_crud,
)

from app.crud.warehouse import (
    CRUDWarehouse,
    warehouse,
)

__all__ = [
    # Base
    "CRUDBase",
    # User
    "CRUDUser",
    "user",
    "CRUDRole",
    "CRUDPermission",
    "CRUDRolePermission",
    "role",
    "permission",
    "role_permission",
    "CRUDAddress",
    "address",
    # Attributes
    "CRUDColor",
    "CRUDSize",
    "color",
    "size",
    # Categories
    "CRUDCategory",
    "CRUDProductCollection",
    "CRUDCollectionProduct",
    "category",
    "product_collection",
    "collection_product",
    # Products
    "CRUDProduct",
    "CRUDProductVariant",
    "CRUDProductImage",
    "product",
    "product_variant",
    "product_image",
    # Cart
    "CRUDCart",
    "CRUDCartItem",
    "CRUDAbandonedCart",
    "cart",
    "cart_item",
    "abandoned_cart",
    # Orders
    "CRUDOrder",
    "CRUDOrderItem",
    "CRUDOrderStatusHistory",
    "CRUDShippingMethod",
    "order",
    "order_item",
    "order_status_history",
    "shipping_method",
    # Payment
    "CRUDPaymentTransaction",
    "payment_transaction",
    # Payment Methods
    "CRUDPaymentMethod",
    "payment_method",
    # Coupons
    "CRUDCoupon",
    "CRUDOrderCoupon",
    "CRUDFlashSale",
    "CRUDFlashSaleProduct",
    "coupon",
    "order_coupon",
    "flash_sale",
    "flash_sale_product",
    # Reviews
    "CRUDProductQuestion",
    "product_question",
    # Wishlist
    "CRUDWishlist",
    "CRUDWishlistItem",
    "wishlist",
    "wishlist_item",
    # Notifications
    "CRUDNotification",
    "CRUDEmailQueue",
    "notification",
    "email_queue",
    # CMS
    "CRUDBannerSlide",
    "CRUDPage",
    "CRUDMenu",
    "CRUDMenuItem",
    "banner_slide",
    "page",
    "menu",
    "menu_item",
    # System
    "CRUDSystemSetting",
    "system_setting",
    # Inventory
    "CRUDInventoryTransaction",
    "CRUDVariantStock",
    "CRUDStockAlert",
    "inventory_transaction",
    "variant_stock",
    "stock_alert",
    # Loyalty
    "CRUDLoyaltyTier",
    "CRUDLoyaltyPoint",
    "CRUDPointTransaction",
    "CRUDReferral",
    "loyalty_tier_crud",
    "loyalty_point_crud",
    "point_transaction_crud",
    "referral_crud",
    # Return & Refund
    "CRUDReturnRequest",
    "CRUDReturnItem",
    "CRUDRefundTransaction",
    "return_request_crud",
    "return_item_crud",
    "refund_transaction_crud",
    # Warehouse
    "CRUDWarehouse",
    "warehouse",
]