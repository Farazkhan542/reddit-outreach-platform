import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import DB, Admin, Current
from app.models import Organization, RedditAccount, Role, User
from app.schemas import InviteIn, OrgOut, RedditAccountOut, UserOut

router = APIRouter(prefix="/org", tags=["org"])


@router.get("", response_model=OrgOut)
async def get_org(current: Current, db: DB):
    return await db.get(Organization, current.org_id)


@router.get("/members", response_model=list[UserOut])
async def list_members(current: Admin, db: DB):
    return (await db.scalars(select(User).where(User.org_id == current.org_id))).all()


@router.post("/members", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def invite_member(data: InviteIn, current: Admin, db: DB):
    """Adds a teammate to the org. They then connect their own Reddit account."""
    if data.role == Role.owner:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "cannot invite another owner")
    if await db.scalar(select(User).where(User.email == data.email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "email already registered")
    # TODO: send an invite email with a signup link instead of creating the user directly.
    user = User(org_id=current.org_id, email=data.email, role=data.role)
    db.add(user)
    await db.commit()
    return user


@router.delete("/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_member(user_id: uuid.UUID, current: Admin, db: DB):
    user = await db.scalar(select(User).where(User.id == user_id, User.org_id == current.org_id))
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if user.role == Role.owner:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "cannot deactivate the owner")
    user.is_active = False
    await db.commit()


@router.get("/reddit-accounts", response_model=list[RedditAccountOut])
async def list_reddit_accounts(current: Current, db: DB):
    query = select(RedditAccount).where(RedditAccount.org_id == current.org_id)
    if not current.is_admin:
        query = query.where(RedditAccount.user_id == current.user.id)
    return (await db.scalars(query)).all()
