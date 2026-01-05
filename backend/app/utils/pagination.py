from typing import Generic, TypeVar, Any
from math import ceil

from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings


T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters."""
    
    page: int = 1
    page_size: int = settings.DEFAULT_PAGE_SIZE
    
    def get_offset(self) -> int:
        """Get offset for SQL query."""
        return (self.page - 1) * self.page_size
    
    def get_limit(self) -> int:
        """Get limit for SQL query."""
        return min(self.page_size, settings.MAX_PAGE_SIZE)


class PageResponse(BaseModel, Generic[T]):
    """Paginated response."""
    
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    
    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int
    ) -> "PageResponse[T]":
        """
        Create paginated response.
        
        Args:
            items: List of items
            total: Total count
            page: Current page
            page_size: Page size
            
        Returns:
            PageResponse instance
        """
        total_pages = ceil(total / page_size) if page_size > 0 else 0
        
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )


async def paginate(
    db: AsyncSession,
    query: Any,
    page: int = 1,
    page_size: int = settings.DEFAULT_PAGE_SIZE
) -> tuple[list, int]:
    """
    Paginate SQLAlchemy query.
    
    Args:
        db: Database session
        query: SQLAlchemy select statement
        page: Page number (1-indexed)
        page_size: Items per page
        
    Returns:
        Tuple (items, total_count)
        
    Example:
        >>> stmt = select(Product).where(Product.is_active == True)
        >>> items, total = await paginate(db, stmt, page=1, page_size=20)
    """
    page_size = min(page_size, settings.MAX_PAGE_SIZE)
    page = max(1, page)
    count_query = select(func.count()).select_from(query.alias())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    offset = (page - 1) * page_size
    paginated_query = query.offset(offset).limit(page_size)
    result = await db.execute(paginated_query)
    items = result.scalars().all()
    
    return items, total


async def paginate_response(
    db: AsyncSession,
    query: Any,
    page: int = 1,
    page_size: int = settings.DEFAULT_PAGE_SIZE
) -> PageResponse:
    """
    Get paginated response directly.
    
    Args:
        db: Database session
        query: SQLAlchemy select statement
        page: Page number
        page_size: Items per page
        
    Returns:
        PageResponse instance
    """
    items, total = await paginate(db, query, page, page_size)
    
    return PageResponse.create(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


def get_pagination_links(
    base_url: str,
    page: int,
    total_pages: int,
    page_size: int
) -> dict[str, str | None]:
    """
    Generate pagination links (for API responses).
    
    Args:
        base_url: Base API URL
        page: Current page
        total_pages: Total pages
        page_size: Page size
        
    Returns:
        Dict with pagination links
        
    Example:
        {
            "self": "/api/v1/products?page=2&page_size=20",
            "first": "/api/v1/products?page=1&page_size=20",
            "last": "/api/v1/products?page=10&page_size=20",
            "next": "/api/v1/products?page=3&page_size=20",
            "prev": "/api/v1/products?page=1&page_size=20"
        }
    """
    def build_url(p: int) -> str:
        return f"{base_url}?page={p}&page_size={page_size}"
    
    links = {
        "self": build_url(page),
        "first": build_url(1),
        "last": build_url(total_pages),
        "next": build_url(page + 1) if page < total_pages else None,
        "prev": build_url(page - 1) if page > 1 else None,
    }
    
    return links