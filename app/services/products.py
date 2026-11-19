from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.repositories.booths import BoothRepository
from app.repositories.products import ProductRepository
from app.repositories.vendors import VendorRepository
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.booths import ConflictError


class ProductService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.vendors = VendorRepository(session)
        self.booths = BoothRepository(session)
        self.products = ProductRepository(session)

    async def _check_ownership(self, booth_id: UUID, user_id: UUID) -> bool:
        booth = await self.booths.get(booth_id=booth_id)
        if booth is None:
            return False
        vendor = await self.vendors.get_by_user_id(user_id=user_id)

        return vendor is not None and booth.vendor_id == vendor.id

    async def create(self, user_id: UUID, booth_id: UUID, data: ProductCreate):
        if not await self._check_ownership(booth_id, user_id):
            raise PermissionError("Booth not found or You do not own it")
        if await self.products.get_by_booth_and_name(booth_id, data.name):
            raise ConflictError("A product with this name is already exists in this booth")
        product = Product(
            booth_id=booth_id,
            name=data.name,
            description=data.description,
            stock=data.stock,
            price=data.price,
        )
        try:
            self.session.add(product)
            await self.session.commit()
            await self.session.refresh(product)
            return product
        except IntegrityError:
            await self.session.rollback()
            raise

    async def get(self, product_id: UUID):
        product = await self.products.get(product_id)
        if product is None or not product.is_active:
            return None
        return product

    async def products_list(
        self,
        page: int,
        size: int,
        booth_id: UUID | None = None,
        active_only: bool = True,
        search: str | None = None,
    ):
        return await self.products.list_(
            page=page,
            size=size,
            booth_id=booth_id,
            active_only=active_only,
            search=search,
        )

    async def list_mine(self, page: int, size: int, booth_id: UUID, user_id: UUID):
        if not await self._check_ownership(booth_id, user_id):
            raise PermissionError("Booth not found or You do not own it")
        return await self.products.list_(
            page=page,
            size=size,
            booth_id=booth_id,
            active_only=False,
        )

    async def update(self, product_id: UUID, user_id: UUID, data: ProductUpdate):
        product = await self.products.get(product_id)
        if product is None:
            return None
        if not await self._check_ownership(product.booth_id, user_id):
            raise PermissionError("Booth not found You do not own it")
        updates_data = data.model_dump(exclude_unset=True, exclude_none=True)
        for field, value in updates_data.items():
            setattr(product, field, value)
        await self.session.commit()
        await self.session.refresh(product)

        return product

    async def delete(self, product_id: UUID, user_id: UUID):
        product = await self.products.get(product_id)
        if product is None:
            return None
        if not await self._check_ownership(product.booth_id, user_id):
            raise PermissionError("Booth not found You do not own it")
        await self.session.delete(product)
        await self.session.commit()
        return True
