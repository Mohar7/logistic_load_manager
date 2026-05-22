"""FastAPI auth dependencies.

- `oauth2_scheme` parses the `Authorization: Bearer <token>` header.
- `get_current_user` decodes the token and resolves the active user.
- `require_role(*roles)` is a factory for role-gated endpoints.

The auth flow is intentionally minimal: stateless JWT, no refresh tokens,
no token revocation list. That's fine for a portfolio demo — the patterns
on display are correct OAuth2-password-flow shapes, FastAPI dependency
chaining, and proper async DB access from inside dependencies.
"""

from __future__ import annotations

from collections.abc import Iterable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import JWTError, decode_access_token
from app.db.database import get_db
from app.db.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=True)


_CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Decode the bearer token and return the matching active `User`.

    Raises 401 on any failure mode (invalid token, missing user, inactive
    user). The error message is intentionally generic — we don't leak
    which check failed.
    """
    try:
        payload = decode_access_token(token)
    except JWTError as exc:
        raise _CREDENTIALS_EXC from exc

    username = payload.get("sub")
    if not username:
        raise _CREDENTIALS_EXC

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise _CREDENTIALS_EXC

    return user


def require_role(*allowed_roles: str):
    """Factory: dependency that 403s unless the user holds one of `roles`.

    Usage:
        @router.delete("/loads/{id}", dependencies=[Depends(require_role("admin"))])
        async def delete_load(...): ...
    """
    roles: tuple[str, ...] = tuple(allowed_roles)

    async def _check(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(roles)}",
            )
        return user

    return _check


def require_any_authenticated(user: User = Depends(get_current_user)) -> User:
    """Pass-through dependency — any logged-in active user is allowed.

    Exists as a named alias so route declarations read intentionally:
        Depends(require_any_authenticated)
    is clearer than passing `get_current_user` directly when the body
    doesn't otherwise need the user object.
    """
    return user


__all__: Iterable[str] = (
    "get_current_user",
    "oauth2_scheme",
    "require_any_authenticated",
    "require_role",
)
