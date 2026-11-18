from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booth import Booth
from app.models.vendor import Vendor
from app.repositories.booths import BoothRepository
from app.repositories.vendors import VendorRepository
from app.schemas.booth import BoothCreate, BoothUpdate


class BoothService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.booths = BoothRepository(session)
        self.vendors = VendorRepository(session)

    async def create(self, user_id: UUID, data: BoothCreate) -> Booth:
        if await self.booths.get_by_slug(data.slug):
            raise ConflictError("A booth with this slug already exists")

        try:
            vendor = await self.vendors.get_by_user_id(user_id)

            if vendor is None:
                vendor = await self.vendors.add(Vendor(user_id=user_id))

            booth = await self.booths.add(
                Booth(
                    vendor_id=vendor.id,
                    name=data.name,
                    slug=data.slug,
                    description=data.description,
                )
            )

            await self.session.commit()
            await self.session.refresh(booth)
            return booth

        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("A booth with this slug already exists") from exc

    async def get(self, booth_id: UUID) -> Booth | None:
        booth = await self.booths.get(booth_id)

        if booth is None:
            return None
        if not booth.is_active:
            return False

        return booth

    async def list_booth(self, page: int, size: int, active_only: bool) -> tuple[list[Booth], int]:
        return await self.booths.list_(page, size, active_only=active_only)

    async def list_mine(self, user_id: UUID, page: int, size: int) -> tuple[list[Booth], int]:
        vendor = await self.vendors.get_by_user_id(user_id)

        if vendor is None:
            return [], 0

        return await self.booths.list_(
            page=page,
            size=size,
            vendor_id=vendor.id,
            active_only=False,
        )

    async def update(
        self,
        booth_id: UUID,
        user_id: UUID,
        data: BoothUpdate,
    ) -> Booth | None:
        booth = await self.booths.get(booth_id)

        if booth is None:
            return None

        vendor = await self.vendors.get_by_user_id(user_id)

        if vendor is None or booth.vendor_id != vendor.id:
            raise PermissionError("You do not own this booth")

        updates = data.model_dump(exclude_unset=True)

        if "slug" in updates and updates["slug"] != booth.slug:
            existing = await self.booths.get_by_slug(updates["slug"])
            if existing is not None:
                raise ConflictError("A booth with this slug already exists")

        for field, value in updates.items():
            if value is not None or field == "description":
                setattr(booth, field, value)

        try:
            await self.session.commit()
            await self.session.refresh(booth)
            return booth
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("A booth with this slug already exists") from exc

    async def delete(self, booth_id: UUID, user_id: UUID) -> None:
        booth = await self.booths.get(booth_id)

        if booth is None:
            return None

        vendor = await self.vendors.get_by_user_id(user_id)

        if vendor is None or booth.vendor_id != vendor.id:
            raise PermissionError("You do not own this booth")

        await self.booths.delete(booth_id)

class ConflictError(Exception):
    pass
