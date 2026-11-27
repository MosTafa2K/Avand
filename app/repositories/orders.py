from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem
from app.models.product import Product


class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_for_user(
        self,
        user_id: UUID,
        page: int,
        size: int,
        product_search: str | None = None,
    ) -> tuple[list[Order], int]:
        query = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.user_id == user_id)
        )
        count_query = select(func.count(func.distinct(Order.id))).select_from(Order)
        conditions = [Order.user_id == user_id]

        if product_search:
            conditions.append(Product.name.ilike(f"%{product_search}%"))
            query = query.join(OrderItem, OrderItem.order_id == Order.id).join(
                Product, Product.id == OrderItem.product_id
            )
            count_query = count_query.join(OrderItem, OrderItem.order_id == Order.id).join(
                Product, Product.id == OrderItem.product_id
            )

        query = query.where(*conditions).distinct()
        count_query = count_query.where(*conditions)
        orders = await self.session.scalars(
            query.order_by(Order.created_at.desc()).offset((page - 1) * size).limit(size)
        )
        total = await self.session.scalar(count_query)
        return list(orders), int(total or 0)
