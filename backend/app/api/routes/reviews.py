from fastapi import APIRouter, Query, status, HTTPException, Depends, File, UploadFile
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

from app.api.deps import (
    SessionDep,
    CurrentUser,
    require_permission
)

from app.crud.review import product_question as question_crud

from app.services.mongo_service import mongo_service

from app.models.review import (
    ReviewResponse,
    ReviewDetailResponse,
    ReviewCreate,
    ReviewUpdate,
    ReviewApprove,
    ProductQuestionResponse,
    ProductQuestionCreate,
    ProductQuestionAnswer,
)
from sqlmodel import select
from app.models.enums import OrderStatusEnum
from app.models.order import Order, OrderItem
from app.models.product import ProductVariant
from app.models.user import User
from app.models.common import Message
from app.core.config import settings
from app.core.storage import S3Storage

router = APIRouter()


def review_list_key_builder(func, namespace: str = "", *args, **kwargs):
    product_id = kwargs.get("product_id") or kwargs.get("kwargs", {}).get("product_id")
    prefix = FastAPICache.get_prefix() or ""
    return f"{prefix}:{namespace}:product:{product_id}"

async def invalidate_product_reviews(product_id: int):
    """
    Chỉ xóa cache review của đúng sản phẩm này.
    """
    try:
        backend = FastAPICache.get_backend()
        prefix = FastAPICache.get_prefix() or ""
        namespace = "reviews"
        
        pattern = f"{prefix}:{namespace}:product:{product_id}*"
        
        if hasattr(backend, "redis"):
            async for key in backend.redis.scan_iter(match=pattern):
                await backend.redis.delete(key)
    except Exception as e:
        import logging
        logging.error(f"Error invalidating review cache: {e}")


def question_list_key_builder(func, namespace: str = "", *args, **kwargs):
    product_id = kwargs.get("product_id") or kwargs.get("kwargs", {}).get("product_id")
    prefix = FastAPICache.get_prefix() or ""
    return f"{prefix}:{namespace}:product:{product_id}"

async def invalidate_product_questions(product_id: int):
    """
    Chỉ xóa cache câu hỏi của đúng sản phẩm này.
    """
    try:
        backend = FastAPICache.get_backend()
        prefix = FastAPICache.get_prefix() or ""
        namespace = "questions"
        
        pattern = f"{prefix}:{namespace}:product:{product_id}*"
        
        if hasattr(backend, "redis"):
            async for key in backend.redis.scan_iter(match=pattern):
                await backend.redis.delete(key)
    except Exception as e:
        import logging
        logging.error(f"Error invalidating question cache: {e}")

@router.post("/upload-image", response_model=dict)
async def upload_review_image(
    current_user: CurrentUser,
    file: UploadFile = File(...),
):
    """
    Tải lên hình ảnh minh họa cho đánh giá sản phẩm lên kho lưu trữ S3.
    """
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400, 
            detail="Chỉ chấp nhận các định dạng ảnh: JPEG, PNG, WEBP"
        )
    
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="Ảnh quá lớn, vui lòng chọn ảnh nhẹ hơn")

    try:
        result = await S3Storage.upload_file(
            file=file.file,
            filename=file.filename,
            folder=settings.S3_REVIEWS_FOLDER,
            content_type=file.content_type,
        )

        final_url = result.get("cdn_url") or result["file_url"]

        return {"url": final_url}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi upload: {str(e)}")


@router.get("/products/{product_id}", response_model=list[ReviewDetailResponse])
@cache(expire=60, namespace="reviews", key_builder=review_list_key_builder)
async def get_product_reviews(
    product_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    rating: int | None = Query(None, ge=1, le=5, description="Filter by rating"),
) -> list[ReviewDetailResponse]:
    """
    Lấy danh sách các đánh giá của một sản phẩm cụ thể (Có hỗ trợ lọc theo số sao và xác thực mua hàng).
    """
    reviews = await mongo_service.get_reviews_by_product(
        product_id=product_id,
        skip=skip,
        limit=limit,
        rating=rating,
    )
    

    response = []
    for r in reviews:
        response.append(ReviewDetailResponse(
            review_id=r["review_id"],
            product_id=r["product_id"],
            user_id=r["user_id"],
            order_id=r.get("order_id"),
            rating=r["rating"],
            title=r.get("title"),
            comment=r.get("comment"),
            is_approved=r.get("is_approved", True),
            helpful_count=r.get("helpful_count", 0),
            created_at=r["created_at"],
            updated_at=r.get("updated_at", r["created_at"]),
            images=r.get("images", []),
            user={
                "user_id": r["user_id"],
                "full_name": r.get("user_name", "Unknown User"),
                "avatar": r.get("user_avatar")
            }
        ))
    
    return response


@router.get("/products/{product_id}/summary", response_model=dict)
@cache(expire=60, namespace="reviews", key_builder=review_list_key_builder)
async def get_review_summary(
    product_id: int,
) -> dict:
    """
    Lấy thông tin tóm tắt về điểm đánh giá trung bình và số lượng đánh giá theo từng mức sao.
    """
    return await mongo_service.get_rating_summary(product_id=product_id)


@router.get("/{review_id}", response_model=ReviewDetailResponse)
async def get_review(
    review_id: str,
) -> ReviewDetailResponse:
    """
    Xem thông tin chi tiết của một đánh giá sản phẩm cụ thể qua ID.
    """
    review = await mongo_service.get_review(review_id)
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    return ReviewDetailResponse(
        review_id=review["review_id"],
        product_id=review["product_id"],
        user_id=review["user_id"],
        order_id=review.get("order_id"),
        rating=review["rating"],
        title=review.get("title"),
        comment=review.get("comment"),
        is_approved=review.get("is_approved", True),
        helpful_count=review.get("helpful_count", 0),
        created_at=review["created_at"],
        updated_at=review.get("updated_at", review["created_at"]),
        images=review.get("images", []),
        user={
            "user_id": review["user_id"],
            "full_name": review.get("user_name", "Unknown User"),
            "avatar": review.get("user_avatar")
        }
    )


@router.get("/me/reviews", response_model=list[ReviewResponse])
async def get_my_reviews(
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> list[ReviewResponse]:
    """
    Lấy danh sách tất cả các đánh giá sản phẩm mà người dùng hiện tại đã viết.
    """
    reviews = await mongo_service.get_reviews_by_user(
        user_id=current_user.user_id,
        skip=skip,
        limit=limit
    )
    
    return [
        ReviewResponse(
            review_id=r["review_id"],
            product_id=r["product_id"],
            user_id=r["user_id"],
            order_id=r.get("order_id"),
            rating=r["rating"],
            title=r.get("title"),
            comment=r.get("comment"),
            is_approved=r.get("is_approved", False),
            helpful_count=r.get("helpful_count", 0),
            created_at=r["created_at"],
            updated_at=r.get("updated_at", r["created_at"]),
            images=r.get("images", [])
        )
        for r in reviews
    ]


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    review_in: ReviewCreate,
) -> ReviewResponse:
    """
    Gửi một đánh giá mới cho sản phẩm (Yêu cầu xác thực đơn hàng nếu muốn gắn nhãn Verified Purchase).
    """
    statement = (
        select(Order)
        .join(OrderItem, Order.order_id == OrderItem.order_id)
        .join(ProductVariant, OrderItem.variant_id == ProductVariant.variant_id) 
        .where(Order.user_id == current_user.user_id)
        .where(ProductVariant.product_id == review_in.product_id) 
        .where(Order.order_status == OrderStatusEnum.COMPLETED)
        .order_by(Order.created_at.desc())
    )
        
    result = await db.execute(statement)
    valid_order = result.scalars().first()

    if not valid_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bạn chưa mua sản phẩm này hoặc đơn hàng chưa thành công (COMPLETED)."
        )
    last_name = current_user.last_name or ""
    first_name = current_user.first_name or ""
    full_name = f"{last_name} {first_name}".strip()

    review_data = {
        "product_id": review_in.product_id,
        "user_id": current_user.user_id,
        "user_name": full_name,
        "user_avatar": current_user.avatar_url,
        "order_id": valid_order.order_id,
        "rating": review_in.rating,
        "title": review_in.title,
        "comment": review_in.comment,
        "images": review_in.image_urls or [],
    }
    
    review_id = await mongo_service.create_review(review_data)
    
    await invalidate_product_reviews(review_in.product_id)
    
    return ReviewResponse(
        review_id=review_id,
        **review_data,
        helpful_count=0
    )


@router.patch("/{review_id}", response_model=ReviewResponse)
async def update_review(
    *,
    current_user: CurrentUser,
    review_id: str,
    review_in: ReviewUpdate,
) -> ReviewResponse:
    """
    Chỉnh sửa nội dung đánh giá sản phẩm của người dùng hiện tại.
    """
    review = await mongo_service.get_review(review_id)
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    if review["user_id"] != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = review_in.model_dump(exclude_unset=True)
    if "image_urls" in update_data:
        update_data["images"] = update_data.pop("image_urls")
        
    updated = await mongo_service.update_review(review_id, update_data)
    
    await invalidate_product_reviews(review["product_id"])
    
    return ReviewResponse(
        review_id=updated["review_id"],
        product_id=updated["product_id"],
        user_id=updated["user_id"],
        order_id=updated.get("order_id"),
        rating=updated["rating"],
        title=updated.get("title"),
        comment=updated.get("comment"),
        is_approved=updated.get("is_approved", False),
        helpful_count=updated.get("helpful_count", 0),
        created_at=updated["created_at"],
        updated_at=updated.get("updated_at"),
        images=updated.get("images", [])
    )


@router.delete("/{review_id}", response_model=Message)
async def delete_my_review(
    current_user: CurrentUser,
    review_id: str,
) -> Message:
    """
    User tự xóa đánh giá của mình.
    """
    review = await mongo_service.get_review(review_id)
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    if review["user_id"] != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await mongo_service.delete_review(review_id)
    await invalidate_product_reviews(review["product_id"])
    
    return Message(message="Review deleted successfully")


@router.delete("/admin/{review_id}", response_model=Message)
async def delete_review_admin(
    review_id: str,
    current_user: User = Depends(require_permission("review.manage")),
) -> Message:
    """
    Admin xóa đánh giá vi phạm (Spam, thô tục...).
    """
    review = await mongo_service.get_review(review_id)
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    await mongo_service.delete_review(review_id)
    
    await mongo_service.push_log({
        "admin_id": current_user.user_id,
        "action": "DELETE_REVIEW",
        "target_id": review_id,
        "details": f"Admin xóa review vi phạm của user {review.get('user_id')}"
    })
    
    await invalidate_product_reviews(review["product_id"])
    
    return Message(message="Admin deleted review successfully")


@router.post("/{review_id}/helpful", response_model=Message)
async def mark_review_helpful(
    current_user: CurrentUser,
    review_id: str,
) -> Message:
    """
    Đánh dấu một đánh giá là hữu ích (Helpful) hoặc hủy bỏ hành động này.
    """
    count = await mongo_service.toggle_helpful(review_id, current_user.user_id)
    review = await mongo_service.get_review(review_id)
    if review:
        await invalidate_product_reviews(review["product_id"])
    
    return Message(message=f"Review helpful updated. Total: {count}")


@router.get("/pending/all", response_model=list[ReviewResponse])
async def get_pending_reviews(
    current_user: User = Depends(require_permission("review.manage")),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[ReviewResponse]:
    """
    Liệt kê toàn bộ các đánh giá đang chờ kiểm duyệt (Dành cho Admin).
    """
    reviews = await mongo_service.get_pending_reviews(skip=skip, limit=limit)
    
    return [
        ReviewResponse(
            review_id=r["review_id"],
            product_id=r["product_id"],
            user_id=r["user_id"],
            order_id=r.get("order_id"),
            rating=r["rating"],
            title=r.get("title"),
            comment=r.get("comment"),
            is_approved=r.get("is_approved", False),
            helpful_count=r.get("helpful_count", 0),
            created_at=r["created_at"],
            updated_at=r.get("updated_at"),
            images=r.get("images", [])
        )
        for r in reviews
    ]


@router.post("/{review_id}/approve", response_model=ReviewResponse)
async def approve_review(
    review_id: str,
    approve_data: ReviewApprove,
    current_user: User = Depends(require_permission("review.manage")),
) -> ReviewResponse:
    """
    Phê duyệt hoặc từ chối công khai một đánh giá sản phẩm (Dành cho Admin).
    """
    result = await mongo_service.approve_review(review_id, approve_data.is_approved)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail="Review rejected and deleted"
        )

    await invalidate_product_reviews(result["product_id"])
        
    return ReviewResponse(
        review_id=result["review_id"],
        product_id=result["product_id"],
        user_id=result["user_id"],
        order_id=result.get("order_id"),
        rating=result["rating"],
        title=result.get("title"),
        comment=result["comment"],
        is_approved=result.get("is_approved", True),
        helpful_count=result.get("helpful_count", 0),
        created_at=result["created_at"],
        updated_at=result.get("updated_at"),
        images=result.get("images", [])
    )



@router.get("/products/{product_id}/questions", response_model=list[ProductQuestionResponse])
@cache(expire=600, namespace="questions", key_builder=question_list_key_builder)
async def get_product_questions(
    db: SessionDep,
    product_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> list[ProductQuestionResponse]:
    """
    Lấy danh sách các câu hỏi và câu trả lời công khai của một sản phẩm.
    """
    questions = await question_crud.get_by_product(
        db=db,
        product_id=product_id,
        public_only=True,
        skip=skip,
        limit=limit
    )
    
    return [
        ProductQuestionResponse(
            question_id=q.question_id,
            product_id=q.product_id,
            user_id=q.user_id,
            question=q.question,
            answer=q.answer,
            answered_by=q.answered_by,
            is_public=q.is_public,
            answered_at=q.answered_at,
            created_at=q.created_at,
            user={
    "user_id": q.user.user_id,
    "full_name": f"{q.user.last_name or ''} {q.user.first_name or ''}".strip(),
} if q.user else None,
answerer={
    "user_id": q.answerer.user_id,
    "full_name": f"{q.answerer.last_name or ''} {q.answerer.first_name or ''}".strip(),
} if q.answerer else None
        )
        for q in questions
    ]


@router.post("/questions", response_model=ProductQuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_question(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    question_in: ProductQuestionCreate,
) -> ProductQuestionResponse:
    """
    Gửi một câu hỏi mới về sản phẩm.
    """
    question = await question_crud.create_question(
        db=db,
        user_id=current_user.user_id,
        product_id=question_in.product_id,
        question=question_in.question
    )
    
    await invalidate_product_questions(question_in.product_id)
    
    return ProductQuestionResponse(
        question_id=question.question_id,
        product_id=question.product_id,
        user_id=question.user_id,
        question=question.question,
        answer=question.answer,
        answered_by=question.answered_by,
        is_public=question.is_public,
        answered_at=question.answered_at,
        created_at=question.created_at,
        user=None,
        answerer=None
    )


@router.get("/me/questions", response_model=list[ProductQuestionResponse])
async def get_my_questions(
    db: SessionDep,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> list[ProductQuestionResponse]:
    """
    Lấy danh sách các câu hỏi mà người dùng hiện tại đã gửi.
    """
    questions = await question_crud.get_by_user(
        db=db,
        user_id=current_user.user_id,
        skip=skip,
        limit=limit
    )
    
    return [
        ProductQuestionResponse(
            question_id=q.question_id,
            product_id=q.product_id,
            user_id=q.user_id,
            question=q.question,
            answer=q.answer,
            answered_by=q.answered_by,
            is_public=q.is_public,
            answered_at=q.answered_at,
            created_at=q.created_at,
            user={
                "user_id": current_user.user_id,
                "full_name": f"{current_user.last_name or ''} {current_user.first_name or ''}".strip(),
            },
            answerer={
                "user_id": q.answerer.user_id,
                "full_name": f"{q.answerer.last_name or ''} {q.answerer.first_name or ''}".strip(),
            } if q.answerer else None
        )
        for q in questions
    ]


@router.get("/questions/unanswered", response_model=list[ProductQuestionResponse])
async def get_unanswered_questions(
    db: SessionDep,
    current_user: User = Depends(require_permission("review.manage")),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[ProductQuestionResponse]:
    """
    Lấy danh sách các câu hỏi chưa được trả lời (Dành cho Admin).
    """
    questions = await question_crud.get_unanswered(
        db=db,
        skip=skip,
        limit=limit
    )
    
    return [
        ProductQuestionResponse(
            question_id=q.question_id,
            product_id=q.product_id,
            user_id=q.user_id,
            question=q.question,
            answer=q.answer,
            answered_by=q.answered_by,
            is_public=q.is_public,
            answered_at=q.answered_at,
            created_at=q.created_at,
            user={
                "user_id": q.user.user_id,
                "full_name": f"{q.user.last_name or ''} {q.user.first_name or ''}".strip(),
            } if q.user else None,
            answerer=None
        )
        for q in questions
    ]


@router.post("/questions/{question_id}/answer", response_model=ProductQuestionResponse)
async def answer_question(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("review.manage")),
    question_id: int,
    answer_data: ProductQuestionAnswer,
) -> ProductQuestionResponse:
    """
    Gửi câu trả lời cho một câu hỏi của khách hàng (Dành cho Admin).
    """
    try:
        question = await question_crud.answer_question(
            db=db,
            question_id=question_id,
            answer=answer_data.answer,
            answered_by=current_user.user_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    await invalidate_product_questions(question.product_id)
    
    return ProductQuestionResponse(
        question_id=question.question_id,
        product_id=question.product_id,
        user_id=question.user_id,
        question=question.question,
        answer=question.answer,
        answered_by=question.answered_by,
        is_public=question.is_public,
        answered_at=question.answered_at,
        created_at=question.created_at,
       user={
            "user_id": question.user.user_id,
            "full_name": f"{question.user.last_name or ''} {question.user.first_name or ''}".strip(),
        } if question.user else None,
        answerer={
            "user_id": current_user.user_id,
            "full_name": f"{current_user.last_name or ''} {current_user.first_name or ''}".strip(),
        }
    )


@router.delete("/questions/{question_id}", response_model=Message)
async def delete_my_question(
    db: SessionDep,
    current_user: CurrentUser,
    question_id: int,
) -> Message:
    """
    User tự xóa câu hỏi của chính mình.
    """
    question = await question_crud.get(db=db, id=question_id)
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    if question.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Bạn không có quyền xóa câu hỏi này"
        )
    
    await question_crud.delete(db=db, id=question_id)
    await invalidate_product_questions(question.product_id)
    
    return Message(message="Đã xóa câu hỏi thành công")


@router.delete("/admin/questions/{question_id}", response_model=Message)
async def delete_question_admin(
    db: SessionDep,
    question_id: int,
    current_user: User = Depends(require_permission("review.manage")),
) -> Message:
    """
    Admin xóa câu hỏi vi phạm (Spam, thô tục...).
    """
    question = await question_crud.get(db=db, id=question_id)
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    await question_crud.delete(db=db, id=question_id)
    
    await mongo_service.push_log({
        "admin_id": current_user.user_id,
        "action": "DELETE_QUESTION",
        "target_id": question_id,
        "details": f"Admin xóa câu hỏi ID {question_id}"
    })
    
    await invalidate_product_questions(question.product_id)
    
    return Message(message="Admin đã xóa câu hỏi thành công")