from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, user_id: UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        return await self.session.scalar(select(User).where(User.email == email.lower()))

    async def list(self, page: int, size: int, search: str | None = None) -> tuple[list[User], int]:
        query = select(User)
        count = select(func.count()).select_from(User)
        if search:
            term = f"%{search}%"
            condition = User.full_name.ilike(term) | User.email.ilike(term)
            query, count = query.where(condition), count.where(condition)
        result = await self.session.scalars(
            query.order_by(User.created_at.desc()).offset((page - 1) * size).limit(size)
        )
        return list(result), int(await self.session.scalar(count) or 0)

    async def add(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
