from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booth import Booth


class BoothRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, booth_id: UUID) -> Booth | None:
        return await self.session.get(Booth, booth_id)

    async def get_by_slug(self, slug: str) -> Booth | None:
        return await self.session.scalar(select(Booth).where(Booth.slug == slug))

    async def add(self, booth: Booth) -> Booth:
        self.session.add(booth)
        await self.session.flush()
        return booth

    async def delete(self, booth_id: UUID):
        booth = await self.get(booth_id)
        if booth:
            await self.session.delete(booth)
            await self.session.flush()

    async def list_(
        self,
        page: int,
        size: int,
        vendor_id: UUID | None = None,
        active_only: bool = True,
    ) -> tuple[list[Booth], int]:
        query = select(Booth)
        count_query = select(func.count()).select_from(Booth)

        if vendor_id is not None:
            query = query.where(Booth.vendor_id == vendor_id)
            count_query = count_query.where(Booth.vendor_id == vendor_id)

        if active_only:
            query = query.where(Booth.is_active.is_(True))
            count_query = count_query.where(Booth.is_active.is_(True))

        result = await self.session.scalars(
            query.order_by(Booth.created_at.desc()).offset((page - 1) * size).limit(size)
        )

        total = await self.session.scalar(count_query)

        return list(result), int(total or 0)
