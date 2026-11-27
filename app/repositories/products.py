from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booth import Booth
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.review import Review


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, product_id: UUID) -> Product | None:
        ratings = self._ratings_subquery()
        sales = self._sales_subquery()
        result = await self.session.execute(
            select(
                Product,
                func.coalesce(ratings.c.average_rating, 0).label("average_rating"),
                func.coalesce(sales.c.sold_count, 0).label("sold_count"),
            )
            .outerjoin(ratings, ratings.c.product_id == Product.id)
            .outerjoin(sales, sales.c.product_id == Product.id)
            .where(Product.id == product_id)
        )
        row = result.one_or_none()
        if row is None:
            return None

        product, rating, sold = row
        product.average_rating = float(rating or 0)
        product.sold_count = int(sold or 0)
        return product

    @staticmethod
    def _ratings_subquery():
        return (
            select(
                Review.product_id,
                func.avg(Review.rating).label("average_rating"),
            )
            .group_by(Review.product_id)
            .subquery()
        )

    @staticmethod
    def _sales_subquery():
        return (
            select(
                OrderItem.product_id,
                func.sum(OrderItem.quantity).label("sold_count"),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .where(Order.status == "completed")
            .group_by(OrderItem.product_id)
            .subquery()
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
        ratings = self._ratings_subquery()
        sales = self._sales_subquery()
        average_rating = func.coalesce(ratings.c.average_rating, 0)
        sold_count = func.coalesce(sales.c.sold_count, 0)

        query = (
            select(
                Product,
                average_rating.label("average_rating"),
                sold_count.label("sold_count"),
            )
            .outerjoin(ratings, ratings.c.product_id == Product.id)
            .outerjoin(sales, sales.c.product_id == Product.id)
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
            conditions.append(average_rating >= min_rating)

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

        sort_expression = sort_expression.asc() if sort_order == "asc" else sort_expression.desc()

        result = await self.session.execute(
            query.order_by(sort_expression).offset((page - 1) * size).limit(size)
        )

        products = []

        for product, rating, sold in result.all():
            product.average_rating = float(rating or 0)
            product.sold_count = int(sold or 0)
            products.append(product)

        if min_rating is not None:
            count_query = count_query.outerjoin(
                ratings, ratings.c.product_id == Product.id
            )

        total = await self.session.scalar(count_query)

        return products, int(total or 0)

    async def delete(self, product: Product):
        await self.session.delete(product)
        await self.session.flush()
