from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from schemas.common import ORMBase


class RegisterTenantRequest(BaseModel):
    tenant_name: str = Field(min_length=2, max_length=200)
    admin_email: EmailStr
    admin_password: str = Field(min_length=8, max_length=128)
    admin_full_name: str | None = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class CurrentUserResponse(ORMBase):
    id: UUID
    tenant_id: UUID
    email: str
    full_name: str | None
    is_tenant_admin: bool
    tenant_name: str | None = None
