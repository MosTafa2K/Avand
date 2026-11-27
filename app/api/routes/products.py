from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DBSession
from app.schemas.common import Page
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services.booths import ConflictError
from app.services.products import ProductService

router = APIRouter()


@router.post(
    "/booths/{booth_id}",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    booth_id: UUID,
    data: ProductCreate,
    db: DBSession,
    user: CurrentUser,
):
    try:
        return await ProductService(db).create(user.id, booth_id, data)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except ConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get("", response_model=Page[ProductRead])
async def list_products(
    db: DBSession,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    booth_id: UUID | None = None,
    search: str | None = Query(None, max_length=100, description="Search for product with name"),
    min_rating: float | None = Query(None, ge=1, le=5),
    min_price: Decimal | None = Query(None, ge=0),  # noqa: B008
    max_price: Decimal | None = Query(None, ge=0),  # noqa: B008
    city: str | None = Query(None, min_length=2, max_length=100),
    sort_by: Literal["created_at", "price", "sales"] = Query("created_at"),
    sort_order: Literal["asc", "desc"] = Query("desc"),
):
    items, total = await ProductService(db).products_list(
        page=page,
        size=size,
        booth_id=booth_id,
        search=search,
        min_rating=min_rating,
        min_price=min_price,
        max_price=max_price,
        city=city,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return Page(items=items, total=total, page=page, size=size)


@router.get("/me/booths/{booth_id}", response_model=Page[ProductRead])
async def list_my_products(
    booth_id: UUID,
    db: DBSession,
    user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    try:
        items, total = await ProductService(db).list_mine(
            user_id=user.id,
            booth_id=booth_id,
            page=page,
            size=size,
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    return Page(items=items, total=total, page=page, size=size)


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(product_id: UUID, db: DBSession):
    product = await ProductService(db).get(product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product


@router.patch("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: UUID,
    data: ProductUpdate,
    db: DBSession,
    user: CurrentUser,
):
    try:
        product = await ProductService(db).update(product_id, user.id, data)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    db: DBSession,
    user: CurrentUser,
):
    try:
        deleted = await ProductService(db).delete(product_id, user.id)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
