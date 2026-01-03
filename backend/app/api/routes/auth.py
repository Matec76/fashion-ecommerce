from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_cache.decorator import cache
from fastapi_cache import FastAPICache

from app.api.deps import SessionDep, CurrentUser
from app.core.security import (
    verify_password,
    create_access_token,
    validate_password_strength,
)
from app.crud.user import user as user_crud
from app.crud.role import role as role_crud
from app.models.auth import (
    TokenUser,
    Token,
    RegisterRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    PasswordChange,
    EmailVerificationRequest,
    LogoutRequest,
    RefreshTokenRequest
)
from app.core.config import settings
from app.models.user import UserResponse
from app.models.common import Message
from app.services.email import email_service
from app.services.token import get_token_service_dep, TokenService

router = APIRouter()

async def invalidate_user_all_caches(user_id: int):
    """
    Xóa toàn bộ các loại cache liên quan đến một người dùng cụ thể để đảm bảo tính nhất quán dữ liệu.
    """
    keys_to_delete = [
        f"user:{user_id}:profile",
        f"user:{user_id}:addresses",
        f"admin:user:{user_id}",
        f"test-token:{user_id}",
    ]
    backend = FastAPICache.get_backend()
    for key in keys_to_delete:
        try:
            await backend.redis.delete(key)
        except Exception:
            pass

def test_token_key_builder(func, namespace: str = "", *args, **kwargs):
    """
    Tạo key cache cho endpoint kiểm tra tính hợp lệ của token.
    """
    current_user = kwargs.get("current_user")
    return f"test-token:{current_user.user_id}"

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    *,
    db: SessionDep,
    user_in: RegisterRequest,
    background_tasks: BackgroundTasks,
    token_service: TokenService = Depends(get_token_service_dep),
) -> UserResponse:
    """
    Đăng ký tài khoản người dùng mới, kiểm tra độ mạnh mật khẩu và gửi email xác thực tài khoản.
    """
    existing_user = await user_crud.get_by_email(db=db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    is_valid, error_msg = validate_password_strength(user_in.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    user = await user_crud.register(db=db, obj_in=user_in)
    verification_token = await token_service.create_email_verification_token(
        email=user.email
    )
    
    background_tasks.add_task(
        email_service.send_welcome_email,
        email_to=user.email,
        username=user.first_name or user.email.split("@")[0]
    )
    
    background_tasks.add_task(
        email_service.send_verification_email,
        email_to=user.email,
        username=user.first_name or user.email.split("@")[0],
        token=verification_token
    )
    
    return user

@router.post("/login", response_model=Token)
async def login(
    response: Response,
    db: SessionDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    token_service: TokenService = Depends(get_token_service_dep),
) -> Token:
    """
    Xác thực thông tin đăng nhập, kiểm tra giới hạn thử lại và cấp cặp Access + Refresh Token.
    """
    is_allowed, attempts_remaining = await token_service.check_rate_limit(
        identifier=form_data.username,
        action="login",
        max_attempts=5,
        window_seconds=3600 
    )
    
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )
    
    user = await user_crud.authenticate(
        db=db,
        email=form_data.username,
        password=form_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Incorrect email or password. {attempts_remaining} attempts remaining.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    await token_service.reset_rate_limit(form_data.username, "login")

    role_name = "Customer"
    role_id = 2176
    permissions = []
    if user.role:
        role_name = user.role.role_name
        role_id = user.role.role_id
        role_data = await role_crud.get_with_permissions(db=db, id=role_id)
        if role_data and role_data.role_permissions:
            permissions = [
                rp.permission.permission_code 
                for rp in role_data.role_permissions 
                if rp.permission
            ]
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.user_id),
        expires_delta=access_token_expires,
        role_id=role_id
    )
    
    refresh_token = await token_service.create_refresh_token(user_id=user.user_id)
    
    await user_crud.update_last_login(db=db, user=user)
    await invalidate_user_all_caches(user.user_id)

    access_token_max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=access_token_max_age,
        expires=access_token_max_age,
        samesite="lax",
        secure=True,
        domain=None
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        refresh_token=refresh_token,
        user=TokenUser(
            user_id=user.user_id,
            email=user.email,
            full_name=f"{user.first_name} {user.last_name}",
            role_id=role_id,
            role_name=role_name,
            permissions=permissions
        )
    )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    response: Response,
    request_data: RefreshTokenRequest,
    db: SessionDep,
    token_service: TokenService = Depends(get_token_service_dep),
) -> Token:
    """
    Dùng Refresh Token cũ để đổi lấy cặp Access + Refresh Token mới (Token Rotation).
    """
    user_id = await token_service.verify_refresh_token(request_data.refresh_token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    user = await user_crud.get(db=db, id=int(user_id))
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="User not found or inactive"
        )
    
    role_name = "Customer"
    role_id = 2176
    if user.role:
        role_name = user.role.role_name
        role_id = user.role.role_id
    
    await token_service.revoke_token(request_data.refresh_token)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        subject=str(user_id),
        expires_delta=access_token_expires,
        role_id=role_id
    )
    new_refresh_token = await token_service.create_refresh_token(user_id)

    access_token_max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    response.set_cookie(
        key="access_token",
        value=f"Bearer {new_access_token}",
        httponly=True,
        max_age=access_token_max_age,
        expires=access_token_max_age,
        samesite="lax",
        secure=True,
        domain=None
    )
    
    return Token(
        access_token=new_access_token,
        token_type="bearer",
        refresh_token=new_refresh_token,
        user=TokenUser(
            user_id=user.user_id,
            email=user.email,
            full_name=f"{user.first_name} {user.last_name}",
            role_id=role_id,
            role_name=role_name
        )
    )

@router.post("/password-reset/request", response_model=Message)
async def request_password_reset(
    db: SessionDep,
    email_in: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    token_service: TokenService = Depends(get_token_service_dep),
) -> Message:
    """
    Khởi tạo yêu cầu quên mật khẩu và gửi email chứa mã token khôi phục cho người dùng.
    """
    is_allowed, attempts_remaining = await token_service.check_rate_limit(
        identifier=email_in.email,
        action="password_reset",
        max_attempts=3,
        window_seconds=3600
    )
    
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many password reset requests. Please try again later."
        )
    
    user = await user_crud.get_by_email(db=db, email=email_in.email)
    
    if user:
        reset_token = await token_service.create_password_reset_token(email=user.email)
        
        background_tasks.add_task(
            email_service.send_password_reset_email,
            email_to=user.email,
            username=user.first_name or user.email.split("@")[0],
            token=reset_token
        )
    
    return Message(message="If the email exists, a password reset link has been sent")

@router.post("/password-reset/confirm", response_model=Message)
async def reset_password(
    db: SessionDep,
    reset_data: PasswordResetConfirm,
    background_tasks: BackgroundTasks,
    token_service: TokenService = Depends(get_token_service_dep),
) -> Message:
    """
    Xác thực token khôi phục và thiết lập mật khẩu mới cho tài khoản người dùng.
    """
    email = await token_service.verify_password_reset_token(reset_data.token)
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    user = await user_crud.get_by_email(db=db, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    is_valid, error_msg = validate_password_strength(reset_data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    await user_crud.update_password(
        db=db,
        user=user,
        new_password=reset_data.new_password
    )

    await token_service.revoke_all_user_tokens(user.user_id)
    
    await token_service.revoke_token(reset_data.token)
    
    await invalidate_user_all_caches(user.user_id)
    
    background_tasks.add_task(
        email_service.send_password_changed_email,
        email_to=user.email,
        username=user.first_name or user.email.split("@")[0]
    )
    
    return Message(message="Password reset successful")

@router.post("/password/change", response_model=Message)
async def change_password(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    password_in: PasswordChange,
    background_tasks: BackgroundTasks,
    token_service: TokenService = Depends(get_token_service_dep),
) -> Message:
    """
    Thay đổi mật khẩu trực tiếp cho người dùng đang trong trạng thái đăng nhập.
    """
    if not verify_password(password_in.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )
    
    is_valid, error_msg = validate_password_strength(password_in.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    if verify_password(password_in.new_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )
    
    await user_crud.update_password(
        db=db,
        user=current_user,
        new_password=password_in.new_password
    )

    await token_service.revoke_all_user_tokens(current_user.user_id)
    
    await invalidate_user_all_caches(current_user.user_id)
    
    background_tasks.add_task(
        email_service.send_password_changed_email,
        email_to=current_user.email,
        username=current_user.first_name or current_user.email.split("@")[0]
    )
    
    return Message(message="Password updated successfully")

@router.post("/verify-email", response_model=Message)
async def verify_email(
    db: SessionDep,
    verification_in: EmailVerificationRequest,
    token_service: TokenService = Depends(get_token_service_dep),
) -> Message:
    """
    Xử lý mã xác thực email để kích hoạt đầy đủ các tính năng của tài khoản.
    """
    email = await token_service.verify_email_token(verification_in.token)
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    user = await user_crud.get_by_email(db=db, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_email_verified:
        return Message(message="Email already verified")
    
    await user_crud.verify_email(db=db, user=user)
    
    await token_service.revoke_token(verification_in.token)
    
    await invalidate_user_all_caches(user.user_id)
    
    return Message(message="Email verified successfully")

@router.post("/resend-verification", response_model=Message)
async def resend_verification(
    db: SessionDep,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    token_service: TokenService = Depends(get_token_service_dep),
) -> Message:
    """
    Gửi lại email chứa liên kết xác thực tài khoản cho người dùng hiện tại.
    """
    if current_user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    is_allowed, attempts_remaining = await token_service.check_rate_limit(
        identifier=str(current_user.user_id),
        action="email_verify",
        max_attempts=3,
        window_seconds=3600
    )
    
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many verification emails sent. Please try again later."
        )
    
    verification_token = await token_service.create_email_verification_token(
        email=current_user.email
    )
    
    background_tasks.add_task(
        email_service.send_verification_email,
        email_to=current_user.email,
        username=current_user.first_name or current_user.email.split("@")[0],
        token=verification_token
    )
    
    return Message(message="Verification email sent")

@router.get("/test-token", response_model=UserResponse)
@cache(expire=60, key_builder=test_token_key_builder)
async def test_token(
    current_user: CurrentUser,
) -> UserResponse:
    """
    Kiểm tra trạng thái hoạt động của Token hiện tại và trả về thông tin cơ bản của người dùng (Có cache).
    """
    return current_user

@router.post("/logout", response_model=Message)
async def logout(
    response: Response,
    request_data: LogoutRequest,
    current_user: CurrentUser,
    token_service: TokenService = Depends(get_token_service_dep),
) -> Message:
    """
    Đăng xuất người dùng khỏi hệ thống: Xóa cache và thu hồi Refresh Token.
    """
    await invalidate_user_all_caches(current_user.user_id)
    
    await token_service.revoke_token(request_data.refresh_token)

    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax",
        secure=True
    )
    
    return Message(message="Logged out successfully")