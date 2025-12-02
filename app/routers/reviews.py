from fastapi import APIRouter, status, Depends, HTTPException
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db_depends import get_async_db
from app.auth import get_current_user
from app.models.reviews import Review as ReviewModel
from app.schemas import CreateReview
from app.schemas import Review as ReviewSchema
from app.models.users import User as UserModel
from app.models.products import Product as ProductModel
from app.services.reviews import update_product_rating

router = APIRouter(
    prefix="/reviews",
    tags=["reviews"],
)


@router.get("/", response_model=List[ReviewSchema], status_code=status.HTTP_200_OK)
async def get_reviews(db: AsyncSession = Depends(get_async_db)):
    result = await db.scalars(select(ReviewModel).where(ReviewModel.is_active == True))
    return result.all()


@router.post("/", response_model=ReviewSchema, status_code=status.HTTP_201_CREATED)
async def create_review(
    review: CreateReview,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    if current_user.role != "buyer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to perform this action",
        )
    stmt = await db.scalars(
        select(ReviewModel).where(
            ReviewModel.is_active == True,
            ReviewModel.user_id == current_user.id,
            ReviewModel.product_id == review.product_id,
        )
    )
    existing_review = stmt.first()
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Review already exists"
        )
    stmt = await db.scalars(
        select(ProductModel).where(
            ProductModel.is_active == True, ProductModel.id == review.product_id
        )
    )
    product = stmt.first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    new_review = ReviewModel(**review.model_dump(), user_id=current_user.id)
    db.add(new_review)
    await db.commit()
    await db.refresh(new_review)
    await update_product_rating(db, new_review.product_id)
    return new_review


@router.delete("/{review_id}", status_code=status.HTTP_202_ACCEPTED)
async def delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to perform this action",
        )
    stmt = await db.scalars(
        select(ReviewModel).where(
            ReviewModel.id == review_id, ReviewModel.is_active == True
        )
    )
    review = stmt.first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review does not exist"
        )
    review.is_active = False
    await db.commit()
    await update_product_rating(db, review.product_id)
    return {"message": "Review deleted"}
