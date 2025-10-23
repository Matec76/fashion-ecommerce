import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
import re
from decimal import Decimal

import emails
from jinja2 import Template
from slugify import slugify

from app.core import security
from app.core.config import settings

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EmailData:
    """Data class chứa thông tin email"""
    html_content: str
    subject: str


# Email Functions

def render_email_template(*, template_name: str, context: dict[str, Any]) -> str:
    template_str = (
        Path(__file__).parent / "email-templates" / "build" / template_name
    ).read_text()
    html_content = Template(template_str).render(context)
    return html_content


def send_email(
    *,
    email_to: str,
    subject: str = "",
    html_content: str = "",
) -> None:
    
    assert settings.emails_enabled, "Chưa cấu hình email"
    
    message = emails.Message(
        subject=subject,
        html=html_content,
        mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
    )
    
    smtp_options = {"host": settings.SMTP_HOST, "port": settings.SMTP_PORT}
    if settings.SMTP_TLS:
        smtp_options["tls"] = True
    elif settings.SMTP_SSL:
        smtp_options["ssl"] = True
    if settings.SMTP_USER:
        smtp_options["user"] = settings.SMTP_USER
    if settings.SMTP_PASSWORD:
        smtp_options["password"] = settings.SMTP_PASSWORD
    
    response = message.send(to=email_to, smtp=smtp_options)
    logger.info(f"Kết quả gửi email: {response}")


def generate_test_email(email_to: str) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Email kiểm tra"
    html_content = render_email_template(
        template_name="test_email.html",
        context={"project_name": settings.PROJECT_NAME, "email": email_to},
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_reset_password_email(email_to: str, email: str, token: str) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Khôi phục mật khẩu"
    link = f"{settings.FRONTEND_HOST}/reset-password?token={token}"
    html_content = render_email_template(
        template_name="reset_password.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "username": email,
            "email": email_to,
            "valid_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
            "link": link,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_new_account_email(
    email_to: str, username: str, password: str
) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Chào mừng bạn đến với {project_name}"
    html_content = render_email_template(
        template_name="new_account.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "username": username,
            "password": password,
            "email": email_to,
            "link": settings.FRONTEND_HOST,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_email_verification_email(email_to: str, token: str) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Xác thực địa chỉ email"
    link = f"{settings.FRONTEND_HOST}/verify-email?token={token}"
    html_content = render_email_template(
        template_name="verify_email.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "email": email_to,
            "valid_hours": settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS,
            "link": link,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_order_confirmation_email(
    email_to: str,
    order_number: str,
    customer_name: str,
    order_total: float,
    order_items: list[dict[str, Any]]
) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Xác nhận đơn hàng #{order_number}"
    link = f"{settings.FRONTEND_HOST}/orders/{order_number}"
    html_content = render_email_template(
        template_name="order_confirmation.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "customer_name": customer_name,
            "order_number": order_number,
            "order_total": format_currency(order_total),
            "order_items": order_items,
            "link": link,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_order_shipped_email(
    email_to: str,
    order_number: str,
    customer_name: str,
    tracking_number: str | None = None
) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Đơn hàng #{order_number} đã được gửi đi"
    link = f"{settings.FRONTEND_HOST}/orders/{order_number}"
    html_content = render_email_template(
        template_name="order_shipped.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "customer_name": customer_name,
            "order_number": order_number,
            "tracking_number": tracking_number,
            "link": link,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_abandoned_cart_email(
    email_to: str,
    customer_name: str,
    cart_items: list[dict[str, Any]],
    cart_total: float
) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Bạn còn sản phẩm trong giỏ hàng"
    link = f"{settings.FRONTEND_HOST}/cart"
    html_content = render_email_template(
        template_name="abandoned_cart.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "customer_name": customer_name,
            "cart_items": cart_items,
            "cart_total": format_currency(cart_total),
            "link": link,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


# String & Format Functions

def generate_slug(text: str) -> str:
    return slugify(text, max_length=settings.PRODUCT_SLUG_MAX_LENGTH)


def format_currency(amount: float | Decimal, currency: str | None = None) -> str:
    if currency is None:
        currency = settings.CURRENCY_CODE
    
    # Format số với dấu phân cách hàng nghìn
    formatted = "{:,.0f}".format(float(amount))
    
    # Thay dấu phẩy thành dấu chấm (phong cách Việt Nam)
    formatted = formatted.replace(",", ".")
    
    # Ký hiệu tiền tệ
    if currency == "VND":
        return f"{formatted}{settings.CURRENCY_SYMBOL}"
    else:
        return f"{settings.CURRENCY_SYMBOL}{formatted}"


def format_phone_number(phone: str) -> str:
    # Loại bỏ tất cả ký tự không phải số
    phone = re.sub(r'\D', '', phone)
    
    # Format theo kiểu Việt Nam
    if len(phone) == 10:
        return f"{phone[:4]} {phone[4:7]} {phone[7:]}"
    elif len(phone) == 11:
        return f"{phone[:4]} {phone[4:7]} {phone[7:]}"
    else:
        return phone


def validate_phone_number(phone: str) -> bool:
    # Loại bỏ ký tự không phải số
    phone = re.sub(r'\D', '', phone)
    
    # Số điện thoại Việt Nam: 10 hoặc 11 số, bắt đầu bằng 0
    if len(phone) not in [10]:
        return False
    
    if not phone.startswith('0'):
        return False
    
    return True


def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


# Price & Discount Calculation

def calculate_discount_amount(
    original_price: float | Decimal,
    discount_type: str,
    discount_value: float | Decimal
) -> Decimal:
    original_price = Decimal(str(original_price))
    discount_value = Decimal(str(discount_value))
    
    if discount_type == "percentage":
        # Giảm theo phần trăm
        discount_amount = original_price * (discount_value / 100)
    else:
        # Giảm số tiền cố định
        discount_amount = discount_value
    
    # Đảm bảo không giảm quá giá gốc
    return min(discount_amount, original_price)


def calculate_final_price(
    original_price: float | Decimal,
    discount_type: str | None = None,
    discount_value: float | Decimal | None = None
) -> Decimal:
    original_price = Decimal(str(original_price))
    
    if discount_type and discount_value:
        discount_amount = calculate_discount_amount(
            original_price, discount_type, discount_value
        )
        final_price = original_price - discount_amount
    else:
        final_price = original_price
    
    return max(final_price, Decimal('0'))


def calculate_tax_amount(subtotal: float | Decimal, tax_rate: float | None = None) -> Decimal:
    if tax_rate is None:
        tax_rate = settings.TAX_RATE
    
    subtotal = Decimal(str(subtotal))
    tax_rate = Decimal(str(tax_rate))
    
    return subtotal * tax_rate


def calculate_shipping_fee(
    subtotal: float | Decimal,
    weight: float | None = None,
    distance: float | None = None
) -> Decimal:
    subtotal = Decimal(str(subtotal))
    
    # Miễn phí vận chuyển nếu đơn hàng đạt ngưỡng
    if subtotal >= Decimal(str(settings.FREE_SHIPPING_THRESHOLD)):
        return Decimal('0')
    
    # Tính phí vận chuyển cơ bản
    shipping_fee = Decimal(str(settings.DEFAULT_SHIPPING_FEE))
    
    # Thêm logic tính phí theo trọng lượng, khoảng cách
    # if weight and weight > 5:  # Nặng hơn 5kg
    #     shipping_fee += Decimal('10000') * Decimal(str(int(weight) - 5))
    # if distance and distance > 10:  # Khoảng cách lớn hơn 10km
    #     shipping_fee += Decimal('5000') * Decimal(str(int(distance) - 10))
    
    return shipping_fee


def calculate_loyalty_points(amount: float | Decimal) -> int:
    amount = Decimal(str(amount))
    points_per_currency = Decimal(str(settings.POINTS_PER_CURRENCY))
    
    # Tính điểm: mỗi POINTS_PER_CURRENCY VND = 1 điểm
    points = int(amount / points_per_currency)
    
    return points


def calculate_points_value(points: int) -> Decimal:
    return Decimal(str(points * settings.POINTS_TO_CURRENCY_RATE))


# Date & Time Functions

def format_datetime(dt: datetime, format: str = "%d/%m/%Y %H:%M") -> str:
    return dt.strftime(format)


def is_within_hours(dt: datetime, hours: int) -> bool:
    now = datetime.now(timezone.utc)
    time_diff = now - dt.replace(tzinfo=timezone.utc)
    return time_diff <= timedelta(hours=hours)


def is_within_days(dt: datetime, days: int) -> bool:
    now = datetime.now(timezone.utc)
    time_diff = now - dt.replace(tzinfo=timezone.utc)
    return time_diff <= timedelta(days=days)


# Pagination Helper

def calculate_skip(page: int, page_size: int) -> int:
    return (page - 1) * page_size


def calculate_total_pages(total: int, page_size: int) -> int:
    return (total + page_size - 1) // page_size