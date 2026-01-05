from decimal import Decimal
from typing import List
from datetime import datetime, date, timezone, timedelta

from fastapi import APIRouter, Query, status, BackgroundTasks, Depends, Request
from fastapi_cache.decorator import cache

from app.api.deps import SessionDep, CurrentUser, OptionalUser ,require_permission
from app.services.mongo_service import mongo_service

from app.crud.product import product as product_crud
from app.crud.order import order as order_crud
from app.crud.user import user as user_crud

from app.models.analytic import (
    SalesReport,
    ProductPerformance,
    CustomerInsights,
    SearchAnalytics,
    DashboardStats,
    SearchTrackRequest,
)
from app.models.user import User
from app.models.enums import OrderStatusEnum

router = APIRouter()

def user_recently_viewed_key_builder(func, namespace: str = "", *args, **kwargs):
    """
    Tạo key cache cho danh sách sản phẩm vừa xem của người dùng.
    """
    current_user = kwargs.get("current_user")
    limit = kwargs.get("limit", 10)
    user_id = current_user.user_id if current_user else "anonymous"
    return f"analytics:recently-viewed:{user_id}:limit:{limit}"

def user_search_history_key_builder(func, namespace: str = "", *args, **kwargs):
    """
    Tạo key cache cho lịch sử tìm kiếm của người dùng.
    """
    current_user = kwargs.get("current_user")
    limit = kwargs.get("limit", 10)
    user_id = current_user.user_id if current_user else "anonymous"
    return f"analytics:search-history:{user_id}:limit:{limit}"


def calculate_growth(current: float, previous: float) -> float:
    """Tính phần trăm tăng trưởng."""
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100, 2)


async def _increment_view_task(product_id: int):
    from app.core.db import async_session_maker
    async with async_session_maker() as session:
        try:
            await product_crud.increment_view_count(db=session, product_id=product_id)
            await session.commit()
        except Exception as e:
            import logging
            logging.error(f"Lỗi khi tăng view count cho product {product_id}: {e}")


@router.post("/track/product/{product_id}", status_code=status.HTTP_200_OK)
async def track_product_view(
    product_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: OptionalUser
):
    """
    Ghi nhận lượt xem sản phẩm.
    Frontend gọi API này ngầm sau khi load trang chi tiết sản phẩm.
    """
    user_id = current_user.user_id if current_user else None
    ip_address = request.client.host

    background_tasks.add_task(
        mongo_service.log_product_view,
        product_id=product_id,
        user_id=user_id,
        ip_address=ip_address
    )

    background_tasks.add_task(_increment_view_task, product_id=product_id)

    return {"status": "tracked", "product_id": product_id}


@router.post("/track/search", status_code=status.HTTP_200_OK)
async def track_search_query(
    body: SearchTrackRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: OptionalUser,
):
    """
    Ghi nhận lịch sử tìm kiếm.
    Frontend gọi API này khi người dùng thực hiện tìm kiếm.
    """
    user_id = current_user.user_id if current_user else None
    
    background_tasks.add_task(
        mongo_service.log_search,
        keyword=body.query,
        user_id=user_id,
        ip_address=request.client.host,
        results_count=body.results_count
    )
    
    return {"status": "tracked", "query": body.query}


@router.get("/me/recently-viewed", response_model=List[dict])
@cache(expire=300, key_builder=user_recently_viewed_key_builder)
async def get_recently_viewed(
    db: SessionDep,
    current_user: CurrentUser,
    limit: int = Query(10, ge=1, le=50),
) -> List[dict]:
    """
    Lấy danh sách sản phẩm người dùng đã xem gần đây (Kết hợp dữ liệu MongoDB và SQL).
    """
    cursor = mongo_service.product_views.find(
        {"user_id": current_user.user_id}
    ).sort("viewed_at", -1).limit(limit * 2)
    
    raw_views = await cursor.to_list(length=limit * 2)
    
    result = []
    seen_products = set()
    
    for view in raw_views:
        p_id = view["product_id"]
        if p_id in seen_products:
            continue
            
        product = await product_crud.get_with_details(db=db, id=p_id)
        if product:
            final_url = None
            if product.images:
                primary_img = next((img for img in product.images if img.is_primary), None)
                final_url = primary_img.image_url if primary_img else product.images[0].image_url
            
            seen_products.add(p_id)
            
            result.append({
                "viewed_at": view["viewed_at"],
                "product": {
                    "product_id": product.product_id,
                    "product_name": product.product_name,
                    "slug": product.slug,
                    "base_price": float(product.base_price),
                    "sale_price": float(product.sale_price) if product.sale_price else None,
                    "image": final_url 
                }
            })
            
        if len(result) >= limit:
            break
            
    return result


@router.get("/me/search-history", response_model=List[dict])
@cache(expire=300, key_builder=user_search_history_key_builder)
async def get_search_history(
    db: SessionDep,
    current_user: CurrentUser,
    limit: int = Query(10, ge=1, le=50),
) -> List[dict]:
    """
    Lấy lịch sử các từ khóa tìm kiếm của người dùng từ MongoDB.
    """
    searches = await mongo_service.get_user_search_history(
        user_id=current_user.user_id,
        limit=limit
    )
    
    return [
        {
            "search_query": s["search_query"],
            "results_count": s.get("results_count", 0),
            "searched_at": s["searched_at"],
        }
        for s in searches
    ]


@router.get("/dashboard", response_model=DashboardStats)
@cache(expire=60)
async def get_dashboard_stats(
    db: SessionDep,
    current_user: User = Depends(require_permission("analytics.view")),
    start_date: date = Query(None),
    end_date: date = Query(None),
    limit: int = Query(5, ge=1, le=20),
) -> DashboardStats:
    """
    Lấy các thông số thống kê tổng quan cho trang Dashboard (Admin).
    """
    if start_date and end_date:
        curr_start = datetime.combine(start_date, datetime.min.time())
        curr_end = datetime.combine(end_date, datetime.max.time())
    else:
        today = datetime.now(timezone(timedelta(hours=7))).date()
        curr_start = datetime.combine(today, datetime.min.time())
        curr_end = datetime.combine(today, datetime.max.time())

    time_diff = curr_end - curr_start
    prev_end = curr_start - timedelta(seconds=1)
    prev_start = prev_end - time_diff

    days_diff = (curr_end.date() - curr_start.date()).days
    days_filter = max(1, days_diff)

    curr_rev = await order_crud.get_revenue_by_date_range(db=db, start_date=curr_start, end_date=curr_end)
    prev_rev = await order_crud.get_revenue_by_date_range(db=db, start_date=prev_start, end_date=prev_end)
    
    curr_orders = await order_crud.count_by_date_range(db=db, start_date=curr_start, end_date=curr_end)
    prev_orders = await order_crud.count_by_date_range(db=db, start_date=prev_start, end_date=prev_end)

    all_time_rev = await order_crud.get_revenue_by_date_range(db=db, start_date=datetime.min, end_date=datetime.max)
    all_time_orders = await order_crud.count_by_date_range(db=db, start_date=datetime.min, end_date=datetime.max)

    pending = await order_crud.count(db=db, filters={"order_status": OrderStatusEnum.PENDING})
    low_stock = await product_crud.count_low_stock(db=db)
    total_users = await user_crud.count(db=db)
    total_prods = await product_crud.count(db=db)

    recent = await order_crud.get_multi(db=db, skip=0, limit=limit)
    
    top_viewed = await mongo_service.get_most_viewed_products(days=days_filter, limit=limit)
    top_products = []
    for item in top_viewed:
        p = await product_crud.get_with_details(db=db, id=item["product_id"])
        if p:
            img = None
            if p.images:
                img = next((i.image_url for i in p.images if i.is_primary), p.images[0].image_url)
            top_products.append({
                "product_id": p.product_id,
                "product_name": p.product_name,
                "price": float(p.base_price),
                "view_count": item["view_count"],
                "image": img
            })

    return DashboardStats(
        period_orders=curr_orders,
        period_revenue=curr_rev,
        revenue_growth=calculate_growth(float(curr_rev), float(prev_rev)),
        orders_growth=calculate_growth(curr_orders, prev_orders),
        all_time_orders=all_time_orders,
        all_time_revenue=all_time_rev,
        pending_orders=pending,
        low_stock_products=low_stock,
        total_customers=total_users,
        total_products=total_prods,
        recent_orders=[
            {
                "order_id": o.order_id,
                "order_number": o.order_number,
                "total_amount": float(o.total_amount),
                "status": o.order_status,
                "created_at": o.created_at
            } for o in recent
        ],
        top_selling_products=top_products
    )


@router.get("/sales", response_model=SalesReport)
@cache(expire=300)
async def get_sales_report(
    db: SessionDep,
    current_user: User = Depends(require_permission("analytics.view")),
    start_date: date = Query(...),
    end_date: date = Query(...),
) -> SalesReport:
    """
    Báo cáo chi tiết về doanh thu, đơn hàng trong một khoảng thời gian cụ thể.
    """
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())
    
    days_diff = (end_date - start_date).days
    period = "daily"
    if days_diff <= 1: period = "hourly"
    elif days_diff > 30: period = "weekly"
    elif days_diff > 90: period = "monthly"

    total_rev = await order_crud.get_revenue_by_date_range(db=db, start_date=start_dt, end_date=end_dt)
    total_ord = await order_crud.count_by_date_range(db=db, start_date=start_dt, end_date=end_dt)
    
    chart_data = await order_crud.get_sales_stats_by_period(
        db=db, start_date=start_dt, end_date=end_dt, period=period
    )

    avg_order = total_rev / total_ord if total_ord > 0 else Decimal(0)

    return SalesReport(
        period=period,
        start_date=start_date,
        end_date=end_date,
        total_orders=total_ord,
        total_revenue=total_rev,
        total_items_sold=0,
        average_order_value=avg_order,
        top_products=[],
        revenue_by_date=chart_data
    )


@router.get("/products/performance", response_model=List[ProductPerformance])
@cache(expire=600)
async def get_product_performance(
    db: SessionDep,
    current_user: User = Depends(require_permission("analytics.view")),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=100),
) -> List[ProductPerformance]:
    """
    Thống kê hiệu suất sản phẩm dựa trên lượt xem, doanh thu và tỷ lệ chuyển đổi.
    """
    top_viewed = await mongo_service.get_most_viewed_products(days=days, limit=limit)
    
    result = []
    for item in top_viewed:
        product = await product_crud.get(db=db, id=item["product_id"])
        if product:
            views_count = item["view_count"]
            sales_count = product.sold_count or 0
            revenue = float(product.base_price) * sales_count
            conversion_rate = (sales_count / views_count * 100) if views_count > 0 else 0
            
            result.append(ProductPerformance(
                product_id=product.product_id,
                product_name=product.product_name,
                views_count=views_count,
                sales_count=sales_count,
                revenue=revenue,
                conversion_rate=conversion_rate,
                average_rating=float(product.rating) if product.rating else None,
                review_count=product.review_count or 0
            ))
    
    return result


@router.get("/search/analytics", response_model=SearchAnalytics)
@cache(expire=600)
async def get_search_analytics(
    db: SessionDep,
    current_user: User = Depends(require_permission("analytics.view")),
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(20, ge=5, le=100),
) -> SearchAnalytics:
    """
    Phân tích dữ liệu tìm kiếm, bao gồm các từ khóa phổ biến và tìm kiếm không có kết quả.
    """
    popular = await mongo_service.get_popular_searches(days=days, limit=limit)
    zero_results = await mongo_service.get_zero_result_searches(days=days, limit=limit*2)
    
    total_searches = sum(item["search_count"] for item in popular)
    unique_searches = len(popular)
    avg_results = 0
    
    return SearchAnalytics(
        period=f"last_{days}_days",
        total_searches=total_searches,
        unique_searches=unique_searches,
        average_results=avg_results,
        top_searches=popular,
        zero_result_searches=[
            {
                "search_query": s["search_query"],
                "searched_at": s["searched_at"],
            }
            for s in zero_results
        ]
    )


@router.get("/customers/insights", response_model=CustomerInsights)
@cache(expire=600)
async def get_customer_insights(
    db: SessionDep,
    current_user: User = Depends(require_permission("analytics.view")),
    days: int = Query(30, ge=1, le=365),
) -> CustomerInsights:
    """
    Phân tích hành vi khách hàng, tỷ lệ quay lại và giá trị vòng đời khách hàng.
    """
    total_customers = await user_crud.count(db=db)
    
    return CustomerInsights(
        total_customers=total_customers,
        new_customers=0,
        returning_customers=0,
        customer_retention_rate=0.0,
        average_lifetime_value=0.0,
        top_customers=[]
    )


@router.get("/most-viewed-products", response_model=List[dict])
@cache(expire=300)
async def get_most_viewed_products(
    db: SessionDep,
    current_user: User = Depends(require_permission("analytics.view")),
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(10, ge=1, le=50),
) -> List[dict]:
    """
    Lấy danh sách các sản phẩm có lượt xem nhiều nhất trong khoảng thời gian xác định.
    """
    views = await mongo_service.get_most_viewed_products(days=days, limit=limit)
    return views


@router.get("/popular-searches", response_model=List[dict])
@cache(expire=300)
async def get_popular_searches(
    db: SessionDep,
    current_user: User = Depends(require_permission("analytics.view")),
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(10, ge=1, le=50),
) -> List[dict]:
    """
    Lấy danh sách các từ khóa được tìm kiếm nhiều nhất trên hệ thống.
    """
    searches = await mongo_service.get_popular_searches(days=days, limit=limit)
    return searches