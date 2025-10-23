from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.ext.asyncio import AsyncSession
from reward_app.database.async_db import get_async_session
import bcrypt

from sqlalchemy import select, insert, update, delete, func, between, and_, text
from sqlalchemy.orm import selectinload

from reward_app.models.member_model import Member

from reward_app.models.refund_model import Refund
from reward_app.utils.common import make_page_info
from reward_app.core.config import make_resp
from datetime import datetime

from reward_app.core.security import get_current_user

import json

from reward_app.service.point_service import save_point

router = APIRouter()

@router.post("/list", name="환급 리스트")
async def list(page: int = Query(1, ge=1), size: int = Query(20, ge=1), db: AsyncSession = Depends(get_async_session)
    , current_user = Depends(get_current_user), 
):
    # list = await db.execute(select(Notice).where(Notice.user_email==email))
    
    user_seq = current_user.get('user_seq')
    offset = (page - 1) * size   

    stmt = select(Refund).where(Refund.del_yn=="N")
    total_results = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total_count = total_results.scalar() or 0  # 전체 데이터 개수

    page_info = make_page_info(total_count, page, size)    

    paged_results = await db.execute(
        stmt.order_by(Refund.crt_date.desc())
        .offset(offset)
        .limit(size)
    )

    list = []
    
    for r in paged_results.all():
        item = r.Refund.__dict__.copy()
        item.pop("_sa_instance_state", None)
        list.append(item)

    # list = [r._mapping for r in paged_results.all()]

    return make_resp("S", {"page_info": page_info, "list":list, })


@router.post("/request/proc", name="환급신청")
async def last_list(
    refund_amount: int =Query(title="신청금액",description="신청금액")
    , bank_name: str =Query(title="은행명",description="은행명")
    , account_number: str =Query(title="계좌번호",description="계좌번호")
    , account_holder: str =Query(title="예금주",description="예금주")
    , db: AsyncSession = Depends(get_async_session)
    , current_user = Depends(get_current_user), 
):    
    user_seq = current_user.get('user_seq')

    # 사용자 있는지 확인    
    member = await db.execute(select(Member).where(Member.user_seq==user_seq))

    if member is None:
        return make_resp("E900")
    # 남은 포인트와 신청금액 비교
    point = member.point

    if point < refund_amount:
        return make_resp("E201")

    stmt = insert(Refund).values(
        refund_amount=refund_amount,
        bank_name=bank_name,
        account_number=account_number,
        user_account_holdername=account_holder,
    ).returning(Refund.refund_seq)
    result = await db.execute(stmt)
    refund_seq = result.scalar()

    result2 = await save_point(db, user_seq, "환급신청", refund_amount, "PC_REFUND", {"refund_seq": refund_seq}, "R")
    if refund_seq and result2:
        await db.commit()
        return make_resp("S")
    else:
        await db.rollback()
        return make_resp("E200")
