from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.review import Review


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, product_id: UUID) -> Product | None:
        average_rating = self._average_rating_expression()
        result = await self.session.execute(
            select(Product, average_rating.label("average_rating")).where(Product.id == product_id)
        )
        row = result.one_or_none()
        if row is None:
            return None

        product, rating = row
        product.average_rating = float(rating or 0)
        return product

    @staticmethod
    def _average_rating_expression():
        return (
            select(func.avg(Review.rating))
            .where(Review.product_id == Product.id)
            .correlate(Product)
            .scalar_subquery()
        )

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
        min_rating: float | None = None,
    ):
        average_rating = self._average_rating_expression()
        query = select(Product, average_rating.label("average_rating"))
        count_query = select(func.count()).select_from(Product)

        conditions = []

        if booth_id is not None:
            conditions.append(Product.booth_id == booth_id)

        if active_only:
            conditions.append(Product.is_active.is_(True))

        if search:
            conditions.append(Product.name.ilike(f"%{search}%"))

        if min_rating is not None:
            conditions.append(func.coalesce(average_rating, 0) >= min_rating)

        if conditions:
            query = query.where(*conditions)
            count_query = count_query.where(*conditions)
        result = await self.session.execute(
            query.order_by(Product.created_at.desc()).offset((page - 1) * size).limit(size)
        )
        products = []
        for product, rating in result.all():
            product.average_rating = float(rating or 0)
            products.append(product)
        total = await self.session.scalar(count_query)

        return products, int(total or 0)

    async def delete(self, product: Product):
        await self.session.delete(product)
        await self.session.flush()
