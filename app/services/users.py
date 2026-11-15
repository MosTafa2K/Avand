from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User
from app.repositories.users import UserRepository
from app.schemas.user import UserCreate, UserUpdate


class ConflictError(Exception):
    pass


class UserService:
    def __init__(self, session: AsyncSession):
        self.repository = UserRepository(session)

    async def create(self, data: UserCreate) -> User:
        if await self.repository.get_by_email(str(data.email)):
            raise ConflictError("A user with this email already exists")
        return await self.repository.add(
            User(
                email=str(data.email).lower(),
                full_name=data.full_name,
                hashed_password=hash_password(data.password),
            )
        )

    async def get(self, user_id: UUID) -> User | None:
        return await self.repository.get(user_id)

    async def update(self, user: User, data: UserUpdate) -> User:
        if data.full_name is not None:
            user.full_name = data.full_name
        await self.repository.session.commit()
        await self.repository.session.refresh(user)
        return user

    async def list(self, page: int, size: int, search: str | None = None) -> tuple[list[User], int]:
        return await self.repository.list(page, size, search)
