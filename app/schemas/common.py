from pydantic import BaseModel, ConfigDict


class APIError(BaseModel):
    code: str
    message: str
    details: dict | None = None


class Page[T](BaseModel):
    model_config = ConfigDict(from_attributes=True)
    items: list[T]
    total: int
    page: int
    size: int
