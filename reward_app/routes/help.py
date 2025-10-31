from fastapi import APIRouter, Depends, HTTPException, status, Query, Form
from typing import Optional
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.ext.asyncio import AsyncSession
from reward_app.database.async_db import get_async_session
import bcrypt

from sqlalchemy import select, insert, update, delete, func, between, and_, text

from reward_app.models.help_model import Help
from reward_app.utils.common import make_page_info
from reward_app.core.config import make_resp
router = APIRouter()

@router.post("/list", name="도움말 리스트")
async def list(
    page: int = Form(default=1, ge=1)
    , size: int = Form(default=20, ge=1)
    , db: AsyncSession = Depends(get_async_session)):
    
    offset = (page - 1) * size   
    
    stmt = select(Help).where(and_(Help.del_yn=="N"))
    total_results = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total_count = total_results.scalar() or 0  # 전체 데이터 개수

    page_info = make_page_info(total_count, page, size)    

    paged_results = await db.execute(
        stmt.order_by(Help.crt_date.desc())
        .offset(offset)
        .limit(size)
    )

    list = []
    
    for r in paged_results.all():
        item = r.Help.__dict__.copy()
        item.pop("_sa_instance_state", None)
        list.append(item)

    # list = [r._mapping for r in paged_results.all()]

    return make_resp("S", {"page_info": page_info,"list":list, })

@router.post("/detail", name="도움말 상세")
async def detail(
    help_seq: int =Form(title="help_seq",description="도움말말 help_seq")
    , db: AsyncSession = Depends(get_async_session)):
    # list = await db.execute(select(Help).where(Help.user_email==email))
    result = True
    r = await db.execute(select(Help).where(Help.help_seq==help_seq))

    help = r.scalars().first()
    
    return make_resp("S",{"data":help})
