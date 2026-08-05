from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.tenant_context import get_current_user
from db.session import get_db
from models.user import User
from schemas.auth import (
    CurrentUserResponse,
    LoginRequest,
    RefreshRequest,
    RegisterTenantRequest,
    TokenResponse,
)
from services import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterTenantRequest, db: Session = Depends(get_db)):
    _tenant, admin = auth_service.register_tenant(
        db,
        tenant_name=payload.tenant_name,
        admin_email=payload.admin_email,
        admin_password=payload.admin_password,
        admin_full_name=payload.admin_full_name,
    )
    return auth_service.issue_tokens(admin)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = auth_service.authenticate(db, email=payload.email, password=payload.password)
    return auth_service.issue_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    return auth_service.refresh_access_token(db, refresh_token=payload.refresh_token)


@router.get("/me", response_model=CurrentUserResponse)
def me(user: User = Depends(get_current_user)):
    response = CurrentUserResponse.model_validate(user)
    response.tenant_name = user.tenant.name if user.tenant else None
    return response
