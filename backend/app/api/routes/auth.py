"""
Authentication routes.

Login, register, password reset, email verification, etc.
"""
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import SessionDep, CurrentUser
from app.core.config import settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    validate_password_strength,
)
from app.crud.user import user as user_crud
from app.schemas.auth import (
    Token,
    LoginRequest,
    RegisterRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    PasswordChange,
    EmailVerificationRequest,
)
from app.schemas.user import UserResponse
from app.schemas.common import Message

router = APIRouter()


# ============== REGISTER ==============

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    *,
    db: SessionDep,
    user_in: RegisterRequest,
) -> UserResponse:
    """
    Register new user.
    
    - **email**: Valid email address
    - **password**: Minimum 8 characters, must contain uppercase, lowercase, number, special char
    - **first_name**: User's first name
    - **last_name**: User's last name
    - **phone**: Optional phone number
    """
    # Check if user already exists
    existing_user = await user_crud.get_by_email(db=db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Validate password strength
    is_valid, error_msg = validate_password_strength(user_in.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Create user using CRUD
    user = await user_crud.register(db=db, obj_in=user_in)
    
    # TODO: Send welcome email (async, don't wait)
    # TODO: Send verification email
    
    return user


# ============== LOGIN ==============

@router.post("/login", response_model=Token)
async def login(
    db: SessionDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """
    OAuth2 compatible token login.
    
    Returns access token.
    """
    # Authenticate user
    user = await user_crud.authenticate(
        db=db,
        email=form_data.username,
        password=form_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.user_id),
        expires_delta=access_token_expires
    )
    
    # Update last login
    await user_crud.update_last_login(db=db, user=user)
    
    return Token(
        access_token=access_token,
        token_type="bearer"
    )


# ============== PASSWORD MANAGEMENT ==============

@router.post("/password-reset/request", response_model=Message)
async def request_password_reset(
    db: SessionDep,
    email_in: PasswordResetRequest,
) -> Message:
    """
    Request password reset.
    
    Sends email with reset token.
    """
    # Get user by email
    user = await user_crud.get_by_email(db=db, email=email_in.email)
    
    # Always return success (don't reveal if user exists)
    if not user:
        return Message(message="If the email exists, a password reset link has been sent")
    
    # TODO: Generate reset token
    # TODO: Send reset email
    
    return Message(message="If the email exists, a password reset link has been sent")


@router.post("/password-reset/confirm", response_model=Message)
async def reset_password(
    db: SessionDep,
    reset_data: PasswordResetConfirm,
) -> Message:
    """
    Reset password using token.
    """
    # TODO: Verify token and get email
    # For now, return error
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Password reset not implemented yet"
    )


@router.post("/password/change", response_model=Message)
async def change_password(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    password_in: PasswordChange,
) -> Message:
    """
    Change current user password.
    
    Requires current password for verification.
    """
    # Verify current password
    if not verify_password(password_in.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )
    
    # Validate new password
    is_valid, error_msg = validate_password_strength(password_in.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Check if new password is same as current
    if verify_password(password_in.new_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )
    
    # Update password
    await user_crud.update_password(
        db=db,
        user=current_user,
        new_password=password_in.new_password
    )
    
    return Message(message="Password updated successfully")


# ============== EMAIL VERIFICATION ==============

@router.post("/verify-email", response_model=Message)
async def verify_email(
    db: SessionDep,
    verification_in: EmailVerificationRequest,
) -> Message:
    """
    Verify email address using token.
    """
    # TODO: Verify token and get user
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Email verification not implemented yet"
    )


@router.post("/resend-verification", response_model=Message)
async def resend_verification(
    db: SessionDep,
    current_user: CurrentUser,
) -> Message:
    """
    Resend email verification link.
    
    Requires authentication.
    """
    # Check if already verified
    if current_user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # TODO: Generate new verification token
    # TODO: Send verification email
    
    return Message(message="Verification email sent")


# ============== TEST TOKEN ==============

@router.get("/test-token", response_model=UserResponse)
async def test_token(
    current_user: CurrentUser,
) -> UserResponse:
    """
    Test access token.
    
    Returns current user info.
    """
    return current_user


# ============== LOGOUT ==============

@router.post("/logout", response_model=Message)
async def logout(
    current_user: CurrentUser,
) -> Message:
    """
    Logout (client should discard tokens).
    
    Note: JWT tokens are stateless, so logout is handled client-side.
    """
    return Message(message="Logged out successfully")
