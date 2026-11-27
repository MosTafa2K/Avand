from decimal import Decimal
from uuid import UUID

from sqlalchemy import Subquery, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booth import Booth
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.review import Review


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, product_id: UUID) -> Product | None:
        average_rating = self._average_rating_expression()
        sold_count = self._sold_count_expression()
        result = await self.session.execute(
            select(
                Product,
                average_rating.label("average_rating"),
                sold_count.label("sold_count"),
            ).where(Product.id == product_id)
        )
        row = result.one_or_none()
        if row is None:
            return None

        product, rating, sold = row
        product.average_rating = float(rating or 0)
        product.sold_count = int(sold or 0)
        return product

    @staticmethod
    def _average_rating_expression():
        return (
            select(func.avg(Review.rating))
            .where(Review.product_id == Product.id)
            .correlate(Product)
            .scalar_subquery()
        )

    @staticmethod
    def _sold_count_expression():
        return (
            select(func.coalesce(func.sum(OrderItem.quantity), 0))
            .join(Order, Order.id == OrderItem.order_id)
            .where(OrderItem.product_id == Product.id, Order.status == "completed")
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
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        city: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ):
        average_rating = self._average_rating_expression()
        sold_count = self._sold_count_expression()
        query = select(
            Product,
            average_rating.label("average_rating"),
            sold_count.label("sold_count"),
        )
        count_query = select(func.count()).select_from(Product)

        conditions = []

        if booth_id is not None:
            conditions.append(Product.booth_id == booth_id)

        if active_only:
            conditions.append(Product.is_active.is_(True))

        if search:
            search_pattern = f"%{search}%"
            conditions.append(
                Product.name.ilike(search_pattern) | Product.description.ilike(search_pattern)
            )

        if min_rating is not None:
            conditions.append(func.coalesce(average_rating, 0) >= min_rating)

        if min_price is not None:
            conditions.append(Product.price >= min_price)
        if max_price is not None:
            conditions.append(Product.price <= max_price)
        if city:
            conditions.append(Booth.city == city)
            query = query.join(Booth, Booth.id == Product.booth_id)
            count_query = count_query.join(Booth, Booth.id == Product.booth_id)

        if conditions:
            query = query.where(*conditions)
            count_query = count_query.where(*conditions)
        sort_expression = {
            "price": Product.price,
            "sales": sold_count,
            "created_at": Product.created_at,
        }.get(sort_by, Product.created_at)
        sort_expression = (
            sort_expression.asc() if sort_order == "asc" else sort_expression.desc()
        )
        result = await self.session.execute(
            query.order_by(sort_expression).offset((page - 1) * size).limit(size)
        )
        products = []
        for product, rating, sold in result.all():
            product.average_rating = float(rating or 0)
            product.sold_count = int(sold or 0)
            products.append(product)
        total = await self.session.scalar(count_query)

        return products, int(total or 0)

    async def delete(self, product: Product):
        await self.session.delete(product)
        await self.session.flush()
