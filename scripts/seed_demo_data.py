"""Seed three demo booths and one hundred products.

The seed is idempotent: running it again reuses the demo booths and products
instead of creating duplicates.
"""

from __future__ import annotations

import asyncio
import random
import sys
from decimal import Decimal
from pathlib import Path

from sqlalchemy import func, select

# Make the project importable when this file is run directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.security import hash_password
from app.db import session_factory
from app.models.booth import Booth
from app.models.product import Product
from app.models.user import User
from app.models.vendor import Vendor

SEED_EMAIL_PREFIX = "demo-vendor-"
BOOTH_SPECS = (
    ("demo-booth-1", "Demo Electronics", "فروشگاه نمونه لوازم الکترونیکی"),
    ("demo-booth-2", "Demo Home Goods", "فروشگاه نمونه لوازم خانه"),
    ("demo-booth-3", "Demo Office Supplies", "فروشگاه نمونه لوازم اداری"),
)


async def seed() -> None:
    rng = random.Random(20261126)

    async with session_factory() as session:
        booths: list[Booth] = []

        for index, (slug, name, description) in enumerate(BOOTH_SPECS, start=1):
            email = f"{SEED_EMAIL_PREFIX}{index}@example.com"
            user = await session.scalar(select(User).where(User.email == email))
            if user is None:
                user = User(
                    email=email,
                    full_name=f"Demo Vendor {index}",
                    hashed_password=hash_password("DemoPassword123!"),
                    role="vendor",
                )
                session.add(user)
                await session.flush()

            vendor = await session.scalar(select(Vendor).where(Vendor.user_id == user.id))
            if vendor is None:
                vendor = Vendor(user_id=user.id)
                session.add(vendor)
                await session.flush()

            booth = await session.scalar(select(Booth).where(Booth.slug == slug))
            if booth is None:
                booth = Booth(
                    vendor_id=vendor.id,
                    name=name,
                    slug=slug,
                    description=description,
                    is_active=True,
                )
                session.add(booth)
                await session.flush()
            booths.append(booth)

        for product_number in range(1, 101):
            name = f"Demo Product {product_number:03d}"
            booth = rng.choice(booths)
            product = await session.scalar(
                select(Product).where(
                    Product.name == name,
                    Product.booth_id.in_([booth.id for booth in booths]),
                )
            )
            if product is None:
                session.add(
                    Product(
                        booth_id=booth.id,
                        name=name,
                        description=f"Sample product {product_number:03d} for demo data",
                        price=Decimal(rng.randint(50, 500000)) / 100,
                        stock=rng.randint(0, 100),
                        is_active=True,
                    )
                )

        await session.commit()

        counts = []
        for booth in booths:
            counts.append(
                (
                    booth.name,
                    await session.scalar(
                        select(func.count(Product.id)).where(Product.booth_id == booth.id)
                    ),
                )
            )
        print("Seeded 3 demo booths and 100 demo products.")
        for booth_name, count in counts:
            print(f"{booth_name}: {count} products")


if __name__ == "__main__":
    asyncio.run(seed())
