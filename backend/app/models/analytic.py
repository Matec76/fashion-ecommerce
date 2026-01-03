from datetime import datetime, date
from typing import List, Optional, Dict, Any
from decimal import Decimal
from sqlmodel import SQLModel


class ChartDataPoint(SQLModel):
    date: str
    revenue: float
    total_orders: int

class TopProductStats(SQLModel):
    product_id: int
    product_name: str
    price: float
    view_count: int
    image: Optional[str] = None

class ProductViewResponse(SQLModel):
    id: str
    product_id: int
    user_id: Optional[int] = None
    viewed_at: datetime

class SearchHistoryResponse(SQLModel):
    search_query: str
    results_count: int
    searched_at: datetime

class SalesReport(SQLModel):
    period: str
    start_date: date
    end_date: date
    total_orders: int
    total_revenue: Decimal
    total_items_sold: int
    average_order_value: Decimal
    top_products: List[Dict[str, Any]]
    revenue_by_date: List[ChartDataPoint]

class ProductPerformance(SQLModel):
    product_id: int
    product_name: str
    views_count: int
    sales_count: int
    revenue: float
    conversion_rate: float
    average_rating: Optional[float] = None
    review_count: int

class CustomerInsights(SQLModel):
    total_customers: int
    new_customers: int
    returning_customers: int
    customer_retention_rate: float
    average_lifetime_value: float
    top_customers: List[Dict[str, Any]]

class SearchAnalytics(SQLModel):
    period: str
    total_searches: int
    unique_searches: int
    average_results: float
    top_searches: List[Dict[str, Any]]
    zero_result_searches: List[Dict[str, Any]]

class DashboardStats(SQLModel):
    period_orders: int
    period_revenue: Decimal
    revenue_growth: float
    orders_growth: float
    all_time_orders: int
    all_time_revenue: Decimal
    pending_orders: int
    low_stock_products: int
    total_customers: int
    total_products: int
    recent_orders: List[Dict[str, Any]]
    top_selling_products: List[Dict[str, Any]]


class SearchTrackRequest(SQLModel):
    query: str
    results_count: int