from typing import List

from fastapi import APIRouter, Query, status, HTTPException, Depends

from app.api.deps import (
    SessionDep,
    CurrentUser,
    require_permission,
)
from app.crud.return_refund import (
    return_request_crud,
    return_item_crud,
    refund_transaction_crud,
)
from app.models.return_refund import (
    ReturnRequestResponse,
    ReturnRequestCreate,
    ReturnRequestUpdate,
    ReturnRequestApprove,
    ReturnRequestReject,
    RefundTransactionResponse,
)
from app.models.enums import ReturnStatusEnum
from app.models.user import User

router = APIRouter()


async def get_return_with_details(db: SessionDep, return_id: int):
    """
    Load thủ công items và refunds để trả về response đầy đủ.
    Dùng cho các hàm Detail / Approve / Reject / Update.
    """
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    from app.models.return_refund import ReturnRequest

    statement = (
        select(ReturnRequest)
        .options(
            selectinload(ReturnRequest.items),
            selectinload(ReturnRequest.refunds)
        )
        .where(ReturnRequest.return_id == return_id)
    )
    
    result = await db.execute(statement)
    return result.scalar_one_or_none()


@router.post("/returns", response_model=ReturnRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_return_request(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    return_in: ReturnRequestCreate,
) -> ReturnRequestResponse:
    """
    Tạo yêu cầu đổi trả hàng cho các đơn hàng đã được giao trong vòng 7 ngày.
    Khách hàng cần cung cấp lý do, mô tả chi tiết và danh sách sản phẩm cần trả.
    """
    return_request = await return_request_crud.create_with_items(
        db=db,
        return_in=return_in,
        user_id=current_user.user_id
    )
    
    return await get_return_with_details(db, return_request.return_id)


@router.get("/returns/me", response_model=List[ReturnRequestResponse])
async def get_my_returns(
    db: SessionDep,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> List[ReturnRequestResponse]:
    """
    Lấy danh sách tất cả các yêu cầu đổi trả hàng đã được tạo bởi người dùng hiện tại.
    """
    return_requests = await return_request_crud.get_by_user(
        db=db,
        user_id=current_user.user_id,
        skip=skip,
        limit=limit
    )
    return return_requests


@router.get("/returns/{return_id}", response_model=ReturnRequestResponse)
async def get_return_request(
    db: SessionDep,
    current_user: CurrentUser,
    return_id: int,
) -> ReturnRequestResponse:
    """
    Xem thông tin chi tiết của một yêu cầu đổi trả cụ thể (Chỉ dành cho chủ sở hữu yêu cầu).
    """
    return_request = await return_request_crud.get(db=db, id=return_id)
    
    if not return_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Return request not found"
        )
    
    if return_request.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this return request"
        )
    
    return await get_return_with_details(db, return_id)


@router.get("/admin/returns", response_model=List[ReturnRequestResponse])
async def list_all_returns(
    db: SessionDep,
    current_user: User = Depends(require_permission("return.view")),
    status_filter: ReturnStatusEnum | None = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> List[ReturnRequestResponse]:
    """
    Liệt kê toàn bộ danh sách yêu cầu đổi trả trên hệ thống (Dành cho Admin).
    Có hỗ trợ lọc theo trạng thái (Đang chờ, Đã duyệt, Đã từ chối).
    """
    if status_filter:
        return_requests = await return_request_crud.get_by_status(
            db=db,
            status=status_filter,
            skip=skip,
            limit=limit
        )
    else:
        return_requests = await return_request_crud.get_all_with_details(
            db=db,
            skip=skip,
            limit=limit
        )
    
    return return_requests


@router.get("/admin/returns/pending/count", response_model=dict)
async def get_pending_returns_count(
    db: SessionDep,
    current_user: User = Depends(require_permission("return.view")),
) -> dict:
    """
    Lấy tổng số lượng yêu cầu đổi trả đang ở trạng thái chờ xử lý (Dành cho Dashboard của Admin).
    """
    count = await return_request_crud.get_pending_count(db=db)
    
    return {"pending_count": count}


@router.post("/admin/returns/{return_id}/approve", response_model=ReturnRequestResponse)
async def approve_return(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("return.manage")),
    return_id: int,
    approve_data: ReturnRequestApprove,
) -> ReturnRequestResponse:
    """
    Phê duyệt yêu cầu đổi trả hàng. Hệ thống sẽ tự động tạo giao dịch hoàn tiền và thông báo cho khách hàng.
    """
    await return_request_crud.approve(
        db=db,
        return_id=return_id,
        refund_amount=approve_data.refund_amount,
        refund_method=approve_data.refund_method,
        processed_note=approve_data.processed_note,
        processed_by=current_user.user_id
    )
    return await get_return_with_details(db, return_id)


@router.post("/admin/returns/{return_id}/reject", response_model=ReturnRequestResponse)
async def reject_return(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("return.manage")),
    return_id: int,
    reject_data: ReturnRequestReject,
) -> ReturnRequestResponse:
    """
    Từ chối yêu cầu đổi trả hàng của khách hàng. Phải cung cấp lý do từ chối rõ ràng.
    """
    await return_request_crud.reject(
        db=db,
        return_id=return_id,
        processed_note=reject_data.processed_note,
        processed_by=current_user.user_id
    )
    return await get_return_with_details(db, return_id)


@router.patch("/admin/returns/{return_id}", response_model=ReturnRequestResponse)
async def update_return(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("return.manage")),
    return_id: int,
    return_in: ReturnRequestUpdate,
) -> ReturnRequestResponse:
    """
    Cập nhật các thông tin liên quan đến yêu cầu đổi trả (Trạng thái, ghi chú xử lý, chi tiết hoàn tiền).
    """
    return_request = await return_request_crud.get(db=db, id=return_id)
    if not return_request:
        raise HTTPException(status_code=404, detail="Return request not found")
    
    await return_request_crud.update(
        db=db,
        db_obj=return_request,
        obj_in=return_in
    )
    return await get_return_with_details(db, return_id)


@router.get("/refunds/{refund_id}", response_model=RefundTransactionResponse)
async def get_refund_status(
    db: SessionDep,
    current_user: CurrentUser,
    refund_id: int,
) -> RefundTransactionResponse:
    """
    Tra cứu trạng thái xử lý của một giao dịch hoàn tiền cụ thể.
    """
    refund = await refund_transaction_crud.get(db=db, id=refund_id)
    if not refund:
        raise HTTPException(status_code=404, detail="Refund not found")
    
    return_request = await return_request_crud.get(db=db, id=refund.return_id)
    if return_request.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return refund


@router.get("/admin/refunds/pending", response_model=List[RefundTransactionResponse])
async def list_pending_refunds(
    db: SessionDep,
    current_user: User = Depends(require_permission("return.view")),
    limit: int = Query(50, ge=1, le=100),
) -> List[RefundTransactionResponse]:
    """
    Liệt kê danh sách các giao dịch hoàn tiền đang chờ thực hiện (Dành cho Admin).
    Hỗ trợ theo dõi các khoản tiền cần trả lại cho khách thông qua cổng thanh toán.
    """
    refunds = await refund_transaction_crud.get_pending(db=db, limit=limit)
    
    return refunds


@router.post("/admin/refunds/{refund_id}/process", response_model=RefundTransactionResponse)
async def process_refund(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("return.manage")),
    refund_id: int,
    gateway_response: str | None = None,
) -> RefundTransactionResponse:
    """
    Xác nhận đã xử lý hoàn tất một giao dịch hoàn tiền sau khi có xác nhận từ cổng thanh toán hoặc ngân hàng.
    """
    refund = await refund_transaction_crud.process_refund(
        db=db,
        refund_id=refund_id,
        gateway_response=gateway_response
    )
    
    return refund