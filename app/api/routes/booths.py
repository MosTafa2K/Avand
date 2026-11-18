from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DBSession
from app.schemas.booth import BoothCreate, BoothRead, BoothUpdate
from app.schemas.common import Page
from app.services.booths import BoothService, ConflictError

router = APIRouter()


@router.get("", response_model=Page[BoothRead])
async def list_booths(
    db: DBSession,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    only_active: bool = Query(False),
):
    items, total = await BoothService(db).list_booth(page, size, only_active)
    return Page(items=items, total=total, page=page, size=size)


@router.get("/me", response_model=Page[BoothRead])
async def list_mine_booths(
    db: DBSession,
    user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    items, total = await BoothService(db).list_mine(user.id, page, size)
    return Page(items=items, total=total, page=page, size=size)


@router.post("", response_model=BoothRead)
async def create_booth(data: BoothCreate, db: DBSession, user: CurrentUser):
    try:
        return await BoothService(db).create(user_id=user.id, data=data)
    except ConflictError as ex:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(ex)) from ex


@router.get("/{booth_id}", response_model=BoothRead)
async def get_booth(
    booth_id: UUID,
    db: DBSession,
):
    booth = await BoothService(db).get(booth_id)

    if booth is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booth not found",
        )
    if not booth:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booth is not active!",
        )

    return booth


@router.patch("/{booth_id}", response_model=BoothRead)
async def update_booth(
    booth_id: UUID,
    data: BoothUpdate,
    db: DBSession,
    user: CurrentUser,
):
    try:
        booth = await BoothService(db).update(booth_id, user.id, data)
    except ConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    if booth is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booth not found",
        )

    return booth


@router.delete("/{booth_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_booth(db: DBSession, user: CurrentUser, booth_id: UUID):
    try:
        await BoothService(db).delete(booth_id, user.id)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
