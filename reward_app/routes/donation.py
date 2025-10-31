from fastapi import APIRouter, Depends, Form
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from reward_app.database.async_db import get_async_session
import bcrypt

from sqlalchemy import select, insert, update, delete, func, between, and_, text
from sqlalchemy.orm import selectinload

from reward_app.models.member_model import Member

from reward_app.models.donation_model import Donation
from reward_app.utils.common import make_page_info
from reward_app.core.config import make_resp
from datetime import datetime

from reward_app.core.security import get_current_user

import json

from reward_app.service.point_service import save_point, reduce_point

router = APIRouter()

@router.post("/list", name="기부 리스트")
async def list(
    page: int = Form(default=1, ge=1)
    , size: int = Form(default=20, ge=1)
    , db: AsyncSession = Depends(get_async_session)
    , current_user = Depends(get_current_user), 
):
    # list = await db.execute(select(Notice).where(Notice.user_email==email))
    
    user_seq = current_user.get('user_seq')
    offset = (page - 1) * size   

    stmt = select(Donation).where(and_(Donation.del_yn=="N",Donation.user_seq==user_seq))
    total_results = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total_count = total_results.scalar() or 0  # 전체 데이터 개수

    page_info = make_page_info(total_count, page, size)    

    paged_results = await db.execute(
        stmt.order_by(Donation.crt_date.desc())
        .offset(offset)
        .limit(size)
    )

    list = []
    
    for r in paged_results.all():
        item = r.Donation.__dict__.copy()
        item.pop("_sa_instance_state", None)
        list.append(item)

    # list = [r._mapping for r in paged_results.all()]

    return make_resp("S", {"page_info": page_info, "list":list, })


@router.post("/request/proc", name="기부신청")
async def request_proc(
    donation_point: int =Form(title="신청금액",description="신청금액", gt=0)
    , db: AsyncSession = Depends(get_async_session)
    , current_user = Depends(get_current_user), 
):    
    user_seq = current_user.get('user_seq')

    # 사용자 있는지 확인    
    result = await db.execute(select(Member).where(Member.user_seq==user_seq))
    member = result.scalar_one_or_none()
    if member is None:
        return make_resp("E900")
    # 남은 포인트와 신청금액 비교
    point = member.user_point

    if point < donation_point:
        return make_resp("E301")

    stmt = insert(Donation).values(
        user_seq=user_seq,
        donation_point=donation_point,
    ).returning(Donation.donation_seq)
    result = await db.execute(stmt)
    donation_seq = result.scalar()

    result2 = await reduce_point(db, user_seq, "기부신청", donation_point, "PC_DONATION", {"donation_seq": donation_seq}, "D")
    if donation_seq and result2:
        await db.commit()
        return make_resp("S")
    else:
        await db.rollback()
        return make_resp("E300")
