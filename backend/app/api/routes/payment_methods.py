from typing import List, Optional, Any
from decimal import Decimal

from fastapi import APIRouter, Query, status, HTTPException, Request, Response
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

from app.api.deps import SessionDep, CurrentUser, SuperUser, PaginationDep
from app.crud.payment_method import payment_method as payment_method_crud
from app.models.payment_method import (
    PaymentMethodResponse, PaymentMethodsResponse, PaymentMethodCreate,
    PaymentMethodUpdate, PaymentMethodStatistics
)
from app.models.common import Message

router = APIRouter()

def payment_list_key_builder(func, namespace: str = "", request: Request = None, response: Response = None, *args, **kwargs):
    prefix = FastAPICache.get_prefix() or ""
    query_params = sorted(request.query_params.items())
    query_string = "&".join([f"{k}={v}" for k, v in query_params])
    suffix = f":{query_string}" if query_string else ":active_default"
    return f"{prefix}:{namespace}{suffix}"

def payment_detail_key_builder(func, namespace: str = "", *args, **kwargs):
    prefix = FastAPICache.get_prefix() or ""
    method_id = kwargs.get("method_id")
    method_code = kwargs.get("method_code")
    identifier = method_id if method_id else method_code
    return f"{prefix}:{namespace}:{identifier}"

async def invalidate_payment_method_cache():
    backend = FastAPICache.get_backend()
    prefix = FastAPICache.get_prefix() or ""
    namespaces = ["payment_method:list", "payment_method:detail", "payment_method:stats"]
    
    if hasattr(backend, "redis"):
        for ns in namespaces:
            pattern = f"{prefix}:{ns}*"
            async for key in backend.redis.scan_iter(match=pattern):
                await backend.redis.delete(key)

@router.get("/", response_model=PaymentMethodsResponse)
@cache(expire=3600, namespace="payment_method:list", key_builder=payment_list_key_builder)
async def get_payment_methods(request: Request, db: SessionDep) -> PaymentMethodsResponse:
    methods = await payment_method_crud.get_active(db=db)
    return PaymentMethodsResponse(data=methods, count=len(methods))

@router.get("/{method_id}", response_model=PaymentMethodResponse)
@cache(expire=3600, namespace="payment_method:detail", key_builder=payment_detail_key_builder)
async def get_payment_method(db: SessionDep, method_id: int) -> PaymentMethodResponse:
    method = await payment_method_crud.get(db=db, id=method_id)
    if not method:
        raise HTTPException(status_code=404, detail="Payment method not found")
    return method

@router.get("/code/{method_code}", response_model=PaymentMethodResponse)
@cache(expire=3600, namespace="payment_method:detail", key_builder=payment_detail_key_builder)
async def get_payment_method_by_code(db: SessionDep, method_code: str) -> PaymentMethodResponse:
    method = await payment_method_crud.get_by_code(db=db, method_code=method_code)
    if not method:
        raise HTTPException(status_code=404, detail=f"Payment method '{method_code}' not found")
    return method

@router.post("/validate", response_model=dict)
async def validate_payment_method(
    *, db: SessionDep, current_user: CurrentUser, payment_method_id: int, order_amount: Decimal
) -> dict:
    is_valid, error_message = await payment_method_crud.validate_for_order(
        db=db, payment_method_id=payment_method_id, order_amount=order_amount
    )
    return {
        "is_valid": is_valid, "error_message": error_message,
        "payment_method_id": payment_method_id, "order_amount": order_amount
    }

@router.post("/calculate-fee", response_model=dict)
async def calculate_processing_fee(
    *, db: SessionDep, current_user: CurrentUser, payment_method_id: int, order_amount: Decimal
) -> dict:
    method = await payment_method_crud.get(db=db, id=payment_method_id)
    if not method:
        raise HTTPException(status_code=404, detail="Payment method not found")
    
    fee = await payment_method_crud.calculate_processing_fee(
        db=db, payment_method_id=payment_method_id, order_amount=order_amount
    )
    return {
        "payment_method_id": payment_method_id, "payment_method_name": method.method_name,
        "order_amount": order_amount, "processing_fee": fee,
        "processing_fee_type": method.processing_fee_type, "total_amount": order_amount + fee
    }

@router.get("/admin/all", response_model=PaymentMethodsResponse)
@cache(expire=300, namespace="payment_method:list", key_builder=payment_list_key_builder)
async def get_all_payment_methods_admin(
    request: Request, db: SessionDep, current_user: SuperUser, pagination: PaginationDep
) -> PaymentMethodsResponse:
    methods = await payment_method_crud.get_multi(
        db=db, skip=pagination.get_offset(), limit=pagination.get_limit(), order_by="display_order"
    )
    total = await payment_method_crud.count(db=db)
    return PaymentMethodsResponse(data=methods, count=total)

@router.post("/admin", response_model=PaymentMethodResponse, status_code=status.HTTP_201_CREATED)
async def create_payment_method(
    *, db: SessionDep, current_user: SuperUser, method_in: PaymentMethodCreate
) -> PaymentMethodResponse:
    existing = await payment_method_crud.get_by_code(db=db, method_code=method_in.method_code)
    if existing:
        raise HTTPException(status_code=400, detail=f"Code '{method_in.method_code}' exists")
    
    existing_name = await payment_method_crud.get_by_name(db=db, method_name=method_in.method_name)
    if existing_name:
        raise HTTPException(status_code=400, detail=f"Name '{method_in.method_name}' exists")
    
    method = await payment_method_crud.create(db=db, obj_in=method_in)
    await invalidate_payment_method_cache()
    return method

@router.patch("/admin/{method_id}", response_model=PaymentMethodResponse)
async def update_payment_method(
    *, db: SessionDep, current_user: SuperUser, method_id: int, method_in: PaymentMethodUpdate
) -> PaymentMethodResponse:
    method = await payment_method_crud.get(db=db, id=method_id)
    if not method:
        raise HTTPException(status_code=404, detail="Payment method not found")
    
    if method_in.method_code and method_in.method_code != method.method_code:
        existing = await payment_method_crud.get_by_code(db=db, method_code=method_in.method_code)
        if existing:
            raise HTTPException(status_code=400, detail=f"Code '{method_in.method_code}' exists")
    
    if method_in.method_name and method_in.method_name != method.method_name:
        existing_name = await payment_method_crud.get_by_name(db=db, method_name=method_in.method_name)
        if existing_name:
            raise HTTPException(status_code=400, detail=f"Name '{method_in.method_name}' exists")
    
    updated_method = await payment_method_crud.update(db=db, db_obj=method, obj_in=method_in)
    await invalidate_payment_method_cache()
    return updated_method

@router.delete("/admin/{method_id}", response_model=Message)
async def delete_payment_method(*, db: SessionDep, current_user: SuperUser, method_id: int) -> Message:
    method = await payment_method_crud.get(db=db, id=method_id)
    if not method:
        raise HTTPException(status_code=404, detail="Payment method not found")
    
    await payment_method_crud.remove(db=db, id=method_id)
    await invalidate_payment_method_cache()
    return Message(message=f"Payment method '{method.method_name}' deleted successfully")

@router.patch("/admin/{method_id}/toggle", response_model=PaymentMethodResponse)
async def toggle_payment_method(*, db: SessionDep, current_user: SuperUser, method_id: int) -> PaymentMethodResponse:
    method = await payment_method_crud.toggle_active(db=db, id=method_id)
    if not method:
        raise HTTPException(status_code=404, detail="Payment method not found")
    
    await invalidate_payment_method_cache()
    return method

@router.get("/admin/{method_id}/statistics", response_model=PaymentMethodStatistics)
@cache(expire=300, namespace="payment_method:stats", key_builder=payment_detail_key_builder)
async def get_payment_method_statistics(db: SessionDep, current_user: SuperUser, method_id: int) -> PaymentMethodStatistics:
    method = await payment_method_crud.get(db=db, id=method_id)
    if not method:
        raise HTTPException(status_code=404, detail="Payment method not found")
    
    stats = await payment_method_crud.get_statistics(db=db, payment_method_id=method_id)
    return PaymentMethodStatistics(payment_method_id=method_id, method_name=method.method_name, **stats)

@router.get("/admin/most-used", response_model=List[dict])
@cache(expire=600, namespace="payment_method:stats", key_builder=payment_list_key_builder)
async def get_most_used_payment_methods(
    request: Request, db: SessionDep, current_user: SuperUser, limit: int = Query(5, ge=1, le=20)
) -> List[dict]:
    most_used = await payment_method_crud.get_most_used(db=db, limit=limit)
    return [
        {
            "payment_method_id": m.payment_method_id, "method_code": m.method_code,
            "method_name": m.method_name, "transaction_count": c, "is_active": m.is_active
        } for m, c in most_used
    ]