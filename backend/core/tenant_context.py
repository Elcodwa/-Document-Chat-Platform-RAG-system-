import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.exceptions import AuthenticationError, AuthorizationError
from core.security import decode_token
from db.session import get_db
from models.user import User
from repositories.user_repo import UserRepository

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise AuthenticationError("Missing authentication token.")

    payload = decode_token(credentials.credentials, expected_type="access")
    user_id = uuid.UUID(payload["sub"])
    tenant_id = uuid.UUID(payload["tenant_id"])

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(tenant_id, user_id)
    if user is None or user.status != "active":
        raise AuthenticationError("User account is inactive or no longer exists.")

    # Defense in depth: even though the token was issued for this tenant,
    # re-check the user's row still belongs to it (covers the edge case of
    # a user being moved/deleted and a stale token still floating around).
    if user.tenant_id != tenant_id:
        raise AuthorizationError("Token tenant does not match user's tenant.")

    return user


def require_tenant_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_tenant_admin:
        raise AuthorizationError("This action requires a tenant administrator.")
    return user
