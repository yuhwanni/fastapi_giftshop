from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.ext.asyncio import AsyncSession
from reward_app.database.async_db import get_async_session
import bcrypt

from sqlalchemy import select, insert, update, delete, func, between, and_, text
from sqlalchemy.orm import selectinload

from reward_app.models.referral_model import Referral
from reward_app.utils.common import make_page_info
from reward_app.core.config import make_resp
from datetime import datetime

from reward_app.core.security import get_current_user

import json

router = APIRouter()

@router.post("/list", name="나를 추천한 친구 목록")
async def list(page: int = Query(1, ge=1), size: int = Query(20, ge=1), db: AsyncSession = Depends(get_async_session)
    , current_user = Depends(get_current_user), 
):
    # list = await db.execute(select(Notice).where(Notice.user_email==email))
    
    user_seq = current_user.get('user_seq')
    offset = (page - 1) * size   


    from_qry = """
        FROM
            PC_REFERRAL r
            LEFT JOIN PC_MEMBER m ON m.user_seq = r.referrer_user_seq
        WHERE
            r.del_yn = 'N' AND r.user_seq=:user_seq
    """

    cnt_qry = f"""
        SELECT count(*) cnt
        {from_qry}
    """
    qry = f"""
        SELECT r.referral_datetime, m.user_name
        {from_qry}
    """
    
    total_results = await db.execute(text(cnt_qry), {'user_seq':user_seq})
    total_count = total_results.scalar() or 0  # 전체 데이터 개수

    page_info = make_page_info(total_count, page, size)    
    qry = qry + f" ORDER BY r.referral_datetime DESC LIMIT {offset}, {size}"
    paged_results = await db.execute(text(qry), {'user_seq':user_seq})

    list = [dict(row) for row in paged_results.mappings()]

    return make_resp("S",{"page_info": page_info, "list":list, })