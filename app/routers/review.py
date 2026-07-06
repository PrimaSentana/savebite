from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.cloudinary import upload_review_photo
from app.core.deps import get_current_merchant, get_current_user
from app.crud.review import add_merchant_reply, create_review, get_review_by_transaction, get_reviews_by_merchant
from app.database import get_db
from app.models.merchants import Merchant
from app.models.review import Review
from app.models.transaction import Order, TransactionStatus
from app.models.user import User
from app.schemas.review import MerchantReplyCreate, ReviewCreate, ReviewResponse

router = APIRouter(prefix="/reviews", tags=["Reviews"])

ALLOWED_TYPES = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
MAX_SIZE = 5 * 1024 * 1024

#user review
@router.post("/", status_code=201)
async def create_review_endpoint(
    transaction_id: int = Form(...),
    rating: float = Form(...),
    comment: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    #cek transaksi dan punya user
    result = await db.execute(
        select(Order).where(
            Order.id == transaction_id,
            Order.user_id == current_user.id
        )
    )
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")
    
    if transaction.status != TransactionStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Berikan review jika transaksi berstatus 'completed'")
    
    existing = await get_review_by_transaction(db, transaction_id)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Review sudah diberikan pada transaksi ini"
        )
    
    if rating < 1.0 or rating > 5.0:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    review = await create_review(
        db,
        user_id = current_user.id, #change this if error
        merchant_id = transaction.merchant_id, #change this if error
        data=ReviewCreate(
            transaction_id=transaction_id,
            rating=rating,
            comment=comment
        )
    )
    
    if photo:
        file_bytes = await photo.read()
        if len(file_bytes) > MAX_SIZE:
            raise HTTPException(status_code=400, detail="File size max 5MB")
        
        photo_url = await upload_review_photo(file_bytes, review.id)
        review.photo_url = photo_url
        await db.commit()
        await db.refresh(review)
    return review

#get merchant review (user)
@router.get("/merchant/{merchant_id}", response_model=List[ReviewResponse])
async def get_merchant_reviews(
    merchant_id: int,
    db: AsyncSession = Depends(get_db)
):
    reviews = await get_reviews_by_merchant(db, merchant_id)

    return [
        {
            "id": review.id,
            "user_id": review.user_id,
            "merchant_id": review.merchant_id,
            "transaction_id": review.transaction_id,
            "rating": review.rating,
            "comment": review.comment,
            "photo_url": review.photo_url,
            "merchant_reply": review.merchant_reply,
            "replied_at": review.replied_at,
            "created_at": review.created_at,
            "updated_at": review.updated_at,
            "reviewer_username": review.user.username if review.user else None,
        }
        for review in reviews
    ]
    
@router.get("/check/{transaction_id}")
async def check_reviewed(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    review = await get_review_by_transaction(db, transaction_id)
    return {
        "is_reviewed": review is not None,
        "review_id": review.id if review else None
    }

# merchant reply
@router.post("/{review_id}/reply")
async def reply_to_review(
    review_id: int,
    data: MerchantReplyCreate,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Review).where(Review.id == review_id)
    )
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review tidak ditemukan")
    
    if review.merchant_id != current_merchant.id:
        raise HTTPException(status_code=403, detail="Tidak bisa membalas review ini")
    
    if review.merchant_reply:
        raise HTTPException(status_code=400, detail="Kamu sudah membalas review ini")
    
    review = await add_merchant_reply(db, review, data.reply)
    return {
        "message": "reply successfully"
    }