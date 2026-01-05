from typing import List
from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.review import (
    ProductQuestion,
    ProductQuestionCreate,
    ProductQuestionUpdate,
)

class CRUDProductQuestion(CRUDBase[ProductQuestion, ProductQuestionCreate, ProductQuestionUpdate]):

    async def get_by_product(
        self,
        *,
        db: AsyncSession,
        product_id: int,
        public_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[ProductQuestion]:
        statement = (
            select(ProductQuestion)
            .options(
                selectinload(ProductQuestion.user),
                selectinload(ProductQuestion.answerer)
            )
            .where(ProductQuestion.product_id == product_id)
        )
        
        if public_only:
            statement = statement.where(ProductQuestion.is_public == True)
        
        statement = statement.order_by(ProductQuestion.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(statement)
        return result.scalars().all()

    async def create_question(
        self,
        *,
        db: AsyncSession,
        user_id: int,
        product_id: int,
        question: str
    ) -> ProductQuestion:
        question_obj = ProductQuestion(
            user_id=user_id,
            product_id=product_id,
            question=question,
            is_public=False
        )
        
        db.add(question_obj)
        await db.commit()
        await db.refresh(question_obj)
        return question_obj

    async def answer_question(
        self,
        *,
        db: AsyncSession,
        question_id: int,
        answer: str,
        answered_by: int
    ) -> ProductQuestion:

        question = await self.get(db=db, id=question_id)
        if not question:
            raise ValueError("Question not found")
        
        question.answer = answer
        question.answered_by = answered_by
        question.answered_at = datetime.now(timezone(timedelta(hours=7)))
        question.is_public = True
        
        db.add(question)
        await db.commit()
        
        statement = (
            select(ProductQuestion)
            .options(
                selectinload(ProductQuestion.user),
                selectinload(ProductQuestion.answerer)
            )
            .where(ProductQuestion.question_id == question_id)
        )
        result = await db.execute(statement)
        return result.scalars().first()

    async def get_unanswered(
        self,
        *,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[ProductQuestion]:
        statement = (
            select(ProductQuestion)
            .options(
                selectinload(ProductQuestion.user),
                selectinload(ProductQuestion.product)
            )
            .where(ProductQuestion.answer == None)
            .order_by(ProductQuestion.created_at)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return result.scalars().all()
    

    async def get_by_user(
        self,
        *,
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[ProductQuestion]:
        statement = (
            select(ProductQuestion)
            .options(
                selectinload(ProductQuestion.product), 
                selectinload(ProductQuestion.answerer) 
            )
            .where(ProductQuestion.user_id == user_id)
            .order_by(ProductQuestion.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return result.scalars().all()

product_question = CRUDProductQuestion(ProductQuestion)