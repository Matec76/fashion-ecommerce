from datetime import datetime, timezone, timedelta
from typing import TYPE_CHECKING, Optional, List, Any, Dict

from sqlmodel import Field, Relationship, SQLModel, Column, TIMESTAMP, Text
from sqlalchemy import text

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.product import Product


class ReviewBase(SQLModel):
    rating: int = Field(ge=1, le=5)
    title: Optional[str] = Field(default=None, max_length=255)
    comment: Optional[str] = None

class ReviewCreate(ReviewBase):
    product_id: int
    order_id: Optional[int] = None
    image_urls: Optional[List[str]] = None

class ReviewUpdate(SQLModel):
    rating: Optional[int] = None
    title: Optional[str] = None
    comment: Optional[str] = None
    image_urls: Optional[List[str]] = None

class ReviewApprove(SQLModel):
    is_approved: bool

class ReviewResponse(ReviewBase):
    review_id: str
    product_id: int
    user_id: int
    order_id: Optional[int] = None
    is_approved: bool
    helpful_count: int
    created_at: datetime
    updated_at: datetime
    images: List[str] = []

class ReviewDetailResponse(ReviewResponse):
    user: Optional[Dict[str, Any]] = None

class ProductQuestionBase(SQLModel):
    question: str = Field(sa_column=Column(Text))

class ProductQuestion(ProductQuestionBase, table=True):
    __tablename__ = "product_questions"

    question_id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.product_id")
    user_id: int = Field(foreign_key="users.user_id")
    answer: Optional[str] = Field(default=None, sa_column=Column(Text))
    answered_by: Optional[int] = Field(default=None, foreign_key="users.user_id")
    is_public: bool = Field(default=False)
    answered_at: Optional[datetime] = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )

    user: Optional["User"] = Relationship(
        back_populates="product_questions",
        sa_relationship_kwargs={"foreign_keys": "ProductQuestion.user_id"}
    )
    product: Optional["Product"] = Relationship(back_populates="product_questions")
    answerer: Optional["User"] = Relationship(
        back_populates="answered_questions",
        sa_relationship_kwargs={"foreign_keys": "ProductQuestion.answered_by"}
    )

class ProductQuestionResponse(ProductQuestionBase):
    question_id: int
    product_id: int
    user_id: int
    answer: Optional[str] = None
    answered_by: Optional[int] = None
    is_public: bool
    answered_at: Optional[datetime] = None
    created_at: datetime
    user: Optional[dict] = None
    answerer: Optional[dict] = None

class ProductQuestionCreate(SQLModel):
    product_id: int
    question: str = Field(min_length=10, max_length=1000)

class ProductQuestionAnswer(SQLModel):
    answer: str = Field(min_length=10, max_length=2000)

class ProductQuestionUpdate(SQLModel):
    answer: Optional[str] = None
    answered_by: Optional[int] = None
    is_public: Optional[bool] = None
    answered_at: Optional[datetime] = None