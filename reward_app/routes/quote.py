from fastapi import APIRouter, Depends, Form
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from reward_app.database.async_db import get_async_session
import bcrypt

from sqlalchemy import select, insert, update, delete, func, between, and_, text

from reward_app.models.quote_model import Quote, QuoteLike
from reward_app.utils.common import make_page_info
from reward_app.core.config import make_resp
from reward_app.core.security import get_current_user

from reward_app.utils.params import LikeYn

router = APIRouter()

@router.post("/list", name="명언리스트")
async def list(
    page: int = Form(default=1, ge=1)
    , size: int = Form(default=20, ge=1)
    , db: AsyncSession = Depends(get_async_session)
    , current_user = Depends(get_current_user)):
    # list = await db.execute(select(Notice).where(Notice.user_email==email))
    user_seq = current_user.get('user_seq')
    offset = (page - 1) * size   


    from_qry = """
        FROM
            PC_QUOTE q
            LEFT JOIN PC_QUOTE_LIKE ql ON ql.quote_seq = q.quote_seq AND ql.user_seq=:user_seq            
        WHERE
            q.del_yn = 'N'
    """

    cnt_qry = f"""
        SELECT count(*) cnt
        {from_qry}
    """
    qry = f"""
        SELECT q.quote_seq, q.person_name, q.content
        , CASE 
            WHEN ql.user_seq IS NOT NULL AND ql.user_seq <> '' THEN 'Y'
            ELSE 'N'
        END AS is_like
        {from_qry}
    """
    
    total_results = await db.execute(text(cnt_qry), {'user_seq':user_seq})
    total_count = total_results.scalar() or 0  # 전체 데이터 개수

    page_info = make_page_info(total_count, page, size)    
    qry = qry + f" ORDER BY q.quote_seq DESC LIMIT {offset}, {size}"
    paged_results = await db.execute(text(qry), {'user_seq':user_seq})

    list = [dict(row) for row in paged_results.mappings()]

    return make_resp("S",{"page_info": page_info, "list":list, })


@router.post("/quote_like", name="명언 좋아요/해제")
async def quote_like(
    quote_seq: int =Form(title="명언번호",description="명언번호")
    , like_yn: LikeYn =Form(title="",description="좋아요 하기 Y 취소 N")
    , db: AsyncSession = Depends(get_async_session)
    , current_user = Depends(get_current_user), 
):
    user_seq = current_user.get('user_seq')

    # 퀴즈가 존재하고 유효기간안에 있는지 확인인
    stmt = select(Quote).where(and_(
        Quote.quote_seq == quote_seq,
        Quote.del_yn == 'N'
    ))
    
    
    r = await db.execute(stmt)
    quote = r.scalars().first()
    

    if quote is None:
        return make_resp("E1000")

    # 기존 제출한 내역이 있는지 확인
    stmt = select(QuoteLike).where(and_(
        QuoteLike.quote_seq == quote_seq,
        QuoteLike.user_seq == user_seq,
    ))

    r = await db.execute(stmt)
    quote_like = r.scalars().first() 
        
    result = False
    if like_yn == "Y" and quote_like is not None:
        return make_resp("S", {"msg":"이미 좋아요 상태"})
    if like_yn == "Y" and quote_like is None:
        stmt = insert(QuoteLike).values(
            quote_seq=quote_seq,
            user_seq=user_seq,
        )
        result = await db.execute(stmt)

    if like_yn == "N" and quote_like is None:
        return make_resp("S", {"msg":"이미 삭제된 상태"})
    if like_yn == "N" and quote_like is not None:
        stmt = delete(QuoteLike).where(
            and_(
                QuoteLike.quote_seq==quote_seq,
                QuoteLike.user_seq==user_seq,
            )
        )
        result = await db.execute(stmt)

    await db.commit()     
    if result:
        return make_resp("S")
    else:
        return make_resp("E0")