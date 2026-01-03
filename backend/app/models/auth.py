from typing import Optional, List
from datetime import date
from pydantic import BaseModel, EmailStr, Field


class TokenUser(BaseModel):
    user_id: int
    email: EmailStr
    full_name: str
    role_id: int
    role_name: str
    permissions: List[str] = []


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str
    user: TokenUser
    

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=40)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=40)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: Optional[date] = None


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


class EmailVerificationRequest(BaseModel):
    token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str