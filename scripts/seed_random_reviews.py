"""Add deterministic random reviews to the existing products."""

from __future__ import annotations

import asyncio
import random
import sys
from pathlib import Path

from sqlalchemy import select

# Make the project importable when this file is run directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db import session_factory
from app.models.product import Product
from app.models.review import Review
from app.models.user import User

COMMENTS = (
    "کیفیت محصول خیلی خوب بود و از خریدم راضی هستم.",
    "محصول مطابق توضیحات بود و بسته‌بندی مناسبی داشت.",
    "ارسال سریع انجام شد و محصول سالم به دستم رسید.",
    "ارزش خرید خوبی دارد و پیشنهادش می‌کنم.",
    "کیفیت قابل قبول است، اما می‌توانست بهتر باشد.",
    "تجربه خوبی بود و دوباره از این فروشگاه خرید می‌کنم.",
)


async def seed_reviews() -> None:
    rng = random.Random(20261126)

    async with session_factory() as session:
        products = list((await session.scalars(select(Product))).all())
        users = list((await session.scalars(select(User))).all())
        if not products:
            raise RuntimeError("No products found.")
        if not users:
            raise RuntimeError("No users found.")

        existing_reviews = await session.execute(select(Review.product_id, Review.user_id))
        existing_pairs = {tuple(row) for row in existing_reviews.all()}
        reviewed_products = {product_id for product_id, _ in existing_pairs}
        added = 0
        for product in products:
            if product.id in reviewed_products:
                continue
            available_users = [
                user for user in users if (product.id, user.id) not in existing_pairs
            ]
            rng.shuffle(available_users)
            review_count = rng.randint(1, min(3, len(available_users)))
            for user in available_users[:review_count]:
                session.add(
                    Review(
                        product_id=product.id,
                        user_id=user.id,
                        rating=rng.randint(1, 5),
                        comment=rng.choice(COMMENTS),
                    )
                )
                existing_pairs.add((product.id, user.id))
                added += 1
            reviewed_products.add(product.id)

        await session.commit()
        print(f"Added {added} random reviews for {len(products)} products.")


if __name__ == "__main__":
    asyncio.run(seed_reviews())
