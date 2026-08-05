import re
import uuid

from sqlalchemy.orm import Session

from app.exceptions import AuthenticationError, ConflictError
from core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from models.tenant import Tenant
from models.user import User
from repositories.tenant_repo import TenantRepository
from repositories.user_repo import UserRepository
from services.audit_service import record_audit_event


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or str(uuid.uuid4())[:8]


def register_tenant(db: Session, *, tenant_name: str, admin_email: str, admin_password: str, admin_full_name: str | None) -> tuple[Tenant, User]:
    tenant_repo = TenantRepository(db)
    user_repo = UserRepository(db)

    base_code = _slugify(tenant_name)
    code = base_code
    suffix = 1
    while tenant_repo.get_by_code(code) is not None:
        suffix += 1
        code = f"{base_code}-{suffix}"

    tenant = Tenant(id=uuid.uuid4(), name=tenant_name, code=code)
    db.add(tenant)
    db.flush()

    if user_repo.get_by_email(tenant.id, admin_email.lower()) is not None:
        raise ConflictError("A user with this email already exists for this tenant.")

    admin = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email=admin_email.lower(),
        full_name=admin_full_name,
        password_hash=hash_password(admin_password),
        is_tenant_admin=True,
    )
    db.add(admin)
    db.commit()

    record_audit_event(db, tenant_id=tenant.id, user_id=admin.id, action="tenant.registered", resource_type="tenant", resource_id=str(tenant.id))
    return tenant, admin


def authenticate(db: Session, *, email: str, password: str) -> User:
    """
    Looks up the user by email across ALL tenants (a user only knows their
    own email, not their tenant code, at login time) - but every query
    after this point is strictly scoped to the tenant_id found here.
    """
    from sqlalchemy import select

    stmt = select(User).where(User.email == email.lower())
    user = db.execute(stmt).scalar_one_or_none()

    if user is None or not verify_password(password, user.password_hash):
        raise AuthenticationError("Invalid email or password.")
    if user.status != "active":
        raise AuthenticationError("This account is inactive.")

    record_audit_event(db, tenant_id=user.tenant_id, user_id=user.id, action="user.login")
    return user


def issue_tokens(user: User) -> dict:
    return {
        "access_token": create_access_token(user_id=user.id, tenant_id=user.tenant_id, is_admin=user.is_tenant_admin),
        "refresh_token": create_refresh_token(user_id=user.id, tenant_id=user.tenant_id, is_admin=user.is_tenant_admin),
        "token_type": "bearer",
    }


def refresh_access_token(db: Session, *, refresh_token: str) -> dict:
    payload = decode_token(refresh_token, expected_type="refresh")
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(uuid.UUID(payload["tenant_id"]), uuid.UUID(payload["sub"]))
    if user is None or user.status != "active":
        raise AuthenticationError("User account is inactive or no longer exists.")
    return issue_tokens(user)
