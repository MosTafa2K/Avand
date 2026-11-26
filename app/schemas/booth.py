from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator
from slugify import slugify


class BoothCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    slug: str | None = Field(
        default=None,
        min_length=2,
        max_length=140,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        json_schema_extra={"examples": ["my-awesome-booth"]},
    )
    description: str | None = None

    @model_validator(mode="after")
    def validate_slug(self):
        if not self.slug:
            self.slug = slugify(self.name)
        return self


class BoothUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    slug: str | None = Field(
        default=None,
        min_length=2,
        max_length=140,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        json_schema_extra={"examples": ["my-awesome-booth"]},
    )
    is_active: bool | None = None
    description: str | None = None


class BoothRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    description: str | None
    is_active: bool
    city: str
    created_at: datetime
    updated_at: datetime
