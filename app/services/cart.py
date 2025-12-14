from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.products import Product as ProductModel
from app.models.cart_items import CartItem as CartItemModel


async def _ensure_product_available(db: AsyncSession, product_id: int) -> None:
    """
    Эта функция проверяет, что товар с указанным product_id существует в базе данных, активен (is_active == True) и доступен для добавления в корзину.
    Он ничего не возвращает, а обрабатывает ситуацию, если товар не найден или неактивен, то функция возвращает ошибку 404 (HTTPException).
    """
    result = await db.scalars(
        select(ProductModel).where(
            ProductModel.id == product_id,
            ProductModel.is_active == True,
        )
    )
    product = result.first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or inactive",
        )


async def _get_cart_item(
    db: AsyncSession, user_id: int, product_id: int
) -> CartItemModel | None:
    """
    Данная функция ищет товар в корзине текущего пользователя по product_id.
    В результате работы возвращает объект CartItemModel или None, если товар в корзине не найден.
    """
    result = await db.scalars(
        select(CartItemModel)
        .options(selectinload(CartItemModel.product))
        .where(
            CartItemModel.user_id == user_id,
            CartItemModel.product_id == product_id,
        )
    )
    return result.first()
