from datetime import datetime, timezone, timedelta
from typing import Optional, List

from sqlmodel import Field, Relationship, SQLModel, Column, TIMESTAMP, Text
from sqlalchemy import text


class BannerSlideBase(SQLModel):
    title: str = Field(max_length=255)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    image_url: str = Field(max_length=500)
    mobile_image_url: Optional[str] = Field(default=None, max_length=500)
    link_url: Optional[str] = Field(default=None, max_length=500)
    button_text: Optional[str] = Field(default=None, max_length=100)
    display_order: int = Field(default=0)
    is_active: bool = Field(default=True)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    click_count: int = Field(default=0)


class BannerSlide(BannerSlideBase, table=True):
    __tablename__ = "banner_slides"

    banner_id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    )


class BannerSlideResponse(BannerSlideBase):
    banner_id: int
    created_at: datetime
    updated_at: datetime


class BannerSlideCreate(BannerSlideBase):
    pass


class BannerSlideUpdate(SQLModel):
    title: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    image_url: Optional[str] = Field(default=None, max_length=500)
    mobile_image_url: Optional[str] = Field(default=None, max_length=500)
    link_url: Optional[str] = Field(default=None, max_length=500)
    button_text: Optional[str] = Field(default=None, max_length=100)
    display_order: Optional[int] = None
    is_active: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class BannerSlidesResponse(SQLModel):
    data: List[BannerSlideResponse]
    count: int


class PageBase(SQLModel):
    title: str = Field(max_length=255)
    slug: str = Field(max_length=255, unique=True, index=True)
    content: Optional[str] = Field(default=None, sa_column=Column(Text))
    excerpt: Optional[str] = Field(default=None, sa_column=Column(Text))
    featured_image: Optional[str] = Field(default=None, max_length=500)
    meta_title: Optional[str] = Field(default=None, max_length=255)
    meta_description: Optional[str] = Field(default=None, sa_column=Column(Text))
    meta_keywords: Optional[str] = Field(default=None, max_length=500)
    is_published: bool = Field(default=False)
    template: Optional[str] = Field(default=None, max_length=100)


class Page(PageBase, table=True):
    __tablename__ = "pages"

    page_id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    )
    published_at: Optional[datetime] = None


class PageResponse(PageBase):
    page_id: int
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]


class PageCreate(PageBase):
    pass


class PageUpdate(SQLModel):
    title: Optional[str] = Field(default=None, max_length=255)
    slug: Optional[str] = Field(default=None, max_length=255)
    content: Optional[str] = None
    excerpt: Optional[str] = None
    featured_image: Optional[str] = Field(default=None, max_length=500)
    meta_title: Optional[str] = Field(default=None, max_length=255)
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = Field(default=None, max_length=500)
    is_published: Optional[bool] = None
    published_at: Optional[datetime] = None
    template: Optional[str] = Field(default=None, max_length=100)


class PagesResponse(SQLModel):
    data: List[PageResponse]
    count: int


class MenuBase(SQLModel):
    name: str = Field(max_length=100)
    location: Optional[str] = Field(default=None, max_length=50)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    is_active: bool = Field(default=True)


class Menu(MenuBase, table=True):
    __tablename__ = "menus"

    menu_id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )

    items: List["MenuItem"] = Relationship(back_populates="menu", cascade_delete=True)


class MenuResponse(MenuBase):
    menu_id: int
    created_at: datetime
    items: List["MenuItemResponse"] = []


class MenuCreate(MenuBase):
    pass


class MenuUpdate(SQLModel):
    name: Optional[str] = Field(default=None, max_length=100)
    location: Optional[str] = Field(default=None, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class MenusResponse(SQLModel):
    data: List[MenuResponse]
    count: int


class MenuItemBase(SQLModel):
    menu_id: int = Field(foreign_key="menus.menu_id")
    parent_item_id: Optional[int] = Field(default=None, foreign_key="menu_items.item_id")
    title: str = Field(max_length=100)
    url: Optional[str] = Field(default=None, max_length=500)
    target: str = Field(default="_self", max_length=20)
    icon: Optional[str] = Field(default=None, max_length=100)
    display_order: int = Field(default=0)
    is_active: bool = Field(default=True)


class MenuItem(MenuItemBase, table=True):
    __tablename__ = "menu_items"

    item_id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )

    menu: Optional["Menu"] = Relationship(back_populates="items")

    parent_item: Optional["MenuItem"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={
            "remote_side": "MenuItem.item_id",
            "foreign_keys": "[MenuItem.parent_item_id]"
        }
    )
    children: List["MenuItem"] = Relationship(
        back_populates="parent_item",
        sa_relationship_kwargs={
            "foreign_keys": "[MenuItem.parent_item_id]"
        }
    )


class MenuItemResponse(MenuItemBase):
    item_id: int
    created_at: datetime
    children: List["MenuItemResponse"] = []


class MenuItemCreate(MenuItemBase):
    pass


class MenuItemUpdate(SQLModel):
    parent_item_id: Optional[int] = None
    title: Optional[str] = Field(default=None, max_length=100)
    url: Optional[str] = Field(default=None, max_length=500)
    target: Optional[str] = Field(default=None, max_length=20)
    icon: Optional[str] = Field(default=None, max_length=100)
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class MenuItemsResponse(SQLModel):
    data: List[MenuItemResponse]
    count: int