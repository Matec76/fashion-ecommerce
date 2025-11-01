"""
User routes.

User profile management, addresses, and admin user management.
"""
from typing import Any

from fastapi import APIRouter, Query, status, HTTPException

from app.api.deps import (
    SessionDep,
    CurrentUser,
    SuperUser,
    PaginationDep,
)
from app.crud.user import user as user_crud
from app.crud.address import address as address_crud
from app.schemas.user import (
    UserResponse,
    UserDetailResponse,
    UserUpdate,
    UserUpdateMe,
    AddressResponse,
    AddressCreate,
    AddressUpdate,
)
from app.schemas.common import Message, PaginatedResponse
from app.utils.pagination import PageResponse

router = APIRouter()


# ============== CURRENT USER ENDPOINTS ==============

@router.get("/me", response_model=UserDetailResponse)
async def get_current_user(
    db: SessionDep,
    current_user: CurrentUser,
) -> UserDetailResponse:
    """
    Get current user profile.
    
    Returns authenticated user's information with role.
    """
    # Get user with role
    from app.crud.role import role as role_crud
    user_with_role = await user_crud.get_multi_with_role(
        db=db,
        filters={"user_id": current_user.user_id},
        limit=1
    )
    
    if user_with_role:
        return user_with_role[0]
    
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    user_in: UserUpdateMe,
) -> UserResponse:
    """
    Update current user profile.
    
    Users can update their own:
    - first_name, last_name
    - phone, date_of_birth, gender
    - avatar_url
    """
    updated_user = await user_crud.update(
        db=db,
        db_obj=current_user,
        obj_in=user_in
    )
    
    return updated_user


@router.delete("/me", response_model=Message)
async def delete_current_user(
    *,
    db: SessionDep,
    current_user: CurrentUser,
) -> Message:
    """
    Delete current user account (soft delete).
    """
    await user_crud.delete(db=db, id=current_user.user_id, soft_delete=True)
    
    return Message(message="Account deleted successfully")


# ============== USER ADDRESS ENDPOINTS ==============

@router.get("/me/addresses", response_model=list[AddressResponse])
async def get_current_user_addresses(
    db: SessionDep,
    current_user: CurrentUser,
) -> list[AddressResponse]:
    """
    Get current user's addresses.
    """
    addresses = await address_crud.get_by_user(
        db=db,
        user_id=current_user.user_id
    )
    
    return addresses


@router.post("/me/addresses", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
async def create_address(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    address_in: AddressCreate,
) -> AddressResponse:
    """
    Create new address for current user.
    """
    address = await address_crud.create_for_user(
        db=db,
        user_id=current_user.user_id,
        obj_in=address_in
    )
    
    return address


@router.get("/me/addresses/{address_id}", response_model=AddressResponse)
async def get_address(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    address_id: int,
) -> AddressResponse:
    """
    Get specific address.
    """
    address = await address_crud.get(db=db, id=address_id)
    
    if not address or address.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )
    
    return address


@router.patch("/me/addresses/{address_id}", response_model=AddressResponse)
async def update_address(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    address_id: int,
    address_in: AddressUpdate,
) -> AddressResponse:
    """
    Update address.
    """
    address = await address_crud.get(db=db, id=address_id)
    
    if not address or address.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )
    
    updated_address = await address_crud.update(
        db=db,
        db_obj=address,
        obj_in=address_in
    )
    
    return updated_address


@router.delete("/me/addresses/{address_id}", response_model=Message)
async def delete_address(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    address_id: int,
) -> Message:
    """
    Delete address.
    """
    result = await address_crud.delete_user_address(
        db=db,
        address_id=address_id,
        user_id=current_user.user_id
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )
    
    return Message(message="Address deleted successfully")


@router.post("/me/addresses/{address_id}/set-default", response_model=AddressResponse)
async def set_default_address(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    address_id: int,
) -> AddressResponse:
    """
    Set address as default.
    """
    address = await address_crud.set_default(
        db=db,
        address_id=address_id,
        user_id=current_user.user_id
    )
    
    return address


# ============== ADMIN USER MANAGEMENT ==============

@router.get("", response_model=list[UserResponse])
async def list_users(
    db: SessionDep,
    current_user: SuperUser,
    pagination: PaginationDep,
    search: str | None = Query(None, description="Search by email, name"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    is_superuser: bool | None = Query(None, description="Filter by superuser status"),
) -> list[UserResponse]:
    """
    List all users (Admin only).
    
    Supports:
    - Pagination
    - Search by email/name
    - Filter by active/superuser status
    """
    # Build filters
    filters = {}
    if is_active is not None:
        filters["is_active"] = is_active
    if is_superuser is not None:
        filters["is_superuser"] = is_superuser
    
    # Get users
    users = await user_crud.get_multi(
        db=db,
        skip=pagination.get_offset(),
        limit=pagination.get_limit(),
        filters=filters
    )
    
    # TODO: Add search functionality
    
    return users


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user(
    db: SessionDep,
    current_user: SuperUser,
    user_id: int,
) -> UserDetailResponse:
    """
    Get user by ID (Admin only).
    """
    users = await user_crud.get_multi_with_role(
        db=db,
        filters={"user_id": user_id},
        limit=1
    )
    
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return users[0]


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    *,
    db: SessionDep,
    current_user: SuperUser,
    user_id: int,
    user_in: UserUpdate,
) -> UserResponse:
    """
    Update user (Admin only).
    """
    user = await user_crud.get(db=db, id=user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if email is being changed and already exists
    if user_in.email and user_in.email != user.email:
        existing = await user_crud.get_by_email(db=db, email=user_in.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
    
    updated_user = await user_crud.update(
        db=db,
        db_obj=user,
        obj_in=user_in
    )
    
    return updated_user


@router.delete("/{user_id}", response_model=Message)
async def delete_user(
    db: SessionDep,
    current_user: SuperUser,
    user_id: int,
    permanent: bool = Query(False, description="Permanently delete user"),
) -> Message:
    """
    Delete user (Admin only).
    """
    user = await user_crud.get(db=db, id=user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent deleting self
    if user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    await user_crud.delete(db=db, id=user_id, soft_delete=not permanent)
    
    return Message(message="User deleted successfully")


@router.post("/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    db: SessionDep,
    current_user: SuperUser,
    user_id: int,
) -> UserResponse:
    """
    Activate user (Admin only).
    """
    user = await user_crud.get(db=db, id=user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already active"
        )
    
    updated_user = await user_crud.update(
        db=db,
        db_obj=user,
        obj_in={"is_active": True}
    )
    
    return updated_user


@router.post("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    db: SessionDep,
    current_user: SuperUser,
    user_id: int,
) -> UserResponse:
    """
    Deactivate user (Admin only).
    """
    user = await user_crud.get(db=db, id=user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already inactive"
        )
    
    updated_user = await user_crud.update(
        db=db,
        db_obj=user,
        obj_in={"is_active": False}
    )
    
    return updated_user