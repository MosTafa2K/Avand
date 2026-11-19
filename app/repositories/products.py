from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, product_id: UUID) -> Product | None:
        return await self.session.scalar(select(Product).where(Product.id == product_id))

    async def get_by_booth_and_name(self, booth_id: UUID, name: str) -> Product | None:
        return await self.session.scalar(
            select(Product).where(
                Product.booth_id == booth_id,
                Product.name == name,
            )
        )

    async def add(self, product: Product):
        self.session.add(product)
        await self.session.flush()
        return product

    async def list_(
        self,
        page: int,
        size: int,
        booth_id: UUID | None = None,
        active_only: bool = True,
        search: str | None = None,
    ):
        query = select(Product)
        count_query = select(func.count()).select_from(Product)

        conditions = []

        if booth_id is not None:
            conditions.append(Product.booth_id == booth_id)

        if active_only:
            conditions.append(Product.is_active.is_(True))

        if search:
            conditions.append(Product.name.ilike(f"%{search}%"))

        if conditions:
            query = query.where(*conditions)
            count_query = count_query.where(*conditions)
        result = await self.session.scalars(
            query.order_by(Product.created_at.desc()).offset((page - 1) * 10).limit(size)
        )
        total = await self.session.scalar(count_query)

        return list(result), int(total or 0)

    async def delete(self, product: Product):
        await self.session.delete(product)
        await self.session.flush()
