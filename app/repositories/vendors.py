from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vendor import Vendor


class VendorRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(self, user_id: UUID) -> Vendor | None:
        return await self.session.scalar(select(Vendor).where(Vendor.user_id == user_id))

    async def add(self, vendor: Vendor) -> Vendor:
        self.session.add(vendor)
        await self.session.flush()
        return vendor
