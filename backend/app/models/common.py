from pydantic import BaseModel

class Message(BaseModel):
    message: str

class PaginatedResponse(BaseModel):
    data: list
    total: int
    page: int
    size: int
    pages: int

class TokenPayload(BaseModel):
    sub: str | None = None
    type: str | None = None
    exp: int | None = None