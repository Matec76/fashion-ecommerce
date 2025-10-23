from sqlmodel import SQLModel, Field


class Message(SQLModel):
    message: str


class Token(SQLModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


class TokenPayload(SQLModel):
    sub: str | None = None
    type: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)


class PasswordResetRequest(SQLModel):
    email: str = Field(max_length=255)


class EmailVerificationRequest(SQLModel):
    token: str