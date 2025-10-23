from enum import Enum


class GenderEnum(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class AddressTypeEnum(str, Enum):
    SHIPPING = "shipping"
    BILLING = "billing"
    BOTH = "both"


class SizeTypeEnum(str, Enum):
    SHOES = "shoes"
    CLOTHING = "clothing"
    ACCESSORIES = "accessories"


class ProductGenderEnum(str, Enum):
    MEN = "men"
    WOMEN = "women"
    UNISEX = "unisex"
    KIDS = "kids"


class OrderStatusEnum(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatusEnum(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class DiscountTypeEnum(str, Enum):
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"


class InventoryChangeEnum(str, Enum):
    IMPORT = "import"
    SALE = "sale"
    RETURN = "return"
    ADJUSTMENT = "adjustment"
    DAMAGED = "damaged"


class ReturnReasonEnum(str, Enum):
    DEFECTIVE = "defective"
    WRONG_ITEM = "wrong_item"
    SIZE_ISSUE = "size_issue"
    CHANGED_MIND = "changed_mind"
    OTHER = "other"


class ReturnStatusEnum(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROCESSING = "processing"
    COMPLETED = "completed"


class RefundMethodEnum(str, Enum):
    ORIGINAL_PAYMENT = "original_payment"
    STORE_CREDIT = "store_credit"
    BANK_TRANSFER = "bank_transfer"


class ItemConditionEnum(str, Enum):
    UNOPENED = "unopened"
    USED = "used"
    DAMAGED = "damaged"


class LoyaltyTransactionEnum(str, Enum):
    EARN_PURCHASE = "earn_purchase"
    EARN_REVIEW = "earn_review"
    EARN_REFERRAL = "earn_referral"
    REDEEM = "redeem"
    EXPIRE = "expire"
    ADJUSTMENT = "adjustment"


class NotificationTypeEnum(str, Enum):
    ORDER = "order"
    PROMOTION = "promotion"
    SYSTEM = "system"
    REVIEW = "review"


class EmailTypeEnum(str, Enum):
    WELCOME = "welcome"
    ORDER_CONFIRMATION = "order_confirmation"
    SHIPPING = "shipping"
    PROMOTION = "promotion"
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFICATION = "email_verification"
    ABANDONED_CART = "abandoned_cart"


class EmailStatusEnum(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class SettingTypeEnum(str, Enum):
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    JSON = "json"


class AdminActionEnum(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
