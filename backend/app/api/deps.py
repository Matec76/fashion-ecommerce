"""
API Dependencies.

Các dependency functions dùng chung cho API routes:
- get_db: Database session dependency
- get_current_user: Lấy current user từ JWT token
- get_current_active_user: Verify user is active
- get_current_superuser: Verify user is superuser
- require_permission: Check user có permission cụ thể
- get_pagination_params: Pagination parameters
"""
from typing import Annotated, Optional
from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, status, Query, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db as _get_db
from app.core.security import decode_token
from app.models.base import TokenPayload
from app.models.user import User
from app.crud.user import user as user_crud
from app.utils.pagination import PaginationParams

# OAuth2 scheme cho JWT token
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False  # Cho phép optional authentication
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency để lấy database session.
    
    Yields:
        AsyncSession: Database session
    """
    async for session in _get_db():
        yield session


# Type alias cho DB session dependency
SessionDep = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: SessionDep,
    token: Annotated[str, Depends(oauth2_scheme)]
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
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token using security function
        payload = decode_token(token)
        
        if payload is None:
            raise credentials_exception
        
        # Verify token type
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
    
    # Lấy user từ database
    user = await user_crud.get(db=db, id=user_id)
    
    if not user:
        raise credentials_exception
    
    return user


# Type alias cho current user dependency
CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_active_user(
    current_user: CurrentUser,
) -> User:
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


# Type alias cho active user dependency
ActiveUser = Annotated[User, Depends(get_current_active_user)]


async def get_current_superuser(
    current_user: CurrentUser,
) -> User:
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
            detail="Not enough permissions. Superuser access required."
        )
    return current_user


# Type alias cho superuser dependency
SuperUser = Annotated[User, Depends(get_current_superuser)]


async def get_current_active_superuser(
    current_user: CurrentUser,
) -> User:
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
            detail="Not enough permissions. Superuser access required."
        )
    
    return current_user


# Type alias
ActiveSuperUser = Annotated[User, Depends(get_current_active_superuser)]


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
        """Check user có permission hay không"""
        
        # Superuser có tất cả permissions
        if current_user.is_superuser:
            return current_user
        
        # User phải active
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        # Kiểm tra permission qua role
        if not current_user.role_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no role assigned"
            )
        
        # Lấy permissions của role
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
        
        # Check permission
        has_permission = False
        if user_role.role_permissions:
            for role_perm in user_role.role_permissions:
                if role_perm.permission and role_perm.permission.permission_code == permission_code:
                    has_permission = True
                    break
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission_code}"
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
    async def permission_checker(
        db: SessionDep,
        current_user: CurrentUser,
    ) -> User:
        """Check user có ít nhất 1 permission"""
        
        # Superuser có tất cả permissions
        if current_user.is_superuser:
            return current_user
        
        # User phải active
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        # Kiểm tra permission qua role
        if not current_user.role_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no role assigned"
            )
        
        # Lấy permissions của role
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
        
        # Check ít nhất 1 permission
        has_permission = False
        if user_role.role_permissions:
            for role_perm in user_role.role_permissions:
                if role_perm.permission and role_perm.permission.permission_code in permission_codes:
                    has_permission = True
                    break
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: requires one of {', '.join(permission_codes)}"
            )
        
        return current_user
    
    return permission_checker


async def get_optional_user(
    db: SessionDep,
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
    if not token:
        return None
    
    try:
        payload = decode_token(token)
        
        if payload is None:
            return None
        
        # Verify token type
        if payload.get("type") != "access":
            return None
        
        token_data = TokenPayload(**payload)
        
        if token_data.sub is None:
            return None
            
        user_id = int(token_data.sub)
        
    except (JWTError, ValidationError, ValueError):
        return None
    
    user = await user_crud.get(db=db, id=user_id)
    return user


# Type alias cho optional user dependency
OptionalUser = Annotated[User | None, Depends(get_optional_user)]


async def get_pagination_params(
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[
        int, 
        Query(
            ge=1, 
            le=settings.MAX_PAGE_SIZE, 
            description="Items per page"
        )
    ] = settings.DEFAULT_PAGE_SIZE,
) -> PaginationParams:
    """
    Dependency để lấy pagination parameters.
    
    Args:
        page: Page number (1-indexed)
        page_size: Items per page
        
    Returns:
        PaginationParams instance
    """
    return PaginationParams(page=page, page_size=page_size)


# Type alias cho pagination dependency
PaginationDep = Annotated[PaginationParams, Depends(get_pagination_params)]


def get_session_id(
    request: Request,
) -> str | None:
    """
    Lấy session ID từ cookie hoặc header (cho guest users).
    
    Args:
        request: FastAPI request
        
    Returns:
        Session ID string hoặc None
    """
    # Try to get from cookie first
    session_id = request.cookies.get("session_id")
    
    if not session_id:
        # Try to get from header
        session_id = request.headers.get("X-Session-ID")
    
    return session_id


# Type alias cho session ID dependency
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


# ============== EXPORT ==============

__all__ = [
    "get_db",
    "SessionDep",
    "get_current_user",
    "CurrentUser",
    "get_current_active_user",
    "ActiveUser",
    "get_current_superuser",
    "SuperUser",
    "get_current_active_superuser",
    "ActiveSuperUser",
    "require_permission",
    "require_any_permission",
    "get_optional_user",
    "OptionalUser",
    "get_pagination_params",
    "PaginationDep",
    "get_session_id",
    "SessionID",
    "verify_email_not_taken",
]
