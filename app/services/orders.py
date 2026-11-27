from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.orders import OrderRepository


class OrderService:
    def __init__(self, session: AsyncSession):
        self.orders = OrderRepository(session)

    async def list_for_user(
        self,
        user_id: UUID,
        page: int,
        size: int,
        product_search: str | None = None,
    ):
        return await self.orders.list_for_user(user_id, page, size, product_search)
