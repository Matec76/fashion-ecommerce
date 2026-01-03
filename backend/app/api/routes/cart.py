from decimal import Decimal

from fastapi import APIRouter, Query, status, HTTPException, Depends

from app.api.deps import (
    SessionDep,
    CurrentUser,
    require_permission,
)
from app.crud.cart import cart as cart_crud
from app.crud.cart import cart_item as cart_item_crud
from app.models.cart import (
    CartResponse,
    CartItemCreate,
    CartItemUpdate,
    CartSummary,
)
from app.models.common import Message
from app.models.user import User

router = APIRouter()


@router.get("/me", response_model=CartResponse)
async def get_my_cart(
    db: SessionDep,
    current_user: CurrentUser,
) -> CartResponse:
    """
    Lấy thông tin chi tiết giỏ hàng của người dùng hiện tại.
    """
    cart = await cart_crud.get_or_create(
        db=db,
        user_id=current_user.user_id
    )
    
    items = cart.items if cart.items else []
    
    total_items = 0
    subtotal = Decimal("0")
    
    items_response = []
    for item in items:
        total_items += item.quantity
        
        variant_data = None
        if item.variant:
            product = item.variant.product
            unit_price = Decimal(0)
            if product:
                unit_price = product.sale_price if product.sale_price else product.base_price
            
            subtotal += unit_price * item.quantity

            variant_data = {
                "variant_id": item.variant.variant_id,
                "sku": item.variant.sku,
                "stock_quantity": item.variant.stock_quantity,
                "product": {
                    "product_id": product.product_id,
                    "product_name": product.product_name,
                    "slug": product.slug,
                    "base_price": float(product.base_price),
                    "sale_price": float(product.sale_price) if product.sale_price else None,
                } if product else None,
                "color": {
                    "color_id": item.variant.color.color_id,
                    "color_name": item.variant.color.color_name,
                    "color_code": item.variant.color.color_code,
                } if item.variant.color else None,
                "size": {
                    "size_id": item.variant.size.size_id,
                    "size_name": item.variant.size.size_name,
                } if item.variant.size else None,
            }
        
        items_response.append({
            "cart_item_id": item.cart_item_id,
            "cart_id": item.cart_id,
            "variant_id": item.variant_id,
            "quantity": item.quantity,
            "added_at": item.added_at,
            "variant": variant_data,
        })
    
    return CartResponse(
        cart_id=cart.cart_id,
        user_id=cart.user_id,
        session_id=cart.session_id,
        created_at=cart.created_at,
        updated_at=cart.updated_at,
        items=items_response,
        total_items=total_items,
        subtotal=subtotal
    )


@router.post("/items", response_model=CartResponse, status_code=status.HTTP_201_CREATED)
async def add_to_cart(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    item_in: CartItemCreate,
) -> CartResponse:
    """
    Thêm một sản phẩm (variant) vào giỏ hàng.
    """
    cart = await cart_crud.get_or_create(
        db=db,
        user_id=current_user.user_id
    )
    
    await cart_item_crud.add_item(
        db=db,
        cart_id=cart.cart_id,
        variant_id=item_in.variant_id,
        quantity=item_in.quantity
    )
    
    return await get_my_cart(db=db, current_user=current_user)


@router.patch("/items/{cart_item_id}", response_model=CartResponse)
async def update_cart_item(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    cart_item_id: int,
    item_in: CartItemUpdate,
) -> CartResponse:
    """
    Cập nhật số lượng của một mục sản phẩm cụ thể trong giỏ hàng.
    """
    cart_item = await cart_item_crud.get(db=db, id=cart_item_id)
    
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )
    
    cart = await cart_crud.get(db=db, id=cart_item.cart_id)
    if cart.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this cart item"
        )
    
    await cart_item_crud.update_quantity(
        db=db,
        cart_item_id=cart_item_id,
        quantity=item_in.quantity
    )
    
    return await get_my_cart(db=db, current_user=current_user)


@router.delete("/items/{cart_item_id}", response_model=CartResponse)
async def remove_from_cart(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    cart_item_id: int,
) -> CartResponse:
    """
    Xóa một mục sản phẩm ra khỏi giỏ hàng.
    """
    cart_item = await cart_item_crud.get(db=db, id=cart_item_id)
    
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )
    
    cart = await cart_crud.get(db=db, id=cart_item.cart_id)
    if cart.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to remove this cart item"
        )
    
    await cart_item_crud.remove_item(db=db, cart_item_id=cart_item_id)
    
    return await get_my_cart(db=db, current_user=current_user)


@router.delete("/clear", response_model=Message)
async def clear_cart(
    *,
    db: SessionDep,
    current_user: CurrentUser,
) -> Message:
    """
    Xóa toàn bộ sản phẩm trong giỏ hàng của người dùng.
    """
    cart = await cart_crud.get_by_user(db=db, user_id=current_user.user_id)
    
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found"
        )
    
    await cart_crud.clear_cart(db=db, cart_id=cart.cart_id)
    
    return Message(message="Cart cleared successfully")


@router.get("/summary", response_model=CartSummary)
async def get_cart_summary(
    db: SessionDep,
    current_user: CurrentUser,
) -> CartSummary:
    """
    Lấy thông tin tóm tắt giỏ hàng.
    Tận dụng kết quả từ get_my_cart để không phải query lại DB.
    """
    cart_response = await get_my_cart(db=db, current_user=current_user)
    
    subtotal = cart_response.subtotal
    total_items = cart_response.total_items
    
    shipping_fee = Decimal("0")
    tax = Decimal("0")
    discount = Decimal("0")
    
    total = subtotal + shipping_fee + tax - discount
    
    return CartSummary(
        subtotal=subtotal,
        discount=discount,
        shipping_fee=shipping_fee,
        tax=tax,
        total=total,
        total_items=total_items
    )


@router.post("/merge", response_model=CartResponse)
async def merge_guest_cart(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    session_id: str,
) -> CartResponse:
    """
    Hợp nhất giỏ hàng. Logic nặng đã nằm ở CRUD, chỉ cần gọi lại get_my_cart.
    """
    await cart_crud.merge_carts(
        db=db,
        user_id=current_user.user_id,
        session_id=session_id
    )
    
    return await get_my_cart(db=db, current_user=current_user)


@router.get("/admin/abandoned", response_model=list[CartResponse])
async def get_abandoned_carts(
    db: SessionDep,
    current_user: User = Depends(require_permission("marketing.abandoned_cart")),
    hours_old: int = Query(24, ge=1, description="Giỏ hàng không hoạt động trong N giờ qua"),
    limit: int = Query(20, ge=1, le=100),
) -> list[CartResponse]:
    """
    Lấy danh sách các giỏ hàng bị bỏ quên.
    """
    carts = await cart_crud.get_abandoned(
        db=db, 
        hours_old=hours_old, 
        limit=limit
    )
    
    response_carts = []
    
    for cart in carts:
        items_response = []
        subtotal = Decimal("0")
        total_items = 0
        
        current_items = cart.items if cart.items else []

        for item in current_items:
            total_items += item.quantity
            variant_data = None
            if item.variant:
                product = item.variant.product
                unit_price = Decimal(0)
                if product:
                    unit_price = product.sale_price if product.sale_price else product.base_price
                
                subtotal += unit_price * item.quantity

                variant_data = {
                    "variant_id": item.variant.variant_id,
                    "sku": item.variant.sku,
                    "stock_quantity": item.variant.stock_quantity,
                    "product": {
                        "product_id": product.product_id,
                        "product_name": product.product_name,
                        "slug": product.slug,
                        "base_price": float(product.base_price),
                        "sale_price": float(product.sale_price) if product.sale_price else None,
                    } if product else None,
                    "color": {
                        "color_id": item.variant.color.color_id,
                        "color_name": item.variant.color.color_name,
                        "color_code": item.variant.color.color_code,
                    } if item.variant.color else None,
                    "size": {
                        "size_id": item.variant.size.size_id,
                        "size_name": item.variant.size.size_name,
                    } if item.variant.size else None,
                }
            
            items_response.append({
                "cart_item_id": item.cart_item_id,
                "cart_id": item.cart_id,
                "variant_id": item.variant_id,
                "quantity": item.quantity,
                "added_at": item.added_at,
                "variant": variant_data,
            })

        response_carts.append(CartResponse(
            cart_id=cart.cart_id,
            user_id=cart.user_id,
            session_id=cart.session_id,
            created_at=cart.created_at,
            updated_at=cart.updated_at,
            items=items_response,
            total_items=total_items,
            subtotal=subtotal
        ))
    
    return response_carts