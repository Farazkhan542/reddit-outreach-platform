from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import DB, Current
from app.core.config import get_settings
from app.core.security import create_access_token
from app.models import Organization, Role, TenantConfig, User
from app.schemas import DevLoginIn, TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/dev-login", response_model=TokenOut)
async def dev_login(data: DevLoginIn, db: DB):
    """Development-only login used until "Continue with Reddit" OAuth is wired up.

    New email + org_name -> creates an org with this user as owner.
    Existing email -> logs in (invited members use this after an owner invites them).
    """
    if not get_settings().is_dev:
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    user = await db.scalar(select(User).where(User.email == data.email))
    if user is None:
        if not data.org_name:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "unknown email; pass org_name to sign up")
        org = Organization(name=data.org_name)
        db.add(org)
        await db.flush()
        db.add(TenantConfig(org_id=org.id))
        user = User(org_id=org.id, email=data.email, role=Role.owner)
        db.add(user)
        await db.commit()

    return TokenOut(access_token=create_access_token(user.id, user.org_id, user.role.value))


@router.get("/me", response_model=UserOut)
async def me(current: Current):
    return current.user


@router.get("/reddit/login")
async def reddit_login():
    # TODO: redirect to https://www.reddit.com/api/v1/authorize with
    # scope="identity read submit privatemessages", duration=permanent, and a signed `state`.
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Reddit OAuth not enabled yet (awaiting API access)")


@router.get("/reddit/callback")
async def reddit_callback(code: str | None = None, state: str | None = None):
    # TODO: verify state, exchange code for tokens, fetch /api/v1/me, upsert User + RedditAccount
    # (tokens stored via core.security.encrypt_token), then issue our JWT.
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Reddit OAuth not enabled yet (awaiting API access)")
