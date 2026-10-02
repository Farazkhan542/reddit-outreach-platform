import uuid
from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import Role, User

bearer = HTTPBearer(auto_error=False)

DB = Annotated[AsyncSession, Depends(get_db)]


@dataclass
class CurrentUser:
    """Identity from the JWT. `org_id` must scope every tenant query."""

    user: User
    org_id: uuid.UUID
    role: Role

    @property
    def is_admin(self) -> bool:
        return self.role in (Role.owner, Role.admin)


async def get_current_user(
    db: DB, creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]
) -> CurrentUser:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing bearer token")
    try:
        payload = decode_access_token(creds.credentials)
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid token") from None

    user = await db.get(User, uuid.UUID(payload["sub"]))
    if user is None or not user.is_active or str(user.org_id) != payload["org_id"]:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "user not found")
    return CurrentUser(user=user, org_id=user.org_id, role=user.role)


async def require_admin(current: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
    if not current.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "owner/admin only")
    return current


Current = Annotated[CurrentUser, Depends(get_current_user)]
Admin = Annotated[CurrentUser, Depends(require_admin)]
