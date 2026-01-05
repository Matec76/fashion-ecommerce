from typing import Annotated, Optional
from collections.abc import AsyncGenerator
import re

from fastapi import Depends, HTTPException, status, Query, Request
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError as JWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db as _get_db
from app.core.security import decode_token
from app.models.common import TokenPayload
from app.models.user import User
from app.crud.user import user as user_crud
from app.utils.pagination import PaginationParams


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False
)

async def get_token(
    request: Request,
    token: Annotated[str | None, Depends(oauth2_scheme)] = None
) -> str:
    """
    Ưu tiên lấy token từ HttpOnly Cookie. Nếu không có thì mới tìm trong Header.
    """
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        if cookie_token.startswith("Bearer "):
            return cookie_token.split(" ")[1]
        return cookie_token

    if token:
        return token
        
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency để lấy database session.
    
    Yields:
        AsyncSession: Database session
    """
    async for session in _get_db():
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: SessionDep,
    token: Annotated[str, Depends(get_token)]
) -> User:
    """
    Lấy current user từ JWT token.
    
    Args:
        db: Database session
        token: JWT access token
        
    Returns:
        User instance
        
    Raises:
        HTTPException: 401 nếu token invalid hoặc user không tồn tại
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_token(token)
        
        if payload is None:
            raise credentials_exception
        
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token_data = TokenPayload(**payload)
        
        if token_data.sub is None:
            raise credentials_exception
            
        user_id = int(token_data.sub)
        
    except (JWTError, ValidationError, ValueError):
        raise credentials_exception
    
    user = await user_crud.get(db=db, id=user_id)
    
    if not user:
        raise credentials_exception
    
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_optional_user(
    db: SessionDep,
    request: Request,
    token: Annotated[str | None, Depends(oauth2_scheme)] = None
) -> User | None:
    """
    Lấy current user nếu có token, None nếu không (cho public endpoints).
    
    Args:
        db: Database session
        token: JWT access token (optional)
        
    Returns:
        User instance hoặc None
    """
    cookie_token = request.cookies.get("access_token")
    final_token = None
    
    if cookie_token:
        if cookie_token.startswith("Bearer "):
            final_token = cookie_token.split(" ")[1]
        else:
            final_token = cookie_token
            
    if not final_token:
        final_token = token
        
    if not final_token:
        return None
    
    try:
        payload = decode_token(final_token) 
        
        if payload is None or payload.get("type") != "access":
            return None
        
        token_data = TokenPayload(**payload)
        
        if token_data.sub is None:
            return None
            
        user_id = int(token_data.sub)
        user = await user_crud.get(db=db, id=user_id)
        return user
        
    except (JWTError, ValidationError, ValueError):
        return None


OptionalUser = Annotated[User | None, Depends(get_optional_user)]


async def get_current_active_user(current_user: CurrentUser) -> User:
    """
    Verify current user is active.
    
    Args:
        current_user: Current user from token
        
    Returns:
        User instance nếu active
        
    Raises:
        HTTPException: 400 nếu user inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


ActiveUser = Annotated[User, Depends(get_current_active_user)]


async def get_current_superuser(current_user: CurrentUser) -> User:
    """
    Verify current user is superuser.
    
    Args:
        current_user: Current user from token
        
    Returns:
        User instance nếu là superuser
        
    Raises:
        HTTPException: 403 nếu không phải superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Superuser access required."
        )
    return current_user


SuperUser = Annotated[User, Depends(get_current_superuser)]


async def get_current_active_superuser(current_user: CurrentUser) -> User:
    """
    Verify current user is active superuser.
    
    Args:
        current_user: Current user from token
        
    Returns:
        User instance nếu là active superuser
        
    Raises:
        HTTPException: 400 nếu inactive, 403 nếu không phải superuser
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Superuser access required."
        )
    
    return current_user


ActiveSuperUser = Annotated[User, Depends(get_current_active_superuser)]


async def _get_user_permissions(
    db: SessionDep,
    current_user: User
) -> set[str]:
    """
    Helper function để lấy tất cả permissions của user.
    
    Args:
        db: Database session
        current_user: Current user
        
    Returns:
        Set of permission codes
        
    Raises:
        HTTPException: Nếu user inactive hoặc không có role
    """
    if current_user.is_superuser:
        return {"*"}
    
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    if not current_user.role_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no role assigned"
        )
    
    from app.crud.role import role as role_crud
    user_role = await role_crud.get_with_permissions(
        db=db,
        id=current_user.role_id
    )
    
    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role not found"
        )
    
    permissions = {
        rp.permission.permission_code
        for rp in user_role.role_permissions
        if rp.permission and rp.permission.permission_code
    }
    
    return permissions


def require_permission(permission_code: str):
    """
    Dependency factory để check permission cụ thể.
    
    Args:
        permission_code: Permission code cần check (ví dụ: "products:create")
        
    Returns:
        Dependency function
        
    Example:
        @router.post("/products")
        async def create_product(
            user: Annotated[User, Depends(require_permission("products:create"))],
            ...
        ):
            ...
    """
    async def permission_checker(
        db: SessionDep,
        current_user: CurrentUser,
    ) -> User:
        """Check user có permission cụ thể"""
        user_permissions = await _get_user_permissions(db, current_user)
        if "*" in user_permissions:
            return current_user
        
        if permission_code not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission_code}"
            )
        
        return current_user
    
    return permission_checker


def require_any_permission(*permission_codes: str):
    """
    Dependency factory để check user có ít nhất 1 trong các permissions.
    
    Args:
        *permission_codes: Danh sách permission codes
        
    Returns:
        Dependency function
        
    Example:
        @router.get("/products")
        async def list_products(
            user: Annotated[User, Depends(require_any_permission("products:read", "products:admin"))],
            ...
        ):
            ...
    """
    if not permission_codes:
        raise ValueError("At least one permission code is required")
    
    async def permission_checker(
        db: SessionDep,
        current_user: CurrentUser,
    ) -> User:
        """Check user có ít nhất 1 permission"""
        user_permissions = await _get_user_permissions(db, current_user)
        
        if "*" in user_permissions:
            return current_user
        
        has_permission = any(
            code in user_permissions 
            for code in permission_codes
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required one of: {', '.join(permission_codes)}"
            )
        
        return current_user
    
    return permission_checker


def require_all_permissions(*permission_codes: str):
    """
    Dependency factory để check user có tất cả các permissions.
    
    Args:
        *permission_codes: Danh sách permission codes
        
    Returns:
        Dependency function
        
    Example:
        @router.post("/products/bulk-delete")
        async def bulk_delete(
            user: Annotated[User, Depends(require_all_permissions("products:read", "products:delete"))],
            ...
        ):
            ...
    """
    if not permission_codes:
        raise ValueError("At least one permission code is required")
    
    async def permission_checker(
        db: SessionDep,
        current_user: CurrentUser,
    ) -> User:
        """Check user có tất cả permissions"""
        user_permissions = await _get_user_permissions(db, current_user)
        
        if "*" in user_permissions:
            return current_user
        
        missing_permissions = [
            code for code in permission_codes
            if code not in user_permissions
        ]
        
        if missing_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Missing: {', '.join(missing_permissions)}"
            )
        
        return current_user
    
    return permission_checker


async def get_pagination_params(
    page: Annotated[int, Query(ge=1, description="Page number (1-indexed)")] = 1,
    page_size: Annotated[int, Query(ge=1, description="Items per page")] = settings.DEFAULT_PAGE_SIZE,
) -> PaginationParams:
    """
    Dependency để lấy pagination parameters.
    
    Args:
        page: Page number (1-indexed)
        page_size: Items per page
        
    Returns:
        PaginationParams instance
        
    Note:
        page_size will be automatically capped at MAX_PAGE_SIZE
    """
    validated_page_size = min(page_size, settings.MAX_PAGE_SIZE)
    
    if validated_page_size != page_size:
        import logging
        logging.warning(
            f"page_size {page_size} exceeded MAX_PAGE_SIZE {settings.MAX_PAGE_SIZE}, "
            f"using {validated_page_size} instead"
        )
    
    return PaginationParams(page=page, page_size=validated_page_size)


PaginationDep = Annotated[PaginationParams, Depends(get_pagination_params)]


SESSION_ID_PATTERN = re.compile(
    r'^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$',
    re.IGNORECASE
)


def validate_session_id(session_id: str | None) -> str | None:
    """
    Validate session ID format.
    
    Args:
        session_id: Session ID to validate
        
    Returns:
        Validated session ID or None if invalid
    """
    if not session_id:
        return None
    
    if len(session_id) > 100:
        return None
    
    if not SESSION_ID_PATTERN.match(session_id):
        return None
    
    return session_id


def get_session_id(request: Request) -> str | None:
    """
    Lấy session ID từ cookie hoặc header (cho guest users).
    
    Args:
        request: FastAPI request
        
    Returns:
        Validated session ID string hoặc None
        
    Note:
        Session ID must be in UUID v4 format for security
    """
    session_id = request.cookies.get("session_id")
    
    if not session_id:
        session_id = request.headers.get("X-Session-ID")
    
    return validate_session_id(session_id)


SessionID = Annotated[str | None, Depends(get_session_id)]


async def verify_email_not_taken(
    db: SessionDep,
    email: str,
    exclude_user_id: int | None = None
) -> str:
    """
    Verify email chưa được sử dụng.
    
    Args:
        db: Database session
        email: Email to check
        exclude_user_id: User ID to exclude (for update operations)
        
    Returns:
        Email if available
        
    Raises:
        HTTPException: 400 nếu email đã tồn tại
    """
    existing = await user_crud.get_by_email(db=db, email=email)
    
    if existing and (exclude_user_id is None or existing.user_id != exclude_user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    return email


__all__ = [
    # Database
    "get_db",
    "SessionDep",
    # Authentication
    "get_current_user",
    "CurrentUser",
    "get_optional_user",
    "OptionalUser",
    # Authorization
    "get_current_active_user",
    "ActiveUser",
    "get_current_superuser",
    "SuperUser",
    "get_current_active_superuser",
    "ActiveSuperUser",
    # Permissions
    "require_permission",
    "require_any_permission",
    "require_all_permissions",
    # Pagination
    "get_pagination_params",
    "PaginationDep",
    # Session
    "get_session_id",
    "SessionID",
    "validate_session_id",
    # Validation
    "verify_email_not_taken",
]