from enum import Enum


class GenderEnum(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class AddressTypeEnum(str, Enum):
    SHIPPING = "SHIPPING"
    BILLING = "BILLING"
    BOTH = "BOTH"


class SizeTypeEnum(str, Enum):
    SHOES = "SHOES"
    CLOTHING = "CLOTHING"
    ACCESSORIES = "ACCESSORIES"


class ProductGenderEnum(str, Enum):
    MEN = "MEN"
    WOMEN = "WOMEN"
    UNISEX = "UNISEX"
    KIDS = "KIDS"


class OrderStatusEnum(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"
    PARTIAL_REFUNDED = "PARTIAL_REFUNDED"
    RETURN_REQUESTED = "RETURN_REQUESTED"
    COMPLETED = "COMPLETED"


class PaymentStatusEnum(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PAID = "PAID"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED" 
    EXPIRED = "EXPIRED"
    REFUNDED = "REFUNDED"
    PARTIAL_REFUNDED = "PARTIAL_REFUNDED"


class ProcessingFeeType(str, Enum):
    FIXED = "FIXED"
    PERCENTAGE = "PERCENTAGE" 


class PaymentMethodType(str, Enum):
    COD = "COD"          
    BANK_TRANSFER = "BANK_TRANSFER"


class DiscountTypeEnum(str, Enum):
    PERCENTAGE = "PERCENTAGE"
    FIXED_AMOUNT = "FIXED_AMOUNT"


class InventoryChangeEnum(str, Enum):
    IMPORT = "IMPORT"
    SALE = "SALE"
    RETURN = "RETURN"
    ADJUSTMENT = "ADJUSTMENT"
    DAMAGED = "DAMAGED"
    TRANSFER_OUT = "TRANSFER_OUT"
    TRANSFER_IN = "TRANSFER_IN"


class StockAlertTypeEnum(str, Enum):
    LOW_STOCK = "LOW_STOCK"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    OVERSTOCK = "OVERSTOCK"
    REORDER_POINT = "REORDER_POINT"


class ReturnReasonEnum(str, Enum):
    DEFECTIVE = "DEFECTIVE"
    WRONG_ITEM = "WRONG_ITEM"
    SIZE_ISSUE = "SIZE_ISSUE"
    CHANGED_MIND = "CHANGED_MIND"
    OTHER = "OTHER"


class ReturnStatusEnum(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"


class RefundMethodEnum(str, Enum):
    ORIGINAL_PAYMENT = "ORIGINAL_PAYMENT"
    STORE_CREDIT = "STORE_CREDIT"
    BANK_TRANSFER = "BANK_TRANSFER"


class ItemConditionEnum(str, Enum):
    UNOPENED = "UNOPENED"
    USED = "USED"
    DAMAGED = "DAMAGED"


class LoyaltyTransactionEnum(str, Enum):
    EARN_PURCHASE = "EARN_PURCHASE"
    EARN_REVIEW = "EARN_REVIEW"
    EARN_REFERRAL = "EARN_REFERRAL"
    REDEEM = "REDEEM"
    EXPIRE = "EXPIRE"
    ADJUSTMENT = "ADJUSTMENT"


class NotificationTypeEnum(str, Enum):
    ORDER = "ORDER"
    PROMOTION = "PROMOTION"
    SYSTEM = "SYSTEM"
    REVIEW = "REVIEW"


class EmailTypeEnum(str, Enum):
    WELCOME = "WELCOME"
    ORDER_CONFIRMATION = "ORDER_CONFIRMATION"
    SHIPPING = "SHIPPING"
    PROMOTION = "PROMOTION"
    PASSWORD_RESET = "PASSWORD_RESET"
    EMAIL_VERIFICATION = "EMAIL_VERIFICATION"
    ABANDONED_CART = "ABANDONED_CART"


class EmailStatusEnum(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class SettingTypeEnum(str, Enum):
    STRING = "STRING"
    NUMBER = "NUMBER"
    BOOLEAN = "BOOLEAN"
    JSON = "JSON"


class AdminActionEnum(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    EXPORT = "EXPORT"