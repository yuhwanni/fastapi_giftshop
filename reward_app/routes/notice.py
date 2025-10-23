from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.ext.asyncio import AsyncSession
from reward_app.database.async_db import get_async_session
import bcrypt

from sqlalchemy import select
from sqlalchemy import insert
from sqlalchemy import update
from sqlalchemy import func

from reward_app.models.notice_model import Notice
from reward_app.utils.common import make_page_info
from reward_app.core.config import make_resp
router = APIRouter()

@router.post("/list", name="공지리스트")
async def list(page: int = Query(1, ge=1), size: int = Query(20, ge=1), db: AsyncSession = Depends(get_async_session)):
    # list = await db.execute(select(Notice).where(Notice.user_email==email))
    result = True

    top_results = await db.execute(select(Notice).where(Notice.del_yn=="N").where(Notice.is_top=="Y").order_by(Notice.crt_date.desc()))
    top_list = [r._mapping for r in top_results.all()]
    
    offset = (page - 1) * size   
    # results = await db.execute(select(Notice).where(Notice.del_yn=="N").where(Notice.is_top=="N").order_by(Notice.crt_date.desc()).offset(offset).limit(size))

    # list = [r._mapping for r in results.all()]

    stmt = select(Notice).where(Notice.del_yn=="N").where(Notice.is_top=="N")
    total_results = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total_count = total_results.scalar() or 0  # 전체 데이터 개수

    page_info = make_page_info(total_count, page, size)    

    paged_results = await db.execute(
        stmt.order_by(Notice.crt_date.desc())
        .offset(offset)
        .limit(size)
    )

    list = []
    
    for r in paged_results.all():
        item = r.Notice.__dict__.copy()
        item.pop("_sa_instance_state", None)
        list.append(item)

    # list = [r._mapping for r in paged_results.all()]

    return make_resp("S", {"page_info": page_info,"top_list":top_list, "list":list, })

@router.post("/detail", name="공지 상세")
async def detail(notice_seq: int =Query(title="notice_seq",description="공지사항 notice_seq"), db: AsyncSession = Depends(get_async_session)):
    # list = await db.execute(select(Notice).where(Notice.user_email==email))
    result = True
    r = await db.execute(select(Notice).where(Notice.notice_seq==notice_seq))

    notice = r.scalars().first()
    
    return make_resp("S",{"data":notice})
