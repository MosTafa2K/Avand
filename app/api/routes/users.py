from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import CurrentUser, DBSession
from app.schemas.common import Page
from app.schemas.user import UserRead, UserUpdate
from app.services.users import UserService

router = APIRouter()


@router.get("/me", response_model=UserRead)
async def me(user: CurrentUser) -> UserRead:
    return user


@router.get("", response_model=Page[UserRead])
async def list_users(
    db: DBSession,
    _: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=100),
):
    items, total = await UserService(db).list(page, size, search)
    return Page(items=items, total=total, page=page, size=size)


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: UUID, db: DBSession, _: CurrentUser):
    user = await UserService(db).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(user_id: UUID, data: UserUpdate, db: DBSession, current: CurrentUser):
    if current.id != user_id and current.role != "admin":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    user = await UserService(db).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return await UserService(db).update(user, data)
