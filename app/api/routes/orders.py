from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DBSession
from app.schemas.common import Page
from app.schemas.order import OrderRead
from app.services.orders import OrderService

router = APIRouter()


@router.get("", response_model=Page[OrderRead])
async def list_orders(
    db: DBSession,
    user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    product_search: str | None = Query(
        None, max_length=100, description="Find orders containing a product by name"
    ),
):
    items, total = await OrderService(db).list_for_user(
        user_id=user.id,
        page=page,
        size=size,
        product_search=product_search,
    )
    return Page(items=items, total=total, page=page, size=size)
