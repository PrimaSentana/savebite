from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.merchants import Merchant
from app.models.review import Review
from app.models.transaction import Order
from app.models.transaction_item import TransactionItem
from app.schemas.review import ReviewCreate

async def get_review_by_id(db: AsyncSession, review_id: int):
    result = await db.execute(
        select(Review)
        .where(Review.id == review_id)
        .options(
            selectinload(Review.user),
            selectinload(Review.transaction).selectinload(Order.items).selectinload(TransactionItem.menu)
        )
    )
    return result.scalar_one_or_none()

async def get_review_by_transaction(db: AsyncSession, transaction_id: int):
    result = await db.execute(
        select(Review).where(Review.transaction_id == transaction_id)
    )
    return result.scalar_one_or_none()

async def get_reviews_by_merchant(db: AsyncSession, merchant_id: int):
    result = await db.execute(
        select(Review)
        .where(Review.merchant_id == merchant_id)
        .options(
            selectinload(Review.user),
            selectinload(Review.transaction).selectinload(Order.items).selectinload(TransactionItem.menu)
        )
        .order_by(Review.created_at.desc())
    )
    return result.scalars().all()

async def create_review(
    db: AsyncSession,
    user_id: int,
    merchant_id: int,
    data: ReviewCreate
) -> Review:
    review = Review(
        user_id = user_id,
        merchant_id = merchant_id,
        transaction_id = data.transaction_id,
        rating = data.rating,
        comment = data.comment
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    await _update_merchant_rating(db, merchant_id)
    return review

async def add_merchant_reply(
    db: AsyncSession,
    review: Review,
    reply: str,
) -> Review:
    review.merchant_reply = reply
    review.replied_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(review)
    return review

async def _update_merchant_rating(db: AsyncSession, merchant_id: int):
    result = await db.execute(
        select(
            func.avg(Review.rating).label("avg_rating"),
            func.count(Review.id).label("review_count")
        )
        .where(Review.merchant_id == merchant_id)
    )
    row = result.one()
    
    merchant_result = await db.execute(
        select(Merchant).where(Merchant.id == merchant_id)
    )
    merchant = merchant_result.scalar_one_or_none()
    
    if merchant:
        merchant.average_rating = round(float(row.avg_rating), 1) if row.avg_rating else None
        merchant.review_count = row.review_count
        await db.commit()