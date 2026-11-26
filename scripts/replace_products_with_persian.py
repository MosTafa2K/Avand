"""Replace all products with 100 Persian-named demo products."""

from __future__ import annotations

import asyncio
import random
import sys
from decimal import Decimal
from pathlib import Path

from sqlalchemy import delete, func, select

# Make the project importable when this file is run directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db import session_factory
from app.models.booth import Booth
from app.models.product import Product

BOOTH_SLUGS = ("demo-booth-1", "demo-booth-2", "demo-booth-3")
CATEGORIES = (
    "گوشی هوشمند",
    "لپ‌تاپ",
    "هدفون بی‌سیم",
    "کیف دستی",
    "کفش ورزشی",
    "چراغ مطالعه",
    "صندلی اداری",
    "ماگ سرامیکی",
    "کوله‌پشتی",
    "ساعت هوشمند",
)
VARIANTS = (
    "آبی",
    "مشکی",
    "سفید",
    "قرمز",
    "سبز",
    "طلایی",
    "نقره‌ای",
    "مدل حرفه‌ای",
    "مدل اقتصادی",
    "مدل ویژه",
)


async def replace_products() -> None:
    rng = random.Random(20261126)

    async with session_factory() as session:
        booths = list(
            (
                await session.scalars(
                    select(Booth).where(Booth.slug.in_(BOOTH_SLUGS))
                )
            ).all()
        )
        booths.sort(key=lambda booth: booth.slug)
        if len(booths) != len(BOOTH_SLUGS):
            raise RuntimeError("The three demo booths must exist before replacing products.")

        await session.execute(delete(Product))

        names = [f"{category} {variant}" for category in CATEGORIES for variant in VARIANTS]
        rng.shuffle(names)
        for name in names:
            session.add(
                Product(
                    booth_id=rng.choice(booths).id,
                    name=name,
                    description="محصول نمونه برای فروشگاه اینترنتی",
                    price=Decimal(rng.randint(5000, 500000)) / 100,
                    stock=rng.randint(0, 100),
                    is_active=True,
                )
            )

        await session.commit()

        print("All previous products were deleted and 100 Persian products were added.")
        for booth in booths:
            count = await session.scalar(
                select(func.count(Product.id)).where(Product.booth_id == booth.id)
            )
            print(f"{booth.name}: {count} products")


if __name__ == "__main__":
    asyncio.run(replace_products())
